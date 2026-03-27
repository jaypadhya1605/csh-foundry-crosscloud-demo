import subprocess, json

r = subprocess.run([
    "az", "monitor", "app-insights", "query",
    "--app", "appinsights-healthcare-foundry-001",
    "-g", "rg-healthcareai-demo-jp-001",
    "--analytics-query",
    'requests | where timestamp > ago(24h) | where cloud_RoleName == "csh-scheduling-agent" | project timestamp, name, duration, success | take 1',
    "-o", "json",
], capture_output=True, text=True, shell=True)

d = json.loads(r.stdout)
cols = [c["name"] for c in d["tables"][0]["columns"]]
print(f"Columns ({len(cols)}):")
for c in cols:
    print(f"  {c}")
rows = d["tables"][0]["rows"]
print(f"\nRows: {len(rows)}")
if rows:
    for i, c in enumerate(cols):
        print(f"  {c} = {str(rows[0][i])[:80]}")
