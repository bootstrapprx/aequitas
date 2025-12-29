---
type: decision
date: 2025-12-24
status: implemented
canon: [Canon I, Canon III]
phase: P7
---

# DECISION: Sandbox Schema Isolation

## Context

The Sandbox Engine allows users to create "what-if" scenarios for tax planning:
- Clone accounting data for projection
- Simulate tax liabilities under different assumptions
- Analyze business decisions without affecting truth tables

**Problem**: How to prevent sandbox projections from contaminating accounting truth?

## Options Considered

### 1. Soft-Delete Flags (Rejected)
- Add `is_sandbox` boolean to existing tables
- Filter queries with `WHERE is_sandbox = false`
- **Risk**: Accidental JOIN contamination, query errors exposing sandbox data
- **Violates**: Canon I (Accounting Truth), Canon III (Immutability)

### 2. Sandbox Schema Isolation (CHOSEN)
- Create separate PostgreSQL schema: `sandbox.*`
- Truth tables remain in `public.*` schema
- Physical separation prevents accidental contamination
- **Aligns with**: Canon I (Truth preservation), Canon III (State isolation)

### 3. Separate Database (Rejected)
- Run sandbox in entirely separate database
- **Risk**: Excessive overhead, cloning complexity
- **Decision**: Schema isolation provides sufficient separation

## Decision

**We chose: Sandbox Schema Isolation**

Implementation:
- PostgreSQL schema `sandbox` for all simulation tables (Migration 033)
- Sandbox models: `Scenario`, `Projection`, `Binding` in isolated schema
- Truth tables remain in `public` schema
- No foreign key constraints between `sandbox.*` and `public.*`
- Scenario states: DRAFT → ACTIVE → ARCHIVED
- Explicit cloning operations to copy truth data into sandbox

## Consequences

### Positive
- **Safety**: Physical schema separation prevents accidental data contamination
- **Canon Compliance**: Sandbox cannot corrupt accounting truth
- **Query Clarity**: Explicit schema prefix (`sandbox.scenarios`) makes intent obvious
- **Rollback Safety**: Deleting sandbox schema has zero impact on truth tables
- **Testing**: Can safely drop/recreate sandbox schema without affecting production data

### Negative
- **Cloning Overhead**: Must explicitly copy data from `public.*` to `sandbox.*`
- **Query Complexity**: Cross-schema queries require explicit schema qualification
- **Migration Coordination**: Two schema migration paths to maintain

### Mitigations
- Cloning service handles data copy transparently
- ORM models use `__table_args__ = {"schema": "sandbox"}` for clarity
- Migration naming convention: `0XX_create_sandbox_*.py`

## Reversal Plan

If schema isolation proves problematic:

1. **Migration Path**:
   - Create migration to merge `sandbox.*` tables into `public.*` with `is_sandbox` flag
   - Add database views to maintain existing API contracts
   - Update services to filter by `is_sandbox = false`

2. **Risk**:
   - Reversal increases contamination risk (reason we rejected soft-delete initially)
   - Only reverse if schema isolation causes performance issues

3. **Alternative**:
   - If multi-tenant sandbox needed, use `company_id + scenario_id` composite keys
   - Maintain schema isolation for safety

## Canon Check

✅ **Compliant with Canon I: Accounting Truth**
> "Truth tables in `public` schema remain immutable and authoritative"
> "Sandbox projections are explicitly non-authoritative"

✅ **Preserves Canon III: Evolution and State**
> "Sandbox scenarios exist in separate schema, cannot alter ledger state"
> "Archived scenarios do not pollute audit trail"

✅ **Aligns with Canon IV: Intelligence and Guidance**
> "Sandbox provides advisory projections, not accounting facts"
> "Tax liability simulations carry disclaimer: 'Estimated / Projected Tax Exposure'"

## Implementation Evidence

- **Migration 033**: `create_sandbox_schema_isolation.py`
- **Migration 034**: `create_sandbox_tables.py`
- **Service**: `app/services/sandbox_service.py` (cloning, scenario management)
- **Models**: `app/models/sandbox.py` (`Scenario`, `Projection`, `Binding`)
- **Schema**: `sandbox` schema in PostgreSQL with isolated tables

## Related Documents

- [[CANON_I_ACCOUNTING_TRUTH]]
- [[CANON_III_EVOLUTION_AND_STATE]]
- [[Phase 7 — Intelligence (Dexter)]]
- [[GOAL — Sandbox UI]]
- [[GOAL — Fiscal Engine]]

---

**Decision Status**: ✅ Implemented and operational (verified 2025-12-28)
