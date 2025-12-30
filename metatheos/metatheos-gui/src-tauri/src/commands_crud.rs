use chrono::NaiveDate;
use metatheos_core::{
    AuditRecord, DailyWriter, Goal, GoalStatus, GoalWriter, Phase, PhaseWriter, Prompt,
    parser::MarkdownParser,
    writer::{AuditWriter, PromptWriter},
};
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

// ============================================================================
// Audit Commands
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
pub struct AuditCreateRequest {
    pub title: String,
    pub date: Option<String>,
    pub scope: Option<String>,
    pub risk: Option<String>,
    pub auditor: Option<String>,
    pub summary: Option<String>,
    pub content: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AuditUpdateRequest {
    pub file_path: String,
    pub title: Option<String>,
    pub date: Option<String>,
    pub scope: Option<String>,
    pub risk: Option<String>,
    pub auditor: Option<String>,
    pub status: Option<String>,
    pub summary: Option<String>,
    pub content: Option<String>,
}

/// Create a new audit record
#[tauri::command]
pub fn create_audit(
    request: AuditCreateRequest,
    state: State<AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap();
    let writer = AuditWriter::new(root.clone());

    // Parse date if provided
    let date = request
        .date
        .and_then(|d| NaiveDate::parse_from_str(&d, "%Y-%m-%d").ok());

    // Build audit
    let audit = AuditRecord {
        title: request.title,
        date,
        scope: request.scope,
        risk: request.risk,
        auditor: request.auditor,
        status: request.summary.as_ref().map(|_| "open".to_string()),
        evidence: request.summary.clone(),
        summary: request.summary,
        content: request.content,
        file_path: std::path::PathBuf::new(), // Will be set by writer
    };

    if audit.summary.as_ref().map(|s| s.trim().is_empty()).unwrap_or(true) {
        return Err("Audit summary is required to describe the claim being verified.".to_string());
    }

    // Create audit
    let file_path = writer
        .create_audit(&audit)
        .map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    Ok(file_path.display().to_string())
}

/// Update an existing audit record
#[tauri::command]
pub fn update_audit(
    request: AuditUpdateRequest,
    state: State<AppState>,
) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = AuditWriter::new(root.clone());

    // Load existing audit
    let file_path = std::path::PathBuf::from(&request.file_path);
    let mut audit = MarkdownParser::parse_audit(&file_path)
        .map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    // Apply updates
    if let Some(title) = request.title {
        audit.title = title;
    }
    if let Some(date_str) = request.date {
        audit.date = NaiveDate::parse_from_str(&date_str, "%Y-%m-%d").ok();
    }
    if let Some(scope) = request.scope {
        audit.scope = Some(scope);
    }
    if let Some(risk) = request.risk {
        audit.risk = Some(risk);
    }
    if let Some(auditor) = request.auditor {
        audit.auditor = Some(auditor);
    }
    if let Some(status) = request.status {
        audit.status = Some(status);
    }
    if let Some(evidence) = request.summary.clone() {
        audit.evidence = Some(evidence);
    }
    if let Some(summary) = request.summary {
        audit.summary = Some(summary);
    }
    if let Some(content) = request.content {
        audit.content = content;
    }

    // Update audit
    writer.update_audit(&audit).map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    Ok(())
}

/// Delete an audit record
#[tauri::command]
pub fn delete_audit(file_path: String, state: State<AppState>) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = AuditWriter::new(root.clone());

    let path = std::path::PathBuf::from(file_path);
    writer.delete_audit(&path).map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    Ok(())
}

// ============================================================================
// Prompt Commands
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
pub struct PromptCreateRequest {
    pub title: String,
    pub prompt_id: Option<String>,
    pub agent: Option<String>,
    pub purpose: Option<String>,
    pub origin: Option<String>,
    pub status: Option<String>,
    pub prompt_text: Option<String>,
    pub content: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PromptUpdateRequest {
    pub file_path: String,
    pub title: Option<String>,
    pub prompt_id: Option<String>,
    pub agent: Option<String>,
    pub purpose: Option<String>,
    pub origin: Option<String>,
    pub status: Option<String>,
    pub prompt_text: Option<String>,
    pub content: Option<String>,
}

/// Create a new prompt
#[tauri::command]
pub fn create_prompt(
    request: PromptCreateRequest,
    state: State<AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap();
    let writer = PromptWriter::new(root.clone());

    let origin = request.origin.unwrap_or_else(|| "unspecified".to_string());
    let status = request.status.unwrap_or_else(|| "draft".to_string());

    // Build prompt
    let prompt = Prompt {
        prompt_id: request.prompt_id,
        agent: request.agent,
        purpose: request.purpose,
        origin: Some(origin),
        status: Some(status),
        timestamp: Some(chrono::Utc::now()),
        prompt_text: request.prompt_text,
        response_text: None,
        title: request.title,
        content: request.content,
        file_path: std::path::PathBuf::new(), // Will be set by writer
    };

    // Create prompt
    let file_path = writer
        .create_prompt(&prompt)
        .map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    Ok(file_path.display().to_string())
}

/// Update an existing prompt
#[tauri::command]
pub fn update_prompt(
    request: PromptUpdateRequest,
    state: State<AppState>,
) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = PromptWriter::new(root.clone());

    // Load existing prompt
    let file_path = std::path::PathBuf::from(&request.file_path);
    let mut prompt = MarkdownParser::parse_prompt(&file_path)
        .map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    // Apply updates
    if let Some(title) = request.title {
        prompt.title = title;
    }
    if let Some(prompt_id) = request.prompt_id {
        prompt.prompt_id = Some(prompt_id);
    }
    if let Some(agent) = request.agent {
        prompt.agent = Some(agent);
    }
    if let Some(purpose) = request.purpose {
        prompt.purpose = Some(purpose);
    }
    if let Some(ref origin) = request.origin {
        prompt.origin = Some(origin.clone());
    }
    if let Some(ref status) = request.status {
        prompt.status = Some(status.clone());
    }
    if let Some(prompt_text) = request.prompt_text {
        prompt.prompt_text = Some(prompt_text);
    }
    if let Some(content) = request.content {
        prompt.content = content;
    }
    if prompt.origin.is_none() {
        prompt.origin = Some(request.origin.unwrap_or_else(|| "unspecified".to_string()));
    }
    if prompt.status.is_none() {
        prompt.status = Some(request.status.unwrap_or_else(|| "draft".to_string()));
    }

    // Update prompt
    writer.update_prompt(&prompt).map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    Ok(())
}

/// Delete a prompt
#[tauri::command]
pub fn delete_prompt(file_path: String, state: State<AppState>) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = PromptWriter::new(root.clone());

    let path = std::path::PathBuf::from(file_path);
    writer.delete_prompt(&path).map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    Ok(())
}
