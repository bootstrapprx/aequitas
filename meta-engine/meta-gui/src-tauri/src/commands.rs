use meta_core::{
    GovernanceContext, GovernanceValidator, GoalQuery, GoalStatus,
    Goal, Audit,
};
use serde::{Serialize, Deserialize};
use tauri::State;
use crate::state::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct GoalDto {
    pub goal_id: String,
    pub title: String,
    pub status: String,
    pub phase: Option<u32>,
    pub owner: Option<String>,
    pub dependencies: Vec<String>,
    pub tags: Vec<String>,
    pub file_path: String,
}

impl From<&Goal> for GoalDto {
    fn from(goal: &Goal) -> Self {
        Self {
            goal_id: goal.goal_id.clone(),
            title: goal.title.clone(),
            status: goal.status.to_string(),
            phase: goal.phase,
            owner: goal.owner.clone(),
            dependencies: goal.dependencies.clone(),
            tags: goal.tags.clone(),
            file_path: goal.file_path.to_string_lossy().to_string(),
        }
    }
}

#[tauri::command]
pub fn get_all_goals(state: State<AppState>) -> Result<Vec<GoalDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root)
        .map_err(|e| e.to_string())?;

    let goals = ctx.all_goals()
        .iter()
        .map(|g| GoalDto::from(*g))
        .collect();

    Ok(goals)
}

#[tauri::command]
pub fn get_goals_by_status(status: String, state: State<AppState>) -> Result<Vec<GoalDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root)
        .map_err(|e| e.to_string())?;

    let goal_status = GoalStatus::from_str(&status)
        .ok_or_else(|| format!("Invalid status: {}", status))?;

    let query = GoalQuery::new(&ctx).with_status(goal_status);
    let goals = query.execute()
        .iter()
        .map(|g| GoalDto::from(*g))
        .collect();

    Ok(goals)
}

#[tauri::command]
pub fn get_goals_by_phase(phase: u32, state: State<AppState>) -> Result<Vec<GoalDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root)
        .map_err(|e| e.to_string())?;

    let query = GoalQuery::new(&ctx).with_phase(phase);
    let goals = query.execute()
        .iter()
        .map(|g| GoalDto::from(*g))
        .collect();

    Ok(goals)
}

#[tauri::command]
pub fn run_audit(state: State<AppState>) -> Result<Audit, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root)
        .map_err(|e| e.to_string())?;

    let audit = GovernanceValidator::validate(&ctx);
    Ok(audit)
}

#[tauri::command]
pub fn get_current_phase(state: State<AppState>) -> Result<Option<u32>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root)
        .map_err(|e| e.to_string())?;

    let current_phase = ctx
        .all_goals()
        .iter()
        .filter(|g| g.is_active())
        .filter_map(|g| g.phase)
        .max();

    Ok(current_phase)
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DashboardData {
    pub current_phase: Option<u32>,
    pub active_goals: Vec<GoalDto>,
    pub blocked_goals: Vec<GoalDto>,
    pub total_goals: usize,
    pub error_count: usize,
    pub warning_count: usize,
}

#[tauri::command]
pub fn get_dashboard_data(state: State<AppState>) -> Result<DashboardData, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root)
        .map_err(|e| e.to_string())?;

    let current_phase = ctx
        .all_goals()
        .iter()
        .filter(|g| g.is_active())
        .filter_map(|g| g.phase)
        .max();

    let active_query = GoalQuery::new(&ctx).with_status(GoalStatus::Active);
    let active_goals: Vec<GoalDto> = active_query.execute()
        .iter()
        .map(|g| GoalDto::from(*g))
        .collect();

    let blocked_query = GoalQuery::new(&ctx).with_status(GoalStatus::Blocked);
    let blocked_goals: Vec<GoalDto> = blocked_query.execute()
        .iter()
        .map(|g| GoalDto::from(*g))
        .collect();

    let total_goals = ctx.all_goals().len();

    let audit = GovernanceValidator::validate(&ctx);

    Ok(DashboardData {
        current_phase,
        active_goals,
        blocked_goals,
        total_goals,
        error_count: audit.error_count(),
        warning_count: audit.warning_count(),
    })
}
