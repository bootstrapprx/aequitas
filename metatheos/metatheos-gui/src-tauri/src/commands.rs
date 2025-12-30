use chrono::{NaiveDate, DateTime, Local};
use metatheos_core::{
    AuditRecord, CanonDoc, DailyContext, DependencyGap, GovernanceContext, GovernanceWarning,
    GovernanceWarningKind, Goal, GoalQuery, GoalRelations, GoalStatus, PhaseGoalBreakdown,
    ProtocolDoc,
};
use metatheos_core::writer::ensure_governance_layout;
use serde::{Deserialize, Serialize};
use tauri::State;

use crate::state::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct LayoutCheckResult {
    pub ok: bool,
    pub missing: Vec<String>,
}

#[tauri::command]
pub fn check_governance_layout(state: State<AppState>) -> Result<LayoutCheckResult, String> {
    let root = state.governance_root.lock().unwrap();
    let expected = [
        "01_DAILY",
        "02_PHASES",
        "03_GOALS_EPICS",
        "04_DECISIONS",
        "05_AUDITS",
        "06_PROMPTS",
    ];

    let missing: Vec<String> = expected
        .iter()
        .filter(|dir| !root.join(dir).exists())
        .map(|d| d.to_string())
        .collect();

    // Run guard for consistent error formatting (discard result, we only report missing list)
    let _ = ensure_governance_layout(&*root);

    Ok(LayoutCheckResult {
        ok: missing.is_empty(),
        missing,
    })
}

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

#[derive(Debug, Serialize, Deserialize)]
pub struct EnrichedGoalDto {
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
    // Enrichment data
    pub missing_dependencies: Vec<String>,
    pub blocked_by: Vec<String>,
    pub reverse_dependencies: Vec<String>,
    pub daily_references: Vec<String>,
    pub is_canonical: bool,
    pub completion_blocked: bool,
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

impl From<&metatheos_core::Phase> for PhaseDto {
    fn from(phase: &metatheos_core::Phase) -> Self {
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

impl From<&metatheos_core::Decision> for DecisionDto {
    fn from(decision: &metatheos_core::Decision) -> Self {
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
    pub status: Option<String>,
    pub evidence: Option<String>,
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
            status: audit.status.clone(),
            evidence: audit.evidence.clone(),
            summary: audit.summary.clone(),
            file_path: audit.file_path.to_string_lossy().to_string(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PromptDto {
    pub prompt_id: Option<String>,
    pub agent: Option<String>,
    pub purpose: Option<String>,
    pub origin: Option<String>,
    pub status: Option<String>,
    pub prompt_text: Option<String>,
    pub title: String,
    pub file_path: String,
    pub timestamp: Option<String>,
}

impl From<&metatheos_core::Prompt> for PromptDto {
    fn from(prompt: &metatheos_core::Prompt) -> Self {
        Self {
            prompt_id: prompt.prompt_id.clone(),
            agent: prompt.agent.clone(),
            purpose: prompt.purpose.clone(),
            origin: prompt.origin.clone(),
            status: prompt.status.clone(),
            prompt_text: prompt.prompt_text.clone(),
            title: prompt.title.clone(),
            file_path: prompt.file_path.to_string_lossy().to_string(),
            timestamp: prompt.timestamp.map(|t| t.to_rfc3339()),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EnrichedAuditDto {
    pub title: String,
    pub date: Option<String>,
    pub scope: Option<String>,
    pub risk: Option<String>,
    pub auditor: Option<String>,
    pub status: Option<String>,
    pub evidence: Option<String>,
    pub summary: Option<String>,
    pub file_path: String,
    // Enrichment data
    pub referenced_goals: Vec<String>,
    pub daily_references: Vec<String>,
    pub related_prompts: Vec<String>,
    pub last_reviewed: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EnrichedPromptDto {
    pub prompt_id: Option<String>,
    pub agent: Option<String>,
    pub purpose: Option<String>,
    pub origin: Option<String>,
    pub status: Option<String>,
    pub prompt_text: Option<String>,
    pub title: String,
    pub file_path: String,
    // Enrichment data
    pub referenced_goals: Vec<String>,
    pub daily_references: Vec<String>,
    pub related_audits: Vec<String>,
    pub timestamp: Option<String>,
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
pub struct ProtocolDocDto {
    pub title: String,
    pub file_path: String,
}

impl From<&ProtocolDoc> for ProtocolDocDto {
    fn from(doc: &ProtocolDoc) -> Self {
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
    pub protocols: Vec<ProtocolDocDto>,
    pub latest_daily: Option<DailyFocusDto>,
    pub active_by_phase: Vec<PhaseGoalsDto>,
    pub orphaned_goals: Vec<GoalDto>,
    pub stale_goals: Vec<GoalDto>,
    pub top_blocked: Vec<GoalDto>,
    pub warnings: Vec<WarningDto>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DailyFocusDto {
    pub date: String,
    pub mode: Option<String>,
    pub goals: Vec<String>,
    pub blockers: Vec<String>,
    pub decisions: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PhaseGoalsDto {
    pub phase: PhaseDto,
    pub active_goals: Vec<GoalDto>,
}

impl From<&PhaseGoalBreakdown> for PhaseGoalsDto {
    fn from(value: &PhaseGoalBreakdown) -> Self {
        Self {
            phase: PhaseDto::from(&value.phase),
            active_goals: value
                .active_goals
                .iter()
                .map(GoalDto::from)
                .collect(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DependencyGapDto {
    pub goal_id: String,
    pub missing: Vec<String>,
}

impl From<&DependencyGap> for DependencyGapDto {
    fn from(gap: &DependencyGap) -> Self {
        Self {
            goal_id: gap.goal_id.clone(),
            missing: gap.missing.clone(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GoalRelationsDto {
    pub goal: GoalDto,
    pub decisions: Vec<DecisionDto>,
    pub audits: Vec<AuditDto>,
    pub daily_refs: Vec<String>,
    pub missing_dependencies: Vec<String>,
    pub out_of_phase: bool,
}

impl From<&GoalRelations> for GoalRelationsDto {
    fn from(rel: &GoalRelations) -> Self {
        Self {
            goal: GoalDto::from(&rel.goal),
            decisions: rel.decisions.iter().map(DecisionDto::from).collect(),
            audits: rel.audits.iter().map(AuditDto::from).collect(),
            daily_refs: rel.daily_refs.iter().map(|d| d.date.to_string()).collect(),
            missing_dependencies: rel.missing_dependencies.clone(),
            out_of_phase: rel.out_of_phase,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DailyContextDto {
    pub date: String,
    pub note: Option<DailyNoteDto>,
    pub active_phase: Option<PhaseDto>,
    pub in_phase_goals: Vec<GoalDto>,
    pub out_of_phase_goals: Vec<GoalDto>,
    pub goal_relations: Vec<GoalRelationsDto>,
    pub recent_decisions: Vec<DecisionDto>,
    pub linked_decisions: Vec<DecisionDto>,
    pub linked_audits: Vec<AuditDto>,
    pub blocked_goals: Vec<GoalDto>,
    pub dependency_gaps: Vec<DependencyGapDto>,
    pub active_goal_count: usize,
    pub blocked_goal_count: usize,
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
pub fn get_enriched_goals(state: State<AppState>) -> Result<Vec<EnrichedGoalDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    // Build reverse dependency map
    let mut reverse_deps: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();
    for goal in &ctx.state.goals {
        for dep in &goal.dependencies {
            reverse_deps
                .entry(dep.clone())
                .or_insert_with(Vec::new)
                .push(goal.goal_id.clone());
        }
    }

    // Build goal ID lookup
    let goal_map: std::collections::HashMap<String, &Goal> = ctx
        .state
        .goals
        .iter()
        .map(|g| (g.goal_id.clone(), g))
        .collect();

    // Collect daily note references
    let mut daily_refs: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();
    for daily in &ctx.state.daily_notes {
        for goal_id in &daily.goals {
            daily_refs
                .entry(goal_id.clone())
                .or_insert_with(Vec::new)
                .push(daily.date.to_string());
        }
    }

    let enriched_goals: Vec<EnrichedGoalDto> = ctx
        .state
        .goals
        .iter()
        .map(|goal| {
            // Find missing dependencies
            let missing_deps: Vec<String> = goal
                .dependencies
                .iter()
                .filter(|dep| !goal_map.contains_key(*dep))
                .cloned()
                .collect();

            // Find blocking dependencies (dependencies not done)
            let blocked_by: Vec<String> = goal
                .dependencies
                .iter()
                .filter_map(|dep| {
                    goal_map.get(dep).and_then(|dep_goal| {
                        if !dep_goal.is_done() {
                            Some(dep.clone())
                        } else {
                            None
                        }
                    })
                })
                .collect();

            let reverse_dependencies = reverse_deps
                .get(&goal.goal_id)
                .cloned()
                .unwrap_or_else(Vec::new);

            let daily_references = daily_refs
                .get(&goal.goal_id)
                .cloned()
                .unwrap_or_else(Vec::new);

            let is_canonical = !goal.canon.is_empty();
            let completion_blocked = !blocked_by.is_empty();

            EnrichedGoalDto {
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
                missing_dependencies: missing_deps,
                blocked_by,
                reverse_dependencies,
                daily_references,
                is_canonical,
                completion_blocked,
            }
        })
        .collect();

    Ok(enriched_goals)
}

#[tauri::command]
pub fn get_all_audits(state: State<AppState>) -> Result<Vec<AuditDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let audits = ctx
        .state
        .audits
        .iter()
        .map(AuditDto::from)
        .collect();

    Ok(audits)
}

#[tauri::command]
pub fn get_all_prompts(state: State<AppState>) -> Result<Vec<PromptDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let prompts = ctx
        .state
        .prompts
        .iter()
        .map(PromptDto::from)
        .collect();

    Ok(prompts)
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
        protocols: summary
            .protocols
            .iter()
            .map(ProtocolDocDto::from)
            .collect(),
        latest_daily: summary.latest_daily.as_ref().map(|d| DailyFocusDto {
            date: d.date.to_string(),
            mode: d.mode.clone(),
            goals: d.goals.clone(),
            blockers: d.blockers.clone(),
            decisions: d.decisions.clone(),
        }),
        active_by_phase: summary
            .active_by_phase
            .iter()
            .map(PhaseGoalsDto::from)
            .collect(),
        orphaned_goals: summary
            .orphaned_goals
            .iter()
            .map(GoalDto::from)
            .collect(),
        stale_goals: summary
            .stale_goals
            .iter()
            .map(GoalDto::from)
            .collect(),
        top_blocked: summary
            .top_blocked
            .iter()
            .map(GoalDto::from)
            .collect(),
        warnings: summary.warnings.iter().map(WarningDto::from).collect(),
    })
}

#[tauri::command]
pub fn get_daily_context(date: String, state: State<AppState>) -> Result<DailyContextDto, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let parsed_date =
        NaiveDate::parse_from_str(&date, "%Y-%m-%d").map_err(|e| format!("Invalid date: {}", e))?;

    let context: DailyContext = ctx.daily_context(parsed_date);

    Ok(DailyContextDto {
        date,
        note: context.note.as_ref().map(DailyNoteDto::from),
        active_phase: context.active_phase.as_ref().map(PhaseDto::from),
        in_phase_goals: context
            .in_phase_goals
            .iter()
            .map(GoalDto::from)
            .collect(),
        out_of_phase_goals: context
            .out_of_phase_goals
            .iter()
            .map(GoalDto::from)
            .collect(),
        goal_relations: context
            .goal_relations
            .values()
            .map(GoalRelationsDto::from)
            .collect(),
        recent_decisions: context
            .recent_decisions
            .iter()
            .map(DecisionDto::from)
            .collect(),
        linked_decisions: context
            .linked_decisions
            .iter()
            .map(DecisionDto::from)
            .collect(),
        linked_audits: context
            .linked_audits
            .iter()
            .map(AuditDto::from)
            .collect(),
        blocked_goals: context
            .blocked_goals
            .iter()
            .map(GoalDto::from)
            .collect(),
        dependency_gaps: context
            .dependency_gaps
            .iter()
            .map(DependencyGapDto::from)
            .collect(),
        active_goal_count: context.active_goal_count,
        blocked_goal_count: context.blocked_goal_count,
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

impl From<&metatheos_core::DailyNote> for DailyNoteDto {
    fn from(d: &metatheos_core::DailyNote) -> Self {
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

#[tauri::command]
pub fn get_enriched_audits(state: State<AppState>) -> Result<Vec<EnrichedAuditDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    // Build goal references map (scan goals for audit mentions)
    let mut goal_refs: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();
    for goal in &ctx.state.goals {
        // Simple heuristic: check content for audit file references
        for audit in &ctx.state.audits {
            let audit_name = audit.file_path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if goal.content.contains(audit_name) || goal.content.contains(&audit.title) {
                goal_refs
                    .entry(audit.file_path.to_string_lossy().to_string())
                    .or_insert_with(Vec::new)
                    .push(goal.goal_id.clone());
            }
        }
    }

    // Build daily note references
    let mut daily_refs: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();
    for daily in &ctx.state.daily_notes {
        for audit in &ctx.state.audits {
            let audit_name = audit.file_path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if daily.content.contains(audit_name) || daily.content.contains(&audit.title) {
                daily_refs
                    .entry(audit.file_path.to_string_lossy().to_string())
                    .or_insert_with(Vec::new)
                    .push(daily.date.to_string());
            }
        }
    }

    // Build prompt relations (audits mentioning prompts)
    let mut prompt_refs: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();
    for audit in &ctx.state.audits {
        for prompt in &ctx.state.prompts {
            let prompt_name = prompt.file_path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if audit.content.contains(prompt_name) ||
               audit.content.contains(&prompt.title) ||
               prompt.prompt_id.as_ref().map(|id| audit.content.contains(id)).unwrap_or(false) {
                prompt_refs
                    .entry(audit.file_path.to_string_lossy().to_string())
                    .or_insert_with(Vec::new)
                    .push(prompt.prompt_id.clone().unwrap_or_else(|| prompt.title.clone()));
            }
        }
    }

    let enriched_audits: Vec<EnrichedAuditDto> = ctx
        .state
        .audits
        .iter()
        .map(|audit| {
            let file_path_str = audit.file_path.to_string_lossy().to_string();

            let referenced_goals = goal_refs
                .get(&file_path_str)
                .cloned()
                .unwrap_or_else(Vec::new);

            let daily_references = daily_refs
                .get(&file_path_str)
                .cloned()
                .unwrap_or_else(Vec::new);

            let related_prompts = prompt_refs
                .get(&file_path_str)
                .cloned()
                .unwrap_or_else(Vec::new);

            EnrichedAuditDto {
                title: audit.title.clone(),
                date: audit.date.map(|d| d.to_string()),
                scope: audit.scope.clone(),
                risk: audit.risk.clone(),
                auditor: audit.auditor.clone(),
                status: audit.status.clone(),
                evidence: audit.evidence.clone(),
                summary: audit.summary.clone(),
                file_path: file_path_str,
                referenced_goals,
                daily_references,
                related_prompts,
                last_reviewed: file_last_reviewed(audit.file_path.as_path()),
            }
        })
        .collect();

    Ok(enriched_audits)
}

#[tauri::command]
pub fn get_enriched_prompts(state: State<AppState>) -> Result<Vec<EnrichedPromptDto>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    // Build goal references map
    let mut goal_refs: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();
    for goal in &ctx.state.goals {
        for prompt in &ctx.state.prompts {
            let prompt_name = prompt.file_path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if goal.content.contains(prompt_name) ||
               goal.content.contains(&prompt.title) ||
               prompt.prompt_id.as_ref().map(|id| goal.content.contains(id)).unwrap_or(false) {
                goal_refs
                    .entry(prompt.file_path.to_string_lossy().to_string())
                    .or_insert_with(Vec::new)
                    .push(goal.goal_id.clone());
            }
        }
    }

    // Build daily note references
    let mut daily_refs: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();
    for daily in &ctx.state.daily_notes {
        for prompt in &ctx.state.prompts {
            let prompt_name = prompt.file_path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if daily.content.contains(prompt_name) ||
               daily.content.contains(&prompt.title) ||
               prompt.prompt_id.as_ref().map(|id| daily.content.contains(id)).unwrap_or(false) {
                daily_refs
                    .entry(prompt.file_path.to_string_lossy().to_string())
                    .or_insert_with(Vec::new)
                    .push(daily.date.to_string());
            }
        }
    }

    // Build audit relations (prompts mentioned in audits)
    let mut audit_refs: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();
    for prompt in &ctx.state.prompts {
        for audit in &ctx.state.audits {
            let prompt_name = prompt.file_path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if audit.content.contains(prompt_name) ||
               audit.content.contains(&prompt.title) ||
               prompt.prompt_id.as_ref().map(|id| audit.content.contains(id)).unwrap_or(false) {
                audit_refs
                    .entry(prompt.file_path.to_string_lossy().to_string())
                    .or_insert_with(Vec::new)
                    .push(audit.title.clone());
            }
        }
    }

    let enriched_prompts: Vec<EnrichedPromptDto> = ctx
        .state
        .prompts
        .iter()
        .map(|prompt| {
            let file_path_str = prompt.file_path.to_string_lossy().to_string();

            let referenced_goals = goal_refs
                .get(&file_path_str)
                .cloned()
                .unwrap_or_else(Vec::new);

            let daily_references = daily_refs
                .get(&file_path_str)
                .cloned()
                .unwrap_or_else(Vec::new);

            let related_audits = audit_refs
                .get(&file_path_str)
                .cloned()
                .unwrap_or_else(Vec::new);

            EnrichedPromptDto {
                prompt_id: prompt.prompt_id.clone(),
                agent: prompt.agent.clone(),
                purpose: prompt.purpose.clone(),
                origin: prompt.origin.clone(),
                status: prompt.status.clone(),
                prompt_text: prompt.prompt_text.clone(),
                title: prompt.title.clone(),
                file_path: file_path_str,
                referenced_goals,
                daily_references,
                related_audits,
                timestamp: prompt.timestamp.map(|t| t.to_rfc3339()),
            }
        })
        .collect();

    Ok(enriched_prompts)
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

fn file_last_reviewed(path: &std::path::Path) -> Option<String> {
    let metadata = std::fs::metadata(path).ok()?;
    let modified = metadata.modified().ok()?;
    let dt: DateTime<Local> = modified.into();
    Some(dt.to_rfc3339())
}
