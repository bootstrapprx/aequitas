# Shell Recovery & update_all (2026-01-03)

## Root Cause
- The “Unknown command” message originated in `metatheos-gui/src-tauri/src/commands.rs::execute_shell_command` default branch, reached whenever the dispatcher did not recognize the input. The GUI terminal was still echoing locally and not invoking the backend for new verbs, so `ingest_roadmap` fell through to this path.

## Fixes Applied
- Terminal wiring: `metatheos-gui/src/lib/Terminal.svelte` now always invokes `execute_shell_command` on Enter (with only `clear`/Ctrl+C handled locally), removing the mock client-side router.
- Dispatcher: Added canonical command list + formatted help, new commands `doctor` and `update_all`, and clearer routing for `phase list` / `goal list`. Aequitas prefix is still rejected with an explicit bridge error.
- Diagnostics: `doctor` reports governance root, DB path, counts (phase/goal/work_item/day/event/annotation), active phase, today’s day presence, roadmap file existence, and ingest availability.
- Recovery macro: `update_all` re-initializes schema, ingests roadmap if no phases, sets an active phase if missing, and prints before/after doctor snapshots with count deltas.

## Commands (dispatcher help)
- help
- doctor
- ingest_roadmap
- update_all
- phase list
- goal list
- aequitas <cmd> (placeholder until Python bridge is wired)

## Verification Attempts
- `cargo tauri dev` blocked by sandboxed Docker access (`permission denied … docker.sock`) so in-app terminal couldn’t be exercised here. Build path compiles; dispatcher and terminal wiring are in place. If Docker access is available, run `cargo tauri dev`, then in the GUI terminal execute: `help`, `doctor`, `ingest_roadmap`, `update_all`, `phase list`, `goal list`.

## Next Steps (if environment permits)
1) Rerun `cargo tauri dev` in an environment with Docker access.  
2) In the GUI terminal, run the acceptance commands above; capture outputs for confirmation.  
3) If Aequitas CLI bridging is required, add a Python/FFI bridge and wire `aequitas` prefix accordingly.
