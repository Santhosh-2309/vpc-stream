# VPC-Stream Project Rules

## What This Is
A microservices-based real-time VPC network anomaly detection system built for DevOps IA3 evaluation.
- Course: DevOps (24CS2018) | Karunya University
- Register Number: URK23CS1003
- Team: ARC — Adaptive Resilient Computing

## Project Goal
Stream real CICIDS2017 network traffic logs in AWS VPC Flow Log format, detect 3 types of anomalies in real time, persist all data to InfluxDB, visualize live alerts on a glassmorphism dashboard and historical trends on Grafana — all deployed via a complete DevOps pipeline.

## Tech Stack
- Language: Python 3.11
- Microservice 1: Log Generator (Flask + flask-limiter)
- Microservice 2: Anomaly Detector (Flask + flask-socketio + influxdb-client)
- Microservice 3: Dashboard (Flask + flask-socketio + Chart.js)
- Database: InfluxDB 2.7 (time-series, self-hosted, free OSS)
- Monitoring: Grafana (connected to InfluxDB, auto-provisioned)
- Containerization: Docker (one Dockerfile per microservice)
- Orchestration: Kubernetes via Minikube
- IaC: Ansible
- CI/CD: Jenkins
- Version Control: Git + GitHub
- Dataset: CICIDS2017 (real network traffic dataset)
- Log Format: AWS VPC Flow Log format

## Microservice Communication
Log Generator → HTTP POST (with X-Internal-Token) → Anomaly Detector
Anomaly Detector → WebSocket → Dashboard
Anomaly Detector → influxdb-client → InfluxDB
Dashboard → Browser renders live alerts + control panel
Grafana → queries InfluxDB → historical dashboards

## Anomaly Types
1. DDoS — request rate exceeds 500 req/s from single source IP
2. Port Scan — sequential destination ports detected from single source IP
3. Unauthorized — source IP matches blocked IP list (loaded from .env)

## Security Rules
- All secrets and config values in .env files only
- Never hardcode ports, passwords, API keys, tokens in code
- One Dockerfile per microservice only
- All Kubernetes YAML files validated before applying
- .env files must never be committed to GitHub
- Input validation on all Flask routes
- All inter-service HTTP requests must include X-Internal-Token header (value from .env)
- Never use default credentials for Jenkins, InfluxDB, or Grafana
- InfluxDB token must come from .env only
- All Flask responses must include security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)
- Log Generator control API rate limited: 10 requests/minute per IP
- All outgoing HTTP requests must set timeout=5
- On startup, every microservice must validate all required env vars are present — if missing, log error and exit with clear message
- Never expose stack traces or internal errors to end users

## Code Style Rules
- Python: PEP8 strictly
- YAML: 2-space indentation always
- Every function must have a docstring
- Keep each microservice app.py under 150 lines
- No unused imports
- Meaningful variable names only
- try/except with logging on every Flask route
- Log all security-relevant events (failed token, invalid input, anomaly detected)

## Git Workflow Rules
- main branch is protected (PRs required)
- Feature branches: feature/log-generator, feature/anomaly-detector, feature/dashboard, feature/kubernetes, feature/ansible, feature/jenkins-pipeline
- Every merge via Pull Request only
- Commit format: feat: / fix: / docs: / chore:

## Kubernetes Rules
- Each service = one Deployment + one Service
- Resource limits required on all deployments (cpu, memory)
- Labels: app: vpc-stream, tier: backend/frontend/database
- Liveness and readiness probes using /health endpoints for Flask services
- Never use latest tag for Docker images, always version
- InfluxDB must have PersistentVolumeClaim so data survives pod restarts

## Ansible Rules
- Single playbook: ansible/setup.yml
- Must install: Docker, Minikube, kubectl, Jenkins
- Must be idempotent
- Use variables for all version numbers

## Jenkins Pipeline Stages
0. Secret Scan — run truffleHog to scan for committed secrets
1. Checkout — pull code from GitHub
2. Test — run pytest for all 3 microservices
3. Build — build Docker images
4. Push — push versioned images to Docker Hub
5. Deploy — apply Kubernetes manifests
