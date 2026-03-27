"""
CSH Scheduling Agent — GCP Cloud Run with Gemini + BigQuery.
Handles: find appointments, cancel, rebook.
Queries BigQuery for real scheduling data.
Uses Gemini for natural language understanding.
Emits OpenTelemetry traces for cross-cloud observability.
"""

import os
import json
import uuid
from datetime import datetime

from flask import Flask, request, jsonify
from google.cloud import bigquery
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Google Generative AI (Gemini via Generative Language API)
try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# GCP Cloud Trace exporter (native GCP tracing)
try:
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    HAS_GCP_TRACE = True
except ImportError:
    HAS_GCP_TRACE = False

# Azure Monitor exporter for cross-cloud tracing
try:
    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
    HAS_AZURE_EXPORTER = True
except ImportError:
    HAS_AZURE_EXPORTER = False

# --- Config ---
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "project-b8139082-b506-40d6-89a")
BQ_DATASET = os.environ.get("BQ_DATASET", "demo_scheduling")
BQ_TABLE = os.environ.get("BQ_TABLE", "appointments")
OTEL_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
APPINSIGHTS_CONNECTION_STRING = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# --- Gemini Setup ---
gemini_client = None
if HAS_GEMINI and GOOGLE_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
        print(f"[Gemini] Initialized with model={GEMINI_MODEL} via Generative Language API")
    except Exception as e:
        print(f"[Gemini] Init failed: {e}. /chat endpoint will be unavailable.")

# --- OpenTelemetry Setup ---
resource = Resource.create({
    "service.name": "csh-scheduling-agent",
    "service.version": "1.0.0",
    "deployment.environment": "demo",
    "cloud.provider": "gcp",
    "cloud.platform": "gcp_cloud_run",
})

provider = TracerProvider(resource=resource)

# Export to GCP Cloud Trace (native GCP tracing)
if HAS_GCP_TRACE:
    gcp_exporter = CloudTraceSpanExporter(project_id=PROJECT_ID)
    provider.add_span_processor(BatchSpanProcessor(gcp_exporter))
    print("[OTel] GCP Cloud Trace exporter configured — traces visible in GCP Console")

# Export to Azure Monitor (App Insights) for cross-cloud observability
if APPINSIGHTS_CONNECTION_STRING and HAS_AZURE_EXPORTER:
    azure_exporter = AzureMonitorTraceExporter(connection_string=APPINSIGHTS_CONNECTION_STRING)
    provider.add_span_processor(BatchSpanProcessor(azure_exporter))
    print("[OTel] Azure Monitor exporter configured — traces flowing to App Insights")

if OTEL_ENDPOINT:
    otlp_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

trace.set_tracer_provider(provider)
tracer = trace.get_tracer("csh-scheduling-agent")

# --- Flask App ---
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# --- BigQuery Client ---
bq_client = bigquery.Client(project=PROJECT_ID)


def query_bigquery(sql, params=None):
    """Execute a BigQuery query and return results as list of dicts."""
    job_config = bigquery.QueryJobConfig()
    if params:
        job_config.query_parameters = params
    query_job = bq_client.query(sql, job_config=job_config)
    results = query_job.result()
    return [dict(row) for row in results]


# --- Agent Tools ---

def find_available_appointments(specialty=None, location=None, provider_name=None, date_from=None):
    """Find available appointment slots, optionally filtered."""
    with tracer.start_as_current_span("find_available_appointments") as span:
        span.set_attribute("agent.tool", "find_available_appointments")
        span.set_attribute("agent.input.specialty", specialty or "any")
        span.set_attribute("agent.input.location", location or "any")

        table_ref = f"`{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`"
        conditions = ["status = 'available'"]
        params = []

        if specialty:
            conditions.append("LOWER(specialty) = LOWER(@specialty)")
            params.append(bigquery.ScalarQueryParameter("specialty", "STRING", specialty))
        if location:
            conditions.append("LOWER(location) LIKE LOWER(@location)")
            params.append(bigquery.ScalarQueryParameter("location", "STRING", f"%{location}%"))
        if provider_name:
            conditions.append("LOWER(provider_name) LIKE LOWER(@provider_name)")
            params.append(bigquery.ScalarQueryParameter("provider_name", "STRING", f"%{provider_name}%"))
        if date_from:
            conditions.append("start_time >= @date_from")
            params.append(bigquery.ScalarQueryParameter("date_from", "TIMESTAMP", date_from))

        where_clause = " AND ".join(conditions)
        sql = f"SELECT * FROM {table_ref} WHERE {where_clause} ORDER BY start_time LIMIT 10"

        results = query_bigquery(sql, params)
        span.set_attribute("agent.output.count", len(results))

        # Serialize timestamps
        for r in results:
            for k, v in r.items():
                if isinstance(v, datetime):
                    r[k] = v.isoformat()

        return results


def cancel_appointment(appointment_id):
    """Cancel an existing appointment by ID."""
    with tracer.start_as_current_span("cancel_appointment") as span:
        span.set_attribute("agent.tool", "cancel_appointment")
        span.set_attribute("agent.input.appointment_id", appointment_id)

        table_ref = f"`{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`"

        # Check it exists and is booked
        check_sql = f"SELECT * FROM {table_ref} WHERE appointment_id = @apt_id"
        params = [bigquery.ScalarQueryParameter("apt_id", "STRING", appointment_id)]
        existing = query_bigquery(check_sql, params)

        if not existing:
            span.set_attribute("agent.output.status", "not_found")
            return {"status": "error", "message": f"Appointment {appointment_id} not found"}

        apt = existing[0]
        if apt["status"] not in ("booked", "rescheduled"):
            span.set_attribute("agent.output.status", "invalid_state")
            return {"status": "error", "message": f"Cannot cancel appointment in '{apt['status']}' state"}

        # Update to cancelled
        update_sql = f"""
        UPDATE {table_ref}
        SET status = 'cancelled', reason_code = 'AGENT_CANCELLED', notes = CONCAT(notes, ' | Cancelled by scheduling agent'), updated_at = CURRENT_TIMESTAMP()
        WHERE appointment_id = @apt_id
        """
        query_bigquery(update_sql, params)

        # Mark the slot as available
        avail_sql = f"""
        UPDATE {table_ref}
        SET status = 'available', reason_code = '', notes = 'Opened by cancellation agent', updated_at = CURRENT_TIMESTAMP()
        WHERE appointment_id = @apt_id
        """
        # Actually we keep the cancelled record and just report success
        span.set_attribute("agent.output.status", "cancelled")

        for k, v in apt.items():
            if isinstance(v, datetime):
                apt[k] = v.isoformat()

        return {
            "status": "success",
            "message": f"Appointment {appointment_id} cancelled successfully",
            "cancelled_appointment": apt
        }


def rebook_appointment(old_appointment_id, new_appointment_id):
    """Rebook: cancel old appointment and book new one."""
    with tracer.start_as_current_span("rebook_appointment") as span:
        span.set_attribute("agent.tool", "rebook_appointment")
        span.set_attribute("agent.input.old_id", old_appointment_id)
        span.set_attribute("agent.input.new_id", new_appointment_id)

        # Cancel old
        cancel_result = cancel_appointment(old_appointment_id)
        if cancel_result.get("status") == "error":
            span.set_attribute("agent.output.status", "cancel_failed")
            return cancel_result

        table_ref = f"`{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`"

        # Check new slot is available
        check_sql = f"SELECT * FROM {table_ref} WHERE appointment_id = @apt_id AND status = 'available'"
        params = [bigquery.ScalarQueryParameter("apt_id", "STRING", new_appointment_id)]
        new_slot = query_bigquery(check_sql, params)

        if not new_slot:
            span.set_attribute("agent.output.status", "slot_unavailable")
            return {"status": "error", "message": f"Slot {new_appointment_id} is not available"}

        # Book the new slot
        old_apt = cancel_result["cancelled_appointment"]
        update_sql = f"""
        UPDATE {table_ref}
        SET status = 'booked',
            patient_id = @patient_id,
            patient_name = @patient_name,
            reason_code = 'RESCHEDULE',
            notes = CONCAT('Rebooked from ', @old_id),
            updated_at = CURRENT_TIMESTAMP()
        WHERE appointment_id = @new_id
        """
        book_params = [
            bigquery.ScalarQueryParameter("patient_id", "STRING", old_apt["patient_id"]),
            bigquery.ScalarQueryParameter("patient_name", "STRING", old_apt["patient_name"]),
            bigquery.ScalarQueryParameter("old_id", "STRING", old_appointment_id),
            bigquery.ScalarQueryParameter("new_id", "STRING", new_appointment_id),
        ]
        query_bigquery(update_sql, book_params)

        slot = new_slot[0]
        for k, v in slot.items():
            if isinstance(v, datetime):
                slot[k] = v.isoformat()

        span.set_attribute("agent.output.status", "rebooked")
        return {
            "status": "success",
            "message": f"Rebooked from {old_appointment_id} to {new_appointment_id}",
            "new_appointment": slot
        }


def get_patient_appointments(patient_id):
    """Get all appointments for a patient."""
    with tracer.start_as_current_span("get_patient_appointments") as span:
        span.set_attribute("agent.tool", "get_patient_appointments")
        span.set_attribute("agent.input.patient_id", patient_id)

        table_ref = f"`{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`"
        sql = f"SELECT * FROM {table_ref} WHERE patient_id = @patient_id ORDER BY start_time"
        params = [bigquery.ScalarQueryParameter("patient_id", "STRING", patient_id)]
        results = query_bigquery(sql, params)
        span.set_attribute("agent.output.count", len(results))

        for r in results:
            for k, v in r.items():
                if isinstance(v, datetime):
                    r[k] = v.isoformat()

        return results


# --- API Routes ---

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "agent": "csh-scheduling-agent",
        "version": "1.0.0",
        "cloud": "GCP",
        "runtime": "Cloud Run",
        "region": "us-central1",
        "ai_model": GEMINI_MODEL if gemini_client else "none",
        "ai_provider": "Google Gemini" if gemini_client else "none",
        "data_store": f"BigQuery ({PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE})",
        "available_actions": ["find_available", "cancel", "rebook", "patient_appointments"],
        "endpoints": {
            "/health": "GET — this health check",
            "/invoke": "POST — structured action+params (used by Foundry)",
            "/chat": "POST — natural language via Gemini",
        }
    })


@app.route("/invoke", methods=["POST"])
def invoke():
    """Main agent endpoint. Accepts an action + parameters."""
    with tracer.start_as_current_span("agent_invoke") as span:
        # Propagate trace context from caller (Foundry)
        body = request.get_json(force=True)

        action = body.get("action", "")
        params = body.get("parameters", {})
        correlation_id = body.get("correlation_id", str(uuid.uuid4()))

        span.set_attribute("agent.action", action)
        span.set_attribute("agent.correlation_id", correlation_id)

        if action == "find_available":
            result = find_available_appointments(
                specialty=params.get("specialty"),
                location=params.get("location"),
                provider_name=params.get("provider_name"),
                date_from=params.get("date_from"),
            )
            return jsonify({
                "correlation_id": correlation_id,
                "action": action,
                "result": result,
                "count": len(result)
            })

        elif action == "cancel":
            appointment_id = params.get("appointment_id")
            if not appointment_id:
                return jsonify({"error": "appointment_id required"}), 400
            result = cancel_appointment(appointment_id)
            return jsonify({
                "correlation_id": correlation_id,
                "action": action,
                "result": result
            })

        elif action == "rebook":
            old_id = params.get("old_appointment_id")
            new_id = params.get("new_appointment_id")
            if not old_id or not new_id:
                return jsonify({"error": "old_appointment_id and new_appointment_id required"}), 400
            result = rebook_appointment(old_id, new_id)
            return jsonify({
                "correlation_id": correlation_id,
                "action": action,
                "result": result
            })

        elif action == "patient_appointments":
            patient_id = params.get("patient_id")
            if not patient_id:
                return jsonify({"error": "patient_id required"}), 400
            result = get_patient_appointments(patient_id)
            return jsonify({
                "correlation_id": correlation_id,
                "action": action,
                "result": result,
                "count": len(result)
            })

        else:
            span.set_attribute("agent.output.status", "unknown_action")
            return jsonify({
                "error": f"Unknown action: {action}",
                "supported_actions": ["find_available", "cancel", "rebook", "patient_appointments"]
            }), 400


# --- Gemini-powered natural language endpoint ---

GEMINI_SYSTEM_PROMPT = """You are a healthcare scheduling assistant for CommonSpirit Health.
You analyze user messages and extract the intent and parameters.

Respond with ONLY a valid JSON object (no markdown, no explanation):
{
  "action": "<one of: find_available, cancel, rebook, patient_appointments>",
  "parameters": { ... },
  "reasoning": "<one sentence explaining your interpretation>"
}

Parameter schemas by action:
- find_available: {"specialty": str|null, "location": str|null, "provider_name": str|null}
- cancel: {"appointment_id": str}
- rebook: {"old_appointment_id": str, "new_appointment_id": str}
- patient_appointments: {"patient_id": str}

If the user's request is ambiguous or not scheduling-related, respond:
{"action": "clarify", "parameters": {}, "reasoning": "explanation"}
"""


@app.route("/chat", methods=["POST"])
def chat():
    """Gemini-powered natural language endpoint.
    Accepts: {"message": "natural language query"}
    Gemini interprets the intent, then executes against BigQuery.
    """
    with tracer.start_as_current_span("gemini_chat") as span:
        if not gemini_client:
            return jsonify({"error": "Gemini not available — check GOOGLE_API_KEY env var"}), 503

        body = request.get_json(force=True)
        user_message = body.get("message", "")
        correlation_id = body.get("correlation_id", str(uuid.uuid4()))

        span.set_attribute("agent.endpoint", "chat")
        span.set_attribute("agent.user_message", user_message[:200])
        span.set_attribute("agent.model", GEMINI_MODEL)

        # Step 1: Gemini interprets the user's intent
        with tracer.start_as_current_span("gemini_intent_extraction") as gemini_span:
            gemini_span.set_attribute("gemini.model", GEMINI_MODEL)
            gemini_span.set_attribute("gemini.input", user_message[:200])

            prompt = f"{GEMINI_SYSTEM_PROMPT}\n\nUser message: {user_message}"
            gemini_response = gemini_client.models.generate_content(
                model=GEMINI_MODEL, contents=prompt
            )
            raw_text = gemini_response.text.strip()

            # Parse the JSON from Gemini
            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3].strip()

            try:
                intent = json.loads(raw_text)
            except json.JSONDecodeError:
                gemini_span.set_attribute("gemini.parse_error", True)
                return jsonify({
                    "correlation_id": correlation_id,
                    "error": "Could not parse Gemini response",
                    "gemini_raw": raw_text[:500],
                    "model": GEMINI_MODEL
                }), 500

            action = intent.get("action", "clarify")
            params = intent.get("parameters", {})
            reasoning = intent.get("reasoning", "")

            gemini_span.set_attribute("gemini.action", action)
            gemini_span.set_attribute("gemini.reasoning", reasoning)

        # Step 2: If Gemini needs clarification, return that
        if action == "clarify":
            return jsonify({
                "correlation_id": correlation_id,
                "model": GEMINI_MODEL,
                "action": "clarify",
                "reasoning": reasoning,
                "message": f"I need more information: {reasoning}"
            })

        # Step 3: Execute the action against BigQuery
        with tracer.start_as_current_span("execute_action") as exec_span:
            exec_span.set_attribute("agent.action", action)

            if action == "find_available":
                result = find_available_appointments(
                    specialty=params.get("specialty"),
                    location=params.get("location"),
                    provider_name=params.get("provider_name"),
                )
                data = {"result": result, "count": len(result)}

            elif action == "cancel":
                apt_id = params.get("appointment_id")
                if not apt_id:
                    return jsonify({"error": "Gemini did not extract appointment_id", "intent": intent}), 400
                data = {"result": cancel_appointment(apt_id)}

            elif action == "rebook":
                old_id = params.get("old_appointment_id")
                new_id = params.get("new_appointment_id")
                if not old_id or not new_id:
                    return jsonify({"error": "Gemini did not extract both appointment IDs", "intent": intent}), 400
                data = {"result": rebook_appointment(old_id, new_id)}

            elif action == "patient_appointments":
                pid = params.get("patient_id")
                if not pid:
                    return jsonify({"error": "Gemini did not extract patient_id", "intent": intent}), 400
                result = get_patient_appointments(pid)
                data = {"result": result, "count": len(result)}

            else:
                return jsonify({"error": f"Unknown action from Gemini: {action}", "intent": intent}), 400

        # Step 4: Use Gemini to format a friendly response
        with tracer.start_as_current_span("gemini_response_format") as fmt_span:
            fmt_span.set_attribute("gemini.model", GEMINI_MODEL)

            summary_prompt = (
                f"The user asked: \"{user_message}\"\n\n"
                f"The scheduling system returned this data:\n{json.dumps(data, default=str)[:2000]}\n\n"
                f"Write a clear, friendly 2-3 sentence summary for a healthcare staff member. "
                f"Include key details like appointment IDs, providers, times, and patient names."
            )
            summary_response = gemini_client.models.generate_content(
                model=GEMINI_MODEL, contents=summary_prompt
            )
            friendly_summary = summary_response.text.strip()
            fmt_span.set_attribute("gemini.summary_length", len(friendly_summary))

        span.set_attribute("agent.action", action)
        span.set_attribute("agent.output.success", True)

        return jsonify({
            "correlation_id": correlation_id,
            "model": GEMINI_MODEL,
            "gemini_reasoning": reasoning,
            "action": action,
            "parameters": params,
            "data": data,
            "summary": friendly_summary,
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
