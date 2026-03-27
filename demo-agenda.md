# CommonSpirit Health — Foundry Cross-Cloud Demo
**Date:** March 27, 2026  
**Attendees:** Murali (CSH), Jay Padhya (Microsoft)  
**Format:** Live terminal demo (no portal required)

---

## Part A — Foundry Platform: Headless Multi-Agent Orchestration (30 min)

### 1. Architecture Overview (5 min)
- Walk through the end-to-end architecture: GCP (BigQuery + Cloud Run) ↔ Azure Foundry (orchestrator agent) ↔ Azure Storage Queue
- Explain how Foundry acts as the central orchestration layer while data stays in GCP

### 2. Cross-Cloud Agent Invocation via Foundry (10 min)
- Live demo: send natural-language scheduling queries to the Foundry orchestrator agent
- Show Foundry routing requests to the GCP Cloud Run agent, which queries BigQuery
- Queries: find available appointments, look up a patient's bookings, cancel an appointment

### 3. Event-Driven Headless Automation (10 min)
- Drop scheduling events into Azure Storage Queue (simulating EHR trigger, patient portal, call center)
- Show the Foundry agent picking up events, reasoning, calling GCP, and completing actions — zero human interaction
- Demonstrate multiple event types processed back-to-back

### 4. Agent Catalog & Governance (5 min)
- List all registered agents in the Foundry project via API
- Show the GCP-hosted agent registered alongside Azure-native agents
- Discuss governance capabilities: versioning, tracing lineage, single pane of glass

---

## Part B — Microsoft Agent Framework: Code-First Orchestration (20 min)

### 5. Agent Framework Orchestrator (10 min)
- Run the same cross-cloud scenario using the Microsoft Agent Framework SDK
- Show how the orchestrator is built in Python with typed tool definitions
- Same flow: Agent Framework → Foundry model (gpt-5.4-mini) → tool calls → GCP Cloud Run → BigQuery
- Highlight: code-first, versionable in Git, runs anywhere

### 6. Cross-Cloud Observability (10 min)
- Run the observability dashboard pulling traces from Azure App Insights
- Show GCP agent telemetry (OpenTelemetry) flowing into Azure Monitor
- Show the end-to-end transaction trace in App Insights (GCP spans visible in Azure)

---

## Wrap-Up (10 min)

### 7. Discussion & Next Steps
- Recap: Foundry platform (headless, governed) vs. Agent Framework (code-first, portable) — complementary approaches
- Discuss priority use cases (denials & appeals, revenue cycle, scheduling)
- Align on sandbox access and next steps
