# PRD — VPC-Stream Build Tasks

## Project Overview
VPC-Stream is a microservices-based real-time VPC network anomaly detection system.
5 services communicate to generate, analyze, persist, and visualize network traffic anomalies.

---

## Build Tasks (In Order)

### Phase 1: Log Generator Microservice
- [ ] Create log-generator/app.py — Flask app that streams CICIDS2017 CSV rows
- [ ] Create log-generator/requirements.txt
- [ ] On startup: validate all required env vars, exit with error if missing
- [ ] Load CICIDS2017 dataset CSV and stream rows as logs
- [ ] Format all logs in AWS VPC Flow Log format (srcaddr, dstaddr, protocol, packets, bytes, action)
- [ ] Never generate random fake logs
- [ ] Implement /start /stop /rate /status /health endpoints
- [ ] Rate limit control endpoints: 10 req/min per IP (flask-limiter)
- [ ] Add X-Internal-Token header to all outgoing HTTP POST requests
- [ ] Add security headers to all responses
- [ ] Add logging and try/except on all routes
- [ ] Validate all inputs on /rate endpoint

### Phase 2: Anomaly Detector Microservice
- [ ] Create anomaly-detector/app.py — Flask + SocketIO
- [ ] Create anomaly-detector/requirements.txt
- [ ] On startup: validate all required env vars, exit with error if missing
- [ ] Validate X-Internal-Token on all incoming requests — return 401 if missing/invalid
- [ ] Implement DDoS detection: >500 req/s from single source IP
- [ ] Implement Port Scan detection: sequential destination ports from single source IP
- [ ] Implement Unauthorized detection: source IP in blocked IP list from .env
- [ ] Write every log entry to InfluxDB — measurement: vpc_logs
- [ ] Write every anomaly to InfluxDB — measurement: anomaly_events (tags: type, severity, src_ip)
- [ ] Emit WebSocket alert on every anomaly detected
- [ ] Expose /health endpoint
- [ ] Add security headers to all responses
- [ ] Add logging and try/except on all routes

### Phase 3: Dashboard Microservice
- [ ] Create dashboard/app.py — Flask + SocketIO
- [ ] Create dashboard/templates/index.html — dark glassmorphism UI
- [ ] Create dashboard/requirements.txt
- [ ] On startup: validate all required env vars, exit with error if missing
- [ ] Dark glassmorphism design — black background, frosted glass cards, neon accents
- [ ] Animated real-time traffic graph using Chart.js (requests/second, last 60 seconds)
- [ ] Live alert feed with severity badges: CRITICAL (red), WARNING (orange), INFO (blue)
- [ ] Live counters: Total Logs Processed, Anomalies Detected, Current req/s
- [ ] Log Generator control panel: Start / Stop / Rate buttons calling Log Generator API
- [ ] WebSocket client receiving alerts from Anomaly Detector
- [ ] Expose /health endpoint
- [ ] Add security headers to all responses

### Phase 4: Dockerfiles
- [ ] Create log-generator/Dockerfile — python:3.11-slim, non-root user
- [ ] Create anomaly-detector/Dockerfile — python:3.11-slim, non-root user
- [ ] Create dashboard/Dockerfile — python:3.11-slim, non-root user
- [ ] Version-tag all images (never latest)
- [ ] Minimize layers, optimize image size
- [ ] Test each container runs independently

### Phase 4.5: Infrastructure Services
- [ ] Add InfluxDB 2.7 to docker-compose.yml — credentials from .env, bucket: vpc_stream, org: vpc_stream_org
- [ ] Add Grafana to docker-compose.yml — auto-provision InfluxDB datasource via grafana/provisioning/datasources/influxdb.yml
- [ ] Create Grafana dashboard JSON (grafana/provisioning/dashboards/vpc-stream.json) showing:
      - Traffic rate over time
      - Anomaly count by type
      - Top source IPs
- [ ] Test InfluxDB and Grafana run together locally via docker-compose

### Phase 5: Kubernetes Manifests
- [ ] Create k8s/log-generator-deployment.yaml — Deployment + Service, resource limits, /health probe
- [ ] Create k8s/anomaly-detector-deployment.yaml — Deployment + Service, resource limits, /health probe
- [ ] Create k8s/dashboard-deployment.yaml — Deployment + Service, resource limits, /health probe
- [ ] Create k8s/influxdb-deployment.yaml — Deployment + Service, port 8086
- [ ] Create k8s/grafana-deployment.yaml — Deployment + Service, port 3000
- [ ] Create k8s/influxdb-pvc.yaml — PersistentVolumeClaim for InfluxDB data
- [ ] Resource limits on all deployments (cpu, memory)
- [ ] Labels: app: vpc-stream, tier: backend/frontend/database
- [ ] Liveness and readiness probes using /health for all 3 Flask services
- [ ] Never use latest tag

### Phase 6: Ansible Playbook
- [ ] Create ansible/setup.yml — single idempotent playbook
- [ ] Install Docker (version from variable)
- [ ] Install Minikube (version from variable)
- [ ] Install kubectl (version from variable)
- [ ] Install Jenkins (version from variable)
- [ ] Safe to run multiple times

### Phase 6.5: Unit Tests
- [ ] Create log-generator/tests/test_app.py — test /health /start /stop /rate /status
- [ ] Create anomaly-detector/tests/test_detection.py — test all 3 anomaly detection functions with mock data
- [ ] Create dashboard/tests/test_app.py — test /health endpoint
- [ ] All tests must pass: pytest --tb=short

### Phase 7: Jenkinsfile
- [ ] Create Jenkinsfile at project root
- [ ] Stage 0 — Secret Scan: run truffleHog, fail pipeline if secrets found
- [ ] Stage 1 — Checkout: pull from GitHub
- [ ] Stage 2 — Test: run pytest for all 3 microservices
- [ ] Stage 3 — Build: build versioned Docker images
- [ ] Stage 4 — Push: push to Docker Hub
- [ ] Stage 5 — Deploy: apply k8s manifests to Minikube
- [ ] Post-build: notifications and cleanup

---

## Demo Day Checklist (April 8, 2026)
- [ ] Ansible provisions entire environment in one command
- [ ] All 5 services running on Minikube (3 Flask + InfluxDB + Grafana)
- [ ] Live dashboard accessible in browser
- [ ] All 3 anomaly types trigger and show on dashboard
- [ ] InfluxDB persisting data across pod restarts
- [ ] Grafana showing historical traffic graph
- [ ] Jenkins pipeline completes all 6 stages clean
- [ ] pytest runs clean in Jenkins Stage 2
- [ ] Self-healing demo: delete pod → Kubernetes restarts it
- [ ] GitHub shows clean branch + PR history
- [ ] /health returns 200 on all 3 Flask services
- [ ] Documentation complete, plagiarism under 10%
