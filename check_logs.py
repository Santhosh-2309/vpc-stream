import subprocess
import sys
import re

def check_logs(container, pattern):
    try:
        out = subprocess.check_output(["docker", "logs", container], stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        found = []
        for line in out.splitlines():
            if re.search(pattern, line, re.IGNORECASE):
                found.append(line)
        return found
    except Exception as e:
        return [f"Failed to fetch logs: {e}"]

print("--- STEP 10: CHECK CONTAINER LOGS FOR ERRORS ---")
issues = {}
issues["scratch-log-generator-1"] = check_logs("scratch-log-generator-1", r"error|critical|traceback")
issues["scratch-anomaly-detector-1"] = check_logs("scratch-anomaly-detector-1", r"error|critical|traceback")
issues["scratch-dashboard-1"] = check_logs("scratch-dashboard-1", r"error|critical|traceback")
issues["scratch-influxdb-1"] = check_logs("scratch-influxdb-1", r"error|critical")
issues["scratch-grafana-1"] = check_logs("scratch-grafana-1", r"error|critical")

has_errors = False
for c, lines in issues.items():
    if lines:
        has_errors = True
        print(f"\n{c} logs contained issues:")
        for l in lines[:10]: # Print first 10
            print("  ", l)

if not has_errors:
    print("\n✅ No critical errors in container logs")
