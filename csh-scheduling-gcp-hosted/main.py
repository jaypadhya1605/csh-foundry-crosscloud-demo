"""
CSH Scheduling GCP Agent — Foundry Hosted Agent
=================================================
This is the Foundry-hosted version of the GCP scheduling agent.
It implements the Foundry "responses" protocol via FoundryCBAgent.

When invoked, it:
1. Receives user queries via the Foundry responses API
2. Routes them to the real GCP Cloud Run endpoint (BigQuery backed)
3. Returns formatted results

Architecture:
  User → Foundry Hosted Agent (Azure ACA) → GCP Cloud Run → BigQuery

This gives you:
  - Governed agent in Foundry UI (versioned, RBAC, audit)
  - Real cross-cloud calls to GCP
  - OTel traces from both Azure and GCP sides
"""
import os
import json
import logging
import httpx
from azure.ai.agentserver.core import FoundryCBAgent, AgentRunContext
from azure.ai.agentserver.core.models.projects._models import (
    Response,
    ResponsesAssistantMessageItemResource,
    ItemContentOutputText,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("csh-scheduling-gcp-agent")

GCP_AGENT_URL = os.environ.get(
    "GCP_AGENT_URL",
    "https://csh-scheduling-agent-732227602168.us-central1.run.app/invoke",
)


class CSHSchedulingAgent(FoundryCBAgent):
    """Foundry hosted agent that proxies to the real GCP Cloud Run scheduling service."""

    async def agent_run(self, context: AgentRunContext) -> Response:
        """Handle an incoming request by routing to the GCP agent."""
        # Extract user input from the request
        raw = context.raw_payload or {}
        user_input = raw.get("input", "")

        # If input is a list of messages, extract the last user message
        if isinstance(user_input, list):
            for msg in reversed(user_input):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        user_input = " ".join(
                            p.get("text", "") for p in content if p.get("type") == "input_text"
                        )
                    else:
                        user_input = str(content)
                    break
            else:
                user_input = str(user_input)

        logger.info(f"Received query: {user_input[:100]}")

        # Parse the user input to determine action and params
        action, params = self._parse_intent(user_input)
        logger.info(f"Parsed action={action}, params={params}")

        # Call the real GCP Cloud Run agent
        result_text = await self._call_gcp_agent(action, params)

        # Build the Foundry response
        return Response(
            id=context.response_id,
            status="completed",
            output=[
                ResponsesAssistantMessageItemResource(
                    id=f"msg_{context.response_id}",
                    type="message",
                    role="assistant",
                    content=[
                        ItemContentOutputText(
                            text=result_text,
                            type="output_text",
                            annotations=[],
                        )
                    ],
                    status="completed",
                )
            ],
        )

    def _parse_intent(self, text: str) -> tuple:
        """Simple intent parser — maps natural language to GCP agent actions."""
        text_lower = text.lower()

        # Find available appointments
        if any(w in text_lower for w in ["find", "available", "search", "look for", "show me"]):
            params = {}
            specialties = ["cardiology", "orthopedics", "dermatology", "neurology", "pediatrics"]
            for s in specialties:
                if s in text_lower:
                    params["specialty"] = s.title()
                    break
            locations = [
                "st. mary", "sacred heart", "chi memorial", "dignity health",
                "st mary", "mary's", "marys",
            ]
            for loc in locations:
                if loc in text_lower:
                    params["location"] = loc
                    break
            return "find_available", params

        # Cancel appointment
        if "cancel" in text_lower:
            import re
            match = re.search(r"APT-\d+", text, re.IGNORECASE)
            if match:
                return "cancel", {"appointment_id": match.group(0).upper()}
            return "cancel", {}

        # Patient appointments
        if "patient" in text_lower or "p-" in text_lower:
            import re
            match = re.search(r"P-\d+", text, re.IGNORECASE)
            if match:
                return "patient_appointments", {"patient_id": match.group(0).upper()}
            return "patient_appointments", {}

        # Rebook
        if "rebook" in text_lower or "reschedule" in text_lower:
            import re
            matches = re.findall(r"APT-\d+", text, re.IGNORECASE)
            if len(matches) >= 2:
                return "rebook", {
                    "old_appointment_id": matches[0].upper(),
                    "new_appointment_id": matches[1].upper(),
                }
            return "rebook", {}

        # Default: find all available
        return "find_available", {}

    async def _call_gcp_agent(self, action: str, params: dict) -> str:
        """Call the real GCP Cloud Run scheduling agent."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    GCP_AGENT_URL,
                    json={"action": action, "parameters": params},
                    timeout=30,
                )
            if response.status_code != 200:
                return f"Error calling GCP agent: HTTP {response.status_code}"

            data = response.json()
            return self._format_result(action, data)

        except httpx.TimeoutException:
            return "GCP agent request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error calling GCP agent: {e}")
            return f"Error communicating with GCP scheduling service: {str(e)}"

    def _format_result(self, action: str, data: dict) -> str:
        """Format the GCP agent response into a readable string."""
        if action == "find_available":
            results = data.get("result", [])
            count = data.get("count", len(results))
            if count == 0:
                return "No available appointments found matching your criteria."
            lines = [f"Found {count} available appointment(s):\n"]
            for apt in results:
                lines.append(
                    f"  - {apt.get('appointment_id')}: {apt.get('specialty')} with "
                    f"{apt.get('provider_name')} at {apt.get('location')}, "
                    f"{apt.get('start_time')}"
                )
            return "\n".join(lines)

        elif action == "cancel":
            result = data.get("result", {})
            if result.get("status") == "success":
                return f"Successfully cancelled: {result.get('message')}"
            return f"Cancel failed: {result.get('message', 'Unknown error')}"

        elif action == "patient_appointments":
            results = data.get("result", [])
            count = data.get("count", len(results))
            if count == 0:
                return "No appointments found for this patient."
            lines = [f"Found {count} appointment(s):\n"]
            for apt in results:
                lines.append(
                    f"  - {apt.get('appointment_id')}: {apt.get('specialty')} with "
                    f"{apt.get('provider_name')}, status={apt.get('status')}, "
                    f"{apt.get('start_time')}"
                )
            return "\n".join(lines)

        elif action == "rebook":
            result = data.get("result", {})
            if result.get("status") == "success":
                return f"Successfully rebooked: {result.get('message')}"
            return f"Rebook failed: {result.get('message', 'Unknown error')}"

        return json.dumps(data, indent=2)


if __name__ == "__main__":
    agent = CSHSchedulingAgent()
    agent.run()
