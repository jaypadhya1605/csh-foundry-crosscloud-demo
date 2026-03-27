# Use Case 1: Multi-Agent Scheduling Workflow — Strategy & Next Meeting Plan

**Date:** March 13, 2026  
**Customer:** CommonSpirit Health (CSH)  
**Stakeholder:** Murali (Technical Lead), Sunil (Exec Sponsor)  
**Microsoft Team:** Jay, Charles, Joey

---

## 1. Refined Problem Statement

CSH operates a large-scale healthcare scheduling operation across 140+ hospitals. Today, appointment scheduling, finding, cancellations, and rebooking are manual, fragmented, and high-cost. They want **headless, multi-agent automation** for these workflows.

**Key constraints:**
- Agents are being built on **Google ADK** using the **A2A** protocol
- Data estate lives in **GCP / BigQuery**
- There is **no unified orchestration, observability, or governance layer** today — this is the gap
- Internal network blocks access to ai.azure.com — any POC must account for this

---

## 2. Sunil's Ask — Redefined for This Use Case

> **"Demonstrate that Azure AI Foundry can serve as the cross-cloud observability, governance, and orchestration control plane for CSH's Google ADK-based scheduling agents — without requiring CSH to replatform their agent runtime or move data out of GCP."**

### What this means concretely:

| Dimension | What We're Proving |
|---|---|
| **Observability** | Foundry ingests OpenTelemetry traces from GCP-hosted ADK agents and surfaces them in a single-pane dashboard (Azure Monitor + App Insights) |
| **Governance** | Foundry enforces policies at the agent boundary — input/output logging, audit trails, PII detection, compliance checks |
| **Orchestration (Phase 2)** | A Foundry-hosted orchestrator agent can coordinate GCP agents via REST/A2A adapter, triggering scheduling workflows end-to-end |
| **Cross-cloud data** | Foundry agents/tools access BigQuery via MCP connectors — no data migration required |

---

## 3. The Scheduling Workflow — Agent Decomposition

A realistic multi-agent scheduling workflow for CSH:

```
Patient calls / message arrives (event-driven trigger)
        │
        ▼
┌──────────────────┐
│  Triage Agent     │  Classifies intent: new appt / reschedule / cancel
└───────┬──────────┘
        │
        ├──── New Appointment ────►  ┌──────────────────┐
        │                            │ Availability Agent │  Queries EHR/scheduling
        │                            │ (finds open slots) │  system via BigQuery
        │                            └───────┬──────────┘
        │                                    │
        │                                    ▼
        │                            ┌──────────────────┐
        │                            │ Booking Agent     │  Confirms & books
        │                            └──────────────────┘
        │
        ├──── Reschedule ──────────► ┌──────────────────┐
        │                            │ Rebooking Agent   │  Cancel old + find new
        │                            └──────────────────┘
        │
        └──── Cancel ──────────────► ┌──────────────────┐
                                     │ Cancellation Agent│  Cancels + triggers
                                     │                   │  backfill logic
                                     └──────────────────┘
        
All agents emit OTel traces ──────► Azure AI Foundry (observe + govern)
```

**Where agents run:** GCP (Google ADK, communicating via A2A)  
**Where governance + observability lives:** Azure AI Foundry  
**Where data lives:** GCP BigQuery + EHR systems  

---

## 4. How This Differs from Amazon Health Connect

| Dimension | Amazon Health Connect | Our Proposed Architecture |
|---|---|---|
| **Cloud lock-in** | Fully AWS (Connect, Lex, Bedrock) | Cross-cloud: agents on GCP, control plane on Azure |
| **Agent framework** | AWS-proprietary | Google ADK (CSH's existing choice) — Foundry is additive |
| **Data location** | Must bring data to AWS | Data stays in GCP BigQuery |
| **Observability** | CloudWatch (AWS only) | Azure Monitor + App Insights (cross-cloud via OTel) |
| **Healthcare specificity** | Pre-built healthcare contact center | Custom agents tailored to CSH's exact workflows |
| **Governance** | AWS-scoped | Foundry governs agents regardless of hosting cloud |

**The pitch:** Amazon Health Connect forces you to move to AWS. We let you keep your agents and data where they are (GCP) and add the missing governance + observability layer on top.

---

## 5. Phased Approach

### Phase 1: Observability Overlay (Lowest friction, highest signal)
- Instrument CSH's existing Google ADK scheduling agents with OpenTelemetry
- Ingest traces into Azure Monitor / Application Insights
- Build a single-pane dashboard showing agent health, latency, errors, workflow completion rates
- **Outcome:** Murali gets his "single pane of dashboard" without changing any agent code

### Phase 2: Governance Boundary
- Add Foundry-based policy enforcement at agent ingress/egress
- PII detection on patient scheduling data
- Audit logging for compliance (HIPAA)
- Alert rules for anomalous agent behavior
- **Outcome:** CSH has a compliance story across their agent fleet

### Phase 3: Orchestration Control Plane
- Build a Foundry-hosted orchestrator agent that coordinates the workflow
- GCP agents exposed via REST APIs, orchestrator calls them in sequence
- Event-driven triggers (queue messages) kick off the orchestrator
- A2A adapter if/when Foundry adds native A2A support
- **Outcome:** Full headless, cross-cloud orchestration from Foundry

---

## 6. Recommended Next Meeting Agenda

### Meeting Title: *"Use Case 1 Deep Dive — Scheduling Agent Observability & Governance with Foundry"*

**Duration:** 60 min  
**Audience:** Murali + CSH technical team, Sunil (first 15 min)

| Time | Topic | Owner |
|---|---|---|
| 0–10 min | **Recap & alignment** — restate the ask, confirm scheduling as priority use case | Jay |
| 10–20 min | **Architecture walkthrough** — show the cross-cloud architecture diagram (agents on GCP, Foundry as control plane), explain OTel-based observability ingestion | Jay / Microsoft |
| 20–35 min | **Live walkthrough** — demonstrate: (1) OTel traces from a sample agent flowing into App Insights, (2) a Foundry dashboard showing multi-agent workflow traces, (3) MCP tool calling BigQuery from Foundry | Microsoft |
| 35–45 min | **Governance demo** — show policy enforcement, PII detection, audit logging on agent I/O | Microsoft |
| 45–55 min | **Discussion** — what does CSH need to instrument their existing ADK agents? Network access blockers? Security team involvement? | Murali |
| 55–60 min | **Next steps & POC scoping** — agree on Phase 1 scope, identify sandbox logistics | All |

### Pre-meeting prep needed from Microsoft:
- [ ] Build a sample Google ADK agent (simple scheduling mock) that emits OTel traces
- [ ] Configure Azure Monitor / App Insights to ingest those traces
- [ ] Create a dashboard showing multi-agent workflow view
- [ ] Prepare MCP connector to BigQuery (or mock equivalent)
- [ ] Address network access blocker (ai.azure.com blocked for Murali)

### Pre-meeting ask to CSH:
- [ ] Confirm scheduling workflow as priority use case
- [ ] Share high-level architecture of their current scheduling systems
- [ ] Identify which ADK agents (if any) are already built for scheduling
- [ ] Confirm security team availability for sandbox/POC discussion

---

## 7. Key Talking Points for Sunil

1. **We're not asking CSH to replatform.** Their agents stay on Google ADK, their data stays in BigQuery. Foundry adds the governance and visibility layer they're missing today.

2. **This fills a real gap.** Murali explicitly said they have a "blind spot" in agent observability and governance. No other platform is offering cross-cloud agent governance today.

3. **Amazon Health Connect is the wrong comparison.** It's a walled-garden, AWS-only solution. Our approach is cloud-agnostic and works *with* CSH's existing investments, not against them.

4. **Phase 1 is low-risk, high-signal.** Just adding observability to existing agents — no workflow changes, no data movement, no replatforming. If it works, Phase 2 and 3 follow naturally.
