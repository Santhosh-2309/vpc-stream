# VPC-Stream Project Context

## What This Is
A microservices-based real-time VPC network anomaly
detection system built for DevOps IA3 evaluation.
Course: DevOps (24CS2018) | Karunya University
Register Number: URK23CS1003

## Project Goal
Simulate Virtual Private Cloud (VPC) network traffic logs,
detect anomalies in real time (DDoS, unauthorized access),
and display live alerts on a dashboard — all deployed using
a complete DevOps pipeline.

## Tech Stack
- Language: Python 3.11
- Microservice 1: Log Generator (Flask)
- Microservice 2: Anomaly Detector (Flask + WebSockets)
- Microservice 3: Live Dashboard (HTML + JS + WebSockets)
- Containerization: Docker (one Dockerfile per service)
- Orchestration: Kubernetes via Minikube
- IaC: Ansible
- CI/CD: Jenkins
- Version Control: Git + GitHub
- Database: None (in-memory stream processing)

## Project Structure
vpc-stream/
├── log-generator/
│   ├── app.py               # Generates fake VPC logs
│   ├── Dockerfile
│   └── requirements.txt
├── anomaly-detector/
│   ├── app.py               # Detects traffic spikes
│   ├── Dockerfile
│   └── requirements.txt
├── dashboard/
│   ├── app.py               # Serves live dashboard
│   ├── templates/
│   │   └── index.html       # Dashboard UI
│   ├── Dockerfile
│   └── requirements.txt
├── k8s/
│   ├── log-generator-deployment.yaml
│   ├── anomaly-detector-deployment.yaml
│   ├── dashboard-deployment.yaml
│   └── services.yaml
├── ansible/
│   └── setup.yml            # Provisions full environment
├── Jenkinsfile              # CI/CD pipeline definition
├── .gitignore               # Must include .env
├── context.md               # This file
└── README.md

## How The System Works
1. Log Generator continuously produces fake VPC traffic logs
   in JSON format and sends them to Anomaly Detector
2. Anomaly Detector reads incoming logs, checks if request
   rate exceeds threshold (500 req/s = anomaly)
3. If anomaly detected, pushes alert via WebSocket
4. Dashboard receives alert and displays red warning live
5. All 3 services run as separate Kubernetes pods
6. Jenkins auto-deploys when code is pushed to GitHub
7. Ansible sets up the entire environment in one command

## Microservice Communication
Log Generator → HTTP POST → Anomaly Detector
Anomaly Detector → WebSocket → Dashboard
Dashboard → Browser renders live alerts

## Security Rules (NEVER break these)
- All secrets and config values in .env files only
- Never hardcode ports, passwords, or API keys in code
- One Dockerfile per microservice only
- All Kubernetes YAML files validated before applying
- .env files must never be committed to GitHub
- Input validation on all Flask routes

## Code Style Rules
- Python: PEP8 formatting strictly
- YAML: 2 space indentation always (never tabs)
- Every function must have a docstring comment
- Keep each microservice app.py under 150 lines
- No unused imports in any file
- Meaningful variable names only (no x, y, z)

## Git Workflow Rules
- main branch is protected (PRs required to merge)
- Feature branches named: feature/service-name
  Example: feature/log-generator
           feature/anomaly-detector
           feature/dashboard
           feature/kubernetes
           feature/ansible
           feature/jenkins-pipeline
- Every merge via Pull Request only, never direct push
- Commit message format:
  feat: add log generation logic
  fix: correct threshold calculation
  docs: update README with setup steps
  chore: add Dockerfile for log-generator

## Kubernetes Rules
- Each microservice = one Deployment + one Service
- Always set resource limits (cpu, memory) in deployments
- Use labels consistently: app: vpc-stream, tier: backend
- Liveness and readiness probes required for each pod
- Never use latest tag for Docker images, always version

## Ansible Rules
- Single playbook: ansible/setup.yml
- Must install: Docker, Minikube, kubectl, Jenkins
- Must be idempotent (safe to run multiple times)
- Use variables for all version numbers

## Jenkins Pipeline Stages (in order)
Stage 1: Checkout     - Pull code from GitHub
Stage 2: Test         - Run Python unit tests
Stage 3: Build        - Build Docker images
Stage 4: Push         - Push images to Docker Hub
Stage 5: Deploy       - Apply Kubernetes manifests

## Evaluation Rubric Mapping
Version Control (8 marks):
  → Feature branches + PRs + clean commit history

CI/CD Pipeline (7 marks):
  → Jenkins 5-stage pipeline fully automated

Containerization (8 marks):
  → Docker + Kubernetes + self-healing pod demo

IaC (7 marks):
  → Ansible playbook full environment setup

## Demo Day Checklist (April 8, 2026)
□ Ansible playbook runs successfully in one command
□ All 3 pods running on Minikube
□ Live dashboard accessible in browser
□ Anomaly alert triggers and shows in dashboard
□ Jenkins pipeline completes all 5 stages
□ Self-healing demo: delete pod → Kubernetes restarts it
□ GitHub repo shows clean branch + PR history
□ Documentation complete, plagiarism under 10%

## Important Notes For Antigravity Agent
- Always use Python 3.11 syntax
- Always use Flask for microservices
- Never install packages globally, use requirements.txt
- Always add error handling (try/except) in Flask routes
- Always add logging to every microservice
- Docker base image: python:3.11-slim (keep images small)
- Kubernetes namespace: default
- All services communicate via Kubernetes service names
- WebSocket library: flask-socketio
```
