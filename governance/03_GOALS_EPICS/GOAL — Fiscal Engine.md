---
type: goal
id: goal-fiscal-engine
status: done
phase: "P7"
depends_on: []
canon: [Canon IV]
owner: you
updated: 2025-12-28
---

# GOAL: Fiscal Engine

## Intent (Plain Language)
- Implement tax calculation engine for projecting tax liabilities based on trial balance facts, with sandbox isolation and mandatory disclaimers.

## Current Reality
- ✅ **Fully Implemented and Operational**

## What's Done
- **Backend**:
  - `/api/v1/fiscal` API endpoints for tax profiles, runs, and positions
  - `ProfileService`, `CalculationService`, `ConsolidationService`
  - Tax models: `EntityTaxProfile`, `TaxRun`, `TaxFact`, `TaxAdjustment`, `TaxPosition`
  - Tax run execution with SUCCESS/PARTIAL/FAILED statuses
  - Tax facts derived from trial balance
  - Tax position tracking and consolidation
  - Deterministic recalculation using input hash
  - Mandatory disclaimer: "Estimated / Projected Tax Exposure"
- **Database**:
  - Migration 025: Fiscal engine tables (tax runs, facts, adjustments, positions)
  - Tax profile management per entity
  - Tax ruleset support

## What's Missing
- Frontend UI for tax calculation management (API functional, no dedicated UI)
- Tax report visualization (data available via API, no UI dashboard)

## Canon Constraints
- **Canon IV: Intelligence and Guidance**
  - Tax projections are estimates, not authoritative determinations
  - Mandatory disclaimer required for all tax calculations
  - Tax engine provides guidance for planning, not compliance filings
- **Canon I: Accounting Truth**
  - Tax facts derive from posted ledger entries (immutable)
  - Tax calculations do not mutate accounting ledger
  - Tax liability is projected, not posted as journal entry

## Definition of Done
- [x] Tax profile management API
- [x] Tax run execution engine
- [x] Tax fact derivation from trial balance
- [x] Tax position tracking
- [x] Consolidated tax calculations
- [x] Deterministic recalculation
- [x] Disclaimers enforced
- [ ] Frontend UI for tax management (planned)
- [ ] Tax report dashboard (planned)

## Deliverables Checklist
- [x] Fiscal engine database models
- [x] Tax calculation services
- [x] API endpoints for tax operations
- [x] Tax profile CRUD
- [x] Tax run workflow (create, execute, retrieve)
- [x] Tax fact extraction from ledger
- [x] Disclaimer enforcement
- [ ] Frontend tax dashboard (future)

## Dependencies
- Requires Trial Balance (✅ Done)
- Requires Fiscal Periods (✅ Done)

## Risks
- ✅ Mitigated: Disclaimer enforcement prevents misuse as tax filing authority
- ⚠️ Future: UI needed to make tax engine user-accessible

## Links
- [[CANON_IV_INTELLIGENCE_AND_GUIDANCE]]
- [[Phase 7 — Intelligence (Dexter)]]
- [[GOAL — Sandbox UI]] (related: sandbox uses fiscal engine for tax projections)

## Task List
- [x] Backend implementation complete
- [x] Verified in production codebase (2025-12-28)
- [ ] Design tax dashboard UI (future)
- [ ] Implement tax report visualization (future)
