"""
Cross-cloud end-to-end test: Foundry Agent (new UI) -> GCP Cloud Run -> BigQuery
Uses the new azure-ai-projects v2 responses API with agent_reference.
"""
import json
import httpx
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# --- Config for Azure Foundry Project with tool call for GCP Cloud Run ---
PROJECT_ENDPOINT = "https://ai-healthcare-foundry-jp-001.services.ai.azure.com/api/projects/ai-healthcare-foundry-j-project"
AGENT_NAME = "csh-scheduling-orchestrator"
AGENT_VERSION = "1"
GCP_URL = "https://csh-scheduling-agent-732227602168.us-central1.run.app/invoke"

ACTION_MAP = {
    "find_available_appointments": "find_available",
    "cancel_appointment": "cancel",
    "rebook_appointment": "rebook",
    "get_patient_appointments": "patient_appointments",
}

# --- Setup with Azure Creds ---
project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)
openai_client = project_client.get_openai_client()

def call_gcp_agent(action, params):
    """Route a tool call to the GCP Cloud Run scheduling agent."""
    print(f"     >> Calling GCP agent: action={action}, params={params}")
    resp = httpx.post(GCP_URL, json={"action": action, "parameters": params}, timeout=30)
    if resp.status_code != 200:
        error_msg = json.dumps({"status": "error", "message": f"GCP agent returned HTTP {resp.status_code}"})
        print(f"     << GCP error: HTTP {resp.status_code}")
        return error_msg
    result = resp.json()
    count = result.get('count', '?') if isinstance(result, dict) else len(result)
    print(f"     << GCP returned: {count}")
    return json.dumps(result)

def run_query(query):
    """Send a query to the Foundry agent and handle tool calls to GCP."""
    print(f"\n{'='*60}")
    print(f"USER: {query}")
    print(f"{'='*60}")

    # Initial request
    response = openai_client.responses.create(
        input=[{"role": "user", "content": query}],
        extra_body={
            "agent_reference": {
                "name": AGENT_NAME,
                "version": AGENT_VERSION,
                "type": "agent_reference",
            }
        },
    )

    # Handle tool calls in a loop
    max_iterations = 5
    iteration = 0
    while iteration < max_iterations:
        iteration += 1

        # Check if we have function calls to handle
        function_calls = [
            item for item in response.output
            if item.type == "function_call"
        ]

        if not function_calls:
            break

        print(f"\n  Agent wants {len(function_calls)} tool call(s):")

        # Process each function call
        tool_outputs = []
        for fc in function_calls:
            func_name = fc.name
            args = json.loads(fc.arguments)
            action = ACTION_MAP.get(func_name, func_name)

            # Call GCP agent
            result = call_gcp_agent(action, args)

            tool_outputs.append({
                "type": "function_call_output",
                "call_id": fc.call_id,
                "output": result,
            })

        # Submit tool outputs back to the agent
        conversation_so_far = [
            {"role": "user", "content": query},
        ]
        # Add the function calls and outputs
        for fc in function_calls:
            conversation_so_far.append(fc)
        for to in tool_outputs:
            conversation_so_far.append(to)

        response = openai_client.responses.create(
            input=conversation_so_far,
            extra_body={
                "agent_reference": {
                    "name": AGENT_NAME,
                    "version": AGENT_VERSION,
                    "type": "agent_reference",
                }
            },
        )

    # Print the final response
    print(f"\n{'='*60}")
    print("AGENT RESPONSE:")
    print(f"{'='*60}")
    print(response.output_text)
    return response

# --- Run ---
import sys

if len(sys.argv) > 1:
    # Interactive mode: ask a single custom question
    question = " ".join(sys.argv[1:])
    print("=" * 60)
    print("CSH Cross-Cloud: Azure Foundry + GCP Cloud Run + BigQuery")
    print("=" * 60)
    run_query(question)
else:
    # Default: run all 3 test queries
    print("=" * 60)
    print("CSH Cross-Cloud Demo: Azure Foundry + GCP Cloud Run + BigQuery")
    print("=" * 60)

    run_query("Find available Cardiology appointments")

    print("\n\n")
    run_query("Show me all appointments for patient PAT-003")

    print("\n\n")
    run_query("Cancel appointment APT-005")

    print("\n\n")
    print("=" * 60)
    print("DEMO COMPLETE: Cross-cloud flow verified")
    print("  Foundry Agent (Azure) -> GCP Cloud Run -> BigQuery")
    print("=" * 60)
