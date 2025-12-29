---
type: goal
id: goal-sandbox-ui
status: planned
phase: "P6"
depends_on: []
canon: []
owner: you
updated: 2025-12-28
---

# GOAL: Sandbox UI

## Intent (Plain Language)
- Provide a UI for the Sandbox module to allow users to create scenarios, view projections, and analyze tax impacts.

## Current Reality
- **Backend**: Fully operational (✅ Done)
  - `/api/v1/sandbox` endpoints
  - Scenario creation, projection binding, tax liability simulation
  - Isolated sandbox schema (Migrations 033-034)
  - DexterSandboxObserver for scenario pattern analysis
- **Frontend**: Not implemented (🔴 Missing)
  - No dedicated sandbox dashboard
  - No UI for scenario creation or viewing
  - Mentioned in post-activation guidance but not accessible

## Canon Constraints
- Sandbox must remain isolated from truth tables (enforced by schema separation)
- Tax projections must carry mandatory disclaimer: "Estimated / Projected Tax Exposure"
- Sandbox scenarios are advisory, not authoritative

## Definition of Done
- [ ] Dedicated sandbox dashboard page
- [ ] Scenario creation/management UI
- [ ] Projection viewing and analysis
- [ ] Tax impact visualization
- [ ] Integration with DexterSandboxObserver insights

## Deliverables Checklist
- [ ] React components for Sandbox dashboard
- [ ] Scenario list and detail views
- [ ] Projection editor and binding interface
- [ ] Tax impact charts and comparisons
- [ ] Disclaimer enforcement in UI

## Risks
- Low (backend already proven operational)

## Task List
- [ ] Design sandbox dashboard UX
- [ ] Implement scenario CRUD interface
- [ ] Build projection visualization
- [ ] Integrate Dexter scenario analysis
- [ ] Add tax impact comparison views
