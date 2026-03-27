# CSH Foundry Cross-Cloud Demo — Live Script
## March 27, 2026 | Jay Padhya | Microsoft Data & AI CSA

---

## PRE-DEMO CHECKLIST

- [ ] PowerPoint open: `CSH_Foundry_CrossCloud_Demo.pptx` (14 slides)
- [ ] VS Code open with workspace: `use case 1/`
- [ ] Terminal ready in `csh-scheduling-orchestrator/` directory
- [ ] Logged in: `az login` (Azure) + `gcloud auth login` (GCP)
- [ ] Browser tabs pre-loaded:
  - **GCP Cloud Run**: `https://console.cloud.google.com/run/detail/us-central1/csh-scheduling-agent/logs?project=project-b8139082-b506-40d6-89a`
  - **GCP BigQuery**: `https://console.cloud.google.com/bigquery?project=project-b8139082-b506-40d6-89a`
  - **GCP Cloud Trace**: `https://console.cloud.google.com/traces?project=project-b8139082-b506-40d6-89a`
  - **Azure Foundry**: `https://ai.azure.com` → project `ai-healthcare-foundry-j-project`

### Foundry Agent Versions
- **v1** = `csh-scheduling-orchestrator` version 1 → used in Part A (Foundry Platform)
- **v2** = `csh-scheduling-orchestrator` version 2 → used in Part B (Agent Framework)
- Both visible in Foundry → Tracing after demo

---

# PART A: FOUNDRY PLATFORM — Headless Multi-Agent Orchestration (30 min)

---

## SLIDE 1 — TITLE (stay 30 seconds)

> **Show**: Slide 1 — "CommonSpirit Health × Microsoft — Cross-Cloud Multi-Agent Orchestration"

**SAY**: "Murali, today I'm going to show you how Microsoft Foundry can act as a headless, cross-cloud orchestration and governance platform — plugging directly into your existing GCP workflows. No migration, no rip-and-replace. Your data stays in BigQuery, your agents stay on Cloud Run. Foundry governs them all."

**SAY**: "We have two parts. Part A: Foundry as the platform — headless, event-driven, governed. Part B: Microsoft Agent Framework — code-first, developer-owned. Let's start."

---

## SLIDE 2 — ARCHITECTURE OVERVIEW (1 min)

> **Show**: Slide 2 — Architecture diagram with GCP (left, green) and Azure (right, blue)

**SAY**: "Here's the architecture. On the left — your world. GCP Cloud Run running the scheduling agent, BigQuery with 20 appointment records, Gemini 2.5 Flash for natural language understanding. We didn't move any of this."

**SAY**: "On the right — Azure AI Foundry as the orchestration and governance layer. It has the agent, the model, the tracing, and the catalog. The two clouds talk via standard HTTPS — no proprietary connectors."

**POINT OUT**: "Notice the arrows — Foundry calls GCP, and GCP's OpenTelemetry traces flow back to Azure. Cross-cloud observability."

---

## SLIDE 3 — CROSS-CLOUD REQUEST FLOW (2 min)

> **Show**: Slide 3 — 8-step numbered flow diagram

**SAY**: "Let me walk you through what happens when someone asks a question."

**WALK THROUGH EACH NUMBER**:
1. "User types a question in VS Code — or this could be an API call from your EHR system"
2. "It hits Azure Foundry. GPT-4o-mini reads the question and reasons about what to do"
3. "Foundry decides: I need scheduling data. It selects the GCP agent tool"
4. "Cross-cloud call — HTTPS POST to your Cloud Run agent in us-central1"
5. "Cloud Run queries BigQuery — SELECT from appointments WHERE specialty = cardiology"
6. "BigQuery returns 2 results — APT-004 and APT-010"
7. "Data flows back to Foundry. GPT-4o-mini writes a friendly human response"
8. "User sees the answer. The whole thing took about 3 seconds."

**SAY**: "Every one of these 8 steps is traced — in Foundry AND in GCP Cloud Trace. Let me prove it live."

---

## SLIDE 4 — PART A HEADER (stay 10 seconds)

> **Show**: Slide 4 — "Part A: Foundry Platform — Headless Multi-Agent Orchestration & Governance"

**SAY**: "Let's go live."

---

## LIVE DEMO A.1 — GCP Agent Standalone with Gemini (5 min)

> **Switch to**: VS Code Terminal

### Command 1 — Health Check

```powershell
python -c "import requests,json; r=requests.get('https://csh-scheduling-agent-732227602168.us-central1.run.app/health'); print(json.dumps(r.json(), indent=2))"
```

**SAY**: "First, let me show you what's running on GCP. This is your scheduling agent — Cloud Run, Gemini 2.5 Flash, connected to BigQuery. 4 actions: find, cancel, rebook, patient lookup."

**POINT OUT in response**:
- `"ai_model": "gemini-2.5-flash"` — Google's model
- `"cloud": "GCP"` — running on your infra
- `"data_store": "BigQuery (...)"`  — your data

### Command 2 — Ask Gemini directly

```powershell
python -c "import requests,json; r=requests.post('https://csh-scheduling-agent-732227602168.us-central1.run.app/chat', json={'message':'Find me a cardiology appointment'}); print(json.dumps(r.json(), indent=2, default=str))"
```

**SAY**: "I'm asking the GCP agent directly — in plain English. Gemini parses the intent, queries BigQuery, and writes a human-friendly summary."

**POINT OUT in response**:
- `"model": "gemini-2.5-flash"` — this is Google Gemini, not Microsoft
- `"gemini_reasoning"` — Gemini's thought process
- `"action": "find_available"` — Gemini figured out what I need
- `"summary"` — friendly response at the bottom

> **Switch to**: GCP Console — BigQuery tab

**SAY**: "Let's verify on GCP. BigQuery → Job history → Project history tab."

**SHOW**: Click the most recent query. Point to:
- **User**: `732227602168-compute@developer.gserviceaccount.com` (the Cloud Run SA, not me)
- **SQL**: `SELECT * FROM appointments WHERE status = 'available' AND specialty = ...`

**SAY**: "This works great standalone. But CSH doesn't have one agent on one cloud. Who orchestrates? Who governs? That's where Foundry comes in."

---

## SLIDE 5 — CROSS-CLOUD INVOCATION (stay 10 seconds)

> **Show**: Slide 5 — Step 1: Cross-Cloud Agent Invocation

---

## LIVE DEMO A.2 — Foundry Orchestrates GCP (8 min)

> **Switch to**: VS Code — open `test_new_agent.py`

### Show the code (1 min)

**SAY**: "Look at this script. It talks to Azure Foundry — not GCP."

**POINT TO these lines**:

**Line 11** — `PROJECT_ENDPOINT = "https://ai-healthcare-foundry-jp-001.services.ai.azure.com/..."`
> "This is the Azure Foundry endpoint. Not GCP."

**Line 13** — `AGENT_VERSION = "1"`
> "We're using v1 of the agent for Part A. I'll show v2 in Part B."

**Lines 24-26** — `project_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())`
> "Azure credentials. No GCP key anywhere in this file."

**Lines 52-60** — `openai_client.responses.create(input=[...], extra_body={"agent_reference": {...}})`
> "We send the user's question to Foundry. Foundry decides what to do."

**Lines 32-33** — `httpx.post(GCP_URL, json={...})`
> "When Foundry says 'call GCP', THIS is the cross-cloud hop. Foundry made the decision."

### Run it — custom question

**SAY**: "Let me ask the SAME question I asked Gemini — but through Foundry."

```powershell
cd csh-scheduling-orchestrator
python test_new_agent.py "Find me a cardiology appointment and let me know first available slot with doctor name"
```

**WHILE IT RUNS, POINT OUT**:
- `>> Calling GCP agent: action=find_available` — "Foundry decided to call GCP"
- `<< GCP returned: 2` — "Same data from BigQuery"
- The final response — "Foundry formatted this with GPT-4o-mini. Same data, different brain."

### Run more questions

```powershell
python test_new_agent.py "I need to find an available orthopedic appointment at Mercy Hospital West"
```

```powershell
python test_new_agent.py "What are all the available appointments across all specialties this week?"
```

### Validate on GCP

> **Switch to**: GCP Console — BigQuery → Job history → Project history

**SAY**: "Hit refresh. See the new queries? I never touched GCP directly. I typed in VS Code, it went to Azure Foundry, Foundry called GCP. The proof is in BigQuery's own logs."

**POINT OUT**: Timestamps match when you ran the commands. User is the Cloud Run service account.

> **Switch to**: GCP Console — Cloud Trace → Trace Explorer → Last 1 hour

**SAY**: "GCP Cloud Trace shows the same requests — `/invoke` spans with agent action attributes. Same trace, visible on both clouds."

### Validate on Foundry

> **Switch to**: Foundry Portal (ai.azure.com) → Project → Tracing

**SAY**: "Now the Azure side. Foundry → Tracing. Here are the same requests."

**SHOW**: Click a recent trace. Walk through:
- User query came in
- GPT-4o-mini reasoned about it  
- Tool call to GCP (show the cross-cloud hop)
- GCP response came back
- Final response formatted

**SAY**: "This is v1 of the agent — the Foundry platform version. One pane of glass for every cross-cloud call."

---

## SLIDE 6 — EVENT-DRIVEN (stay 10 seconds)

> **Show**: Slide 6 — Step 2: Event-Driven Headless Automation

---

## LIVE DEMO A.3 — Headless Event-Driven Processing (5 min)

> **Switch to**: VS Code Terminal

**SAY**: "Now — no human at all. Scheduling events arrive in a queue. Foundry processes them automatically."

```powershell
python event_driven_demo.py demo
```

**WHILE IT RUNS, EXPLAIN**:
- "3 events drop into Azure Storage Queue — simulating HL7 messages from an EHR system"
- "Each event gets picked up, sent to Foundry, Foundry calls GCP, results come back"
- "Zero human interaction. This is headless processing at scale."

**POINT OUT results**:
- Event 1: `find_available → 2 slots`
- Event 2: `patient_appointments → 2 records`
- Event 3: `cancel → already cancelled`

**SAY**: "In production, this is an Azure Function triggered by the queue. HL7 events, FHIR messages, scheduling requests — they all flow through Foundry to GCP automatically."

---

## SLIDE 7 — AGENT CATALOG (stay 10 seconds)

> **Show**: Slide 7 — Step 3: Agent Catalog & Governance

---

## LIVE DEMO A.4 — Governance (2 min)

> **Switch to**: Foundry Portal → Project → Agents (or Models + Endpoints)

**SAY**: "Every agent — Azure, GCP, on-prem — is registered in Foundry's catalog. Versioned, governed, discoverable."

**SHOW**: Agent list showing `csh-scheduling-orchestrator` with versions

**SAY**: "Version 1 is our Foundry platform agent. Version 2 — which I'll show next — is the Agent Framework version. Both tracked, both traced."

---

## SLIDE 8 — PART A RESULTS (stay 30 seconds)

> **Show**: Slide 8 — Part A results with all checks passed

**SAY**: "Part A summary: Foundry orchestrated your GCP agent, processed events headlessly, traced everything across both clouds, and all agents are governed in one catalog. Zero changes to your GCP infrastructure. Now let me show you the developer story."

---

# PART B: MICROSOFT AGENT FRAMEWORK — Code-First Orchestration (20 min)

---

## SLIDE 9 — PART B HEADER (stay 15 seconds)

> **Show**: Slide 9 — "Part B: Microsoft Agent Framework — Code-First Agent Orchestration"

**SAY**: "Part A was Foundry as the platform — no-code, config-driven. But CSH has developers who want to embed this in their apps. EHR portals, patient apps, internal tools. Agent Framework gives them full code control — same Foundry governance underneath."

---

## SLIDE 10 — AGENT FRAMEWORK DEMO (stay 10 seconds)

> **Show**: Slide 10 — Agent Framework architecture

---

## LIVE DEMO B.1 — Code Walkthrough (3 min)

> **Switch to**: VS Code — open `agent_framework_demo.py`

### Show the SDK import

**Line 18** — `from agent_framework.azure import AzureAIClient`

**SAY**: "This is the Microsoft Agent Framework SDK. Open source, runs anywhere — local, container, cloud."

### Show the tools

**Lines 42-76** — The 4 tool functions

**SAY**: "Developers define tools as typed Python functions. Look at the annotations:"

```python
def find_available_appointments(
    specialty: Annotated[str | None, "Medical specialty to filter by"] = None,
    location: Annotated[str | None, "Facility location to filter by"] = None,
```

**SAY**: "The type hints and descriptions become the tool schema automatically. No manual JSON schema. The SDK handles it."

### Show the GCP call inside tools

**Lines 85-95** — `_call_gcp_sync` function

```python
def _call_gcp_sync(action, parameters):
    resp = httpx.post(GCP_URL, json={"action": action, "parameters": parameters}, timeout=30)
```

**SAY**: "Each tool calls the same GCP Cloud Run endpoint. The GCP agent doesn't know if it's being called by Foundry platform or Agent Framework. Same API contract."

### Show agent creation

**Lines 112-127** — `AzureAIClient(...).as_agent(...)`

```python
AzureAIClient(
    project_endpoint=PROJECT_ENDPOINT,
    model_deployment_name=MODEL_DEPLOYMENT,
    credential=credential,
).as_agent(
    name="csh-scheduling-orchestrator",
    instructions=AGENT_INSTRUCTIONS,
    tools=[find_available_appointments, get_patient_appointments, cancel_appointment, rebook_appointment],
)
```

**SAY**: "Endpoint, model, instructions, tools — wired together in one call. This creates v2 of the agent in Foundry."

### Show streaming

**Lines 137-140**:
```python
stream = agent.run(query, session=session, stream=True)
async for chunk in stream:
    if chunk.text:
        print(chunk.text, end="", flush=True)
```

**SAY**: "Tokens stream back in real-time. In a patient portal, this means users see the response appearing word by word. Much better UX than waiting for the full response."

### Show session

**Line 129** — `session = agent.create_session()`

**SAY**: "The session is stateful — the agent remembers previous questions. Platform version was stateless per call. This is better for conversational apps."

---

## LIVE DEMO B.2 — Run Agent Framework (5 min)

> **Switch to**: VS Code Terminal

```powershell
python agent_framework_demo.py
```

**WHILE IT STREAMS, POINT OUT**:
- "See the text appearing word by word? That's streaming."
- `>> [GCP Tool Call] action=find_available` — "Same GCP call. Same data."
- `<< [GCP Response] count=2` — "BigQuery returned the same 2 cardiology slots."
- "Three questions, same session. Agent has context across all three."

### Compare the two approaches side by side

**SAY**: "Same question, two approaches:"

| | Part A (v1 — Foundry Platform) | Part B (v2 — Agent Framework) |
|---|---|---|
| Agent defined | In Foundry portal | In Python code |
| Tools | Foundry manages | Developer defines with type hints |
| Streaming | No | Yes |
| Session | Stateless | Stateful |
| Best for | Ops teams, no-code | Developers, embedded in apps |
| GCP backend | Same | Same |
| Foundry tracing | Yes | Yes |

---

## LIVE DEMO B.3 — Verify v2 in Foundry Tracing (3 min)

> **Switch to**: Foundry Portal → Tracing

**SAY**: "Now look at Foundry Tracing. I'll filter by the most recent traces."

**SHOW**:
- The v1 traces from Part A (earlier timestamps)
- The v2 traces from Part B (most recent)
- Click a v2 trace and show: same waterfall — user query → model reasoning → GCP tool call → response

**SAY**: "Both versions — v1 platform, v2 Agent Framework — show up in the same tracing view. One governance layer. Murali, your ops team sees everything here regardless of whether the developer used the portal or the SDK."

---

## SLIDE 11 — OBSERVABILITY (stay 10 seconds)

> **Show**: Slide 11 — Cross-Cloud Observability

---

## LIVE DEMO B.4 — Observability Dashboard (3 min)

> **Switch to**: VS Code Terminal

```powershell
python observability_dashboard.py
```

**WHILE IT RUNS, EXPLAIN**: "This pulls data from App Insights using KQL — success rates, latency percentiles, cross-cloud traces, error breakdown."

**POINT OUT**:
- "100% success rate across all calls"
- "Latency includes the cross-cloud hop to GCP"
- "Both v1 and v2 traces visible"

> **Switch to**: GCP Console — Cloud Trace → Last 1 hour

**SAY**: "And on the GCP side — same requests visible in Cloud Trace. Same trace ID, both clouds. That's cross-cloud observability."

---

## SLIDE 12 — RESULTS DASHBOARD (stay 30 seconds)

> **Show**: Slide 12 — Full results

**SAY**: "Everything passed. Cross-cloud invocation, event-driven processing, Agent Framework, observability. Zero changes to GCP. All governed by Foundry."

---

## SLIDE 13 — WHAT THIS MEANS FOR CSH (1 min)

> **Show**: Slide 13 — summary slide

**SAY**: "Here's what this means for CommonSpirit:"
- "Your GCP agents keep running where they are. No migration."
- "Foundry orchestrates them — today with 1 agent, tomorrow with 10 across GCP, AWS, on-prem."
- "Every call is traced across clouds. One pane of glass."
- "Your developers get Agent Framework for embedding in apps. Your ops team gets the Foundry portal."
- "One governance platform for all your AI agents, regardless of cloud."

---

## SLIDE 14 — NEXT STEPS / CLOSE (1 min)

> **Show**: Slide 14 — Next Steps

**SAY**: "Next steps: we can expand this to your real EHR data, add HL7/FHIR event triggers, connect additional agents across your infrastructure. The foundation is built. Let's talk about the roadmap."

---

# APPENDIX — Quick Reference

## Key URLs

| Resource | URL |
|----------|-----|
| GCP Cloud Run | `https://console.cloud.google.com/run/detail/us-central1/csh-scheduling-agent` |
| GCP BigQuery Jobs | `https://console.cloud.google.com/bigquery` → Job history → **Project history** tab |
| GCP Cloud Trace | `https://console.cloud.google.com/traces` → Set time to **Last 1 hour** |
| Azure Foundry | `https://ai.azure.com` → project → **Tracing** |
| GCP Agent URL | `https://csh-scheduling-agent-732227602168.us-central1.run.app` |

## Key Files + Line Numbers

| File | Lines | What |
|------|-------|------|
| `gcp-scheduling-agent/app.py` L15 | `from google.cloud import bigquery` | BigQuery client |
| `gcp-scheduling-agent/app.py` L26 | `from google import genai` | Gemini SDK |
| `gcp-scheduling-agent/app.py` L51 | `GEMINI_MODEL = "gemini-2.0-flash"` | Model config (env overrides to 2.5-flash) |
| `gcp-scheduling-agent/app.py` L58 | `gemini_client = genai.Client(api_key=...)` | Gemini init |
| `gcp-scheduling-agent/app.py` L74-89 | OTel setup + Cloud Trace + Azure exporter | Dual-cloud tracing |
| `gcp-scheduling-agent/app.py` L281 | `/health` endpoint | Agent capabilities |
| `gcp-scheduling-agent/app.py` L302 | `/invoke` endpoint | Structured API (Foundry calls this) |
| `gcp-scheduling-agent/app.py` L396 | `/chat` endpoint | Natural language via Gemini |
| `test_new_agent.py` L11 | `PROJECT_ENDPOINT = "...foundry..."` | Azure Foundry endpoint |
| `test_new_agent.py` L13 | `AGENT_VERSION = "1"` | v1 agent for Part A |
| `test_new_agent.py` L24-26 | `AIProjectClient(credential=DefaultAzureCredential())` | Azure auth only |
| `test_new_agent.py` L52-60 | `responses.create(... agent_reference ...)` | Foundry agent call |
| `test_new_agent.py` L32-33 | `httpx.post(GCP_URL, ...)` | Cross-cloud hop to GCP |
| `agent_framework_demo.py` L18 | `from agent_framework.azure import AzureAIClient` | MAF SDK import |
| `agent_framework_demo.py` L42-76 | Tool functions with Annotated types | Typed tool definitions |
| `agent_framework_demo.py` L85-95 | `_call_gcp_sync()` | GCP Cloud Run call |
| `agent_framework_demo.py` L112-127 | `AzureAIClient(...).as_agent(...)` | Agent creation (v2) |
| `agent_framework_demo.py` L129 | `session = agent.create_session()` | Stateful session |
| `agent_framework_demo.py` L137-140 | `agent.run(query, stream=True)` | Streaming response |
| `event_driven_demo.py` L27 | `STORAGE_ACCOUNT = "stcshdemo2026"` | Azure Storage Queue |
| `event_driven_demo.py` L42-72 | Sample events (HL7-like) | Simulated EHR events |

## Live Questions (from demo-live-questions.txt)

```powershell
python test_new_agent.py "Show me all appointments for patient P-1007 and tell me if any need follow-up"
python test_new_agent.py "I need to find an available orthopedic appointment at Mercy Hospital West"
python test_new_agent.py "Cancel appointment APT-012 because the patient requested a different provider"
python test_new_agent.py "Patient P-1001 Maria Garcia needs a new cardiology appointment, what slots are open with Dr. Sarah Chen?"
python test_new_agent.py "What are all the available appointments across all specialties this week?"
```

## Emergency Fixes

| Issue | Fix |
|-------|-----|
| GCP agent down | Check: `curl https://csh-scheduling-agent-732227602168.us-central1.run.app/health` |
| Foundry auth fail | Run: `az login` then retry |
| BigQuery no new queries | Check **Project history** tab (not Personal history) |
| Cloud Trace empty | Set time range to **Last 1 hour** (not the default week view) |
| Event-driven fails | Check storage account: `az storage queue list --account-name stcshdemo2026` |
