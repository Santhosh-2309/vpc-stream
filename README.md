# VPC-Stream

Real-time VPC network anomaly detection system built with microservices architecture.

## Overview

VPC-Stream simulates AWS VPC Flow Logs using the CICIDS2017 dataset, detects 3 types of network anomalies in real time (DDoS, Port Scan, Unauthorized Access), persists all data to InfluxDB, and visualizes live alerts on a glassmorphism dashboard with historical trends on Grafana.

Built for DevOps IA3 evaluation — Course: DevOps (24CS2018) | Karunya University

**Team ARC** — Adaptive Resilient Computing

## Architecture

| Service | Port | Description |
|---------|------|-------------|
| Log Generator | 5001 | Streams CICIDS2017 dataset rows in VPC Flow Log format |
| Anomaly Detector | 5002 | Detects DDoS, Port Scan, Unauthorized anomalies; writes to InfluxDB |
| Dashboard | 5003 | Dark glassmorphism UI with live alerts, traffic graph, control panel |
| InfluxDB | 8086 | Time-series database for all logs and anomaly events |
| Grafana | 3000 | Historical traffic dashboards auto-provisioned from InfluxDB |

## Tech Stack

- **Language:** Python 3.11
- **Framework:** Flask + Flask-SocketIO
- **Database:** InfluxDB 2.7
- **Monitoring:** Grafana
- **Containerization:** Docker
- **Orchestration:** Kubernetes (Minikube)
- **IaC:** Ansible
- **CI/CD:** Jenkins (6-stage pipeline with truffleHog secret scan)
- **Dataset:** CICIDS2017

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Santhosh-2309/vpc-stream.git
cd vpc-stream

# 2. Copy environment variables
cp .env.example .env
# Edit .env with your actual credentials

# 3. Run with Docker Compose
docker-compose up --build

# 4. Access services
# Dashboard:  http://localhost:5003
# Grafana:    http://localhost:3000
# InfluxDB:   http://localhost:8086
```

## Project Structure

```
vpc-stream/
├── log-generator/          # Microservice 1: CICIDS2017 log streamer
├── anomaly-detector/       # Microservice 2: DDoS/PortScan/Unauthorized detection
├── dashboard/              # Microservice 3: Glassmorphism live dashboard
├── k8s/                    # Kubernetes deployment manifests
├── ansible/                # Infrastructure provisioning playbook
├── grafana/                # Grafana auto-provisioning configs
├── Jenkinsfile             # 6-stage CI/CD pipeline
├── docker-compose.yml      # Local development orchestration
├── .env.example            # Environment variable template
├── context.md              # Project rules and architecture
├── AGENTS.md               # AI agent safety rules
└── PRD.md                  # Build task tracker
```

## DevOps Pipeline (Jenkins)

| Stage | Description |
|-------|-------------|
| 0. Secret Scan | truffleHog scans for committed secrets |
| 1. Checkout | Pull code from GitHub |
| 2. Test | Run pytest for all 3 microservices |
| 3. Build | Build versioned Docker images |
| 4. Push | Push images to Docker Hub |
| 5. Deploy | Apply Kubernetes manifests to Minikube |

## Security

- All secrets in `.env` files only (never hardcoded)
- Inter-service auth via `X-Internal-Token` header
- Security headers on all Flask responses
- Rate limiting on control endpoints
- Input validation on all routes
- truffleHog secret scanning in CI/CD

## License

This project is for academic evaluation purposes.
