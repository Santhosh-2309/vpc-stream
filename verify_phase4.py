import os

root = r"c:\Users\Admin\.gemini\antigravity\scratch"
svcs = ["log-generator", "anomaly-detector", "dashboard"]
ports = ["5001", "5002", "5003"]

print("=== VERIFICATION ===\n")
for i, s in enumerate(svcs):
    df = open(os.path.join(root, s, "Dockerfile")).read()
    rf = open(os.path.join(root, s, "requirements.txt")).read()
    lc = len(df.strip().splitlines())
    print(f"{s}:")
    print(f"  Dockerfile lines:  {lc}")
    print(f"  python:3.11-slim:  {'python:3.11-slim' in df}")
    print(f"  appuser:           {'appuser' in df}")
    print(f"  ARG VERSION:       {'ARG VERSION' in df}")
    print(f"  LABEL version:     {'LABEL version' in df}")
    print(f"  EXPOSE {ports[i]}:       {'EXPOSE ' + ports[i] in df}")
    print(f"  gunicorn in req:   {'gunicorn' in rf}")
    if i > 0:
        print(f"  eventlet in req:   {'eventlet' in rf}")
        print(f"  eventlet in CMD:   {'eventlet' in df}")
    print()

print("=== REQUIREMENTS ===\n")
for s in svcs:
    rf = open(os.path.join(root, s, "requirements.txt")).read()
    print(f"--- {s}/requirements.txt ---")
    print(rf)
