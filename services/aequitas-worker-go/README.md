# aequitas-worker-go

Go-based integrations and jobs worker for Aequitas. This service owns integrations and background jobs. It does **not** own accounting rules or data.

## What this is
- Minimal scaffold for the Go integrations/job layer.
- Exposes `/health` and `/jobs` with canonical tracing headers.
- Structured JSON logging with request/correlation IDs.

## What this is NOT
- No accounting logic, validations, or ledger access.
- No QuickBooks or external connectors yet.
- No queues or background workers implemented.

## Run locally
```bash
cd services/aequitas-worker-go
go run cmd/server/main.go
```

Service listens on `SERVICE_PORT` (default `8080`).

## Build Docker image
```bash
cd services/aequitas-worker-go
docker build -t aequitas-worker-go .
```

## Endpoints
- `GET /health` → `{ "status": "ok", "service": "aequitas-worker-go" }`
- `POST /jobs` → `{ "job_id": "<uuid>", "status": "accepted" }` (scaffold only)
