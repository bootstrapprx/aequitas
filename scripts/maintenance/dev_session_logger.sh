#!/bin/bash

# Configuration
SESSION_ROOT="dev_sessions"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
SESSION_ID="log_${TIMESTAMP}"
CURRENT_SESSION_DIR="${SESSION_ROOT}/${SESSION_ID}"

# Output files
COMMANDS_FILE="${CURRENT_SESSION_DIR}/commands.txt"
OUTPUT_FILE="${CURRENT_SESSION_DIR}/output.txt"
ERRORS_FILE="${CURRENT_SESSION_DIR}/errors.txt"
ANTIGRAVITY_FILE="${CURRENT_SESSION_DIR}/antigravity_interactions.txt"
METADATA_FILE="${CURRENT_SESSION_DIR}/metadata.json"
DOCKER_STREAM_LOG="${CURRENT_SESSION_DIR}/docker_stream.log"
BROWSER_LOG="${CURRENT_SESSION_DIR}/browser.log"

# Ensure maintenance scripts directory is in path or referenced correctly
SCRIPT_DIR="$(dirname "$0")"
ROTATE_SCRIPT="${SCRIPT_DIR}/session_rotate.py"

# Function to initialize the session
init_session() {
    # Create directory structure
    mkdir -p "$CURRENT_SESSION_DIR"

    # Gather Metadata
    USER_NAME="Thome" # Static as per requirements
    MACHINE_USER=$(whoami)
    GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    REPO_VERSION=$(grep -oP '"version": "\K[^"]+' package.json 2>/dev/null || echo "unknown")
    # Generating Metadata JSON
    cat <<EOF > "$METADATA_FILE"
{
  "session_id": "${SESSION_ID}",
  "start_timestamp": "${TIMESTAMP}",
  "end_timestamp": null,
  "developer_name": "${USER_NAME}",
  "machine_user": "${MACHINE_USER}",
  "git_branch": "${GIT_BRANCH}",
  "repo_version": "${REPO_VERSION}"
}
EOF
    
    # Initialize log files
    touch "$COMMANDS_FILE" "$OUTPUT_FILE" "$ERRORS_FILE" "$ANTIGRAVITY_FILE"
    
    # Update 'latest' symlink
    rm -f "${SESSION_ROOT}/latest"
    ln -s "$(basename "$CURRENT_SESSION_DIR")" "${SESSION_ROOT}/latest"
    
    echo "Session initialized: $SESSION_ID"
}

# Logging functions
log_command() {
    echo "$@" >> "$COMMANDS_FILE"
}

log_output() {
    echo "$@" >> "$OUTPUT_FILE"
}

log_error() {
    echo "$@" >> "$ERRORS_FILE"
}

log_antigravity() {
    echo "--- [$(date)] ---" >> "$ANTIGRAVITY_FILE"
    echo "$@" >> "$ANTIGRAVITY_FILE"
    echo "" >> "$ANTIGRAVITY_FILE"
}

# Function to end the session
stream_docker_logs() {
    # Check if we are in a folder with docker-compose
    if [ -f "docker-compose.dev.yml" ]; then
        echo "Starting Docker log stream..." >> "$OUTPUT_FILE"
        # Run logs follow in background
        docker compose -f docker-compose.dev.yml logs -f > "$DOCKER_STREAM_LOG" 2>&1 &
        DOCKER_LOG_PID=$!
        echo $DOCKER_LOG_PID > "${CURRENT_SESSION_DIR}/docker.pid"
    fi
}

launch_browser() {
    URL="http://localhost:5173"
    echo "Attempting to launch browser for $URL..." >> "$OUTPUT_FILE"
    
    if command -v google-chrome >/dev/null; then
        google-chrome --enable-logging --v=1 "$URL" > "$BROWSER_LOG" 2>&1 &
        BROWSER_PID=$!
        echo $BROWSER_PID > "${CURRENT_SESSION_DIR}/browser.pid"
    elif command -v chromium >/dev/null; then
        chromium --enable-logging --v=1 "$URL" > "$BROWSER_LOG" 2>&1 &
        BROWSER_PID=$!
        echo $BROWSER_PID > "${CURRENT_SESSION_DIR}/browser.pid"
    elif command -v xdg-open >/dev/null; then
        xdg-open "$URL" > "$BROWSER_LOG" 2>&1 &
    elif command -v open >/dev/null; then
         # macOS
        open "$URL" > "$BROWSER_LOG" 2>&1 &
    else
        echo "No browser command found to launch." >> "$ERRORS_FILE"
    fi
}

cleanup_background_processes() {
    if [ -f "${CURRENT_SESSION_DIR}/docker.pid" ]; then
        kill $(cat "${CURRENT_SESSION_DIR}/docker.pid") 2>/dev/null
    fi
    # We typically don't kill the browser as the user might want to keep it, 
    # but strictly "session" implies it ends. For now we leave it open as it's a GUI app.
}

end_session() {
    END_TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    
    # Update end timestamp in metadata using sed (safe for simple replacement) or tmp file
    # Using a temporary file approach to be safer with JSON structure if needed, but sed is fine for this specific key
    # Update end timestamp in metadata using sed
    if [ -f "$METADATA_FILE" ]; then
        sed -i "s/\"end_timestamp\": null/\"end_timestamp\": \"$END_TIMESTAMP\"/" "$METADATA_FILE"
    fi

    echo "Session ended: $SESSION_ID"
    
    # Trigger rotation
    if [ -f "$ROTATE_SCRIPT" ]; then
        python3 "$ROTATE_SCRIPT"
    else
        echo "Warning: Rotation script not found at $ROTATE_SCRIPT"
    fi
}

# Main execution block
# Checks if sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being executed directly
    case "$1" in
        init)
            init_session
            ;;
        end)
            # For 'end', we need to know WHICH session to end if multiple are active?
            # Requirement implies a single session wrapper context. 
            # For simplicity in this deliverable, 'end' will rely on finding the LATEST session or passing ID.
            # But the requirements say "When session ends... Trigger rotation".
            # If this script wraps a shell, we trap EXIT.
            echo "Direct execution 'end' requires knowing the session context. Use 'wrap' to start a logged shell."
            ;;
        wrap)
            # Starts a new shell and logs interaction
            init_session
            echo "Starting logged shell. Type 'exit' to end session."
            
            # Simple logging wrapper using 'script' command if available for full output capture
            # Or just spawning a subshell.
            # Requirement E: "Capture terminal commands... stdout... stderr"
            # The 'script' utility is the robust way to capture all terminal I/O.
            
            SHELL_LOG="${CURRENT_SESSION_DIR}/full_terminal.log"
            
            # Use 'script' to record the session
            if command -v script >/dev/null; then
                  # Backround helpers
                 stream_docker_logs
                 launch_browser
                 
                 # Linux 'script' syntax
                 script -f -q "$SHELL_LOG"
                 
                 # Cleanup
                 cleanup_background_processes
                 
                 # After script exits (user types exit)
                 end_session
            else
                echo "Error: 'script' command not found. Cannot auto-capture full terminal."
            fi
            ;;
        *)
            echo "Usage: $0 {init|wrap}"
            exit 1
            ;;
    esac
fi
