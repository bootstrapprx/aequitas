# Development Session Logging Policy

## Overview
Aequitas includes an automated system to capture, store, rotate, and archive CLI development sessions. This ensures that development activity, errors, and agent interactions are preserved for audit and debugging purposes without cluttering the repository.

## Directory Structure
Logs are stored locally in the `/dev_sessions/` directory, which is ignored by git.

```
/dev_sessions/
  ├── log_2025-12-06_12-00-00/
  │   ├── commands.txt               # Captured terminal commands
  │   ├── output.txt                 # Standard output
  │   ├── errors.txt                 # Standard error
  │   ├── antigravity_interactions.txt # Agent prompt/response logs
  │   └── metadata.json              # Session metadata
  └── rotation.log                   # Log of deleted old sessions
```

## Usage

### Starting a Logged Session
To start a fully logged terminal session, use the Makefile shortcut:

```bash
make session
```

Alternatively, run the script directly:

```bash
./scripts/maintenance/dev_session_logger.sh wrap
```
### Stopping and Saving
To stop the recording and save all logs:
1. **Type `exit`** or press `Ctrl+D` in the terminal.
   - This ends the shell recording.
   - Stops the realtime Docker stream.
   - Saves final metadata.
   - Triggers the rotation policy (deleting old sessions).

**Tip**: To ensure a full dump of all Docker container logs is included, you can run `make stop` **inside** (or outside) the session before exiting, but the real-time stream (`docker_stream.log`) already captures them as they happen.

### Manual Logging (Advanced)
You can source the script in your own loops or automation to use the logging functions directly:

```bash
source ./scripts/maintenance/dev_session_logger.sh init

log_command "npm install"
log_output "Installing dependencies..."
log_error "Warning: deprecated package"
log_antigravity "User: How do I fix this? \nAgent: Run npm audit fix."

end_session
```

## Rotation Policy
The system maintains a maximum of **10 complete sessions**.
- When a new session ends, the rotation script (`session_rotate.py`) runs.
- If more than 10 session folders exist, the oldest ones are permanently deleted.
- Rotation actions are logged in `/dev_sessions/rotation.log`.

## Configuration
- **Script Location**: `/scripts/maintenance/dev_session_logger.sh`
- **Rotation Logic**: `/scripts/maintenance/session_rotate.py`
- **Max Sessions**: 10 (Defined in `session_rotate.py`)

## Troubleshooting
- **Missing `script` command**: The wrapper mode requires the `script` utility (standard on most Linux/Unix systems).
- **Permissions**: Ensure scripts in `scripts/maintenance/` are executable (`chmod +x`).

## Limitations
- **Browser Interactions**: This system logs CLI interactions and backend/docker logs only. Browser events (clicks, navigation, console logs) are **not** captured.
- **Docker Logs**: Docker logs are captured only when `make stop` is run while a session is active.
