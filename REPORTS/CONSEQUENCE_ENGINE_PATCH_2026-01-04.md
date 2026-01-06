# Consequence Engine Patch (2026-01-04)

## What Changed
- Added `metatheos-core/src/store/consequences.rs` and `queries.rs` to detect cascades without new schema.
- Patched commands:
  - `set_work_item_status`: when a task is done, check if all tasks for the goal are done and emit `goal_ready_to_complete`.
  - `update_goal_status`: now DB-first; emits phase progress events and `phase_ready_to_close` when all goals in a phase are done.
  - `create_day`: after linking day goals, evaluates required-goal completion and emits `day_success` or `day_progress`.
- Fixed `get_meta` SQL to use a valid `meta` table select.
- Phase cards adjusted to avoid nested buttons (Svelte warning resolved).

## Consequences Implemented
- Task → Goal readiness: when all tasks under a goal are done, an event is logged (`goal_ready_to_complete`, reason `all_tasks_done`).
- Goal → Phase progress: logs `phase_progress_updated` with totals/done; logs `phase_ready_to_close` when all goals in the phase are done.
- Day required goals: logs `day_success` when all required goals are done; otherwise `day_progress` with counts.
- No automatic closure; only detection and events.

## What’s Intentionally Not Automated
- Goals/phases/days are not auto-closed; UI/commands must act on events.
- No new tables or schedulers; pure DB queries and events.

## How This Keeps Determinism
- Consequences run synchronously after mutations and only emit events / calculations; no background workers or schema changes.
- All operations stay within SurrealDB and existing commands.
