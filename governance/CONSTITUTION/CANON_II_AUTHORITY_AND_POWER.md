# CANON II — AUTHORITY, BOUNDARIES & POWER

(Who may decide, who may act, who may suggest)

### 1. Purpose and Scope

This canon defines power separation and enforcement boundaries.


### 2. Authority Hierarchy

Authority flows as:

Accounting Truth → Backend → API Contracts → UI / Integrations

Nothing bypasses this order.

### 3. Separation of Responsibilities

Humans decide

Systems enforce

Intelligence suggests

These roles never collapse.

### 4. Backend as Final Authority

The backend is the final arbiter of truth.
UI and integrations are advisory layers only.

### 5. API Contracts as Law

APIs define:

allowed actions,

required validations,

deterministic outcomes.

Breaking a contract is a system failure.

### 6. Forbidden Operations

Prohibited:

bypassing validation

direct database mutation

UI-driven truth

silent retries with side effects

### 7. Idempotency and Determinism

Repeated actions must produce the same result or fail explicitly.

Idempotency is mandatory.

### 8. Language Responsibility Boundaries

Each language has a defined role.
Logic does not leak across boundaries.

### 9. Permission Models

No role may exceed its scope.
Even superusers are constrained.

### 10. Auditability and Traceability

Every action must be:

attributable,

timestamped,

explainable.

### 11. Explicit Failure

Errors must be loud, specific, and actionable.
Silent failure is forbidden.

### 12. Prohibited Shortcuts

There are no “temporary” bypasses.
There are no “just this once” exceptions.

### 13. Final Declaration

Power is constrained to protect truth.