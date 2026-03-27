"""Create the scheduling orchestrator as a new-style Foundry agent (visible in new UI)."""
import json
import requests
from azure.identity import DefaultAzureCredential

ENDPOINT = "https://ai-healthcare-foundry-jp-001.services.ai.azure.com/api/projects/ai-healthcare-foundry-j-project"
API_VERSION = "2025-05-01"

cred = DefaultAzureCredential()
token = cred.get_token("https://ai.azure.com/.default").token
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

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

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_available_appointments",
            "description": "Find available appointment slots at CommonSpirit Health. Searches GCP scheduling system via Google Cloud Run.",
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty": {"type": "string", "description": "Medical specialty (Cardiology, Orthopedics, etc.)"},
                    "location": {"type": "string", "description": "Hospital or clinic location"},
                    "provider_name": {"type": "string", "description": "Provider/doctor name"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment in the GCP scheduling system.",
            "parameters": {
                "type": "object",
                "properties": {"appointment_id": {"type": "string", "description": "Appointment ID (e.g., APT-001)"}},
                "required": ["appointment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rebook_appointment",
            "description": "Cancel old appointment and book a new one via GCP scheduling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_appointment_id": {"type": "string", "description": "Current appointment ID to cancel"},
                    "new_appointment_id": {"type": "string", "description": "New appointment ID to book"}
                },
                "required": ["old_appointment_id", "new_appointment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_appointments",
            "description": "Look up all appointments for a patient from GCP BigQuery.",
            "parameters": {
                "type": "object",
                "properties": {"patient_id": {"type": "string", "description": "Patient ID (e.g., PAT-001)"}},
                "required": ["patient_id"]
            }
        }
    }
]

# Step 1: List existing agents to see what's there
print("=== Listing existing agents ===")
r = requests.get(f"{ENDPOINT}/agents?api-version={API_VERSION}", headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    agents = data.get("data", data.get("value", []))
    for a in agents:
        name = a.get("name", "")
        aid = a.get("id", "")
        model = a.get("model", "")
        tcount = len(a.get("tools", []))
        print(f"  {aid} | {name} | model={model} | tools={tcount}")

# Step 2: Create new agent
print("\n=== Creating new-style agent: csh-scheduling-orchestrator ===")
agent_def = {
    "model": "gpt-5.4-mini",
    "name": "csh-scheduling-orchestrator",
    "instructions": INSTRUCTIONS,
    "tools": TOOLS,
    "temperature": 0.7,
    "metadata": {
        "description": "Cross-cloud scheduling orchestrator: Azure Foundry + GCP Cloud Run + BigQuery"
    }
}

r = requests.post(
    f"{ENDPOINT}/agents?api-version={API_VERSION}",
    headers=headers,
    json=agent_def,
)
print(f"  Status: {r.status_code}")
result = r.json()
if r.status_code in (200, 201):
    print(f"  Agent ID: {result.get('id')}")
    print(f"  Name: {result.get('name')}")
    print(f"  Model: {result.get('model')}")
    print(f"  Tools: {len(result.get('tools', []))}")
    print(f"\nAgent created successfully!")
else:
    print(f"  Error: {json.dumps(result, indent=2)}")
