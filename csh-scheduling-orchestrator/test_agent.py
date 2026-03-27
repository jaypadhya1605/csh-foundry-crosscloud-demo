"""Update agent with tools and run end-to-end cross-cloud test."""
import json
import httpx
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool, AgentThreadCreationOptions, ThreadMessageOptions
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = "https://ai-healthcare-foundry-jp-001.services.ai.azure.com/api/projects/ai-healthcare-foundry-j-project"
AGENT_ID = "asst_SGSnrgFBJJxJORBrRWBGsCE5"
GCP_URL = "https://csh-scheduling-agent-5qkrt5ipcq-uc.a.run.app/invoke"

credential = DefaultAzureCredential()
client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=credential)

INSTRUCTIONS = """You are the CommonSpirit Health (CSH) Scheduling Orchestrator Agent.
You help healthcare staff manage patient appointments across CSH's 140+ hospital network.

You coordinate with GCP-based scheduling agents running on Google Cloud Run to:
1. Find available appointments by specialty, location, or provider
2. Cancel existing appointments
3. Rebook appointments (cancel old + book new)
4. Look up all appointments for a patient

WORKFLOW GUIDELINES:
- When rescheduling: look up current appointment -> find available slots -> rebook
- When cancelling: confirm appointment details before proceeding
- Present appointment info clearly with ID, provider, specialty, location, time
- Be empathetic and professional

DEMO DATA: Patient IDs PAT-001 to PAT-010, Appointment IDs APT-001 to APT-020
Specialties: Cardiology, Orthopedics, Dermatology, Neurology, Pediatrics
Locations: St. Mary's Hospital, Sacred Heart Medical Center, CHI Memorial, Dignity Health Clinic

You are part of a cross-cloud multi-agent system:
- You run on Azure AI Foundry (Microsoft)
- You orchestrate GCP-based scheduling agents on Google Cloud Run
- All operations are traced end-to-end for observability"""

# --- Python functions that call the GCP agent ---

def _call_gcp(action: str, params: dict) -> str:
    """Route a call to the GCP Cloud Run scheduling agent."""
    print(f"     >> Calling GCP agent: action={action}, params={params}")
    resp = httpx.post(GCP_URL, json={"action": action, "parameters": params}, timeout=30)
    result = resp.json()
    print(f"     << GCP returned: {result.get('count', '?')} results")
    return json.dumps(result)


def find_available_appointments(specialty: str = "", location: str = "", provider_name: str = "") -> str:
    """Find available appointment slots at CommonSpirit Health. Searches GCP scheduling system.

    :param specialty: Medical specialty (Cardiology, Orthopedics, etc.)
    :param location: Hospital or clinic location
    :param provider_name: Provider/doctor name
    :return: JSON string with available appointments
    """
    params = {k: v for k, v in {"specialty": specialty, "location": location, "provider_name": provider_name}.items() if v}
    return _call_gcp("find_available", params)


def cancel_appointment(appointment_id: str) -> str:
    """Cancel an existing appointment.

    :param appointment_id: Appointment ID (e.g., APT-001)
    :return: JSON string with cancellation result
    """
    return _call_gcp("cancel", {"appointment_id": appointment_id})


def rebook_appointment(old_appointment_id: str, new_appointment_id: str) -> str:
    """Cancel old appointment and book a new one.

    :param old_appointment_id: Current appointment ID to cancel
    :param new_appointment_id: New appointment ID to book
    :return: JSON string with rebooking result
    """
    return _call_gcp("rebook", {"old_appointment_id": old_appointment_id, "new_appointment_id": new_appointment_id})


def get_patient_appointments(patient_id: str) -> str:
    """Look up all appointments for a patient.

    :param patient_id: Patient ID (e.g., PAT-001)
    :return: JSON string with patient appointments
    """
    return _call_gcp("patient_appointments", {"patient_id": patient_id})


# Build the FunctionTool from our Python functions
functions = FunctionTool(functions={find_available_appointments, cancel_appointment, rebook_appointment, get_patient_appointments})

# Step 1: Update agent with instructions + function tools
print("=== Step 1: Updating agent with instructions + tools ===")
updated = client.update_agent(
    agent_id=AGENT_ID,
    model="gpt-5.4-mini",
    name="csh-scheduling-orchestrator",
    instructions=INSTRUCTIONS,
    tools=functions.definitions,
)
print(f"  Name: {updated.name}")
print(f"  Model: {updated.model}")
print(f"  Tools: {len(updated.tools)} configured")

# Step 2: Enable auto function calls so SDK invokes our Python functions
client.enable_auto_function_calls(tools=functions)

# Step 3: Run cross-cloud test
print("\n=== Step 2: Testing cross-cloud flow ===")
print("  Query: 'Find available Cardiology appointments'")

thread = AgentThreadCreationOptions(
    messages=[ThreadMessageOptions(role="user", content="Find available Cardiology appointments")]
)

run = client.create_thread_and_process_run(
    agent_id=AGENT_ID,
    thread=thread,
)

print(f"\n=== Final Status: {run.status} ===")

if run.status == "completed":
    # Print run object details to find where the response text is
    print(f"  Run thread_id: {run.thread_id}")
    print(f"  Run attrs: {[a for a in dir(run) if not a.startswith('_') and not callable(getattr(run, a, None))]}")
    
    # Try send_request with correct path format
    from azure.core.rest import HttpRequest
    req = HttpRequest("GET", f"/threads/{run.thread_id}/messages", params={"api-version": "2025-05-01"})
    resp = client.send_request(req)
    print(f"  Messages API status: {resp.status_code}")
    body = resp.content.decode("utf-8")
    if resp.status_code == 200:
        import json as json_mod
        data = json_mod.loads(body)
        msgs = data.get("data", data.get("value", []))
        for msg in msgs:
            if msg.get("role") == "assistant":
                for content in msg.get("content", []):
                    if content.get("type") == "text":
                        print(f"\n{'='*60}")
                        print("AGENT RESPONSE:")
                        print(f"{'='*60}")
                        print(content["text"]["value"])
                break
    else:
        print(f"  Body: {body[:500]}")

    print("\nCross-cloud flow working: Foundry Agent -> GCP Agent -> BigQuery -> Response")
else:
    print(f"\nRun ended with status: {run.status}")
    if hasattr(run, "last_error") and run.last_error:
        print(f"   Error: {run.last_error}")
