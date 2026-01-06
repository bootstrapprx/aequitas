# Annotation Everywhere (2026-01-03)

## Scope
- Implemented universal annotations without schema changes; SurrealDB remains canonical.
- Added Tauri commands for add/get/delete with scope validation and event logging.
- Introduced reusable UI widget and wired it into day dashboard, goal detail, and work item nodes.

## Design Rationale
- Aligns with SCHEMAFULL `annotation` table (`entity_type`, `entity_id`, `content`, `author_type`, `created_at`).
- Accepts canonical scopes: phase, goal, work_item, day, event, ai_run (legacy task/subgoal map to work_item).
- Events are logged on creation to keep auditability while keeping annotations non-blocking.

## Why Annotations Stay Non-Authoritative
- Stored separately from core entities; no logic branches on annotation presence.
- Append-only helper; failures surface locally but never block main workflows.
- Author type is informational only; no ownership or status gating.

## Surfaces
- Day Dashboard: `Day Notes` panel bound to the active day.
- Goal Detail: Goal-level panel plus per-work-item inline panels (collapse-friendly).
- Goal Editor: Shares the same panel for existing goals.

## Commands
- `add_annotation(scope_type, scope_id, body, author?)` – validates scope, writes `annotation`, logs `event`.
- `get_annotations(scope_type, scope_id)` – scoped fetch, newest first.
- `delete_annotation(id)` – optional cleanup helper.

## Verification
- Create annotations on day/goal/work_item; verify they render immediately and persist across reload.
- Ensure invalid scope types are rejected cleanly.
- Confirm core flows (goal detail/tree, dashboard) still load with annotations absent.
