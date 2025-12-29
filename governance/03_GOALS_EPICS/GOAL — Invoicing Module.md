---
type: goal
id: goal-invoicing
status: planned
phase: "P6"
depends_on: [goal-fin-event-tax]
canon: []
owner: you
updated: 2025-12-28
---

# GOAL: Invoicing Module

## Intent (Plain Language)
- Create the Invoicing module to allow users to create and send invoices.
- "Invoice-first UX" means accounting happens automatically behind the scenes.

## Canon Constraints
- Must emit "Invoice Issued" Financial Events.

## Definition of Done
- [ ] Users can send PDF invoices.
- [ ] Journal entries created automatically.

## Deliverables Checklist
- [ ] UI for Invoice creation.
- [ ] PDF generation.
- [ ] Event emission.

## Risks
- UX complexity.

## Task List
- [ ] Design data model.
- [ ] Implement UI.
