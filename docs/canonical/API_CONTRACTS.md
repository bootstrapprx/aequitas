# 🔗 Aequitas — API Contracts (Canonical)

> **Canonical document**
> Defines the official service boundaries and API contracts between:
>
> * **Python Core (Authority)**
> * **Go Workers (Integrations & Jobs)**
> * **Rust Engines (High-Performance Compute)**
>
> Any integration that violates these contracts is **invalid by default**.

---

## 1) Non‑Negotiable Principles

### 1.1 Authority vs Execution

* **Python is the sole authority** for accounting truth.
* **Go moves data** and performs integration jobs.
* **Rust computes** heavy matching/analytics and returns *candidates*, never decisions.
* **PostgreSQL stores historical truth** and deterministic aggregates.

### 1.2 Determinism & Auditability

All cross-service outputs must be:

* deterministic given the same inputs
* traceable (request IDs, correlation IDs)
* explainable (why a result was produced)

### 1.3 Idempotency is mandatory

Any API that can be called more than once must support idempotency.

---

## 2) Service Catalog

### 2.1 Python Core API (FastAPI)

**Role:** accounting authority, orchestration, validations

**Owns:**

* Companies, users, permissions
* ChartForge / master chart
* Accounting engine (journal, ledger, trial balance, statements)
* Mapping decisions (accept/reject)

**Interfaces:**

* REST/JSON for synchronous operations
* Background job triggers (async patterns)

### 2.2 Go Worker Service (Jobs)

**Role:** integrations & long-running tasks

**Owns:**

* QuickBooks sync pipelines
* webhook ingestion
* retry queues
* scheduled jobs

**Interfaces:**

* Pull work from queue OR receive job requests from Python
* Push results back to Python via callback endpoint OR write staging tables

### 2.3 Rust Engine Service (Compute)

**Role:** high-performance computation

**Owns:**

* similarity scoring
* clustering
* candidate generation
* large consolidation computations (compute-only)

**Interfaces:**

* HTTP/gRPC compute endpoints
* never writes authoritative ledger data

---

## 3) Canonical Cross‑Service Headers

All inter-service HTTP calls MUST include:

* `X-Aequitas-Request-Id`: UUIDv4 (created by caller)
* `X-Aequitas-Correlation-Id`: UUIDv4 (propagated across calls)
* `X-Aequitas-Idempotency-Key`: string (for idempotent operations)
* `X-Aequitas-Actor`: `system|user:<uuid>`
* `X-Aequitas-Company-Id`: company UUID (when company-scoped)
* `X-Aequitas-Contract-Version`: e.g. `2025-12-22`

---

## 4) Canonical Error Envelope

All services must return errors in this structure:

```json
{
  "error": {
    "code": "AEQ_<DOMAIN>_<NAME>",
    "message": "Human readable summary",
    "details": {"any": "structured context"},
    "request_id": "uuid",
    "correlation_id": "uuid"
  }
}
```

### 4.1 Error Code Naming

* `AEQ_AUTH_*` authentication/authorization
* `AEQ_QBO_*` QuickBooks integration
* `AEQ_MAP_*` mapping engine
* `AEQ_ACCT_*` accounting
* `AEQ_DATA_*` database / integrity
* `AEQ_ENGINE_*` rust compute engines

---

## 5) Contract: Python ↔ Go (Integrations & Jobs)

### 5.1 Pattern A — Python triggers a job, Go executes

**Endpoint (Python → Go):**

`POST /jobs`

**Request (example):**

```json
{
  "job_type": "qbo.sync_accounts",
  "company_id": "uuid",
  "payload": {
    "realm_id": "1234567890",
    "full_sync": false
  },
  "callback": {
    "url": "/api/v1/integrations/jobs/callback",
    "auth": "internal"
  }
}
```

**Response:**

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

### 5.2 Pattern B — Go calls back with results

**Endpoint (Go → Python):**

`POST /api/v1/integrations/jobs/callback`

**Callback payload:**

```json
{
  "job_id": "uuid",
  "job_type": "qbo.sync_accounts",
  "company_id": "uuid",
  "status": "succeeded",
  "result": {
    "staged": {
      "accounts": 245
    },
    "source_checksum": "sha256:...",
    "notes": ["Fetched 245 accounts from QBO"]
  },
  "errors": []
}
```

### 5.3 Staging rule (critical)

Go must **never** directly mutate authoritative accounting tables.

Go may:

* write to **staging tables** (e.g., `staging_qbo_accounts`)
* or return payloads for Python to ingest

Python then:

* validates
* deduplicates
* applies idempotently
* logs audit trail

### 5.4 Idempotency (jobs)

* `X-Aequitas-Idempotency-Key` for `POST /jobs`
* same key + same job_type + same company_id must return the **same `job_id`**

---

## 6) Contract: Python ↔ Rust (Compute)

### 6.1 Mapping Candidates

**Endpoint (Python → Rust):**

`POST /engine/mapping/candidates`

**Request:**

```json
{
  "company_id": "uuid",
  "run_id": "uuid",
  "company_accounts": [
    {"id": "uuid", "name": "Bank Charges", "type": "Expense", "code": ""}
  ],
  "master_accounts": [
    {"id": "uuid", "code": "62010", "name": "Bank Service Charges"}
  ],
  "options": {
    "top_k": 5,
    "min_score": 0.70,
    "use_embeddings": true
  }
}
```

**Response (candidates only):**

```json
{
  "run_id": "uuid",
  "candidates": [
    {
      "company_account_id": "uuid",
      "suggestions": [
        {
          "master_account_id": "uuid",
          "score": 0.91,
          "signals": {
            "name_similarity": 0.88,
            "embedding_similarity": 0.94,
            "type_compatibility": 1.0
          },
          "explain": ["High semantic similarity", "Category compatible"]
        }
      ]
    }
  ],
  "metrics": {"elapsed_ms": 128}
}
```

### 6.2 Rust restrictions (hard)

Rust must never:

* write to `journal_entries`, `journal_entry_lines`, `account_balances`
* create mappings as authoritative truth
* apply accounting rules

Rust may:

* return candidates, scores, and explain signals

Python must:

* apply business rules
* resolve conflicts
* persist mappings
* log audit trail

### 6.3 Consolidation compute

**Endpoint (Python → Rust):**

`POST /engine/consolidation/compute`

Rust returns:

* computed aggregates
* reconciliation diagnostics
* never posts entries

Python decides:

* elimination entries
* final consolidated statements

---

## 7) Contract Versioning

### 7.1 Version field

All inter-service requests must send:

* `X-Aequitas-Contract-Version: YYYY-MM-DD`

### 7.2 Breaking change policy

* breaking changes require a new version date
* services must support N and N-1 for a deprecation window

---

## 8) Security & Trust Boundaries

### 8.1 Internal Auth

Inter-service calls must be authenticated using one of:

* mTLS (preferred)
* internal JWT with service identity
* network policy (last resort)

### 8.2 Least privilege

* Go service credentials cannot post to accounting endpoints
* Rust service has no DB write creds (prefer none at all)

---

## 9) Observability

All services must log:

* request_id
* correlation_id
* company_id
* actor
* duration
* outcome (success/error code)

---

## 10) Canonical “Who Owns What” Summary

* **Python** owns truth, validation, persistence, audit
* **Go** owns data movement and reliability under failure
* **Rust** owns compute-heavy suggestions and aggregates
* **SQL** owns deterministic aggregation and historical truth
* **TS** owns UX and visualization

---

**Aequitas Contract Motto**

> Engines suggest. Workers move. Python decides.
