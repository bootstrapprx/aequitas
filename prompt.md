
# 🔒 MASTER PROMPT — Phase 3C Implementation (CODE + CANONICAL DOCS)

**Role:** `api-engineer` (contract-enforcer / backend guardian)

**Mission:**
Implement **Phase 3C** of the Aequitas accounting system by converting frozen specifications into **working FastAPI code**, while also **canonizing documentation structure** so contracts, DTOs, and API boundaries become authoritative and discoverable.

This is a **code-first execution task**, not a documentation exercise.

---

## 🔐 Authoritative Inputs (Read, Do Not Redesign)

These documents are **frozen contracts**:

1. `PHASE_3C1_DTO_SPECIFICATION.md`
   → Canonical DTOs, field classification, immutability overlays

2. `PHASE_3C2_WRITE_APIS.md`
   → Write API inventory, controller skeletons, rejection matrices, audit rules

3. `API_BOUNDARIES.md`
   → Allowed / forbidden operations, permission model, security rationale

4. PostgreSQL schema at Alembic **revision 023 (head)**
   → Database is the final authority

---

## 🚫 Non-Negotiable Constraints

* ❌ No force flags
* ❌ No bypassing validation
* ❌ No partial writes
* ❌ No silent coercion
* ❌ No business logic in controllers
* ❌ No mutation of POSTED entries (except VOID)
* ❌ No mutation of LOCKED accounts (except allowed fields)
* ❌ No bulk write endpoints
* ❌ No cross-company writes
* ❌ No undocumented fields in APIs

**Assume hostile or buggy clients at all times.**

---

## ✅ Required Guarantees

* UUID-only references (no string FKs)
* Enum values exactly match PostgreSQL enums
* Deterministic failures with explicit error codes
* Transactional service layer
* Database + service + API invariants must agree
* Error responses always follow the canonical shape

```json
{
  "error_code": "LOCKED_ACCOUNT | STATE_CONFLICT | ...",
  "message": "Human-readable explanation",
  "details": { "field": "context" }
}
```

---

## 📦 Deliverables (MANDATORY)

### **A. Canonical Documentation Canonization (FIRST STEP)**

1. **Create canonical folder structure:**

```
docs/
└── canonical/
    ├── README.md
    ├── DATA_DICTIONARY.md
    ├── API_BOUNDARIES.md
    ├── PHASE_3C1_DTO_SPECIFICATION.md
    └── PHASE_3C2_WRITE_APIS.md
```

2. **Move / rename documents** into this folder using **exact names above**.
3. **Create `docs/canonical/README.md`** that:

   * Explains what “canonical” means
   * Declares these documents as authoritative contracts
   * States that code must conform to them, not vice-versa
4. **Update root `README.md`**:

   * Add a “Canonical Contracts” section
   * Link to `docs/canonical/README.md`
   * Explicitly state that API behavior, DTOs, and accounting rules are governed there

⚠️ This step is required **before** touching API code.

---

### **B. Phase 3C-2 — Write API Implementation (CODE)**

Implement **all 17 write endpoints** defined in `PHASE_3C2_WRITE_APIS.md` as working FastAPI code.

#### 1. DTOs (from Phase 3C-1)

* Create Pydantic schemas under:

  ```
  backend/app/schemas/accounting/
  ```
* Split clearly into:

  * Create DTOs
  * Update DTOs
  * Response DTOs
* Enforce immutability rules at validation + service layer

#### 2. Routers & Controllers

Create or refactor routers under:

```
backend/app/api/v1/routes/
```

Required routers:

* `accounting_chart.py`
* `journal_entries.py`
* `fiscal_periods.py`
* `chart_templates.py` (admin)

Controllers must:

1. Check permissions (PermissionService)
2. Validate DTO consistency
3. Delegate to service layer
4. Map service exceptions → canonical errors
5. Return response DTOs

**No business logic allowed in controllers.**

#### 3. Permission Service Alignment

Ensure `PermissionService` exposes and is used consistently:

* `can_view_company(user_id, company_id)`
* `can_manage_company(user_id, company_id)`
* Superuser checks where required (unlock, reopen)

#### 4. Canonical Error System

Create a **single error translation module**, e.g.:

```
backend/app/api/errors.py
```

Responsibilities:

* Define canonical error codes
* Map service exceptions → HTTP status + payload
* Used by all controllers

---

### **C. Minimal Integration Tests (MANDATORY)**

Add tests proving invariants actually hold:

1. Journal Entry lifecycle:

   * Create DRAFT
   * Update DRAFT
   * POST (balanced only)
   * Reject POST when unbalanced

2. Account locking:

   * Lock account
   * Reject immutable field updates
   * Allow cosmetic updates

3. Fiscal periods:

   * Prevent overlap
   * Close with no drafts
   * Reopen requires superuser

Tests must fail if:

* Constraints are bypassed
* Wrong error codes are returned

---

## 📋 Output Requirements

At completion, provide:

1. **List of files created/modified**
2. **Confirmation checklist**:

   * All endpoints implemented
   * All DTOs enforced
   * All docs moved & linked
   * All tests passing
3. **Explicit note of any deviations** (ideally none)

---

## 🧭 Philosophy Reminder

* Documentation is law
* Database is the final authority
* APIs are contracts, not conveniences
* Accounting correctness > developer comfort
* If unsure, **reject the request**

---

**Begin execution now. Do not ask follow-up questions.**
