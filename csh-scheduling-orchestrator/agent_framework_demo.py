"""
CSH Cross-Cloud Orchestrator — Microsoft Agent Framework Edition
=================================================================
Same demo as test_new_agent.py but built with the Microsoft Agent Framework SDK.
Shows Foundry as the multi-agent orchestration platform with code-first agents.

Architecture:
  User query → Agent Framework (local) → gpt-5.4-mini (Foundry) → tool calls → GCP Cloud Run → BigQuery

Usage:
  python agent_framework_demo.py
"""
import os
import json
import asyncio
import httpx
from typing import Annotated
from dotenv import load_dotenv
from agent_framework.azure import AzureAIClient
from azure.identity.aio import DefaultAzureCredential

load_dotenv(override=False)

# --- Config ---
PROJECT_ENDPOINT = os.getenv(
    "FOUNDRY_PROJECT_ENDPOINT",
    "https://ai-healthcare-foundry-jp-001.services.ai.azure.com/api/projects/ai-healthcare-foundry-j-project",
)
MODEL_DEPLOYMENT = os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-5.4-mini")
GCP_URL = "https://csh-scheduling-agent-732227602168.us-central1.run.app/invoke"

AGENT_INSTRUCTIONS = """You are the CommonSpirit Health scheduling orchestrator.
You coordinate appointment scheduling across the healthcare system.
When users ask about appointments, use the tools provided to query the scheduling system.
Always provide clear, helpful responses with the relevant appointment details.
You have access to BigQuery data through a GCP-hosted scheduling agent."""


# --- Tools (function calling routed to GCP Cloud Run) ---

def find_available_appointments(
    specialty: Annotated[str | None, "Medical specialty to filter by (e.g. Cardiology, Orthopedics)"] = None,
    location: Annotated[str | None, "Facility location to filter by"] = None,
    provider_name: Annotated[str | None, "Provider name to filter by"] = None,
) -> str:
    """Find available appointment slots in the scheduling system. Can filter by specialty, location, or provider."""
    params = {}
    if specialty:
        params["specialty"] = specialty
    if location:
        params["location"] = location
    if provider_name:
        params["provider_name"] = provider_name
    return _call_gcp_sync("find_available", params)


def get_patient_appointments(
    patient_id: Annotated[str, "The patient ID to look up (e.g. PAT-003)"],
) -> str:
    """Look up all appointments for a specific patient by their patient ID."""
    return _call_gcp_sync("patient_appointments", {"patient_id": patient_id})


def cancel_appointment(
    appointment_id: Annotated[str, "The appointment ID to cancel (e.g. APT-005)"],
) -> str:
    """Cancel an existing appointment by its appointment ID."""
    return _call_gcp_sync("cancel", {"appointment_id": appointment_id})


def rebook_appointment(
    old_appointment_id: Annotated[str, "The appointment ID to cancel"],
    new_appointment_id: Annotated[str, "The new appointment ID to book"],
) -> str:
    """Rebook: cancel an existing appointment and book a new one in its place."""
    return _call_gcp_sync("rebook", {
        "old_appointment_id": old_appointment_id,
        "new_appointment_id": new_appointment_id,
    })


def _call_gcp_sync(action: str, parameters: dict) -> str:
    """Call the GCP Cloud Run scheduling agent."""
    print(f"     >> [GCP Tool Call] action={action}, params={parameters}")
    try:
        resp = httpx.post(GCP_URL, json={"action": action, "parameters": parameters}, timeout=30)
        result = resp.json()
        count = result.get("count", "?") if isinstance(result, dict) else len(result)
        print(f"     << [GCP Response] count={count}")
        return json.dumps(result)
    except Exception as e:
        error = json.dumps({"status": "error", "message": str(e)})
        print(f"     << [GCP Error] {e}")
        return error


# --- Main demo ---

async def run_demo():
    print("=" * 70)
    print("  CSH Cross-Cloud Demo — Microsoft Agent Framework")
    print("  Foundry (gpt-5.4-mini) + GCP Cloud Run + BigQuery")
    print("=" * 70)

    queries = [
        "Find available Cardiology appointments",
        "Show me all appointments for patient PAT-003",
        "Cancel appointment APT-005",
    ]

    async with (
        DefaultAzureCredential() as credential,
        AzureAIClient(
            project_endpoint=PROJECT_ENDPOINT,
            model_deployment_name=MODEL_DEPLOYMENT,
            credential=credential,
        ).as_agent(
            name="csh-scheduling-orchestrator",
            instructions=AGENT_INSTRUCTIONS,
            tools=[
                find_available_appointments,
                get_patient_appointments,
                cancel_appointment,
                rebook_appointment,
            ],
        ) as agent,
    ):
        session = agent.create_session()

        for query in queries:
            print(f"\n{'='*70}")
            print(f"  USER: {query}")
            print(f"{'='*70}")

            print("\n  AGENT: ", end="", flush=True)
            stream = agent.run(query, session=session, stream=True)
            async for chunk in stream:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print("\n")
            await stream.get_final_response()

    print("\n" + "=" * 70)
    print("  DEMO COMPLETE — Agent Framework + Foundry + GCP")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_demo())
