import urllib.request
import json
import sys

run_arg = sys.argv[1] if len(sys.argv) > 1 else "latest"

if run_arg == "latest":
    runs_url = "https://api.github.com/repos/georgebarbosa3090/XApp-RDL-F1/actions/runs"
    req_runs = urllib.request.Request(runs_url, headers={"User-Agent": "CI-Checker"})
    with urllib.request.urlopen(req_runs) as resp:
        runs_data = json.loads(resp.read().decode())
    latest_run = runs_data["workflow_runs"][0]
    run_id = str(latest_run["id"])
    print(f"Latest Run: ID={run_id}, Commit={latest_run.get('head_sha')[:7]} - {latest_run.get('head_commit', {}).get('message', '').splitlines()[0]}")
else:
    run_id = run_arg

url = f"https://api.github.com/repos/georgebarbosa3090/XApp-RDL-F1/actions/runs/{run_id}"
req = urllib.request.Request(url, headers={"User-Agent": "CI-Checker"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())

print(f"Run {run_id}: Status={data.get('status')}, Conclusion={data.get('conclusion')}")

jobs_url = f"{url}/jobs"
req_jobs = urllib.request.Request(jobs_url, headers={"User-Agent": "CI-Checker"})
with urllib.request.urlopen(req_jobs) as resp:
    jobs_data = json.loads(resp.read().decode())

for job in jobs_data.get("jobs", []):
    print(f"\nJob: {job.get('name')} | Status: {job.get('status')} | Conclusion: {job.get('conclusion')}")
    for step in job.get("steps", []):
        status = step.get("status")
        conclusion = step.get("conclusion")
        name = step.get("name")
        started_at = step.get("started_at")
        completed_at = step.get("completed_at")
        print(f"  Step: {name:<42} | {status:<11} | {str(conclusion):<8} | {started_at} -> {completed_at}")
