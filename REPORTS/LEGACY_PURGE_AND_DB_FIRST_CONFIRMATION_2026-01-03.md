# Legacy Purge & DB-First Confirmation (2026-01-03)

## What Was Removed/Replaced
- Removed markdown fallbacks for phases/goals:
  - `get_all_phases` / `get_active_phase` now require DB; no GovernanceContext fallback.
  - Goal/Phase CRUD now write/read SurrealDB directly (removed GoalWriter/PhaseWriter dual writes).
- Goal Explorer UI copy cleaned:
  - Deleted “Grouped by phase … 03_GOALS_EPICS”, “Governance write mode active”, “All Goals (Reference)”, “vault” mentions.
  - Replaced with “Goals are stored and managed in the database. Changes are immediately persistent.”
- Doctor diagnostics now report legacy folders if present and assert DB-backed sources.

## Root Cause of Wrong Copy
- GoalExplorer still displayed legacy markdown status text, implying vault writes and reference mode despite DB-first backend, causing user-facing inconsistency.

## Current DB-Only State
- DB is authoritative for phases, goals, work_items, days, annotations, events.
- Legacy markdown writers for phases/goals removed from CRUD paths; no markdown fallback for phase/goal reads.
- Doctor output includes legacy files detected (ignored) visibility; help/update_all/doctor available via shell dispatcher.

## Verification Status
- Code compiled (`cargo fmt` run). `cargo tauri dev` not executed here due to sandboxed Docker access denial; run locally with Docker access to verify GUI terminal commands: `help`, `doctor`, `ingest_roadmap`, `update_all`, `phase list`, `goal list`.

## Next Checks (when environment allows)
- Run GUI terminal acceptance commands above; ensure doctor shows DB-backed tables and legacy files ignored.
- Confirm sidebar/goals render without markdown wording; creating/updating goals/phases persists via DB.
