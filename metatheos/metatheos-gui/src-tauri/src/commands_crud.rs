use chrono::NaiveDate;
use metatheos_core::{DailyWriter, Goal, GoalStatus, GoalWriter, Phase, PhaseWriter};
use serde::{Deserialize, Serialize};
use std::str::FromStr;
use tauri::State;

use crate::state::AppState;

// ============================================================================
// Request/Response Types
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
pub struct GoalCreateRequest {
    pub goal_id: String,
    pub title: String,
    pub status: String,
    pub phase: Option<String>,
    pub owner: Option<String>,
    pub dependencies: Vec<String>,
    pub canon: Vec<String>,
    pub tags: Vec<String>,
    pub content: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GoalUpdateRequest {
    pub title: Option<String>,
    pub status: Option<String>,
    pub phase: Option<String>,
    pub owner: Option<String>,
    pub dependencies: Option<Vec<String>>,
    pub canon: Option<Vec<String>>,
    pub tags: Option<String>,
    pub content: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PhaseCreateRequest {
    pub phase_id: String,
    pub title: String,
    pub status: String,
    pub start_date: Option<String>,
    pub target_date: Option<String>,
    pub dependencies: Vec<String>,
    pub content: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PhaseUpdateRequest {
    pub title: Option<String>,
    pub status: Option<String>,
    pub start_date: Option<String>,
    pub target_date: Option<String>,
    pub dependencies: Option<Vec<String>>,
    pub content: Option<String>,
}

// ============================================================================
// Goal Commands
// ============================================================================

/// Create a new goal
#[tauri::command]
pub fn create_goal(
    request: GoalCreateRequest,
    state: State<AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap();
    let writer = GoalWriter::new(root.clone());

    // Parse status
    let status = GoalStatus::from_str(&request.status)
        .ok_or_else(|| format!("Invalid status: {}", request.status))?;

    // Build goal
    let goal = Goal {
        goal_id: request.goal_id.clone(),
        title: request.title,
        status,
        phase: request.phase,
        owner: request.owner,
        dependencies: request.dependencies,
        canon: request.canon,
        tags: request.tags,
        updated: Some(chrono::Utc::now().naive_utc().date()),
        file_path: std::path::PathBuf::new(), // Will be set by writer
        content: request.content,
    };

    // Create goal
    writer
        .create_goal(&goal)
        .map_err(|e| e.to_string())?;

    Ok(request.goal_id)
}

/// Update an existing goal
#[tauri::command]
pub fn update_goal(
    goal_id: String,
    request: GoalUpdateRequest,
    state: State<AppState>,
) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();

    // Load current goal
    let ctx = metatheos_core::GovernanceContext::load(&*root).map_err(|e| e.to_string())?;
    let mut goal = ctx
        .all_goals()
        .iter()
        .find(|g| g.goal_id == goal_id)
        .cloned()
        .map(|g| g.clone())
        .ok_or_else(|| format!("Goal '{}' not found", goal_id))?;

    // Apply updates
    if let Some(title) = request.title {
        goal.title = title;
    }
    if let Some(status_str) = request.status {
        goal.status = GoalStatus::from_str(&status_str)
            .ok_or_else(|| format!("Invalid status: {}", status_str))?;
    }
    if let Some(phase) = request.phase {
        goal.phase = Some(phase);
    }
    if let Some(owner) = request.owner {
        goal.owner = Some(owner);
    }
    if let Some(deps) = request.dependencies {
        goal.dependencies = deps;
    }
    if let Some(canon) = request.canon {
        goal.canon = canon;
    }
    if let Some(tags_str) = request.tags {
        goal.tags = tags_str.split(',').map(|s| s.trim().to_string()).collect();
    }
    if let Some(content) = request.content {
        goal.content = content;
    }

    goal.updated = Some(chrono::Utc::now().naive_utc().date());

    // Write updated goal
    let writer = GoalWriter::new(root.clone());
    writer.update_goal(&goal).map_err(|e| e.to_string())?;

    Ok(())
}

/// Delete a goal (archives it)
#[tauri::command]
pub fn delete_goal(goal_id: String, state: State<AppState>) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = GoalWriter::new(root.clone());

    writer.delete_goal(&goal_id).map_err(|e| e.to_string())?;

    Ok(())
}

// ============================================================================
// Phase Commands
// ============================================================================

/// Create a new phase
#[tauri::command]
pub fn create_phase(
    request: PhaseCreateRequest,
    state: State<AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap();
    let writer = PhaseWriter::new(root.clone());

    // Parse dates
    let start_date = request
        .start_date
        .as_ref()
        .and_then(|s| NaiveDate::from_str(s).ok());

    let target_date = request
        .target_date
        .as_ref()
        .and_then(|s| NaiveDate::from_str(s).ok());

    // Build phase
    let phase = Phase {
        phase_id: request.phase_id.clone(),
        title: request.title,
        status: request.status,
        start_date,
        target_date,
        dependencies: request.dependencies,
        file_path: std::path::PathBuf::new(), // Will be set by writer
        content: request.content,
    };

    // Create phase
    writer
        .create_phase(&phase)
        .map_err(|e| e.to_string())?;

    Ok(request.phase_id)
}

/// Update an existing phase
#[tauri::command]
pub fn update_phase(
    phase_id: String,
    request: PhaseUpdateRequest,
    state: State<AppState>,
) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();

    // Load current phase
    let ctx = metatheos_core::GovernanceContext::load(&*root).map_err(|e| e.to_string())?;
    let mut phase = ctx
        .all_phases()
        .iter()
        .find(|p| p.phase_id == phase_id)
        .cloned()
        .map(|p| p.clone())
        .ok_or_else(|| format!("Phase '{}' not found", phase_id))?;

    // Apply updates
    if let Some(title) = request.title {
        phase.title = title;
    }
    if let Some(status) = request.status {
        phase.status = status;
    }
    if let Some(start_str) = request.start_date {
        phase.start_date = NaiveDate::from_str(&start_str).ok();
    }
    if let Some(target_str) = request.target_date {
        phase.target_date = NaiveDate::from_str(&target_str).ok();
    }
    if let Some(deps) = request.dependencies {
        phase.dependencies = deps;
    }
    if let Some(content) = request.content {
        phase.content = content;
    }

    // Write updated phase
    let writer = PhaseWriter::new(root.clone());
    writer.update_phase(&phase).map_err(|e| e.to_string())?;

    Ok(())
}

/// Set a phase as active
#[tauri::command]
pub fn set_active_phase(phase_id: String, state: State<AppState>) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = PhaseWriter::new(root.clone());

    writer
        .set_active_phase(&phase_id)
        .map_err(|e| e.to_string())?;

    Ok(())
}

// ============================================================================
// Daily Note Commands (Enhanced)
// ============================================================================

/// Delete a daily note (archives it)
#[tauri::command]
pub fn delete_daily_note(date: String, state: State<AppState>) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = DailyWriter::new(root.clone());

    let parsed_date =
        NaiveDate::from_str(&date).map_err(|e| format!("Invalid date format: {}", e))?;

    writer
        .delete_daily_note(parsed_date)
        .map_err(|e| e.to_string())?;

    Ok(())
}

/// Enhanced version of update_daily_note using DailyWriter
#[tauri::command]
pub fn write_daily_note(date: String, content: String, state: State<AppState>) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = DailyWriter::new(root.clone());

    let parsed_date =
        NaiveDate::from_str(&date).map_err(|e| format!("Invalid date format: {}", e))?;

    writer
        .write_daily_note(parsed_date, &content)
        .map_err(|e| e.to_string())?;

    Ok(())
}
