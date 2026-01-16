/// Phase 3 — Governance State & Git Integration
/// Git operations for governance history, accountability, and reversibility
///
/// Hard Constraints:
/// - No AI reasoning, inference, or suggestions
/// - No auto-commits (all commits explicit and human-confirmed)
/// - Canon/Constitution remain read-only
/// - Git is historical memory of governance authority
use serde::{Deserialize, Serialize};
use std::process::Command;
use tauri::State;

use crate::state::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct GitStatus {
    pub is_repo: bool,
    pub current_branch: Option<String>,
    pub is_clean: bool,
    pub modified_files: Vec<String>,
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CommitResult {
    pub success: bool,
    pub commit_hash: Option<String>,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FileCommit {
    pub hash: String,
    pub author: String,
    pub date: String,
    pub message: String,
}

/// Detect if governance root is a Git repository and get its status
#[tauri::command]
pub fn get_governance_git_status(state: State<AppState>) -> Result<GitStatus, String> {
    let root = state.repo_root.lock().unwrap();
    let root_path = root.to_str().ok_or("Invalid path encoding")?;

    // Check if .git exists
    let git_dir = root.join(".git");
    if !git_dir.exists() {
        return Ok(GitStatus {
            is_repo: false,
            current_branch: None,
            is_clean: true,
            modified_files: vec![],
            error: Some("Repository is not a Git repository".to_string()),
        });
    }

    // Get current branch
    let branch_output = Command::new("git")
        .args(&["rev-parse", "--abbrev-ref", "HEAD"])
        .current_dir(root_path)
        .output();

    let current_branch = match branch_output {
        Ok(output) if output.status.success() => {
            Some(String::from_utf8_lossy(&output.stdout).trim().to_string())
        }
        _ => None,
    };

    // Get modified files (only in governance directory)
    let status_output = Command::new("git")
        .args(&["status", "--porcelain", "."])
        .current_dir(root_path)
        .output();

    let (is_clean, modified_files) = match status_output {
        Ok(output) if output.status.success() => {
            let output_str = String::from_utf8_lossy(&output.stdout);
            let files: Vec<String> = output_str
                .lines()
                .filter(|line| !line.is_empty())
                .map(|line| {
                    // Format: " M file.md" or "?? file.md"
                    line.split_whitespace().nth(1).unwrap_or("").to_string()
                })
                .collect();

            let clean = files.is_empty();
            (clean, files)
        }
        _ => (true, vec![]),
    };

    Ok(GitStatus {
        is_repo: true,
        current_branch,
        is_clean,
        modified_files,
        error: None,
    })
}

/// Commit governance changes with explicit message and optional related IDs
#[tauri::command]
pub fn commit_governance_changes(
    message: String,
    related_ids: Option<String>,
    state: State<AppState>,
) -> Result<CommitResult, String> {
    let root = state.repo_root.lock().unwrap();
    let root_path = root.to_str().ok_or("Invalid path encoding")?;

    // Reject empty messages
    if message.trim().is_empty() {
        return Err("Commit message cannot be empty".to_string());
    }

    // Build full commit message with related IDs if provided
    let full_message = if let Some(ids) = related_ids {
        if ids.trim().is_empty() {
            message
        } else {
            format!("{}\n\nRelated: {}", message, ids)
        }
    } else {
        message
    };

    // Stage all changes in governance directory
    let add_output = Command::new("git")
        .args(&["add", "."])
        .current_dir(root_path)
        .output()
        .map_err(|e| format!("Failed to stage changes: {}", e))?;

    if !add_output.status.success() {
        return Err(format!(
            "Git add failed: {}",
            String::from_utf8_lossy(&add_output.stderr)
        ));
    }

    // Commit with message
    let commit_output = Command::new("git")
        .args(&["commit", "-m", &full_message])
        .current_dir(root_path)
        .output()
        .map_err(|e| format!("Failed to commit: {}", e))?;

    if !commit_output.status.success() {
        let stderr = String::from_utf8_lossy(&commit_output.stderr);
        return Err(format!("Git commit failed: {}", stderr));
    }

    // Get commit hash
    let hash_output = Command::new("git")
        .args(&["rev-parse", "HEAD"])
        .current_dir(root_path)
        .output()
        .map_err(|e| format!("Failed to get commit hash: {}", e))?;

    let commit_hash = if hash_output.status.success() {
        Some(
            String::from_utf8_lossy(&hash_output.stdout)
                .trim()
                .to_string(),
        )
    } else {
        None
    };

    Ok(CommitResult {
        success: true,
        commit_hash,
        message: "Governance changes committed successfully".to_string(),
    })
}

/// Get commit history for a specific governance file
#[tauri::command]
pub fn get_file_history(
    file_path: String,
    limit: Option<usize>,
    state: State<AppState>,
) -> Result<Vec<FileCommit>, String> {
    let gov_root = state.governance_root.lock().unwrap();
    let repo_root = state.repo_root.lock().unwrap();
    let root_path = repo_root.to_str().ok_or("Invalid path encoding")?;

    // Verify file is within governance root
    let target = std::path::Path::new(&file_path);
    if !target.starts_with(&*gov_root) {
        return Err("File is outside governance root".to_string());
    }

    let limit_arg = format!("-{}", limit.unwrap_or(20));

    // Get git log for this file with custom format
    let log_output = Command::new("git")
        .args(&[
            "log",
            &limit_arg,
            "--format=%H|%an|%ad|%s",
            "--date=iso",
            "--",
            &file_path,
        ])
        .current_dir(root_path)
        .output()
        .map_err(|e| format!("Failed to get file history: {}", e))?;

    if !log_output.status.success() {
        return Err(format!(
            "Git log failed: {}",
            String::from_utf8_lossy(&log_output.stderr)
        ));
    }

    let output_str = String::from_utf8_lossy(&log_output.stdout);
    let commits: Vec<FileCommit> = output_str
        .lines()
        .filter_map(|line| {
            let parts: Vec<&str> = line.split('|').collect();
            if parts.len() >= 4 {
                Some(FileCommit {
                    hash: parts[0].to_string(),
                    author: parts[1].to_string(),
                    date: parts[2].to_string(),
                    message: parts[3..].join("|"), // Handle messages with | in them
                })
            } else {
                None
            }
        })
        .collect();

    Ok(commits)
}

/// Get last commit hash affecting governance directory
#[tauri::command]
pub fn get_last_governance_commit(state: State<AppState>) -> Result<Option<String>, String> {
    let root = state.repo_root.lock().unwrap();
    let root_path = root.to_str().ok_or("Invalid path encoding")?;

    let log_output = Command::new("git")
        .args(&["log", "-1", "--format=%H", "--", "."])
        .current_dir(root_path)
        .output()
        .map_err(|e| format!("Failed to get last commit: {}", e))?;

    if !log_output.status.success() {
        return Ok(None);
    }

    let hash = String::from_utf8_lossy(&log_output.stdout)
        .trim()
        .to_string();
    if hash.is_empty() {
        Ok(None)
    } else {
        Ok(Some(hash))
    }
}
