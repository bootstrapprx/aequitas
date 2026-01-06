use chrono::NaiveDate;
use metatheos_core::{
    service::GoalService,
    store::dto::GoalDbDto,
    writer::{AuditWriter, PromptWriter},
    AuditRecord, DailyWriter, Goal, GoalStatus, Prompt,
};
use serde::{Deserialize, Serialize};
use std::str::FromStr;
use std::sync::Arc;
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
    pub parent_id: Option<String>,
    pub level: Option<String>,
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
    pub parent_id: Option<String>,
    pub level: Option<String>,
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
pub async fn create_goal(
    request: GoalCreateRequest,
    state: State<'_, AppState>,
) -> Result<String, String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    // Initialize service
    let goal_service = GoalService::new(store);

    // Validate ID format
    if !Goal::validate_id(&request.goal_id) {
        return Err(format!("Invalid goal id '{}'", request.goal_id));
    }

    // Parse status
    let status = GoalStatus::from_str(&request.status)
        .ok_or_else(|| format!("Invalid status: {}", request.status))?;

    // Build goal (service will handle validation and phase/level derivation)
    let goal = Goal {
        goal_id: request.goal_id,
        title: request.title,
        status,
        phase: request.phase,
        owner: request.owner,
        parent_id: request.parent_id,
        level: request.level,
        dependencies: request.dependencies,
        canon: request.canon,
        tags: request.tags,
        updated: None, // Service will set this
        file_path: std::path::PathBuf::new(),
        content: request.content,
    };

    // Use service to create (handles all validation and business rules)
    goal_service
        .create_goal(goal)
        .await
        .map_err(|e| e.to_string())
}

/// Update an existing goal
#[tauri::command]
pub async fn update_goal(
    goal_id: String,
    request: GoalUpdateRequest,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;
    let mut goal: Goal = store
        .get_db()
        .select(("goal", goal_id.as_str()))
        .await
        .map_err(|e| e.to_string())?
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
    if let Some(parent_id) = request.parent_id {
        if parent_id.trim().is_empty() {
            goal.parent_id = None;
        } else {
            goal.parent_id = Some(parent_id);
        }
    }
    if let Some(level) = request.level {
        goal.level = Some(level);
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

    // Validate parent exists and inherit phase/level when missing
    if let Some(parent_id) = &goal.parent_id {
        let parent: Goal = store
            .get_db()
            .select(("goal", parent_id.as_str()))
            .await
            .map_err(|e| e.to_string())?
            .ok_or_else(|| format!("Parent goal '{}' not found", parent_id))?;
        let parent_phase = parent.phase.clone().ok_or_else(|| {
            "Parent goal is missing a phase; phase is the canonical scope root".to_string()
        })?;
        if goal.phase.is_none() {
            goal.phase = Some(parent_phase.clone());
        } else if !goal
            .phase
            .as_ref()
            .map(|p| p.eq_ignore_ascii_case(&parent_phase))
            .unwrap_or(false)
        {
            return Err(
                "Parent → child phase mismatch: child must inherit parent's phase".to_string(),
            );
        }
        if goal.level.is_none() {
            goal.level = Some("subgoal".to_string());
        }
    } else if goal.level.is_none() {
        goal.level = Some("goal".to_string());
    }

    if goal.phase.is_none() {
        return Err("Goal must belong to a phase (phase is the canonical scope root)".to_string());
    }

    // Guard against children drifting across phases
    let mut children_out_of_phase: Vec<Goal> = Vec::new();
    if let Ok(mut resp) = store
        .get_db()
        .query("SELECT * FROM goal WHERE parent_id = $pid")
        .bind(("pid", goal.goal_id.clone()))
        .await
    {
        let kids: Result<Vec<Goal>, _> = resp.take(0);
        if let Ok(list) = kids {
            for child in list {
                if let (Some(child_phase), Some(goal_phase)) = (&child.phase, &goal.phase) {
                    if !child_phase.eq_ignore_ascii_case(goal_phase) {
                        children_out_of_phase.push(child);
                    }
                }
            }
        }
    }
    if !children_out_of_phase.is_empty() {
        return Err("Parent-child phase mismatch detected: update child tasks/sub-goals to the parent phase before saving".to_string());
    }

    goal.updated = Some(chrono::Utc::now().naive_utc().date());

    let goal_dto = GoalDbDto::from(goal);
    store
        .get_db()
        .update::<Option<serde_json::Value>>(("goal", goal_id.as_str()))
        .content(goal_dto)
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

/// Delete a goal (archives it)
#[tauri::command]
pub async fn delete_goal(goal_id: String, state: State<'_, AppState>) -> Result<(), String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;
    let _: Option<serde_json::Value> = store
        .get_db()
        .delete(("goal", goal_id.as_str()))
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

// ============================================================================
// Phase Commands
// ============================================================================

/// Create a new phase
#[tauri::command]
pub async fn create_phase(
    request: PhaseCreateRequest,
    state: State<'_, AppState>,
) -> Result<String, String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    let phase_id = request.phase_id.clone();

    // Normalize dates to plain strings; empty strings become nulls so Surreal stores a JSON null
    let start_date_value = match request.start_date.clone() {
        Some(ref s) if s.is_empty() => serde_json::Value::Null,
        Some(ref s) => serde_json::json!(s),
        None => serde_json::Value::Null,
    };
    let target_date_value = match request.target_date.clone() {
        Some(ref s) if s.is_empty() => serde_json::Value::Null,
        Some(ref s) => serde_json::json!(s),
        None => serde_json::Value::Null,
    };

    // Build phase payload (use json to omit created_at - let schema defaults apply)
    let phase_payload = serde_json::json!({
        "id": phase_id,
        "phase_id": phase_id,
        "title": request.title,
        "status": request.status,
        "start_date": start_date_value,
        "target_date": target_date_value,
        "dependencies": request.dependencies,
        "content": request.content,
        "file_path": "",
    });

    // Use CREATE (not UPDATE) to create new records - this applies schema defaults
    let _: Option<serde_json::Value> = store
        .get_db()
        .create(("phase", phase_id.as_str()))
        .content(phase_payload)
        .await
        .map_err(|e| e.to_string())?;

    Ok(phase_id)
}

/// Update an existing phase
#[tauri::command]
pub async fn update_phase(
    phase_id: String,
    request: PhaseUpdateRequest,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    // Use a generic map to build updates, avoiding deserialization of potentially malformed existing records
    let mut updates = serde_json::Map::new();

    // Always ensure phase_id is present (auto-repair)
    updates.insert("phase_id".to_string(), serde_json::json!(phase_id));

    if let Some(title) = request.title {
        updates.insert("title".to_string(), serde_json::json!(title));
    }
    if let Some(status) = request.status {
        updates.insert("status".to_string(), serde_json::json!(status));
    }
    if let Some(start_str) = request.start_date {
        // Store as string, relying on SurrealDB/serde to handle format if needed,
        // or just consistent string storage. Phase struct uses NaiveDate.
        if start_str.is_empty() {
            updates.insert("start_date".to_string(), serde_json::Value::Null);
        } else {
            updates.insert("start_date".to_string(), serde_json::json!(start_str));
        }
    }
    if let Some(target_str) = request.target_date {
        if target_str.is_empty() {
            updates.insert("target_date".to_string(), serde_json::Value::Null);
        } else {
            updates.insert("target_date".to_string(), serde_json::json!(target_str));
        }
    }
    if let Some(deps) = request.dependencies {
        updates.insert("dependencies".to_string(), serde_json::json!(deps));
    }
    if let Some(content) = request.content {
        updates.insert("content".to_string(), serde_json::json!(content));
    }

    // Use MERGE to update/patch the record
    // We use IgnoredAny to completely bypass any deserialization of the return value,
    // as we don't need it and it has caused "Invalid revision" and "invalid type" errors previously.
    let _: Option<serde::de::IgnoredAny> = store
        .get_db()
        .update(("phase", phase_id.as_str()))
        .merge(serde_json::Value::Object(updates))
        .await
        .map_err(|e| e.to_string())?;

    Ok(())
}

/// Set a phase as active
#[tauri::command]
pub async fn set_active_phase(phase_id: String, state: State<'_, AppState>) -> Result<(), String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    store
        .set_meta("active_phase", &phase_id)
        .await
        .map_err(|e| e.to_string())
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

    // Archive markdown (source of truth)
    writer
        .delete_daily_note(parsed_date)
        .map_err(|e| e.to_string())?;

    // Remove from SurrealDB cache if available
    if let Some(store) = state.db.lock().unwrap().as_ref() {
        let store = store.clone();
        let date_clone = date.clone();
        tauri::async_runtime::spawn(async move {
            let _ = store
                .get_db()
                .delete::<Option<metatheos_core::DailyNote>>(("daily_notes", date_clone.as_str()))
                .await;
        });
    }

    Ok(())
}

/// Enhanced version of update_daily_note using DailyWriter
#[tauri::command]
pub async fn write_daily_note(
    date: String,
    content: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap().clone();
    let writer = DailyWriter::new(root.clone());

    let parsed_date =
        NaiveDate::from_str(&date).map_err(|e| format!("Invalid date format: {}", e))?;

    // Write to markdown (source of truth)
    writer
        .write_daily_note(parsed_date, &content)
        .map_err(|e| e.to_string())?;

    // Update SurrealDB cache if available
    if let Some(store) = state.db.lock().unwrap().as_ref() {
        let store = store.clone();
        let date_clone = date.clone();
        tauri::async_runtime::spawn(async move {
            // Re-parse the daily note to get full structure (Manual construction due to parser removal)
            let daily_path = root.join("01_DAILY").join(format!("{}.md", date_clone));

            // Basic DailyNote construction for cache update
            // Full parsing is disabled in DB-only mode, but we keep content in sync
            let note = metatheos_core::DailyNote {
                date: NaiveDate::from_str(&date_clone).unwrap_or_default(),
                content: content.clone(), // Use the content we just wrote
                file_path: daily_path,
                phase: None,
                mode: None,
                protocol: None,
                goals_worked: vec![],
                decisions_made: vec![],
                divergences: vec![],
                goals: vec![],
                blockers: vec![],
                decisions: vec![],
                linked_goals: vec![],
                extra: std::collections::HashMap::new(),
            };

            let _ = store
                .get_db()
                .update::<Option<metatheos_core::DailyNote>>(("daily_notes", date_clone.as_str()))
                .content(note)
                .await;
        });
    }

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
pub fn create_audit(request: AuditCreateRequest, state: State<AppState>) -> Result<String, String> {
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

    if audit
        .summary
        .as_ref()
        .map(|s| s.trim().is_empty())
        .unwrap_or(true)
    {
        return Err("Audit summary is required to describe the claim being verified.".to_string());
    }

    // Create audit in markdown (source of truth)
    let file_path = writer
        .create_audit(&audit)
        .map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    // Add to SurrealDB cache if available
    if let Some(store) = state.db.lock().unwrap().as_ref() {
        let store = store.clone();
        let audit_clone = audit.clone();
        let stem = file_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown")
            .to_string();
        tauri::async_runtime::spawn(async move {
            let _ = store
                .get_db()
                .create::<Option<metatheos_core::AuditRecord>>(("audits", stem.as_str()))
                .content(audit_clone)
                .await;
        });
    }

    Ok(file_path.display().to_string())
}

/// Update an existing audit record
#[tauri::command]
pub fn update_audit(_request: AuditUpdateRequest, _state: State<AppState>) -> Result<(), String> {
    // TODO: Rewrite to use DB directly - MarkdownParser removed in DB-only architecture
    Err("update_audit deprecated: MarkdownParser removed. Use DB directly.".to_string())
}

/// Delete an audit record
#[tauri::command]
pub fn delete_audit(file_path: String, state: State<AppState>) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = AuditWriter::new(root.clone());

    let path = std::path::PathBuf::from(&file_path);
    let stem = path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("unknown")
        .to_string();

    // Archive markdown (source of truth)
    writer
        .delete_audit(&path)
        .map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    // Remove from SurrealDB cache if available
    if let Some(store) = state.db.lock().unwrap().as_ref() {
        let store = store.clone();
        tauri::async_runtime::spawn(async move {
            let _ = store
                .get_db()
                .delete::<Option<metatheos_core::AuditRecord>>(("audits", stem.as_str()))
                .await;
        });
    }

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

    // Create prompt in markdown (source of truth)
    let file_path = writer
        .create_prompt(&prompt)
        .map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    // Add to SurrealDB cache if available
    if let Some(store) = state.db.lock().unwrap().as_ref() {
        let store = store.clone();
        let prompt_clone = prompt.clone();
        let stem = file_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown")
            .to_string();
        tauri::async_runtime::spawn(async move {
            let _ = store
                .get_db()
                .create::<Option<metatheos_core::Prompt>>(("prompts", stem.as_str()))
                .content(prompt_clone)
                .await;
        });
    }

    Ok(file_path.display().to_string())
}

/// Update an existing prompt
#[tauri::command]
pub fn update_prompt(_request: PromptUpdateRequest, _state: State<AppState>) -> Result<(), String> {
    // TODO: Rewrite to use DB directly - MarkdownParser removed in DB-only architecture
    Err("update_prompt deprecated: MarkdownParser removed. Use DB directly.".to_string())
}

/// Delete a prompt
#[tauri::command]
pub fn delete_prompt(file_path: String, state: State<AppState>) -> Result<(), String> {
    let root = state.governance_root.lock().unwrap();
    let writer = PromptWriter::new(root.clone());

    let path = std::path::PathBuf::from(&file_path);
    let stem = path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("unknown")
        .to_string();

    // Archive markdown (source of truth)
    writer
        .delete_prompt(&path)
        .map_err(|e: metatheos_core::errors::MetaError| e.to_string())?;

    // Remove from SurrealDB cache if available
    if let Some(store) = state.db.lock().unwrap().as_ref() {
        let store = store.clone();
        tauri::async_runtime::spawn(async move {
            let _ = store
                .get_db()
                .delete::<Option<metatheos_core::Prompt>>(("prompts", stem.as_str()))
                .await;
        });
    }

    Ok(())
}
