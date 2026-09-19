#!/usr/bin/env python3
import os
import shutil
import datetime

# Configuration
SESSION_DIR = "dev_sessions"
MAX_SESSIONS = 10
LOG_FILE = os.path.join(SESSION_DIR, "rotation.log")

def log_message(message):
    """Appends a message to the rotation log with a timestamp."""
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def rotate_sessions():
    """Checks the number of session folders and deletes the oldest if > MAX_SESSIONS."""
    if not os.path.exists(SESSION_DIR):
        print(f"Directory {SESSION_DIR} does not exist.")
        return

    # specific logic: count only directories that look like sessions (start with log_)
    # This prevents deleting other files or the log folder itself if naming changes
    try:
        items = os.listdir(SESSION_DIR)
    except OSError as e:
        print(f"Error accessing {SESSION_DIR}: {e}")
        return

    sessions = []
    for item in items:
        path = os.path.join(SESSION_DIR, item)
        if os.path.isdir(path) and item.startswith("log_"):
            sessions.append(path)

    session_count = len(sessions)
    
    if session_count > MAX_SESSIONS:
        # Sort by modification time (or creation time), oldest first
        # relying on folder naming structure YYYY-MM-DD which sorts alphabetically correctly too
        # but mtime is safer if names change slightly.
        sessions.sort(key=os.path.getmtime)
        
        excess = session_count - MAX_SESSIONS
        sessions_to_delete = sessions[:excess]

        for session_path in sessions_to_delete:
            try:
                shutil.rmtree(session_path)
                folder_name = os.path.basename(session_path)
                msg = f"Deleted old session: {folder_name}"
                print(msg)
                log_message(msg)
            except OSError as e:
                msg = f"Failed to delete {session_path}: {e}"
                print(msg)
                log_message(msg)
    else:
        # Optional: verbose logging
        # log_message(f"Session count {session_count} is within limit ({MAX_SESSIONS}).")
        pass

if __name__ == "__main__":
    rotate_sessions()
