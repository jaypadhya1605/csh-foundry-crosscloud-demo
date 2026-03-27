"""
Event-Driven Headless Agent Demo
=================================
Demonstrates the event-driven workflow Murali asked for:
  1. Event arrives in Azure Storage Queue (simulating EHR/Pub-Sub/queue trigger)
  2. Processor picks up event automatically - NO human interaction
  3. Foundry agent is invoked headlessly
  4. Agent coordinates with GCP scheduling agent on Cloud Run
  5. GCP agent queries BigQuery and returns results
  6. All traces flow to Azure App Insights for cross-cloud observability

Usage:
  python event_driven_demo.py send     # Send sample scheduling events to the queue
  python event_driven_demo.py process  # Start headless processor (listens for events)
  python event_driven_demo.py demo     # Send events then process them (full demo)
"""
import sys
import json
import time
import base64
import httpx
from azure.storage.queue import QueueClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# --- Config ---
STORAGE_ACCOUNT = "stcshdemo2026"
STORAGE_KEY = ""  # Not used — RBAC auth via DefaultAzureCredential
QUEUE_NAME = "scheduling-events"
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

# --- Sample Events (simulating what would come from EHR/Pub-Sub/queue) ---
SAMPLE_EVENTS = [
    {
        "event_type": "scheduling_request",
        "source": "EHR_SYSTEM",
        "payload": {
            "request": "Find available Cardiology appointments at St. Luke Medical Center",
            "requester": "Nurse Station 3A",
            "priority": "normal",
        },
    },
    {
        "event_type": "cancellation_request",
        "source": "PATIENT_PORTAL",
        "payload": {
            "request": "Look up all appointments for patient P-1001 and tell me their status",
            "requester": "Patient Self-Service",
            "priority": "normal",
        },
    },
    {
        "event_type": "scheduling_request",
        "source": "CALL_CENTER",
        "payload": {
            "request": "Find available Orthopedics appointments this week",
            "requester": "Agent Sarah",
            "priority": "high",
        },
    },
]


def get_queue_client():
    return QueueClient(
        account_url=f"https://{STORAGE_ACCOUNT}.queue.core.windows.net",
        queue_name=QUEUE_NAME,
        credential=DefaultAzureCredential(),
    )


def ensure_queue():
    """Create the queue if it doesn't exist."""
    client = get_queue_client()
    try:
        client.create_queue()
    except Exception:
        pass  # Already exists
    return client


def send_events():
    """Send sample scheduling events to Azure Storage Queue."""
    print("=" * 60)
    print("SENDING SCHEDULING EVENTS TO QUEUE")
    print(f"  (Simulating events from EHR, Patient Portal, Call Center)")
    print("=" * 60)

    client = ensure_queue()
    for i, event in enumerate(SAMPLE_EVENTS, 1):
        msg = base64.b64encode(json.dumps(event).encode()).decode()
        client.send_message(msg)
        print(f"  [{i}/{len(SAMPLE_EVENTS)}] Sent: {event['event_type']} from {event['source']}")
        print(f"           \"{event['payload']['request'][:60]}\"")

    print(f"\n  {len(SAMPLE_EVENTS)} events sent to queue '{QUEUE_NAME}'")


def call_gcp_agent(action, params):
    """Route a tool call to the GCP Cloud Run scheduling agent."""
    print(f"       >> GCP call: action={action}")
    resp = httpx.post(GCP_URL, json={"action": action, "parameters": params}, timeout=30)
    if resp.status_code != 200:
        return json.dumps({"status": "error", "message": f"HTTP {resp.status_code}"})
    result = resp.json()
    count = result.get("count", "ok") if isinstance(result, dict) else len(result)
    print(f"       << GCP returned: {count}")
    return json.dumps(result)


def invoke_agent(query):
    """Invoke the Foundry agent headlessly with a query, handling tool calls."""
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)
    openai_client = project_client.get_openai_client()

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

    # Handle tool calls
    max_iterations = 5
    for _ in range(max_iterations):
        function_calls = [item for item in response.output if item.type == "function_call"]
        if not function_calls:
            break

        conversation = [{"role": "user", "content": query}]
        tool_outputs = []
        for fc in function_calls:
            args = json.loads(fc.arguments)
            action = ACTION_MAP.get(fc.name, fc.name)
            result = call_gcp_agent(action, args)
            tool_outputs.append({
                "type": "function_call_output",
                "call_id": fc.call_id,
                "output": result,
            })

        for fc in function_calls:
            conversation.append(fc)
        for to in tool_outputs:
            conversation.append(to)

        response = openai_client.responses.create(
            input=conversation,
            extra_body={
                "agent_reference": {
                    "name": AGENT_NAME,
                    "version": AGENT_VERSION,
                    "type": "agent_reference",
                }
            },
        )

    return response.output_text


def process_events():
    """Listen on queue and process events headlessly - no human interaction."""
    print("=" * 60)
    print("HEADLESS EVENT PROCESSOR - LISTENING FOR SCHEDULING EVENTS")
    print("=" * 60)
    print(f"  Queue:  {QUEUE_NAME} (Azure Storage Queue)")
    print(f"  Agent:  {AGENT_NAME} (Azure AI Foundry)")
    print(f"  GCP:    csh-scheduling-agent (Google Cloud Run)")
    print(f"  Data:   BigQuery (GCP)")
    print(f"  Traces: App Insights (Azure Monitor)")
    print()

    client = get_queue_client()
    event_num = 0

    while True:
        messages = client.receive_messages(messages_per_page=1, visibility_timeout=60)
        batch = list(messages)
        if not batch:
            break

        for msg in batch:
            event_num += 1
            body = json.loads(base64.b64decode(msg.content).decode())
            event_type = body.get("event_type", "unknown")
            source = body.get("source", "unknown")
            query = body["payload"]["request"]
            priority = body["payload"].get("priority", "normal")
            requester = body["payload"].get("requester", "unknown")

            print(f"\n{'='*60}")
            print(f"EVENT #{event_num}: {event_type}")
            print(f"  Source: {source} | Requester: {requester} | Priority: {priority}")
            print(f"  Request: \"{query}\"")
            print(f"{'='*60}")

            print(f"\n  [Invoking Foundry agent headlessly...]")
            start = time.time()
            response_text = invoke_agent(query)
            elapsed = time.time() - start

            print(f"\n  AGENT RESPONSE ({elapsed:.1f}s):")
            print(f"  {'-'*56}")
            for line in response_text.split("\n"):
                print(f"  {line}")
            print(f"  {'-'*56}")

            client.delete_message(msg)
            print(f"  [Event #{event_num} processed and acknowledged]")

    if event_num == 0:
        print("  No events in queue. Run 'python event_driven_demo.py send' first.")
    else:
        print(f"\n\n{'='*60}")
        print(f"HEADLESS PROCESSING COMPLETE: {event_num} events")
        print(f"{'='*60}")
        print(f"  Flow: Queue Event -> Foundry Agent -> GCP Agent -> BigQuery -> Response")
        print(f"  All operations traced in Azure App Insights")
        print(f"{'='*60}")


def demo():
    """Full demo: send events then process them."""
    send_events()
    print("\n")
    time.sleep(2)
    process_events()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python event_driven_demo.py [send|process|demo]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "send":
        send_events()
    elif cmd == "process":
        process_events()
    elif cmd == "demo":
        demo()
    else:
        print(f"Unknown command: {cmd}. Use send, process, or demo.")
