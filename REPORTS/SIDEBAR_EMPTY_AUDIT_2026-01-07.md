# Sidebar Empty Audit — 2026-01-07

## Diagnostics
- Added `diagnose_store_state` Tauri command (read-only).
- Fields: governance_root, db_path, db_open_ok, tables_present, counts {phase, goal, work_item, day, day_goal}, active_phase, today_day_exists, last_error.
- UI banner in App shows DB path and counts; rerun button available.

## Root Cause
- Phase/goal reads were still using legacy tables; canonical tables (`phase`, `goal`) were ignored, causing empty UI despite data.
- Active phase not set when phases existed, leading goals query to return empty.

## Fixes
- Store getters now prefer canonical tables (`phase`, `goal`) with legacy fallback.
- Added DB-only `set_active_phase_db` and best-phase auto-selection on app init when none set.
- Added manual default phase seed command (`seed_default_phase_db`) for empty DBs.
- Diagnostics command exposes counts/errors to UI for quick checks.

## How to Verify
1. Run diagnostics: `invoke("diagnose_store_state")` — expect non-zero phase/goal counts if data exists.
2. Ensure active phase is set: `invoke("get_active_phase")` should return a phase; if null but phases exist, app will set best candidate.
3. Goals view should list phases and goals; Goal Detail should load from canonical work_items.
4. If DB empty: banner offers “Initialize default phase”; after running, phases should appear.
