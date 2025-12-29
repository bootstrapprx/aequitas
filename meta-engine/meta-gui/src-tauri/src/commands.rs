use chrono::NaiveDate;
use meta_core::{
    CanonDoc, GovernanceContext, GovernanceWarning, GovernanceWarningKind, Goal, GoalQuery,
    GoalStatus, AuditRecord,
};
use serde::{Deserialize, Serialize};
use tauri::State;

use crate::state::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct GoalDto {
    pub goal_id: String,
    pub title: String,
    pub status: String,
    pub phase: Option<String>,
    pub owner: Option<String>,
    pub dependencies: Vec<String>,
    pub canon: Vec<String>,
    pub tags: Vec<String>,
    pub updated: Option<String>,
    pub file_path: String,
}

impl From<&Goal> for GoalDto {
    fn from(goal: &Goal) -> Self {
        Self {
            goal_id: goal.goal_id.clone(),
            title: goal.title.clone(),
            status: goal.status.to_string(),
            phase: goal.phase.clone(),
            owner: goal.owner.clone(),
            dependencies: goal.dependencies.clone(),
            canon: goal.canon.clone(),
            tags: goal.tags.clone(),
            updated: goal.updated.map(|d| d.to_string()),
            file_path: goal.file_path.to_string_lossy().to_string(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PhaseDto {
    pub phase_id: String,
    pub title: String,
    pub status: Option<String>,
    pub updated: Option<String>,
}

impl From<&meta_core::Phase> for PhaseDto {
    fn from(phase: &meta_core::Phase) -> Self {
        PhaseDto {
            phase_id: phase.phase_id.clone(),
            title: phase.title.clone(),
            status: Some(phase.status.clone()),
            updated: None,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DecisionDto {
    pub decision_id: String,
    pub title: String,
    pub status: Option<String>,
    pub date: Option<String>,
    pub updated: Option<String>,
    pub file_path: String,
}

impl From<&meta_core::Decision> for DecisionDto {
    fn from(decision: &meta_core::Decision) -> Self {
        Self {
            decision_id: decision.decision_id.clone(),
            title: decision.title.clone(),
            status: decision.status.as_ref().map(|s| s.to_string()),
            date: decision.date.map(|d| d.to_string()),
            updated: decision.updated.map(|d| d.to_string()),
            file_path: decision.file_path.to_string_lossy().to_string(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AuditDto {
    pub title: String,
    pub date: Option<String>,
    pub scope: Option<String>,
    pub risk: Option<String>,
    pub auditor: Option<String>,
    pub summary: Option<String>,
    pub file_path: String,
}

impl From<&AuditRecord> for AuditDto {
    fn from(audit: &AuditRecord) -> Self {
        Self {
            title: audit.title.clone(),
            date: audit.date.map(|d| d.to_string()),
            scope: audit.scope.clone(),
            risk: audit.risk.clone(),
            auditor: audit.auditor.clone(),
            summary: audit.summary.clone(),
            file_path: audit.file_path.to_string_lossy().to_string(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CanonDocDto {
    pub title: String,
    pub file_path: String,
}

impl From<&CanonDoc> for CanonDocDto {
    fn from(doc: &CanonDoc) -> Self {
        Self {
            title: doc.title.clone(),
            file_path: doc.file_path.to_string_lossy().to_string(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WarningDto {
    pub kind: String,
    pub message: String,
    pub related: Vec<String>,
}

impl From<&GovernanceWarning> for WarningDto {
    fn from(warning: &GovernanceWarning) -> Self {
        Self {
            kind: match warning.kind {
                GovernanceWarningKind::MissingDailyNote => "missing_daily_note".to_string(),
                GovernanceWarningKind::GoalMissingPhase => "goal_missing_phase".to_string(),
                GovernanceWarningKind::GoalMissingStatus => "goal_missing_status".to_string(),
                GovernanceWarningKind::GoalMissingRecentDaily => {
                    "goal_missing_recent_daily".to_string()
                }
                GovernanceWarningKind::DecisionUnlinked => "decision_unlinked".to_string(),
                GovernanceWarningKind::PhaseWithoutActiveGoals => {
                    "phase_without_active_goals".to_string()
                }
            },
            message: warning.message.clone(),
            related: warning.related.clone(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DashboardData {
    pub current_phase: Option<PhaseDto>,
    pub active_goals: Vec<GoalDto>,
    pub blocked_goals: Vec<GoalDto>,
    pub total_goals: usize,
    pub today_exists: bool,
    pub today_path: String,
    pub today_mode: Option<String>,
    pub today_goals: Vec<String>,
    pub today_blockers: Vec<String>,
    pub today_decisions: Vec<String>,
    pub today_divergences: Vec<String>,
    pub recent_decisions: Vec<DecisionDto>,
    pub canon_docs: Vec<CanonDocDto>,
    pub warnings: Vec<WarningDto>,
}

#[tauri::command]
pub fn get_all_goals(state: State<AppState>) -> Result<Vec<GoalDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let goals = ctx
        .state
        .goals
        .iter()
        .map(GoalDto::from)
        .collect();

    Ok(goals)
}

#[tauri::command]
pub fn get_goals_by_status(status: String, state: State<AppState>) -> Result<Vec<GoalDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let goal_status = parse_goal_status(&status)?;

    let query = GoalQuery::new(&ctx).with_status(goal_status);
    let goals = query
        .execute()
        .iter()
        .map(|g| GoalDto::from(*g))
        .collect();

    Ok(goals)
}

#[tauri::command]
pub fn get_goals_by_phase(phase: String, state: State<AppState>) -> Result<Vec<GoalDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let query = GoalQuery::new(&ctx).with_phase(phase);
    let goals = query
        .execute()
        .iter()
        .map(|g| GoalDto::from(*g))
        .collect();

    Ok(goals)
}

#[tauri::command]
pub fn list_audits(state: State<AppState>) -> Result<Vec<AuditDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let audits = ctx
        .all_audits()
        .iter()
        .map(|a| AuditDto::from(*a))
        .collect();

    Ok(audits)
}

#[tauri::command]
pub fn get_dashboard_data(state: State<AppState>) -> Result<DashboardData, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let summary = ctx.summary();

    Ok(DashboardData {
        current_phase: summary.current_phase.as_ref().map(PhaseDto::from),
        active_goals: summary.active_goals.iter().map(GoalDto::from).collect(),
        blocked_goals: summary.blocked_goals.iter().map(GoalDto::from).collect(),
        total_goals: summary.total_goals,
        today_exists: summary.today_exists,
        today_path: summary.today_path.to_string_lossy().to_string(),
        today_mode: summary.today_mode.clone(),
        today_goals: summary.today_goals.clone(),
        today_blockers: summary.today_blockers.clone(),
        today_decisions: summary.today_decisions.clone(),
        today_divergences: summary.today_divergences.clone(),
        recent_decisions: summary
            .recent_decisions
            .iter()
            .map(DecisionDto::from)
            .collect(),
        canon_docs: summary
            .canon_docs
            .iter()
            .map(CanonDocDto::from)
            .collect(),
        warnings: summary.warnings.iter().map(WarningDto::from).collect(),
    })
}
#[tauri::command]
pub fn update_goal_status(
    goal_id: String,
    new_status: String,
    state: State<AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let status_enum = parse_goal_status(&new_status)?;
    ctx.update_goal_status(&goal_id, status_enum)
        .map_err(|e| e.to_string())?;

    Ok(format!("Updated {} to {}", goal_id, new_status))
}

#[tauri::command]
pub fn create_daily_note(date: String, state: State<AppState>) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let parsed_date =
        NaiveDate::parse_from_str(&date, "%Y-%m-%d").map_err(|e| format!("Invalid date: {}", e))?;

    let path = ctx.ensure_daily_note(parsed_date).map_err(|e| e.to_string())?;
    Ok(path.to_string_lossy().to_string())
}

#[tauri::command]
pub fn set_daily_mode(
    date: String,
    mode: Option<String>,
    state: State<AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let parsed_date =
        NaiveDate::parse_from_str(&date, "%Y-%m-%d").map_err(|e| format!("Invalid date: {}", e))?;

    let path = ctx
        .set_daily_mode(parsed_date, mode)
        .map_err(|e| e.to_string())?;
    Ok(path.to_string_lossy().to_string())
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DailyUpdateRequest {
    pub date: String,
    pub mode: Option<String>,
    pub protocol: Option<String>,
    pub goals: Option<Vec<String>>,
    pub blockers: Option<Vec<String>>,
    pub decisions: Option<Vec<String>>,
    pub divergences: Option<Vec<String>>,
    pub content: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DailyNoteDto {
    pub date: String,
    pub mode: Option<String>,
    pub protocol: Option<String>,
    pub goals: Vec<String>,
    pub blockers: Vec<String>,
    pub decisions: Vec<String>,
    pub divergences: Vec<String>,
    pub content: String,
}

impl From<&meta_core::DailyNote> for DailyNoteDto {
    fn from(d: &meta_core::DailyNote) -> Self {
        Self {
            date: d.date.to_string(),
        mode: d.mode.clone(),
        protocol: d.protocol.clone(),
        goals: d.goals.clone(),
        blockers: d.blockers.clone(),
        decisions: d.decisions.clone(),
        divergences: d.divergences.clone(),
        content: d.content.clone(),
    }
}
}

#[tauri::command]
pub fn get_daily_note(date: String, state: State<AppState>) -> Result<Option<DailyNoteDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let parsed_date =
        NaiveDate::parse_from_str(&date, "%Y-%m-%d").map_err(|e| format!("Invalid date: {}", e))?;

    let daily = ctx.get_daily(parsed_date);
    Ok(daily.map(|d| DailyNoteDto::from(&d)))
}

#[tauri::command]
pub fn update_daily_note(
    payload: DailyUpdateRequest,
    state: State<AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let parsed_date = NaiveDate::parse_from_str(&payload.date, "%Y-%m-%d")
        .map_err(|e| format!("Invalid date: {}", e))?;

    let path = ctx
        .update_daily(
            parsed_date,
            payload.mode.clone(),
            payload.protocol.clone(),
            payload.goals.clone(),
            payload.blockers.clone(),
            payload.decisions.clone(),
            payload.divergences.clone(),
            payload.content.clone(),
        )
        .map_err(|e| e.to_string())?;

    Ok(path.to_string_lossy().to_string())
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DailySummaryDto {
    pub date: String,
    pub mode: Option<String>,
    pub path: String,
}

#[tauri::command]
pub fn list_daily_notes(state: State<AppState>) -> Result<Vec<DailySummaryDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let notes = ctx
        .list_daily()
        .iter()
        .map(|d| DailySummaryDto {
            date: d.date.to_string(),
            mode: d.mode.clone(),
            path: d.file_path.to_string_lossy().to_string(),
        })
        .collect();

    Ok(notes)
}

fn parse_goal_status(status: &str) -> Result<GoalStatus, String> {
    match status.to_lowercase().as_str() {
        "planned" => Ok(GoalStatus::Planned),
        "active" => Ok(GoalStatus::Active),
        "blocked" => Ok(GoalStatus::Blocked),
        "partial" => Ok(GoalStatus::Partial),
        "done" | "completed" => Ok(GoalStatus::Done),
        other => Ok(GoalStatus::Unknown(other.to_string())),
    }
}
