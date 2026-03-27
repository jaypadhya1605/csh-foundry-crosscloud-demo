"""
Register the GCP Cloud Run Scheduling Agent in Azure AI Foundry (New UI / v2 API).

This creates the agent using the new `create_version` API so it appears
directly in the Operate → Assets → Agents view (not the classic agents page).

Governance benefits:
  - Visible in Foundry UI agent catalog (new nextgen portal)
  - Version-controlled with immutable versions
  - Access control via Foundry RBAC
  - Audit logs for every invocation
  - Part of the governed agent catalog alongside the orchestrator

Observability already flows via OTel → App Insights independently.
"""
import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool

PROJECT_ENDPOINT = "https://ai-healthcare-foundry-jp-001.services.ai.azure.com/api/projects/ai-healthcare-foundry-j-project"

AGENT_NAME = "csh-scheduling-gcp-agent"
MODEL = "gpt-5.4-mini"

INSTRUCTIONS = """You are the CommonSpirit Health (CSH) GCP Scheduling Agent.
You run on Google Cloud Run and are backed by BigQuery for appointment data.

CAPABILITIES:
1. find_available_appointments - Query BigQuery for open appointment slots by specialty, location, or provider
2. cancel_appointment - Cancel an existing appointment by ID (updates status in BigQuery)
3. rebook_appointment - Cancel old + book new appointment in one operation
4. get_patient_appointments - Look up all appointments for a given patient ID

DATA SOURCE: Google BigQuery dataset `demo_scheduling.appointments`
RUNTIME: Google Cloud Run (us-central1)
ENDPOINT: https://csh-scheduling-agent-732227602168.us-central1.run.app/invoke
OBSERVABILITY: OpenTelemetry traces exported to Azure App Insights via AzureMonitorTraceExporter

This agent is registered in Azure AI Foundry for governance purposes:
- Versioning and change tracking
- Access control via Foundry RBAC
- Audit logging of all invocations
- Cross-cloud agent catalog visibility

DEMO DATA:
- Patient IDs: P-1001 to P-1010
- Appointment IDs: APT-001 to APT-020
- Specialties: Cardiology, Orthopedics, Dermatology, Neurology, Pediatrics
- Locations: St. Mary's Hospital, Sacred Heart Medical Center, CHI Memorial, Dignity Health Clinic"""

TOOLS = [
    FunctionTool(
        name="find_available_appointments",
        description="Query BigQuery for available appointment slots at CommonSpirit Health facilities. Runs on GCP Cloud Run.",
        parameters={
            "type": "object",
            "properties": {
                "specialty": {"type": "string", "description": "Medical specialty (e.g., Cardiology, Orthopedics)"},
                "location": {"type": "string", "description": "Hospital or clinic name"},
                "provider_name": {"type": "string", "description": "Provider/doctor name"},
            },
            "required": [],
        },
        strict=False,
    ),
    FunctionTool(
        name="cancel_appointment",
        description="Cancel an appointment in BigQuery via GCP Cloud Run agent.",
        parameters={
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string", "description": "Appointment ID (e.g., APT-001)"}
            },
            "required": ["appointment_id"],
        },
        strict=False,
    ),
    FunctionTool(
        name="rebook_appointment",
        description="Cancel an old appointment and book a new one via GCP Cloud Run.",
        parameters={
            "type": "object",
            "properties": {
                "old_appointment_id": {"type": "string", "description": "Current appointment ID to cancel"},
                "new_appointment_id": {"type": "string", "description": "New appointment ID to book"},
            },
            "required": ["old_appointment_id", "new_appointment_id"],
        },
        strict=False,
    ),
    FunctionTool(
        name="get_patient_appointments",
        description="Look up all appointments for a patient from BigQuery via GCP Cloud Run.",
        parameters={
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "Patient ID (e.g., P-1001)"}
            },
            "required": ["patient_id"],
        },
        strict=False,
    ),
]


def main():
    print("=" * 60)
    print("  REGISTER GCP AGENT IN AZURE AI FOUNDRY (New UI / v2)")
    print("=" * 60)

    # Connect to Foundry project using the new v2 SDK
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    # Check if agent already exists
    print(f"\n  Checking if '{AGENT_NAME}' already exists...")
    try:
        existing = project_client.agents.get(agent_name=AGENT_NAME)
        print(f"  Agent '{AGENT_NAME}' already exists.")
        versions = list(project_client.agents.list_versions(agent_name=AGENT_NAME))
        print(f"  Existing versions: {len(versions)}")
        for v in versions:
            print(f"    Version {v.version}")
        print(f"\n  Creating a new version...")
    except Exception:
        print(f"  Agent '{AGENT_NAME}' does not exist yet. Creating...")

    # Create agent version using the new v2 API (PromptAgentDefinition)
    agent = project_client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=MODEL,
            instructions=INSTRUCTIONS,
            tools=TOOLS,
            temperature=0.3,
        ),
        description="GCP Cloud Run scheduling agent - BigQuery backed. Cross-cloud agent registered in Foundry for governance.",
        metadata={
            "cloud": "GCP",
            "runtime": "Cloud Run",
            "region": "us-central1",
            "data_source": "BigQuery",
            "endpoint": "https://csh-scheduling-agent-732227602168.us-central1.run.app/invoke",
            "observability": "OTel to Azure App Insights",
        },
    )

    print(f"\n  {'='*56}")
    print(f"  REGISTRATION SUCCESSFUL (New Foundry UI / v2 API)")
    print(f"  {'='*56}")
    print(f"  Agent Name:  {agent.name}")
    print(f"  Version:     {agent.version}")
    print(f"  Model:       {MODEL}")
    print(f"  Tools:       {len(TOOLS)} functions")
    print()
    print("  GOVERNANCE BENEFITS NOW ACTIVE:")
    print("    [x] Visible in Operate → Assets → Agents (new UI)")
    print("    [x] Immutable version created")
    print("    [x] Access control via Foundry RBAC")
    print("    [x] Audit logs for every invocation")
    print("    [x] OTel traces in App Insights (independent)")
    print()
    print("  AGENT CATALOG (both visible in new Foundry UI):")
    print("    - csh-scheduling-orchestrator  (Azure Foundry)")
    print(f"    - {AGENT_NAME}  (GCP Cloud Run)")
    print(f"  {'='*56}")


if __name__ == "__main__":
    main()
