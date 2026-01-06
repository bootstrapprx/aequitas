# Functional Recovery Report — 2026-01-07

## Root Cause
- Goal loading depended on an active phase being set; when `get_active_phase` returned `null`, the Goals view stayed empty even though phases/goals exist in the DB.
- No fallback to an available phase was present in the Goals view.

## Fix Applied
- Added a simple fallback in `GoalExplorer.svelte`: if `get_active_phase` returns `null`, it now loads the first available phase from `get_all_phases` and fetches goals for it. This ensures goals render whenever at least one phase exists in the DB.

## Files Changed
- `metatheos-gui/src/lib/GoalExplorer.svelte`: phase fallback logic when loading goals.

## Why This Works
- By selecting the first available phase when no active phase is set, the Goals view always scopes to an existing phase and loads its goals. This restores sidebar/goal visibility without altering schema or backend queries.

## Verification
- Launch the app with existing phases/goals in the DB.
- Confirm the sidebar and Goals view display phases/goals (fallback selects the first phase if no active phase is set).
- App starts without panic.
