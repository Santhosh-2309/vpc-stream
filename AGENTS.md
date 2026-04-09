# AGENTS.md — Safety Rules for VPC-Stream

## 🔒 Secret Management
- Never hardcode API keys, passwords, tokens, or credentials in source code
- All secrets in .env files only
- .env files in .gitignore, never committed
- Use os.environ.get("VAR_NAME") always
- On startup, validate all required env vars — exit with clear error if missing

## 🛡️ Input Validation
- Validate all incoming request data on every Flask route
- Check required fields, correct types, acceptable ranges
- Sanitize all user-provided input
- Return 400/422 with clear error messages for invalid input
- Never trust client-side data

## 🔐 Internal Service Authentication
- All inter-service HTTP requests must include X-Internal-Token header
- Token loaded from .env only, never hardcoded
- Anomaly Detector must reject any request missing valid token with 401

## 🛡️ Security Headers
- All Flask responses must include via before_request hook:
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block

## 🚦 Rate Limiting
- Log Generator /start /stop /rate /status endpoints: 10 requests/minute per IP using flask-limiter
- Never leave control endpoints completely open

## ⏱️ Request Timeouts
- All outgoing HTTP requests must use timeout=5
- Never use requests.get() or requests.post() without timeout parameter

## 🔑 Default Credentials
- Never use default credentials for any service
- Jenkins admin/admin must be changed on first run
- InfluxDB and Grafana credentials must come from .env only

## 🌊 Data Sources
- Never use randomly generated fake data
- Always use CICIDS2017 dataset for log generation
- Logs must follow AWS VPC Flow Log format strictly

## 🗑️ File Deletion Safety
- Always ask for explicit confirmation before deleting any file or directory
- Never auto-delete without user approval
- List files to be deleted and wait for confirmation

## 🐳 Docker Safety
- Containers must run as non-root users where possible
- Never use latest tag — always version Docker images

## ☸️ Kubernetes Safety
- All deployments must have resource limits (cpu, memory)
- Never apply unvalidated YAML manifests

## 🔍 Secret Scanner
- Jenkins Stage 0 must run truffleHog before any build
- Pipeline must fail if secrets are detected in repo

## 📋 General
- try/except with logging on every Flask route
- Never expose stack traces to end users
- Log all security events: failed token, invalid input, anomaly detected
- All outgoing HTTP: timeout=5 always
