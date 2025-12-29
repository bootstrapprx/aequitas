---
type: phase
phase_id: "P6"
status: planned
depends_on: []
owner: you
updated: 2025-12-28


## What it means
- User-facing modules: Invoicing, Assets, Payroll, etc.

## Status
- ⚪ Planned (Module framework exists, operational modules not implemented)

## What's Done
- Module framework: `CompanyModule` model with `ModuleType` enum
- Module types defined: ACCOUNTING, FISCAL, INVOICING, CONTRACTS, INVENTORY, PAYROLL
- Module activation tracking (which companies have which modules enabled)
- Module selection in onboarding wizard (Step 4)
- ACCOUNTING module fully operational (see Phase 4)
- FISCAL module fully operational (tax engine, see Phase 7)

## What's Missing
- INVOICING module: No models, services, or API endpoints (enum only)
- ASSETS module: Account types exist, no dedicated asset tracking, depreciation, or lifecycle management
- PAYROLL module: No models, services, or API endpoints (enum only)
- INVENTORY module: No implementation
- CONTRACTS module: No implementation
- Sandbox UI: Backend fully operational, no dedicated frontend dashboard

## Goals
- [[GOAL — Invoicing Module]]
- [[GOAL — Assets Module]]
- [[GOAL — Payroll Module]]
- [[GOAL — Sandbox UI]]
