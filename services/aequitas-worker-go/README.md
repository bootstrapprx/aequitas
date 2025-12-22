# aequitas-worker-go

Go-based integrations and jobs worker for Aequitas. This service owns integrations and background jobs. It does **not** own accounting rules or data.

## Phase 1 — Operational Extraction (COMPLETE)

This service implements **Phase 1: Operational Extraction**, moving external integrations (QuickBooks) from Python to Go.

### What this service does

- **External integrations**: QuickBooks Online account sync
- **Job execution**: Asynchronous job processing with lifecycle tracking
- **Retry logic**: Exponential backoff for transient failures
- **Callback mechanism**: Reports results back to Python Core
- **Observability**: Structured JSON logging with canonical tracing headers

### What this service does NOT do

- ❌ No accounting validation
- ❌ No financial decision logic
- ❌ No ledger manipulation
- ❌ No mapping or classification (that's Python's job)
- ❌ No direct database writes (callbacks only)

> **Architecture Principle**: Go moves data. Python decides truth.

## Configuration

Set the following environment variables:

### Required
- `QBO_CLIENT_ID` - QuickBooks OAuth Client ID
- `QBO_CLIENT_SECRET` - QuickBooks OAuth Client Secret

### Optional
- `SERVICE_PORT` - HTTP port (default: `8080`)
- `LOG_LEVEL` - Logging level: `debug`, `info`, `error` (default: `info`)
- `QBO_ENV` - QuickBooks environment: `sandbox` or `production` (default: `sandbox`)
- `QBO_BASE_URL` - QuickBooks API base URL (auto-configured based on `QBO_ENV`)

## Run locally

```bash
cd services/aequitas-worker-go

# Set credentials (get from QuickBooks Developer Portal)
export QBO_CLIENT_ID="your-client-id"
export QBO_CLIENT_SECRET="your-client-secret"
export QBO_ENV="sandbox"

go run cmd/server/main.go
```

Service listens on `http://localhost:8080` by default.

## Build Docker image

```bash
cd services/aequitas-worker-go
docker build -t aequitas-worker-go .
```

## Endpoints

### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "aequitas-worker-go"
}
```

### Submit Job
```
POST /jobs
```

**Headers:**
- `X-Aequitas-Request-Id` (optional, auto-generated if missing)
- `X-Aequitas-Correlation-Id` (optional, auto-generated if missing)
- `X-Aequitas-Idempotency-Key` (optional, for idempotent operations)

**Request Body:**
```json
{
  "job_type": "qbo.sync_accounts",
  "company_id": "uuid",
  "payload": {
    "realm_id": "1234567890",
    "access_token": "bearer-token",
    "full_sync": false
  },
  "callback": {
    "url": "http://python-core:8000/api/v1/integrations/jobs/callback",
    "auth": "internal"
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "accepted"
}
```

## Supported Jobs

### `qbo.sync_accounts`

Fetches the chart of accounts from QuickBooks Online.

**Payload:**
- `realm_id` (string, required) - QuickBooks company realm ID
- `access_token` (string, required) - OAuth access token
- `full_sync` (boolean, optional) - Whether to perform full sync

**Result Format:**
```json
{
  "accounts": [
    {
      "id": "1",
      "name": "Cash",
      "type": "Bank",
      "subtype": "CashOnHand",
      "active": true,
      "currency": "USD",
      "source": "quickbooks"
    }
  ],
  "source": "quickbooks",
  "count": 245
}
```

**Callback Payload:**
```json
{
  "job_id": "uuid",
  "job_type": "qbo.sync_accounts",
  "company_id": "uuid",
  "status": "succeeded",
  "result": {
    "accounts": [...],
    "source": "quickbooks",
    "count": 245
  },
  "errors": []
}
```

## Architecture

### Job Lifecycle

1. **Accept** - Validate request, generate job ID, return immediately
2. **Execute** - Run job asynchronously in goroutine
3. **Retry** - Exponential backoff for transient failures (3 attempts)
4. **Callback** - Send results to Python Core via HTTP POST

### Observability

All operations are logged with:
- `request_id` - Unique per request
- `correlation_id` - Propagated across service boundaries
- `job_id` - Unique per job execution

Logs are structured JSON to stdout for aggregation.

### Error Handling

Errors follow the canonical error envelope:

```json
{
  "error": {
    "code": "AEQ_QBO_SYNC_FAILED",
    "message": "Human readable summary"
  }
}
```

Error codes:
- `AEQ_JOB_*` - Job execution errors
- `AEQ_QBO_*` - QuickBooks integration errors

## Development

### Run tests
```bash
go test ./...
```

### Format code
```bash
go fmt ./...
```

## Contract Compliance

This service strictly adheres to:
- [`LANGUAGE_MAP.md`](../../docs/canonical/LANGUAGE_MAP.md) - Language boundaries
- [`API_CONTRACTS.md`](../../docs/canonical/API_CONTRACTS.md) - Service contracts

**Critical Rules:**
- Go never validates accounting rules
- Go never writes to authoritative tables
- Go returns raw, neutral data structures
- Python remains the sole authority for financial truth
