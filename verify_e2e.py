import requests
import time
import sys

def check(name, test_fn):
    try:
        res = test_fn()
        if res:
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ {name} -> Error: {e}")
        sys.exit(1)

print("--- STEP 4: HEALTH CHECK ALL FLASK SERVICES ---")
check("log-generator health", lambda: requests.get("http://localhost:5001/health").json() == {"status": "ok"})
check("anomaly-detector health", lambda: requests.get("http://localhost:5002/health").json() == {"status": "ok"})
check("dashboard health", lambda: requests.get("http://localhost:5003/health").json() == {"status": "ok"})

print("\n--- STEP 5: TEST LOG GENERATOR CONTROL API ---")
check("/status initial", lambda: requests.get("http://localhost:5001/status").status_code == 200)
check("/start generator", lambda: requests.get("http://localhost:5001/start").status_code == 200)
time.sleep(5)
status_chk = requests.get("http://localhost:5001/status").json()
check("/status streaming=True", lambda: status_chk.get("streaming") is True)
check("/rate valid", lambda: requests.post("http://localhost:5001/rate", json={"rate": 10}).status_code == 200)
check("/rate invalid", lambda: requests.post("http://localhost:5001/rate", json={"rate": 9999}).status_code == 400)
check("/stop generator", lambda: requests.get("http://localhost:5001/stop").status_code == 200)

print("\n--- STEP 6: TEST ANOMALY DETECTOR SECURITY ---")
url = "http://localhost:5002/log"
bad_payload = {"srcaddr": "10.0.0.1"}
good_payload = {"srcaddr": "10.0.1.1", "dstaddr": "10.1.0.1", "dstport": 80, "protocol": 6, "packets": 10, "bytes": 1024, "action": "ACCEPT"}

check("no token", lambda: requests.post(url, json=bad_payload).status_code == 401)
check("wrong token", lambda: requests.post(url, json=bad_payload, headers={"X-Internal-Token": "bad"}).status_code == 401)
check("valid token & payload", lambda: requests.post(url, json=good_payload, headers={"X-Internal-Token": "ARC-VpcStream-2026-SecureToken-XK9"}).status_code == 200)

print("\n--- STEP 7: TEST DASHBOARD UI ---")
check("dashboard root loads", lambda: requests.get("http://localhost:5003/").status_code == 200)
check("proxy /control/start", lambda: requests.post("http://localhost:5003/control/start").status_code == 200)
check("proxy /control/stop", lambda: requests.post("http://localhost:5003/control/stop").status_code == 200)

print("\n--- STEP 8: VERIFY INFLUXDB IS RUNNING ---")
influx = requests.get("http://localhost:8086/health").json()
check("influxdb health", lambda: influx.get("status") == "pass")

print("\n--- STEP 9: VERIFY GRAFANA IS RUNNING ---")
try:
    grafana = requests.get("http://localhost:3000/api/health").json()
    check("grafana health", lambda: grafana.get("database") == "ok")
except:
    print("❌ grafana health -> Could not connect / parse JSON. Status")
    sys.exit(1)

print("\nEndpoints checked successfully.")
