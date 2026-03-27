"""
CSH Scheduling Orchestrator Agent — Azure AI Foundry (MAF)
Orchestrates healthcare scheduling workflows across Azure + GCP agents.
Calls the GCP Cloud Run scheduling agent for appointment operations.
Emits OpenTelemetry traces to Application Insights for cross-cloud observability.
"""

import asyncio
import os
import json
import logging
import httpx
from typing import Annotated
from dotenv import load_dotenv

load_dotenv(override=True)

from agent_framework import Agent
from agent_framework.azure import AzureAIAgentClient
from azure.ai.agentserver.agentframework import from_agent_framework
from azure.identity.aio import DefaultAzureCredential

# --- Config ---
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o")
GCP_AGENT_URL = os.getenv("GCP_AGENT_URL", "https://csh-scheduling-agent-5qkrt5ipcq-uc.a.run.app")

logger = logging.getLogger("csh-scheduling-orchestrator")
logging.basicConfig(level=logging.INFO)


# --- Tools that call the GCP Scheduling Agent ---

async def _call_gcp_agent(action: str, parameters: dict) -> dict:
    """Internal helper to call the GCP Cloud Run scheduling agent."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GCP_AGENT_URL}/invoke",
            json={"action": action, "parameters": parameters},
        )
        response.raise_for_status()
        return response.json()


def find_available_appointments(
    specialty: Annotated[str, "Medical specialty to search for (e.g., Cardiology, Orthopedics, Dermatology)"] = "",
    location: Annotated[str, "Hospital or clinic location to search in"] = "",
    provider_name: Annotated[str, "Provider/doctor name to search for"] = "",
) -> str:
    """
    Find available appointment slots at CommonSpirit Health facilities.
    Searches the GCP-based scheduling system for open appointments.
    Optionally filter by specialty, location, or provider name.
    """
    logger.info(f"[ORCHESTRATOR] Calling GCP agent: find_available | specialty={specialty}, location={location}")

    params = {}
    if specialty:
        params["specialty"] = specialty
    if location:
        params["location"] = location
    if provider_name:
        params["provider_name"] = provider_name

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_call_gcp_agent("find_available", params))

    count = result.get("count", 0)
    appointments = result.get("result", [])

    if count == 0:
        return f"No available appointments found for the given criteria (specialty: {specialty or 'any'}, location: {location or 'any'})."

    output = f"Found {count} available appointment(s):\n\n"
    for apt in appointments:
        output += f"**Appointment ID: {apt['appointment_id']}**\n"
        output += f"  Provider: {apt.get('provider_name', 'N/A')}\n"
        output += f"  Specialty: {apt.get('specialty', 'N/A')}\n"
        output += f"  Location: {apt.get('location', 'N/A')}\n"
        output += f"  Time: {apt.get('start_time', 'N/A')} to {apt.get('end_time', 'N/A')}\n\n"

    return output


def cancel_appointment(
    appointment_id: Annotated[str, "The appointment ID to cancel (e.g., APT-001)"],
) -> str:
    """
    Cancel an existing appointment at CommonSpirit Health.
    Calls the GCP scheduling agent to process the cancellation.
    """
    logger.info(f"[ORCHESTRATOR] Calling GCP agent: cancel | appointment_id={appointment_id}")

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_call_gcp_agent("cancel", {"appointment_id": appointment_id}))

    inner = result.get("result", {})
    status = inner.get("status", "unknown")

    if status == "success":
        apt = inner.get("cancelled_appointment", {})
        return (
            f"Appointment {appointment_id} has been successfully cancelled.\n"
            f"  Patient: {apt.get('patient_name', 'N/A')}\n"
            f"  Provider: {apt.get('provider_name', 'N/A')}\n"
            f"  Was scheduled: {apt.get('start_time', 'N/A')}"
        )
    else:
        return f"Could not cancel appointment {appointment_id}: {inner.get('message', 'Unknown error')}"


def rebook_appointment(
    old_appointment_id: Annotated[str, "The current appointment ID to cancel"],
    new_appointment_id: Annotated[str, "The new available appointment ID to book"],
) -> str:
    """
    Rebook a patient: cancel their existing appointment and book a new one.
    First cancels the old appointment, then books the new slot.
    """
    logger.info(f"[ORCHESTRATOR] Calling GCP agent: rebook | {old_appointment_id} -> {new_appointment_id}")

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        _call_gcp_agent("rebook", {
            "old_appointment_id": old_appointment_id,
            "new_appointment_id": new_appointment_id,
        })
    )

    inner = result.get("result", {})
    status = inner.get("status", "unknown")

    if status == "success":
        new_apt = inner.get("new_appointment", {})
        return (
            f"Successfully rebooked!\n"
            f"  Old appointment {old_appointment_id} cancelled.\n"
            f"  New appointment booked: {new_appointment_id}\n"
            f"  Provider: {new_apt.get('provider_name', 'N/A')}\n"
            f"  New time: {new_apt.get('start_time', 'N/A')}"
        )
    else:
        return f"Could not rebook: {inner.get('message', 'Unknown error')}"


def get_patient_appointments(
    patient_id: Annotated[str, "The patient ID to look up (e.g., PAT-001)"],
) -> str:
    """
    Look up all appointments for a specific patient.
    Returns their complete appointment history including booked, cancelled, and rescheduled.
    """
    logger.info(f"[ORCHESTRATOR] Calling GCP agent: patient_appointments | patient_id={patient_id}")

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        _call_gcp_agent("patient_appointments", {"patient_id": patient_id})
    )

    count = result.get("count", 0)
    appointments = result.get("result", [])

    if count == 0:
        return f"No appointments found for patient {patient_id}."

    output = f"Found {count} appointment(s) for patient {patient_id}:\n\n"
    for apt in appointments:
        status_emoji = {"booked": "✅", "cancelled": "❌", "available": "🟢", "rescheduled": "🔄", "no_show": "⚠️"}.get(apt.get("status", ""), "❓")
        output += f"{status_emoji} **{apt['appointment_id']}** — {apt.get('status', 'N/A').upper()}\n"
        output += f"  Provider: {apt.get('provider_name', 'N/A')} ({apt.get('specialty', 'N/A')})\n"
        output += f"  Location: {apt.get('location', 'N/A')}\n"
        output += f"  Time: {apt.get('start_time', 'N/A')}\n\n"

    return output


async def main():
    """Main function to run the orchestrator agent."""
    async with (
        DefaultAzureCredential() as credential,
        AzureAIAgentClient(
            project_endpoint=PROJECT_ENDPOINT,
            model_deployment_name=MODEL_DEPLOYMENT_NAME,
            credential=credential,
        ) as client,
    ):
        agent = Agent(
            client,
            name="CSHSchedulingOrchestrator",
            instructions="""You are the CommonSpirit Health (CSH) Scheduling Orchestrator Agent.
You help healthcare staff manage patient appointments across CSH's 140+ hospital network.

You have access to the following capabilities (powered by GCP-based scheduling agents):
1. **Find available appointments** — Search for open slots by specialty, location, or provider
2. **Cancel appointments** — Cancel existing patient appointments
3. **Rebook appointments** — Cancel an old appointment and book a new one in a single step
4. **Look up patient appointments** — View all appointments for a specific patient

WORKFLOW GUIDELINES:
- When a user wants to reschedule, first look up their current appointment, then find available slots, then rebook.
- When cancelling, confirm the appointment details before proceeding.
- Always present appointment information clearly with ID, provider, specialty, location, and time.
- Be empathetic and professional — these are real patient scheduling operations.
- If you find available slots for rebooking, present the options and ask which one the patient prefers.

DEMO DATA REFERENCE:
- Patient IDs: PAT-001 through PAT-010
- Appointment IDs: APT-001 through APT-020
- Specialties: Cardiology, Orthopedics, Dermatology, Neurology, Pediatrics
- Locations: St. Mary's Hospital, Sacred Heart Medical Center, CHI Memorial, Dignity Health Clinic

You are part of a cross-cloud multi-agent system:
- You run on Azure AI Foundry (Microsoft)
- You orchestrate GCP-based scheduling agents running on Google Cloud Run
- All operations are traced end-to-end for observability""",
            tools=[
                find_available_appointments,
                cancel_appointment,
                rebook_appointment,
                get_patient_appointments,
            ],
        )

        logger.info("CSH Scheduling Orchestrator Agent running on http://localhost:8088")
        server = from_agent_framework(agent)
        await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
