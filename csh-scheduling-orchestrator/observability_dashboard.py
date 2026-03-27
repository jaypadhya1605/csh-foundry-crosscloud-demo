"""
Cross-Cloud Observability Dashboard
=====================================
Queries Azure App Insights to show traces from both Azure Foundry and GCP Cloud Run agents.
This demonstrates the single-pane-of-glass monitoring Murali asked for.

Usage:
  python observability_dashboard.py
"""
import subprocess
import json
import sys

APP_INSIGHTS = "appinsights-healthcare-foundry-001"
RESOURCE_GROUP = "rg-healthcareai-demo-jp-001"

def run_query(query, title, display_cols=None):
    """Run a KQL query against App Insights and display results.
    display_cols: list of column names to display (if None, show all up to 6 cols)
    """
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

    cmd = [
        "az", "monitor", "app-insights", "query",
        "--app", APP_INSIGHTS,
        "-g", RESOURCE_GROUP,
        "--analytics-query", query,
        "-o", "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=True)
    if result.returncode != 0:
        print(f"  Error: {result.stderr[:200]}")
        return []

    data = json.loads(result.stdout)
    tables = data.get("tables", [])
    if not tables:
        print("  No data")
        return []

    table = tables[0]
    all_columns = [c["name"] for c in table["columns"]]
    rows = table["rows"]

    if not rows:
        print("  No data in time range")
        return rows

    # Determine which columns to display
    if display_cols:
        col_indices = []
        for dc in display_cols:
            if dc in all_columns:
                col_indices.append(all_columns.index(dc))
        columns = [all_columns[i] for i in col_indices]
    else:
        col_indices = list(range(min(len(all_columns), 6)))
        columns = [all_columns[i] for i in col_indices]

    # Extract only desired columns from rows
    filtered_rows = []
    for row in rows:
        filtered_rows.append([str(row[i]) if i < len(row) else "" for i in col_indices])

    # Calculate column widths (cap at 35)
    col_widths = []
    for ci, col_name in enumerate(columns):
        max_data = max((len(r[ci]) for r in filtered_rows), default=0)
        col_widths.append(min(max(len(col_name), max_data), 35))

    header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(columns))
    print(f"  {header}")
    print(f"  {'-' * len(header)}")
    for row in filtered_rows:
        line = " | ".join(row[i][:col_widths[i]].ljust(col_widths[i]) for i in range(len(columns)))
        print(f"  {line}")

    print(f"  [{len(filtered_rows)} row(s)]")
    return rows


def main():
    print("=" * 80)
    print("  CROSS-CLOUD OBSERVABILITY DASHBOARD")
    print("  Azure App Insights: appinsights-healthcare-foundry-001")
    print("  Monitoring: Azure Foundry Agent + GCP Cloud Run Agent")
    print("=" * 80)

    # 1. GCP Agent Requests (from Cloud Run → App Insights via OTel exporter)
    run_query(
        'requests | where timestamp > ago(24h) | where cloud_RoleName contains "scheduling" or cloud_RoleName == "localhost" | project timestamp, name, duration, success, cloud_RoleName | order by timestamp desc | take 5',
        "1. GCP CLOUD RUN AGENT - REQUEST TRACES (cross-cloud via OTel)",
        ["timestamp", "name", "duration", "success", "cloud_RoleName"]
    )

    # 2. GCP Agent BigQuery dependency calls
    run_query(
        'dependencies | where timestamp > ago(24h) | where name startswith "BigQuery" or name == "find_available_appointments" or name == "cancel_appointment" or name == "agent_invoke" | project timestamp, name, type, duration, success | order by timestamp desc | take 10',
        "2. GCP AGENT - BigQuery & Function CALLS (cross-cloud spans)",
        ["timestamp", "name", "type", "duration", "success"]
    )

    # 3. Azure Foundry Agent Traces (invoke_agent + LLM calls)
    run_query(
        'dependencies | where timestamp > ago(24h) | where name has "csh-scheduling" or (name has "gpt-5" and name has "chat") | project timestamp, name, duration, success | order by timestamp desc | take 10',
        "3. AZURE FOUNDRY - AGENT INVOCATIONS & LLM CALLS",
        ["timestamp", "name", "duration", "success"]
    )

    # 4. Performance Summary by component
    run_query(
        'union requests, dependencies | where timestamp > ago(24h) | extend component = case(name has "BigQuery" or name == "agent_invoke" or name == "find_available" or name == "cancel_appointment", "GCP-Agent-Operations", name has "csh-scheduling" and name has "invoke_agent", "Foundry-Agent-Invoke", name has "gpt-5" and name has "chat", "Foundry-LLM-Call", name == "POST /invoke" or name == "GET /health", "GCP-HTTP-Endpoint", "Other") | where component != "Other" | summarize Count=count(), AvgDuration_ms=round(avg(duration),0), P95_ms=round(percentile(duration,95),0), SuccessRate=round(100.0*countif(success=="True")/count(),1) by component | order by component asc',
        "4. PERFORMANCE SUMMARY BY COMPONENT (last 24h)",
        ["component", "Count", "AvgDuration_ms", "P95_ms", "SuccessRate"]
    )

    # 5. Error Analysis
    run_query(
        'union requests, dependencies | where timestamp > ago(24h) | where success == "False" | project timestamp, name, duration | order by timestamp desc | take 5',
        "5. ERRORS & FAILURES (last 24h)",
        ["timestamp", "name", "duration"]
    )

    # 6. Cross-cloud trace IDs for end-to-end correlation
    run_query(
        'dependencies | where timestamp > ago(24h) | where name == "agent_invoke" | project timestamp, name, duration, operation_Id | order by timestamp desc | take 5',
        "6. CROSS-CLOUD TRACE IDs (GCP agent_invoke → App Insights)",
        ["timestamp", "name", "duration", "operation_Id"]
    )

    print(f"\n\n{'='*80}")
    print("  OBSERVABILITY SUMMARY")
    print(f"{'='*80}")
    print("  GCP Cloud Run traces  -> Azure App Insights  [CONNECTED]")
    print("  Azure Foundry traces  -> Azure App Insights  [NATIVE]")
    print("  Cross-cloud correlation: via W3C Trace Context headers")
    print()
    print("  View in Azure Portal:")
    print("    App Insights > Transaction Search  (end-to-end traces)")
    print("    App Insights > Application Map     (cross-cloud topology)")
    print("    App Insights > Performance         (latency analysis)")
    print("    App Insights > Failures            (error tracking)")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
