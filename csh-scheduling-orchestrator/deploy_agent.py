"""Deploy the CSH Scheduling Orchestrator agent to Foundry using API key."""
import os
os.environ["PROJECT_CONNECTION_STRING"] = "eastus2.api.azureml.ms;2852c4f9-8fcc-47c1-8e96-c4142a9ae463;rg-healthcareai-demo-jp-001;ai-healthcare-foundry-j-project"

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = "https://ai-healthcare-foundry-jp-001.services.ai.azure.com/api/projects/ai-healthcare-foundry-j-project"

# Use DefaultAzureCredential (user is already az-logged in)
credential = DefaultAzureCredential()
client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

print("=== Listing Existing Agents ===")
try:
    for a in client.agents.list():
        print(f"  Name: {a.name} | Model: {getattr(a, 'model', '?')}")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== Creating csh-scheduling-orchestrator ===")
try:
    agent = client.agents.create_version(
        agent_name="csh-scheduling-orchestrator",
        body={
            "model": "gpt-5.4-mini",
            "name": "csh-scheduling-orchestrator",
            "description": "Cross-cloud scheduling orchestrator for CommonSpirit Health. Coordinates GCP scheduling agents from Azure AI Foundry.",
            "instructions": """You are the CommonSpirit Health (CSH) Scheduling Orchestrator Agent.
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
        }
    )
    print(f"  Created!")
    print(f"  Name: {agent.name}")
except Exception as e:
    print(f"  create_version Error: {e}")
    
    # Fallback: try create_agent via agents operations  
    print("\n  Trying alternative create method...")
    try:
        from azure.ai.agents import AgentsClient as AC2
        client2 = AC2(endpoint=PROJECT_ENDPOINT, credential=credential)
        agent = client2.create_agent(
            model="gpt-5.4-mini",
            name="csh-scheduling-orchestrator",
            instructions="You are the CSH Scheduling Orchestrator Agent for cross-cloud healthcare scheduling.",
        )
        print(f"  Created via AgentsClient! ID: {agent.id}")
    except Exception as e2:
        print(f"  AgentsClient Error: {e2}")
        import traceback
        traceback.print_exc()
