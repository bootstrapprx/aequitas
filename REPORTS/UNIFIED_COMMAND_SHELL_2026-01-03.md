# Unified Command Shell (2026-01-03)

## Routing Rules
- Default to Metatheos CLI-compatible commands.
- If the first token is `aequitas`, treat as Aequitas CLI request (currently blocked for in-process execution; returns a clear error).
- Supported Metatheos verbs: `ingest_roadmap`, `phase list`, `goal list`, `help` (extensible).
- Unknown commands return structured errors without crashing the UI.

## Implementation
- Tauri command `execute_shell_command(input)` dispatches based on the first token, executes in-process against the shared store, and returns `ShellResult { success, output, error, timestamp, command }`.
- Terminal panel now sends user input to `execute_shell_command`, renders stdout/stderr, and keeps prompts/resets (`clear` supported).
- Ingestion command (`ingest_roadmap`) is callable from the shell and reports counts.
- Aequitas CLI bridging is acknowledged but not yet wired (Python Typer CLI would require a separate bridge).

## Known Limitations
- Aequitas commands are not executed; a placeholder error is returned.
- Command set is minimal; extend routing as new CLI verbs are needed.
- No history or autocomplete; shell is a thin transport, not a DSL.

## How to Use
- Open the GUI shell panel (Terminal) and run:
  - `ingest_roadmap`
  - `phase list`
  - `goal list`
  - `help`
- `clear` resets the panel.

## Philosophy
- Shell is the authoritative control surface; it routes to existing command handlers without introducing a new language.
- Deterministic, local-only execution; shared DB context; no raw process spawning.
