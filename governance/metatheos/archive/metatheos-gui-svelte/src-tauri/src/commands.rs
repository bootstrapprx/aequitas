use chrono::{DateTime, Local, NaiveDate, Utc};
use metatheos_core::store;
use metatheos_core::{
    service::GoalService, AequitasDashboard, Annotation, AnnotationAuthor, AnnotationScope,
    AuditRecord, CanonDoc, DailyContext, DashboardCalculator, DependencyGap, Event, EventAction,
    Goal, GoalQuery, GoalRelations, GoalStatus, GovernanceContext, GovernanceWarning,
    GovernanceWarningKind, PhaseGoalBreakdown, ProtocolDoc, ReadOnlyGovernanceContext, WorkItem,
    WorkItemLevel, WorkItemStatus,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use tauri::State;
use uuid::Uuid;

use crate::state::AppState;
use metatheos_core::store::consequences::ConsequenceEngine;

#[derive(Debug, Serialize, Deserialize)]
pub struct LayoutCheckResult {
    pub ok: bool,
    pub missing: Vec<String>,
}

#[tauri::command]
pub async fn check_governance_layout(
    _state: State<'_, AppState>,
) -> Result<LayoutCheckResult, String> {
    let missing: Vec<String> = Vec::new();
    Ok(LayoutCheckResult { ok: true, missing })
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GoalDto {
    pub goal_id: String,
    pub title: String,
    pub status: String,
    pub phase: Option<String>,
    pub level: Option<String>,
    pub owner: Option<String>,
    pub parent_id: Option<String>,
    pub dependencies: Vec<String>,
    pub canon: Vec<String>,
    pub tags: Vec<String>,
    pub updated: Option<String>,
    pub file_path: String,
    pub completion_pct: u8,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EnrichedGoalDto {
    pub goal_id: String,
    pub title: String,
    pub status: String,
    pub phase: Option<String>,
    pub level: Option<String>,
    pub owner: Option<String>,
    pub parent_id: Option<String>,
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
    pub completion_pct: u8,
}

impl From<&Goal> for GoalDto {
    fn from(goal: &Goal) -> Self {
        let completion_pct = match goal.status {
            GoalStatus::Done | GoalStatus::Archived => 100,
            GoalStatus::Partial => 50,
            _ => 0,
        };
        Self {
            goal_id: goal.goal_id.clone(),
            title: goal.title.clone(),
            status: goal.status.to_string(),
            phase: goal.phase.clone(),
            level: goal.level.clone(),
            owner: goal.owner.clone(),
            parent_id: goal.parent_id.clone(),
            dependencies: goal.dependencies.clone(),
            canon: goal.canon.clone(),
            tags: goal.tags.clone(),
            updated: goal.updated.map(|d| d.to_string()),
            file_path: goal.file_path.to_string_lossy().to_string(),
            completion_pct,
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
pub struct PhaseMetricsDto {
    pub phase_id: Option<String>,
    pub total_goals: usize,
    pub active: usize,
    pub blocked: usize,
    pub done: usize,
    pub completion_pct: f64,
}

// Helper to resolve active phase from DB (Day -> Meta -> First Active)
async fn resolve_active_phase_db(
    store: &metatheos_core::store::SurrealStore,
    date: Option<NaiveDate>,
) -> Result<Option<metatheos_core::Phase>, String> {
    // 1. Check Day (if provided)
    if let Some(d) = date {
        if let Ok(Some(note)) = store.get_daily_note(d).await {
            if let Some(pid) = &note.phase {
                if let Ok(all_phases) = store.get_all_phases().await {
                    if let Some(p) = all_phases.into_iter().find(|p| &p.phase_id == pid) {
                        return Ok(Some(p));
                    }
                }
            }
        }
    }

    // 2. Check Meta (Global Active Phase)
    if let Ok(Some(active_id)) = store.get_meta("active_phase").await {
        if let Ok(all_phases) = store.get_all_phases().await {
            if let Some(p) = all_phases.into_iter().find(|p| p.phase_id == active_id) {
                return Ok(Some(p));
            }
        }
    }

    // 3. Fallback: First Active Phase
    if let Ok(all_phases) = store.get_all_phases().await {
        // Priority sort? Assuming ID order or just first active for now.
        if let Some(p) = all_phases
            .into_iter()
            .find(|p| p.status.eq_ignore_ascii_case("active"))
        {
            return Ok(Some(p));
        }
    }

    Ok(None)
}

#[tauri::command]
pub async fn get_all_phases(state: State<'_, AppState>) -> Result<Vec<PhaseDto>, String> {
    println!("🔍 [get_all_phases] Called from UI");
    let store_opt = {
        let guard = state.db.lock().unwrap();
        guard.as_ref().cloned()
    };

    let store = store_opt.ok_or_else(|| {
        println!("❌ [get_all_phases] Store not initialized!");
        "Store not initialized".to_string()
    })?;

    println!("📊 [get_all_phases] Querying store.get_all_phases()...");
    let phases = store.get_all_phases().await.map_err(|e| {
        println!("❌ [get_all_phases] Query failed: {}", e);
        e.to_string()
    })?;

    println!("✅ [get_all_phases] Got {} phases from DB", phases.len());
    for phase in &phases {
        println!("  └─ Phase: {} | {} | {}", phase.phase_id, phase.title, phase.status);
    }

    let dtos: Vec<PhaseDto> = phases.iter().map(PhaseDto::from).collect();
    println!("✅ [get_all_phases] Returning {} PhaseDto objects to UI", dtos.len());
    Ok(dtos)
}

#[tauri::command]
pub async fn get_active_phase(
    date: Option<String>,
    state: State<'_, AppState>,
) -> Result<Option<PhaseDto>, String> {
    let parsed_date = date.and_then(|d| NaiveDate::parse_from_str(&d, "%Y-%m-%d").ok());

    let store_opt = {
        let guard = state.db.lock().unwrap();
        guard.as_ref().cloned()
    };

    let store = store_opt.ok_or("Store not initialized")?;
    let phase = resolve_active_phase_db(&store, parsed_date).await?;
    Ok(phase.as_ref().map(PhaseDto::from))
}

/// Set active phase using meta key (DB-first, no markdown)
#[tauri::command]
pub async fn set_active_phase_db(
    state: State<'_, AppState>,
    phase_id: String,
) -> Result<(), String> {
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
    pub completed_goals: usize,
    pub planned_goals: usize,
    pub archived_goals: usize,
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
            active_goals: value.active_goals.iter().map(GoalDto::from).collect(),
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
    pub phase_defined: bool,
    pub phase_metrics: PhaseMetricsDto,
    pub phase_goals: Vec<GoalDto>,
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
pub async fn get_all_goals(state: State<'_, AppState>) -> Result<Vec<GoalDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    let goals = GoalQuery::new(&ctx)
        .execute()
        .into_iter()
        .map(|g| ctx.goal_with_effective_phase(g))
        .map(|g| GoalDto::from(&g))
        .collect();

    Ok(goals)
}

#[tauri::command]
pub async fn get_enriched_goals(
    state: State<'_, AppState>,
) -> Result<Vec<EnrichedGoalDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;
    let phase_scope = ctx.phase_scope(Local::now().naive_local().date(), None);
    let phase_id = phase_scope.metrics.phase_id.clone();
    let scoped_goals = phase_scope.goals;

    // Build reverse dependency map
    let mut reverse_deps: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for goal in &scoped_goals {
        for dep in &goal.dependencies {
            reverse_deps
                .entry(dep.clone())
                .or_insert_with(Vec::new)
                .push(goal.goal_id.clone());
        }
    }

    // Build goal ID lookup
    let goal_map: std::collections::HashMap<String, &Goal> = scoped_goals
        .iter()
        .map(|g| (g.goal_id.clone(), g))
        .collect();

    // Collect daily note references
    let mut daily_refs: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for daily in &ctx.state.daily_notes {
        if let Some(pid) = &phase_id {
            if !daily
                .phase
                .as_ref()
                .map(|p| p.eq_ignore_ascii_case(pid))
                .unwrap_or(false)
            {
                continue;
            }
        } else {
            continue;
        }
        for goal_id in &daily.goals {
            daily_refs
                .entry(goal_id.clone())
                .or_insert_with(Vec::new)
                .push(daily.date.to_string());
        }
    }

    // Build parent map for sub-goals
    let mut children_map: std::collections::HashMap<String, Vec<&Goal>> =
        std::collections::HashMap::new();
    for goal in &scoped_goals {
        if let Some(parent) = &goal.parent_id {
            children_map
                .entry(parent.clone())
                .or_insert_with(Vec::new)
                .push(goal);
        }
    }

    let enriched_goals: Vec<EnrichedGoalDto> = scoped_goals
        .iter()
        .map(|g| ctx.goal_with_effective_phase(g))
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

            // Calculate completion
            let children = children_map
                .get(&goal.goal_id)
                .map(|v| v.as_slice())
                .unwrap_or(&[]);
            let completion_pct = if !children.is_empty() {
                let total_children = children.len();
                let sum_pct: u32 = children
                    .iter()
                    .map(|c| match c.status {
                        GoalStatus::Done | GoalStatus::Archived => 100,
                        GoalStatus::Partial => 50,
                        _ => 0,
                    })
                    .sum();
                (sum_pct / total_children as u32) as u8
            } else {
                match goal.status {
                    GoalStatus::Done | GoalStatus::Archived => 100,
                    GoalStatus::Partial => 50,
                    _ => 0,
                }
            };

            EnrichedGoalDto {
                goal_id: goal.goal_id.clone(),
                title: goal.title.clone(),
                status: goal.status.to_string(),
                phase: goal.phase.clone(),
                level: goal.level.clone(),
                owner: goal.owner.clone(),
                parent_id: goal.parent_id.clone(),
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
                completion_pct,
            }
        })
        .collect();

    Ok(enriched_goals)
}

#[tauri::command]
pub async fn get_all_audits(state: State<'_, AppState>) -> Result<Vec<AuditDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    let audits = ctx.state.audits.iter().map(AuditDto::from).collect();

    Ok(audits)
}

#[tauri::command]
pub async fn get_all_prompts(state: State<'_, AppState>) -> Result<Vec<PromptDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    let prompts = ctx.state.prompts.iter().map(PromptDto::from).collect();

    Ok(prompts)
}

#[tauri::command]
pub async fn get_goals_by_status(
    status: String,
    state: State<'_, AppState>,
) -> Result<Vec<GoalDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    let goal_status = parse_goal_status(&status)?;

    let query = GoalQuery::new(&ctx).with_status(goal_status);
    let goals = query
        .execute()
        .iter()
        .map(|g| ctx.goal_with_effective_phase(g))
        .map(|g| GoalDto::from(&g))
        .collect();

    Ok(goals)
}

#[tauri::command]
pub async fn get_goals_by_phase(
    phase: String,
    state: State<'_, AppState>,
) -> Result<Vec<EnrichedGoalDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    // 1. Filter goals by phase
    let scoped_goals: Vec<metatheos_core::Goal> = ctx
        .state
        .goals
        .iter()
        .filter_map(|g| {
            let resolved = ctx.goal_with_effective_phase(g);
            let matches = resolved
                .phase
                .as_ref()
                .map(|p| p.eq_ignore_ascii_case(&phase))
                .unwrap_or(false);
            if matches {
                Some(resolved)
            } else {
                None
            }
        })
        .collect();

    // 2. Build Maps for Enrichment (Scoped to this phase)
    let goal_map: std::collections::HashMap<String, &Goal> = scoped_goals
        .iter()
        .map(|g| (g.goal_id.clone(), g))
        .collect();

    let mut reverse_deps: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for goal in &scoped_goals {
        for dep in &goal.dependencies {
            reverse_deps
                .entry(dep.clone())
                .or_insert_with(Vec::new)
                .push(goal.goal_id.clone());
        }
    }

    let mut daily_refs: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for daily in &ctx.state.daily_notes {
        for goal_id in &daily.goals {
            if goal_map.contains_key(goal_id) {
                daily_refs
                    .entry(goal_id.clone())
                    .or_insert_with(Vec::new)
                    .push(daily.date.to_string());
            }
        }
    }

    let mut children_map: std::collections::HashMap<String, Vec<&Goal>> =
        std::collections::HashMap::new();
    for goal in &scoped_goals {
        if let Some(parent) = &goal.parent_id {
            children_map
                .entry(parent.clone())
                .or_insert_with(Vec::new)
                .push(goal);
        }
    }

    // 3. Enrich
    let enriched_goals: Vec<EnrichedGoalDto> = scoped_goals
        .iter()
        .map(|goal| {
            // Find missing dependencies (in this scope)
            let missing_deps: Vec<String> = goal
                .dependencies
                .iter()
                .filter(|dep| !goal_map.contains_key(*dep))
                .cloned()
                .collect();

            // Find blocking dependencies
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

            // Calculate completion
            let children = children_map
                .get(&goal.goal_id)
                .map(|v| v.as_slice())
                .unwrap_or(&[]);
            let completion_pct = if !children.is_empty() {
                let total_children = children.len();
                let sum_pct: u32 = children
                    .iter()
                    .map(|c| match c.status {
                        GoalStatus::Done | GoalStatus::Archived => 100,
                        GoalStatus::Partial => 50,
                        _ => 0,
                    })
                    .sum();
                (sum_pct / total_children as u32) as u8
            } else {
                match goal.status {
                    GoalStatus::Done | GoalStatus::Archived => 100,
                    GoalStatus::Partial => 50,
                    _ => 0,
                }
            };

            EnrichedGoalDto {
                goal_id: goal.goal_id.clone(),
                title: goal.title.clone(),
                status: goal.status.to_string(),
                phase: goal.phase.clone(),
                level: goal.level.clone(),
                owner: goal.owner.clone(),
                parent_id: goal.parent_id.clone(),
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
                completion_pct,
            }
        })
        .collect();

    Ok(enriched_goals)
}

#[tauri::command]
pub async fn list_audits(state: State<'_, AppState>) -> Result<Vec<AuditDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    let audits = ctx
        .all_audits()
        .iter()
        .map(|a| AuditDto::from(*a))
        .collect();

    Ok(audits)
}

#[tauri::command]
pub async fn get_dashboard_data(state: State<'_, AppState>) -> Result<DashboardData, String> {
    let root = state.governance_root.lock().unwrap().clone();

    let store_opt = {
        let db_mutex = state.db.lock().unwrap();
        db_mutex.clone()
    };

    let ctx = if let Some(store) = store_opt {
        GovernanceContext::from_store(&store, root)
            .await
            .map_err(|e| e.to_string())?
    } else {
        GovernanceContext::load_async(&root)
            .await
            .map_err(|e| e.to_string())?
    };

    let summary = ctx.summary();

    // Calculate additional stats
    let completed_count = ctx
        .state
        .goals
        .iter()
        .filter(|g| g.status == GoalStatus::Done)
        .count();

    let planned_count = ctx
        .state
        .goals
        .iter()
        .filter(|g| g.status == GoalStatus::Planned)
        .count();

    let archived_count = ctx
        .state
        .goals
        .iter()
        .filter(|g| g.status == GoalStatus::Archived)
        .count();

    Ok(DashboardData {
        current_phase: summary.current_phase.as_ref().map(PhaseDto::from),
        active_goals: summary.active_goals.iter().map(GoalDto::from).collect(),
        blocked_goals: summary.blocked_goals.iter().map(GoalDto::from).collect(),
        total_goals: summary.total_goals,
        completed_goals: completed_count,
        planned_goals: planned_count,
        archived_goals: archived_count,
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
        canon_docs: summary.canon_docs.iter().map(CanonDocDto::from).collect(),
        protocols: summary.protocols.iter().map(ProtocolDocDto::from).collect(),
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
        orphaned_goals: summary.orphaned_goals.iter().map(GoalDto::from).collect(),
        stale_goals: summary.stale_goals.iter().map(GoalDto::from).collect(),
        top_blocked: summary.top_blocked.iter().map(GoalDto::from).collect(),
        warnings: summary.warnings.iter().map(WarningDto::from).collect(),
    })
}

#[tauri::command]
pub async fn get_daily_context(
    date: String,
    state: State<'_, AppState>,
) -> Result<DailyContextDto, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    let parsed_date =
        NaiveDate::parse_from_str(&date, "%Y-%m-%d").map_err(|e| format!("Invalid date: {}", e))?;

    let context: DailyContext = ctx.daily_context(parsed_date);
    let scope = ctx.phase_scope(
        parsed_date,
        context.active_phase.as_ref().map(|p| p.phase_id.as_str()),
    );
    let phase_metrics = PhaseMetricsDto {
        phase_id: scope.metrics.phase_id.clone(),
        total_goals: scope.metrics.total_goals,
        active: scope.metrics.active,
        blocked: scope.metrics.blocked,
        done: scope.metrics.done,
        completion_pct: scope.metrics.completion_pct,
    };

    Ok(DailyContextDto {
        date,
        note: context.note.as_ref().map(DailyNoteDto::from),
        active_phase: context.active_phase.as_ref().map(PhaseDto::from),
        phase_defined: context.phase_defined,
        phase_metrics,
        phase_goals: scope.goals.iter().map(GoalDto::from).collect(),
        in_phase_goals: context.in_phase_goals.iter().map(GoalDto::from).collect(),
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
        linked_audits: context.linked_audits.iter().map(AuditDto::from).collect(),
        blocked_goals: context.blocked_goals.iter().map(GoalDto::from).collect(),
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
pub async fn update_goal_status(
    goal_id: String,
    new_status: String,
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

    // Parse status
    let status_enum = parse_goal_status(&new_status)?;

    // Use service to update (handles validation, transition check, and consequences)
    goal_service
        .update_status(&goal_id, status_enum)
        .await
        .map_err(|e| e.to_string())?;

    Ok(format!("Updated {} to {}", goal_id, new_status))
}

#[tauri::command]
pub async fn create_daily_note(date: String, state: State<'_, AppState>) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    let parsed_date =
        NaiveDate::parse_from_str(&date, "%Y-%m-%d").map_err(|e| format!("Invalid date: {}", e))?;

    let path = ctx
        .ensure_daily_note(parsed_date)
        .map_err(|e| e.to_string())?;
    Ok(path.to_string_lossy().to_string())
}

#[tauri::command]
pub async fn set_daily_mode(
    date: String,
    mode: Option<String>,
    state: State<'_, AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    let parsed_date =
        NaiveDate::parse_from_str(&date, "%Y-%m-%d").map_err(|e| format!("Invalid date: {}", e))?;

    let path = ctx
        .set_daily_mode(parsed_date, mode)
        .map_err(|e| e.to_string())?;
    Ok(path.to_string_lossy().to_string())
}

#[tauri::command]
pub async fn begin_day(
    day_type: String,
    phase_id: String,
    selected_goals: Vec<String>,
    state: State<'_, AppState>,
) -> Result<(), String> {
    // 1. Validation Logic
    if day_type.to_lowercase() == "heavy" {
        if selected_goals.len() != 2 {
            return Err("Constraint Violation: Heavy Days must have exactly 2 goals.".to_string());
        }
    }

    // 2. Access DB
    let store_option = {
        let db_guard = state.db.lock().unwrap();
        db_guard.as_ref().map(|s| s.clone())
    };

    if let Some(store) = store_option {
        // 3. Create/Upsert Daily Note (DB Only)
        let today = Local::now().naive_local().date();

        let note = metatheos_core::DailyNote {
            date: today,
            mode: Some(day_type),
            phase: Some(phase_id),
            goals: selected_goals,
            // Matched fields
            protocol: None,
            goals_worked: vec![],
            decisions_made: vec![],
            linked_goals: vec![],
            blockers: vec![],
            decisions: vec![],
            divergences: vec![],
            file_path: std::path::PathBuf::new(), // DB only
            content: String::new(),
            extra: std::collections::HashMap::new(),
        };

        store
            .upsert_daily_note(&note)
            .await
            .map_err(|e| e.to_string())?;
        Ok(())
    } else {
        Err("Database not initialized. Cannot begin day.".to_string())
    }
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
    pub raw_content: Option<String>,
    pub properties: std::collections::HashMap<String, String>,
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
            raw_content: None,
            properties: d
                .extra
                .iter()
                .map(|(k, v)| (k.clone(), v.to_string().trim_matches('"').to_string()))
                .collect(),
        }
    }
}

#[tauri::command]
pub async fn get_daily_note(
    date: String,
    state: State<'_, AppState>,
) -> Result<Option<DailyNoteDto>, String> {
    // MARKDOWN-FIRST: Read directly from filesystem (no DB layer)
    // TODO (Phase 4): When SurrealDB is re-enabled as read cache, check cache first before FS

    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;
    let parsed_date =
        NaiveDate::parse_from_str(&date, "%Y-%m-%d").map_err(|e| format!("Invalid date: {}", e))?;
    let daily = ctx.get_daily(parsed_date);
    Ok(daily.map(|d| DailyNoteDto::from(&d)))
}

#[tauri::command]
pub async fn update_daily_note(
    payload: DailyUpdateRequest,
    state: State<'_, AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

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

#[allow(dead_code)]
#[tauri::command]
pub async fn list_daily_notes(state: State<'_, AppState>) -> Result<Vec<DailySummaryDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

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
pub async fn get_enriched_audits(
    state: State<'_, AppState>,
) -> Result<Vec<EnrichedAuditDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    // Build goal references map (scan goals for audit mentions)
    let mut goal_refs: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for goal in &ctx.state.goals {
        // Simple heuristic: check content for audit file references
        for audit in &ctx.state.audits {
            let audit_name = audit
                .file_path
                .file_stem()
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
    let mut daily_refs: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for daily in &ctx.state.daily_notes {
        for audit in &ctx.state.audits {
            let audit_name = audit
                .file_path
                .file_stem()
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
    let mut prompt_refs: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for audit in &ctx.state.audits {
        for prompt in &ctx.state.prompts {
            let prompt_name = prompt
                .file_path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if audit.content.contains(prompt_name)
                || audit.content.contains(&prompt.title)
                || prompt
                    .prompt_id
                    .as_ref()
                    .map(|id| audit.content.contains(id))
                    .unwrap_or(false)
            {
                prompt_refs
                    .entry(audit.file_path.to_string_lossy().to_string())
                    .or_insert_with(Vec::new)
                    .push(
                        prompt
                            .prompt_id
                            .clone()
                            .unwrap_or_else(|| prompt.title.clone()),
                    );
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
pub async fn get_enriched_prompts(
    state: State<'_, AppState>,
) -> Result<Vec<EnrichedPromptDto>, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let ctx = GovernanceContext::load_async(&root)
        .await
        .map_err(|e| e.to_string())?;

    // Build goal references map
    let mut goal_refs: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for goal in &ctx.state.goals {
        for prompt in &ctx.state.prompts {
            let prompt_name = prompt
                .file_path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if goal.content.contains(prompt_name)
                || goal.content.contains(&prompt.title)
                || prompt
                    .prompt_id
                    .as_ref()
                    .map(|id| goal.content.contains(id))
                    .unwrap_or(false)
            {
                goal_refs
                    .entry(prompt.file_path.to_string_lossy().to_string())
                    .or_insert_with(Vec::new)
                    .push(goal.goal_id.clone());
            }
        }
    }

    // Build daily note references
    let mut daily_refs: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for daily in &ctx.state.daily_notes {
        for prompt in &ctx.state.prompts {
            let prompt_name = prompt
                .file_path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if daily.content.contains(prompt_name)
                || daily.content.contains(&prompt.title)
                || prompt
                    .prompt_id
                    .as_ref()
                    .map(|id| daily.content.contains(id))
                    .unwrap_or(false)
            {
                daily_refs
                    .entry(prompt.file_path.to_string_lossy().to_string())
                    .or_insert_with(Vec::new)
                    .push(daily.date.to_string());
            }
        }
    }

    // Build audit relations (prompts mentioned in audits)
    let mut audit_refs: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for prompt in &ctx.state.prompts {
        for audit in &ctx.state.audits {
            let prompt_name = prompt
                .file_path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("");
            if audit.content.contains(prompt_name)
                || audit.content.contains(&prompt.title)
                || prompt
                    .prompt_id
                    .as_ref()
                    .map(|id| audit.content.contains(id))
                    .unwrap_or(false)
            {
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

// ============================================================================
// Governance File Explorer (Phase 1)
// ============================================================================

#[derive(Debug, Serialize, Deserialize, Clone)]
pub enum GovernanceFileType {
    Canon,
    Goal,
    Phase,
    Decision,
    Audit,
    Prompt,
    Daily,
    Archive,
    Constitution,
    Markdown,
    Directory,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct GovernanceFileNode {
    pub name: String,
    pub path: String,
    pub file_type: GovernanceFileType,
    pub is_writable: bool,
    pub is_directory: bool,
    pub children: Vec<GovernanceFileNode>,
    pub frontmatter: Option<serde_json::Value>,
    pub size: Option<u64>,
    pub modified: Option<String>,
}

#[tauri::command]
pub fn get_governance_tree(state: State<AppState>) -> Result<GovernanceFileNode, String> {
    let root = state.governance_root.lock().unwrap();
    println!("INFO: get_governance_tree called on root: {:?}", *root);
    let result = build_governance_tree(&*root, None);

    if let Ok(ref node) = result {
        match serde_json::to_string(node) {
            Ok(json) => println!(
                "INFO: Serialization successful. Payload length: {}",
                json.len()
            ),
            Err(e) => println!("ERROR: Serialization failed: {}", e),
        }
    } else if let Err(ref e) = result {
        println!("ERROR: build_governance_tree failed: {}", e);
    }

    println!("INFO: get_governance_tree finished");
    result
}

fn build_governance_tree(
    root_path: &std::path::Path,
    relative_path: Option<&std::path::Path>,
) -> Result<GovernanceFileNode, String> {
    let current_path = if let Some(rel) = relative_path {
        root_path.join(rel)
    } else {
        root_path.to_path_buf()
    };

    let name = current_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("governance")
        .to_string();

    let path_str = current_path.to_string_lossy().to_string();

    let metadata = std::fs::metadata(&current_path).map_err(|e| e.to_string())?;
    let is_directory = metadata.is_dir();

    let modified = metadata.modified().ok().map(|m| {
        let dt: DateTime<Local> = m.into();
        dt.to_rfc3339()
    });

    let size = if is_directory {
        None
    } else {
        Some(metadata.len())
    };

    // Determine file type and writability
    let (file_type, is_writable) = determine_file_type(&current_path, root_path);

    let mut children = Vec::new();

    if is_directory {
        let mut entries: Vec<_> = std::fs::read_dir(&current_path)
            .map_err(|e| e.to_string())?
            .filter_map(|e| e.ok())
            .collect();

        entries.sort_by_key(|e| e.path());

        for entry in entries {
            let entry_name = entry.file_name();
            let entry_name_str = entry_name.to_string_lossy();

            // Skip hidden files and .obsidian
            if entry_name_str.starts_with('.') {
                continue;
            }

            // Skip backup files
            if entry_name_str.ends_with(".backup") {
                continue;
            }

            let child_rel_path = if let Some(rel) = relative_path {
                rel.join(&entry_name)
            } else {
                std::path::PathBuf::from(&entry_name)
            };

            match build_governance_tree(root_path, Some(&child_rel_path)) {
                Ok(child) => children.push(child),
                Err(_) => {} // Skip unreadable files
            }
        }
    }

    // Extract frontmatter for markdown files
    let frontmatter = if !is_directory && path_str.ends_with(".md") {
        extract_frontmatter(&current_path).ok()
    } else {
        None
    };

    Ok(GovernanceFileNode {
        name,
        path: path_str,
        file_type,
        is_writable,
        is_directory,
        children,
        frontmatter,
        size,
        modified,
    })
}

fn determine_file_type(
    path: &std::path::Path,
    _root: &std::path::Path,
) -> (GovernanceFileType, bool) {
    let path_str = path.to_string_lossy();
    let name = path.file_name().and_then(|n| n.to_str()).unwrap_or("");

    // Check if in canon folder (read-only)
    if path_str.contains("canon") {
        return (GovernanceFileType::Constitution, false);
    }

    // Check if in 00_MASTER (Canon - read-only)
    if path_str.contains("00_MASTER") {
        return (GovernanceFileType::Canon, false);
    }

    // Check if in 90_ARCHIVE (read-only)
    if path_str.contains("90_ARCHIVE") {
        return (GovernanceFileType::Archive, false);
    }

    // Check specific governance types (writable)
    if path_str.contains("01_DAILY") {
        return (GovernanceFileType::Daily, true);
    }

    if path_str.contains("02_PHASES") {
        return (GovernanceFileType::Phase, true);
    }

    if path_str.contains("03_GOALS_EPICS") {
        return (GovernanceFileType::Goal, true);
    }

    if path_str.contains("04_DECISIONS") {
        return (GovernanceFileType::Decision, true);
    }

    if path_str.contains("05_AUDITS") {
        return (GovernanceFileType::Audit, true);
    }

    if path_str.contains("06_PROMPTS") {
        return (GovernanceFileType::Prompt, true);
    }

    // Directories
    if path.is_dir() {
        return (GovernanceFileType::Directory, false);
    }

    // Default markdown files
    if name.ends_with(".md") {
        return (GovernanceFileType::Markdown, true);
    }

    (GovernanceFileType::Directory, false)
}

fn extract_frontmatter(path: &std::path::Path) -> Result<serde_json::Value, String> {
    let content = std::fs::read_to_string(path).map_err(|e| e.to_string())?;

    // Simple frontmatter extraction
    if let Some(stripped) = content.strip_prefix("---\n") {
        if let Some(end_idx) = stripped.find("\n---\n") {
            let yaml_str = &stripped[..end_idx];
            let yaml_value: serde_yaml::Value =
                serde_yaml::from_str(yaml_str).map_err(|e| e.to_string())?;
            let json_value: serde_json::Value =
                serde_json::to_value(yaml_value).map_err(|e| e.to_string())?;
            return Ok(json_value);
        }
    }

    Ok(serde_json::Value::Null)
}

#[tauri::command]
pub fn get_file_content(file_path: String) -> Result<String, String> {
    std::fs::read_to_string(&file_path).map_err(|e| format!("Failed to read file: {}", e))
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FileBacklinks {
    pub path: String,
    pub backlinks: Vec<String>,
    pub forward_links: Vec<String>,
}

#[tauri::command]
pub fn get_file_backlinks(
    file_path: String,
    state: State<AppState>,
) -> Result<FileBacklinks, String> {
    let root = state.governance_root.lock().unwrap();
    let target_path = std::path::Path::new(&file_path);

    let target_name = target_path
        .file_stem()
        .and_then(|s| s.to_str())
        .ok_or("Invalid file path")?;

    // Read the target file to extract forward links
    let content = std::fs::read_to_string(target_path)
        .map_err(|e| format!("Failed to read target file: {}", e))?;

    let forward_links = extract_links(&content);

    // Search all governance files for backlinks
    let mut backlinks = Vec::new();

    for entry in walkdir::WalkDir::new(&*root)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        let path = entry.path();
        if path.extension().and_then(|s| s.to_str()) != Some("md") {
            continue;
        }

        if path == target_path {
            continue;
        }

        if let Ok(file_content) = std::fs::read_to_string(path) {
            if file_content.contains(target_name) {
                backlinks.push(path.to_string_lossy().to_string());
            }
        }
    }

    Ok(FileBacklinks {
        path: file_path,
        backlinks,
        forward_links,
    })
}

fn extract_links(content: &str) -> Vec<String> {
    let mut links = Vec::new();
    let link_pattern = regex::Regex::new(r"\[\[([^\]]+)\]\]").unwrap();

    for cap in link_pattern.captures_iter(content) {
        if let Some(link) = cap.get(1) {
            links.push(link.as_str().to_string());
        }
    }

    links
}

/// Safe file write with atomic operation and timestamped backup
/// Phase 2 — Controlled Editing Layer
#[tauri::command]
pub fn safe_write_file(
    file_path: String,
    new_content: String,
    state: State<AppState>,
) -> Result<String, String> {
    use std::fs;
    use std::io::Write;

    let root = state.governance_root.lock().unwrap();
    let target_path = std::path::Path::new(&file_path);

    // Verify file is within governance root
    if !target_path.starts_with(&*root) {
        return Err("File is outside governance root".to_string());
    }

    // Verify file is writable (not in read-only folders)
    let path_str = target_path.to_string_lossy();
    if path_str.contains("canon")
        || path_str.contains("00_MASTER")
        || path_str.contains("90_ARCHIVE")
    {
        return Err(
            "Cannot modify read-only governance files (Canon, Constitution, Archive)".to_string(),
        );
    }

    // Create parent directories if needed
    if let Some(parent) = target_path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("Failed to create directories: {}", e))?;
    }

    let mut backup_info = String::from("(no backup created)");

    // Create timestamped backup only if file exists
    if target_path.exists() {
        let timestamp = chrono::Local::now().format("%Y%m%d_%H%M%S");
        let backup_name = format!(
            "{}.backup.{}",
            target_path.file_name().unwrap().to_string_lossy(),
            timestamp
        );
        let backup = target_path.with_file_name(backup_name);

        fs::copy(target_path, &backup).map_err(|e| format!("Failed to create backup: {}", e))?;

        backup_info = backup.to_string_lossy().to_string();
    }

    // Write to temporary file first (atomic write pattern)
    let temp_name = format!("{}.tmp", target_path.file_name().unwrap().to_string_lossy());
    let temp_path = target_path.with_file_name(temp_name);

    {
        let mut temp_file = fs::File::create(&temp_path)
            .map_err(|e| format!("Failed to create temp file: {}", e))?;
        temp_file
            .write_all(new_content.as_bytes())
            .map_err(|e| format!("Failed to write temp file: {}", e))?;
        temp_file
            .sync_all()
            .map_err(|e| format!("Failed to sync temp file: {}", e))?;
    }

    // Atomic rename (overwrites target)
    fs::rename(&temp_path, target_path)
        .map_err(|e| format!("Failed to atomically replace file: {}", e))?;

    Ok(format!(
        "File written successfully. Backup created at {}",
        backup_info
    ))
}

/// Get Aequitas Dashboard - Overview of project completion and health (DB-powered)
/// Phase 1 Day 5-6 - "Finish Aequitas" mission tracker
/// Uses SurrealDB for fast, cached queries
#[tauri::command]
pub async fn get_aequitas_dashboard(
    state: State<'_, AppState>,
) -> Result<AequitasDashboard, String> {
    let root = state.governance_root.lock().unwrap().clone();
    let governance_root_str = root.to_string_lossy().to_string();

    // Clone the Arc<SurrealStore> before dropping the guard
    let store_option = {
        let db_guard = state.db.lock().unwrap();
        db_guard.as_ref().map(|s| s.clone())
    };

    // Check if DB is initialized
    if let Some(store) = store_option {
        // Use SurrealDB for fast queries
        let mut dashboard = dashboard_from_db(&store, &governance_root_str).await?;

        // Phase 1: Enforce Active Phase Resolution Authority
        // Even if goals are empty, show the resolved active phase.
        if let Ok(Some(active_phase)) =
            resolve_active_phase_db(&store, Some(Local::now().naive_local().date())).await
        {
            dashboard.current_phase.phase_title = Some(active_phase.title);
            dashboard.current_phase.phase_status = Some(active_phase.status);
            // Attempt to parse number, or leave if not numeric (UI resilience check needed)
            if let Ok(num) = active_phase.phase_id.replace("phase-", "").parse::<u8>() {
                dashboard.current_phase.phase_number = Some(num);
            } else if let Ok(num) = active_phase.phase_id.parse::<u8>() {
                dashboard.current_phase.phase_number = Some(num);
            }
            // If ID is "P1", "P2" (legacy style compat)
            if active_phase.phase_id.to_uppercase().starts_with("P") {
                if let Ok(num) = active_phase.phase_id[1..].parse::<u8>() {
                    dashboard.current_phase.phase_number = Some(num);
                }
            }
            dashboard.phase_defined = true;
        }

        Ok(dashboard)
    } else {
        // Fallback to markdown parsing if DB not ready yet
        let ctx = GovernanceContext::load_async(&root)
            .await
            .map_err(|e| format!("Failed to load governance context: {}", e))?;

        let calculator = DashboardCalculator::new(&ctx);
        Ok(calculator.calculate())
    }
}

/// Build dashboard from SurrealDB queries (fast path)
async fn dashboard_from_db(
    store: &metatheos_core::store::SurrealStore,
    governance_root: &str,
) -> Result<AequitasDashboard, String> {
    let ctx = GovernanceContext::from_store(store, std::path::PathBuf::from(governance_root))
        .await
        .map_err(|e| format!("Failed to load governance context: {}", e))?;
    let calculator = DashboardCalculator::new(&ctx);
    Ok(calculator.calculate())
}

#[tauri::command]
pub async fn get_ai_context(
    state: State<'_, AppState>,
    date: Option<String>,
) -> Result<ReadOnlyGovernanceContext, String> {
    let root = state
        .governance_root
        .lock()
        .map_err(|e| e.to_string())?
        .clone();
    let maybe_store = state.db.lock().map_err(|e| e.to_string())?.clone();

    let ctx = if let Some(store) = maybe_store {
        GovernanceContext::from_store(&store, root)
            .await
            .map_err(|e| e.to_string())?
    } else {
        GovernanceContext::load_async(&root)
            .await
            .map_err(|e| e.to_string())?
    };

    let target_date = if let Some(d) = date {
        NaiveDate::parse_from_str(&d, "%Y-%m-%d").map_err(|e| e.to_string())?
    } else {
        Local::now().naive_local().date()
    };

    Ok(ctx.get_read_only_context(target_date))
}

// === WorkItem Commands (canonical, SCHEMAFULL) ===
/// LEGACY — DO NOT USE DIRECTLY
/// Calls below exist only for backward compatibility and route to canonical handlers.

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkItemDto {
    pub id: String,
    pub goal_id: String,
    pub parent_id: Option<String>,
    pub level: String,
    pub status: String,
    pub title: String,
    pub description: Option<String>,
    pub order_index: i32,
    pub created_at: Option<String>,
    pub completed_at: Option<String>,
    // Legacy compatibility
    pub kind: Option<String>,
}

impl From<WorkItem> for WorkItemDto {
    fn from(item: WorkItem) -> Self {
        Self {
            id: item.id,
            goal_id: item.goal_id,
            parent_id: item.parent_id,
            level: match item.level {
                WorkItemLevel::Goal => "goal",
                WorkItemLevel::Subgoal => "subgoal",
                WorkItemLevel::Task => "task",
            }
            .to_string(),
            status: match item.status {
                WorkItemStatus::Open => "open",
                WorkItemStatus::Active => "active",
                WorkItemStatus::Blocked => "blocked",
                WorkItemStatus::Done => "done",
            }
            .to_string(),
            title: item.title,
            description: if item.description.is_empty() {
                None
            } else {
                Some(item.description)
            },
            order_index: item.order_index,
            created_at: item.created_at.map(|d| d.to_rfc3339()),
            completed_at: item.completed_at.map(|d| d.to_rfc3339()),
            kind: Some(
                match item.level {
                    WorkItemLevel::Goal => "Goal",
                    WorkItemLevel::Subgoal => "Subgoal",
                    WorkItemLevel::Task => "Task",
                }
                .to_string(),
            ),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkItemNodeDto {
    pub item: WorkItemDto,
    pub children: Vec<WorkItemNodeDto>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GoalDetailDto {
    pub goal: WorkItemDto,
    pub phase: Option<PhaseDto>,
    pub tree: Vec<WorkItemNodeDto>,
}

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct MigrationReport {
    pub goals_scanned: usize,
    pub root_items_created: usize,
    pub legacy_items_migrated: usize,
    pub items_skipped: usize,
    pub warnings: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DiagnosticsReport {
    pub governance_root: String,
    pub db_path: String,
    pub db_open_ok: bool,
    pub tables_present: Vec<String>,
    pub counts: std::collections::HashMap<String, usize>,
    pub active_phase: Option<String>,
    pub today_day_exists: bool,
    pub last_error: Option<String>,
}

#[tauri::command]
pub async fn diagnose_store_state(state: State<'_, AppState>) -> Result<DiagnosticsReport, String> {
    let governance_root = state.governance_root.lock().unwrap().clone();
    let db_path = governance_root.join(".metatheos.db");
    let mut report = DiagnosticsReport {
        governance_root: governance_root.to_string_lossy().to_string(),
        db_path: db_path.to_string_lossy().to_string(),
        db_open_ok: false,
        tables_present: Vec::new(),
        counts: std::collections::HashMap::new(),
        active_phase: None,
        today_day_exists: false,
        last_error: None,
    };

    let store = match metatheos_core::store::SurrealStore::init(db_path.clone()).await {
        Ok(s) => {
            report.db_open_ok = true;
            s
        }
        Err(e) => {
            report.last_error = Some(e.to_string());
            return Ok(report);
        }
    };

    // Tables: canonical names
    let tables = vec!["phase", "goal", "work_item", "day", "day_goal"];
    report.tables_present = tables.iter().map(|s| s.to_string()).collect();
    for t in tables {
        let query = format!("SELECT count() as count FROM {}", t);
        let mut resp = store.db.query(query).await.map_err(|e| e.to_string())?;
        #[derive(serde::Deserialize)]
        struct CountRow {
            count: i64,
        }
        let c = resp
            .take::<Vec<CountRow>>(0)
            .ok()
            .and_then(|rows| rows.first().map(|r| r.count as usize))
            .unwrap_or(0);
        report.counts.insert(t.to_string(), c);
    }

    // active phase from meta
    if let Ok(Some(ap)) = store.get_meta("active_phase").await {
        report.active_phase = Some(ap);
    }

    // today day exists?
    let today = Local::now()
        .naive_local()
        .date()
        .format("%Y-%m-%d")
        .to_string();
    if let Ok(mut resp) = store
        .db
        .query("SELECT * FROM day WHERE id = $id")
        .bind(("id", today))
        .await
    {
        let rows: Result<Vec<serde_json::Value>, _> = resp.take(0);
        report.today_day_exists = rows.ok().map(|v| !v.is_empty()).unwrap_or(false);
    }

    Ok(report)
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateWorkItemRequest {
    pub parent_id: Option<String>,
    pub goal_id: Option<String>,
    pub level: String,
    pub title: String,
    pub description: Option<String>,
    pub order_index: Option<i32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateWorkItemRequest {
    pub id: String,
    pub title: Option<String>,
    pub description: Option<String>,
    pub order_index: Option<i32>,
}

fn parse_level(s: &str) -> Result<WorkItemLevel, String> {
    WorkItemLevel::from_str(s).ok_or_else(|| "Invalid work item level".to_string())
}

fn parse_status(s: &str) -> Result<WorkItemStatus, String> {
    WorkItemStatus::from_str(s).ok_or_else(|| "Invalid work item status".to_string())
}

#[allow(dead_code)]
fn map_goal_status_to_work_item_status(status: &GoalStatus) -> WorkItemStatus {
    match status {
        GoalStatus::Planned => WorkItemStatus::Open,
        GoalStatus::Active => WorkItemStatus::Active,
        GoalStatus::Blocked => WorkItemStatus::Blocked,
        GoalStatus::Partial => WorkItemStatus::Active,
        GoalStatus::Done | GoalStatus::Archived => WorkItemStatus::Done,
        GoalStatus::Unknown(_) => WorkItemStatus::Open,
    }
}

fn validate_parent_child(
    parent_level: Option<&WorkItemLevel>,
    level: &WorkItemLevel,
) -> Result<(), String> {
    match (parent_level, level) {
        (None, WorkItemLevel::Goal) => Ok(()),
        (None, _) => Err("Root work items must be level 'goal'".to_string()),
        (Some(WorkItemLevel::Goal), WorkItemLevel::Subgoal) => Ok(()),
        (Some(WorkItemLevel::Goal), WorkItemLevel::Task) => Ok(()),
        (Some(WorkItemLevel::Subgoal), WorkItemLevel::Task) => Ok(()),
        (Some(WorkItemLevel::Subgoal), WorkItemLevel::Subgoal) => {
            Err("Subgoals cannot contain subgoals".to_string())
        }
        (Some(WorkItemLevel::Task), _) => Err("Tasks cannot have children".to_string()),
        (Some(_), WorkItemLevel::Goal) => Err("Goal cannot be child item".to_string()),
    }
}

fn build_work_item_tree(items: Vec<WorkItem>) -> Vec<WorkItemNodeDto> {
    let mut by_parent: std::collections::HashMap<Option<String>, Vec<WorkItem>> =
        std::collections::HashMap::new();
    for item in items {
        by_parent
            .entry(item.parent_id.clone())
            .or_default()
            .push(item);
    }

    fn build(
        parent: Option<String>,
        map: &mut std::collections::HashMap<Option<String>, Vec<WorkItem>>,
    ) -> Vec<WorkItemNodeDto> {
        let mut children = map.remove(&parent).unwrap_or_default();
        children.sort_by(|a, b| {
            a.order_index
                .cmp(&b.order_index)
                .then_with(|| a.created_at.cmp(&b.created_at))
        });
        children
            .into_iter()
            .map(|child| WorkItemNodeDto {
                item: child.clone().into(),
                children: build(Some(child.id.clone()), map),
            })
            .collect()
    }

    build(None, &mut by_parent)
}

#[tauri::command]
pub async fn get_goal_detail(
    state: State<'_, AppState>,
    goal_id: String,
) -> Result<GoalDetailDto, String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    // Fetch all work items for this goal
    let items = store
        .get_work_items_by_goal(&goal_id)
        .await
        .map_err(|e| e.to_string())?;

    let mut root: Option<WorkItem> = items
        .iter()
        .find(|i| i.level == WorkItemLevel::Goal && i.parent_id.is_none() && i.id == goal_id)
        .cloned()
        .or_else(|| {
            items
                .iter()
                .find(|i| i.level == WorkItemLevel::Goal)
                .cloned()
        });

    if root.is_none() {
        if let Ok(mut resp) = store
            .db
            .query("SELECT * FROM goals WHERE goal_id = $id LIMIT 1")
            .bind(("id", goal_id.clone()))
            .await
        {
            #[derive(serde::Deserialize)]
            struct LegacyGoal {
                goal_id: String,
                title: String,
                status: Option<serde_json::Value>,
                content: Option<String>,
            }
            if let Ok(mut legacy) = resp.take::<Vec<LegacyGoal>>(0) {
                if let Some(g) = legacy.pop() {
                    let status = g
                        .status
                        .as_ref()
                        .and_then(|v| v.as_str())
                        .and_then(WorkItemStatus::from_str)
                        .unwrap_or(WorkItemStatus::Open);
                    root = Some(WorkItem {
                        id: g.goal_id.clone(),
                        goal_id: g.goal_id.clone(),
                        parent_id: None,
                        level: WorkItemLevel::Goal,
                        title: g.title,
                        description: g.content.unwrap_or_default(),
                        status,
                        order_index: 0,
                        created_at: None,
                        completed_at: None,
                    });
                }
            }
        }
    }

    let root = root.ok_or_else(|| "Root goal work item not found".to_string())?;

    let mut items = items;
    if !items.iter().any(|i| i.id == root.id) {
        items.push(root.clone());
    }

    // Best-effort phase lookup from legacy goals table
    let mut phase_dto = None;
    if let Ok(mut resp) = store
        .db
        .query("SELECT * FROM goals WHERE goal_id = $id LIMIT 1")
        .bind(("id", goal_id.clone()))
        .await
    {
        #[derive(serde::Deserialize)]
        #[allow(dead_code)]
        struct LegacyGoalPhase {
            phase: Option<String>,
            title: String,
            status: Option<serde_json::Value>,
        }
        if let Ok(mut legacy_goals) = resp.take::<Vec<LegacyGoalPhase>>(0) {
            if let Some(legacy) = legacy_goals.pop() {
                if let Some(phase_id) = legacy.phase {
                    if let Ok(mut phase_resp) = store
                        .db
                        .query("SELECT * FROM phases WHERE phase_id = $pid LIMIT 1")
                        .bind(("pid", phase_id.clone()))
                        .await
                    {
                        #[derive(serde::Deserialize)]
                        struct LegacyPhaseDto {
                            phase_id: String,
                            title: String,
                            status: String,
                        }
                        if let Ok(mut phases) = phase_resp.take::<Vec<LegacyPhaseDto>>(0) {
                            if let Some(p) = phases.pop() {
                                phase_dto = Some(PhaseDto {
                                    phase_id: p.phase_id,
                                    title: p.title,
                                    status: Some(p.status),
                                    updated: None,
                                });
                            }
                        }
                    }
                }
            }
        }
    }

    Ok(GoalDetailDto {
        goal: root.clone().into(),
        phase: phase_dto,
        tree: build_work_item_tree(items),
    })
}

#[tauri::command]
pub async fn create_work_item(
    state: State<'_, AppState>,
    req: CreateWorkItemRequest,
) -> Result<WorkItemDto, String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    let level = parse_level(&req.level)?;
    let mut goal_id = req.goal_id.clone();

    if let Some(pid) = req.parent_id.as_ref() {
        let parent: Option<WorkItem> = store
            .db
            .select(("work_item", pid.as_str()))
            .await
            .map_err(|e| e.to_string())?;
        let parent = parent.ok_or_else(|| "Parent work item not found".to_string())?;
        if goal_id.is_none() {
            goal_id = Some(parent.goal_id.clone());
        }
        validate_parent_child(Some(&parent.level), &level)?;
    } else {
        validate_parent_child(None, &level)?;
    }

    let goal_id = goal_id.ok_or_else(|| "goal_id is required".to_string())?;

    let item = WorkItem {
        id: Uuid::new_v4().to_string(),
        goal_id,
        parent_id: req.parent_id.clone(),
        level,
        title: req.title.clone(),
        description: req.description.unwrap_or_default(),
        status: WorkItemStatus::Open,
        order_index: req.order_index.unwrap_or(0),
        created_at: Some(chrono::Utc::now()),
        completed_at: None,
    };

    store
        .add_work_item(&item)
        .await
        .map_err(|e| e.to_string())?;

    // Mirror status to legacy goal when creating root goal item for compatibility
    if item.level == WorkItemLevel::Goal && item.parent_id.is_none() {
        if let Ok(mut resp) = store
            .db
            .query("SELECT status FROM goals WHERE goal_id = $id LIMIT 1")
            .bind(("id", item.goal_id.clone()))
            .await
        {
            let _ignored: Result<Vec<serde_json::Value>, _> = resp.take(0);
            let _: std::result::Result<Option<serde_json::Value>, _> = store
                .db
                .update(("goals", item.goal_id.as_str()))
                .content(serde_json::json!({ "goal_id": item.goal_id, "status": "active" }))
                .await;
        }
    }

    Ok(item.into())
}

#[tauri::command]
pub async fn update_work_item(
    state: State<'_, AppState>,
    req: UpdateWorkItemRequest,
) -> Result<WorkItemDto, String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    let mut item: WorkItem = store
        .db
        .select(("work_item", req.id.as_str()))
        .await
        .map_err(|e| e.to_string())?
        .ok_or_else(|| "Work item not found".to_string())?;

    if let Some(title) = req.title {
        item.title = title;
    }
    if let Some(desc) = req.description {
        item.description = desc;
    }
    if let Some(order) = req.order_index {
        item.order_index = order;
    }

    store
        .update_work_item(&item)
        .await
        .map_err(|e| e.to_string())?;

    Ok(item.into())
}

#[tauri::command]
pub async fn set_work_item_status(
    state: State<'_, AppState>,
    id: String,
    status: String,
) -> Result<WorkItemDto, String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    let mut item: WorkItem = store
        .db
        .select(("work_item", id.as_str()))
        .await
        .map_err(|e| e.to_string())?
        .ok_or_else(|| "Work item not found".to_string())?;

    let new_status = parse_status(&status)?;
    item.status = new_status.clone();
    if matches!(new_status, WorkItemStatus::Done) {
        item.completed_at = Some(chrono::Utc::now());
    }

    store
        .update_work_item(&item)
        .await
        .map_err(|e| e.to_string())?;

    if matches!(new_status, WorkItemStatus::Done) {
        let engine = ConsequenceEngine {
            store: store.clone(),
        };
        let _ = engine.on_work_item_completed(&item.id).await;
    }

    Ok(item.into())
}

// Legacy compatibility wrappers (prevent writing legacy shapes)
#[tauri::command]
pub async fn add_work_item(
    state: State<'_, AppState>,
    goal_id: String,
    _phase_id: String,
    parent_id: Option<String>,
    kind: String,
    title: String,
) -> Result<WorkItemDto, String> {
    let level = match kind.as_str() {
        "Subgoal" => "subgoal",
        "Task" => "task",
        _ => return Err("Invalid kind".to_string()),
    };
    create_work_item(
        state,
        CreateWorkItemRequest {
            parent_id,
            goal_id: Some(goal_id),
            level: level.to_string(),
            title,
            description: None,
            order_index: None,
        },
    )
    .await
}

#[tauri::command]
pub async fn get_work_items(
    state: State<'_, AppState>,
    goal_id: String,
) -> Result<Vec<WorkItemDto>, String> {
    let detail = get_goal_detail(state, goal_id).await?;
    fn flatten(nodes: &[WorkItemNodeDto], out: &mut Vec<WorkItemDto>) {
        for n in nodes {
            out.push(n.item.clone());
            flatten(&n.children, out);
        }
    }
    let mut items = Vec::new();
    flatten(&detail.tree, &mut items);
    Ok(items)
}

#[tauri::command]
pub async fn toggle_work_item(
    state: State<'_, AppState>,
    item_id: String,
) -> Result<WorkItemDto, String> {
    let detail = set_work_item_status(state.clone(), item_id.clone(), "done".to_string()).await;
    if let Ok(item) = detail {
        if item.status == "done" {
            return Ok(item);
        }
    }
    set_work_item_status(state, item_id, "open".to_string()).await
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct LegacyWorkItem {
    id: String,
    goal_id: String,
    parent_id: Option<String>,
    kind: Option<String>,
    status: Option<String>,
    title: String,
    description: Option<String>,
    created_at: Option<String>,
}

fn legacy_status_to_canonical(s: &str) -> WorkItemStatus {
    match s.to_lowercase().as_str() {
        "done" => WorkItemStatus::Done,
        _ => WorkItemStatus::Open,
    }
}

fn legacy_kind_to_level(k: &str) -> Option<WorkItemLevel> {
    match k.to_lowercase().as_str() {
        "goal" => Some(WorkItemLevel::Goal),
        "subgoal" => Some(WorkItemLevel::Subgoal),
        "task" => Some(WorkItemLevel::Task),
        "sub_goal" => Some(WorkItemLevel::Subgoal),
        _ => None,
    }
}

#[tauri::command]
pub async fn migrate_legacy_work_items(
    state: State<'_, AppState>,
    dry_run: bool,
) -> Result<MigrationReport, String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    let mut report = MigrationReport::default();

    let goals = store.get_all_goals().await.map_err(|e| e.to_string())?;
    report.goals_scanned = goals.len();

    for goal in goals {
        // 1) Ensure root work_item exists
        let mut root_exists = false;
        let mut existing_items = store
            .get_work_items_by_goal(&goal.goal_id)
            .await
            .map_err(|e| e.to_string())?;
        if existing_items
            .iter()
            .any(|i| i.level == WorkItemLevel::Goal && i.parent_id.is_none())
        {
            root_exists = true;
        }

        if !root_exists {
            report.root_items_created += 1;
            if !dry_run {
                let root_item = WorkItem {
                    id: goal.goal_id.clone(),
                    goal_id: goal.goal_id.clone(),
                    parent_id: None,
                    level: WorkItemLevel::Goal,
                    title: goal.title.clone(),
                    description: goal.content.clone(),
                    status: match goal.status {
                        GoalStatus::Planned => WorkItemStatus::Open,
                        GoalStatus::Active => WorkItemStatus::Active,
                        GoalStatus::Blocked => WorkItemStatus::Blocked,
                        GoalStatus::Partial => WorkItemStatus::Active,
                        GoalStatus::Done | GoalStatus::Archived => WorkItemStatus::Done,
                        GoalStatus::Unknown(_) => WorkItemStatus::Open,
                    },
                    order_index: 0,
                    created_at: Some(Utc::now()),
                    completed_at: None,
                };
                if let Err(e) = store.add_work_item(&root_item).await {
                    report.warnings.push(format!(
                        "[MIGRATION] Failed to create root for {}: {}",
                        goal.goal_id, e
                    ));
                }
                existing_items.push(root_item);
            }
        }

        // 2) Legacy work_items migration (if legacy table exists)
        if let Ok(mut legacy_resp) = store
            .db
            .query("SELECT * FROM work_items WHERE goal_id = $gid")
            .bind(("gid", goal.goal_id.clone()))
            .await
        {
            if let Ok(legacy_items) = legacy_resp.take::<Vec<LegacyWorkItem>>(0) {
                for legacy in legacy_items {
                    let level = if let Some(kind) = &legacy.kind {
                        legacy_kind_to_level(kind).unwrap_or(WorkItemLevel::Task)
                    } else {
                        WorkItemLevel::Task
                    };

                    // Determine parent mapping
                    let parent_id = if let Some(pid) = legacy.parent_id.clone() {
                        Some(pid)
                    } else {
                        Some(goal.goal_id.clone()) // attach to root
                    };

                    // Duplicate check
                    let exists = existing_items.iter().any(|i| {
                        i.goal_id == goal.goal_id
                            && i.title.eq_ignore_ascii_case(&legacy.title)
                            && i.level == level
                            && i.parent_id == parent_id
                    });
                    if exists {
                        report.items_skipped += 1;
                        continue;
                    }

                    report.legacy_items_migrated += 1;
                    if dry_run {
                        continue;
                    }

                    let status = legacy
                        .status
                        .as_ref()
                        .map(|s| legacy_status_to_canonical(s))
                        .unwrap_or(WorkItemStatus::Open);
                    let created_at = legacy
                        .created_at
                        .as_ref()
                        .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
                        .map(|d| d.with_timezone(&Utc))
                        .or_else(|| Some(Utc::now()));

                    let item = WorkItem {
                        id: legacy.id.clone(),
                        goal_id: goal.goal_id.clone(),
                        parent_id,
                        level,
                        title: legacy.title.clone(),
                        description: legacy.description.clone().unwrap_or_default(),
                        status,
                        order_index: 0,
                        created_at,
                        completed_at: None,
                    };

                    if let Err(e) = store.add_work_item(&item).await {
                        report.warnings.push(format!(
                            "[MIGRATION] Failed to migrate legacy item {}: {}",
                            legacy.id, e
                        ));
                    } else {
                        existing_items.push(item);
                    }
                }
            }
        }

        // 3) Order normalization and completion timestamps (only when executing)
        if !dry_run {
            // Refresh canonical items
            let mut canon = store
                .get_work_items_by_goal(&goal.goal_id)
                .await
                .map_err(|e| e.to_string())?;

            // Completion timestamp fix
            for item in canon.iter_mut() {
                if item.status == WorkItemStatus::Done && item.completed_at.is_none() {
                    item.completed_at = Some(Utc::now());
                    let _ = store.update_work_item(item).await;
                }
            }

            // Order normalization
            use std::collections::HashMap;
            let mut groups: HashMap<Option<String>, Vec<WorkItem>> = HashMap::new();
            for item in canon.into_iter() {
                groups.entry(item.parent_id.clone()).or_default().push(item);
            }
            for (_parent, mut siblings) in groups {
                siblings.sort_by(|a, b| a.created_at.cmp(&b.created_at));
                for (idx, mut s) in siblings.into_iter().enumerate() {
                    if s.order_index != idx as i32 {
                        s.order_index = idx as i32;
                        let _ = store.update_work_item(&s).await;
                    }
                }
            }
        }
    }

    // Post validation: ensure each goal has one root
    if !dry_run {
        for goal in store.get_all_goals().await.map_err(|e| e.to_string())? {
            if let Ok(items) = store.get_work_items_by_goal(&goal.goal_id).await {
                let roots = items
                    .iter()
                    .filter(|i| i.level == WorkItemLevel::Goal && i.parent_id.is_none())
                    .count();
                if roots != 1 {
                    report.warnings.push(format!(
                        "[MIGRATION] Goal {} has {} root items",
                        goal.goal_id, roots
                    ));
                }
            }
        }
    }

    Ok(report)
}

/// Manual seeding helper to create a default active phase when DB is empty
#[tauri::command]
pub async fn seed_default_phase_db(state: State<'_, AppState>) -> Result<(), String> {
    let store = state
        .db
        .lock()
        .map_err(|e| e.to_string())?
        .as_ref()
        .cloned()
        .ok_or("Store not initialized")?;

    let phase_id = "P0".to_string();
    // Upsert canonical phase
    let payload = serde_json::json!({
        "id": phase_id,
        "phase_id": phase_id,
        "title": "Bootstrap",
        "status": "active",
        "description": "Default bootstrap phase",
        "order_index": 0
    });
    let _ = store
        .db
        .create::<Option<serde_json::Value>>(("phase", "P0"))
        .content(payload.clone())
        .await;
    let _ = store
        .db
        .update::<Option<serde_json::Value>>(("phase", "P0"))
        .content(payload)
        .await;

    // Set active phase meta
    let _ = store.set_meta("active_phase", "P0").await;
    Ok(())
}

// === Annotation Commands ===

fn parse_scope(scope_type: &str) -> Option<AnnotationScope> {
    match scope_type.to_lowercase().as_str() {
        "phase" => Some(AnnotationScope::Phase),
        "goal" => Some(AnnotationScope::Goal),
        "work_item" | "workitem" | "task" | "subgoal" => Some(AnnotationScope::WorkItem),
        "day" => Some(AnnotationScope::Day),
        "event" => Some(AnnotationScope::Event),
        "ai_run" | "ai" => Some(AnnotationScope::AiRun),
        _ => None,
    }
}

#[tauri::command]
pub async fn add_annotation(
    state: State<'_, AppState>,
    scope_type: String, // phase | goal | work_item | day | event | ai_run
    scope_id: String,
    body: String,
    author: Option<String>,
) -> Result<Annotation, String> {
    let scope = parse_scope(&scope_type).ok_or_else(|| "Invalid scope_type".to_string())?;

    let item = Annotation {
        id: format!("ANN-{}", Uuid::new_v4()),
        entity_type: scope.clone(),
        entity_id: scope_id.clone(),
        content: body,
        author_type: match author
            .unwrap_or_else(|| "user".to_string())
            .to_lowercase()
            .as_str()
        {
            "ai" => AnnotationAuthor::Ai,
            _ => AnnotationAuthor::User,
        },
        author_ref: None,
        created_at: chrono::Utc::now(),
    };

    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;

    store
        .add_annotation(&item)
        .await
        .map_err(|e| e.to_string())?;

    // Log event (best-effort)
    let event = Event::new(
        "annotation",
        &item.id,
        EventAction::Create,
        item.author_type.as_str(),
        serde_json::json!({
            "scope_type": scope.as_str(),
            "scope_id": scope_id,
        }),
    );
    let _ = store.log_event(&event).await;

    Ok(item)
}

#[tauri::command]
pub async fn get_annotations(
    state: State<'_, AppState>,
    scope_type: String,
    scope_id: String,
) -> Result<Vec<Annotation>, String> {
    let scope = parse_scope(&scope_type).ok_or_else(|| "Invalid scope_type".to_string())?;

    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;
    store
        .get_annotations(scope.as_str(), &scope_id)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn delete_annotation(state: State<'_, AppState>, id: String) -> Result<(), String> {
    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;
    store
        .delete_annotation(&id)
        .await
        .map_err(|e| e.to_string())
}

// ============================================================================
// EVENT RETRIEVAL COMMANDS - For Surfacing System Intelligence
// ============================================================================

/// Get recent events with optional filtering
#[tauri::command]
pub async fn get_recent_events(
    state: State<'_, AppState>,
    limit: Option<usize>,
    entity_type: Option<String>,
    actor: Option<String>,
) -> Result<Vec<Event>, String> {
    let store = {
        let guard = state.db.lock().map_err(|e| e.to_string())?;
        guard.as_ref().cloned().ok_or("Store not initialized")?
    };

    let limit_value = limit.unwrap_or(50).min(500); // Cap at 500

    // Build query with optional filters
    let query = if entity_type.is_some() && actor.is_some() {
        "SELECT * FROM event WHERE entity_type = $etype AND actor = $actor ORDER BY created_at DESC LIMIT $limit"
    } else if entity_type.is_some() {
        "SELECT * FROM event WHERE entity_type = $etype ORDER BY created_at DESC LIMIT $limit"
    } else if actor.is_some() {
        "SELECT * FROM event WHERE actor = $actor ORDER BY created_at DESC LIMIT $limit"
    } else {
        "SELECT * FROM event ORDER BY created_at DESC LIMIT $limit"
    };

    let mut response = store
        .get_db()
        .query(query)
        .bind(("etype", entity_type.unwrap_or_default()))
        .bind(("actor", actor.unwrap_or_default()))
        .bind(("limit", limit_value))
        .await
        .map_err(|e| e.to_string())?;

    let events: Vec<Event> = response.take(0).map_err(|e| e.to_string())?;
    Ok(events)
}

/// Get all events for a specific entity
#[tauri::command]
pub async fn get_events_by_entity(
    state: State<'_, AppState>,
    entity_type: String,
    entity_id: String,
) -> Result<Vec<Event>, String> {
    let store = {
        let guard = state.db.lock().map_err(|e| e.to_string())?;
        guard.as_ref().cloned().ok_or("Store not initialized")?
    };

    let mut response = store
        .get_db()
        .query("SELECT * FROM event WHERE entity_type = $etype AND entity_id = $eid ORDER BY created_at DESC")
        .bind(("etype", entity_type))
        .bind(("eid", entity_id))
        .await
        .map_err(|e| e.to_string())?;

    let events: Vec<Event> = response.take(0).map_err(|e| e.to_string())?;
    Ok(events)
}

/// Get actionable events (system-generated events that suggest user action)
#[tauri::command]
pub async fn get_actionable_events(state: State<'_, AppState>) -> Result<Vec<Event>, String> {
    let store = {
        let guard = state.db.lock().map_err(|e| e.to_string())?;
        guard.as_ref().cloned().ok_or("Store not initialized")?
    };

    let mut response = store
        .get_db()
        .query(
            "SELECT * FROM event
             WHERE actor = 'system'
             AND (
                 payload.type = 'goal_ready_to_complete'
                 OR payload.type = 'phase_ready_to_close'
                 OR payload.type = 'day_success'
                 OR payload.type = 'day_progress'
             )
             ORDER BY created_at DESC
             LIMIT 100",
        )
        .await
        .map_err(|e| e.to_string())?;

    let events: Vec<Event> = response.take(0).map_err(|e| e.to_string())?;
    Ok(events)
}

/// Get event counts by type for dashboard metrics
#[tauri::command]
pub async fn get_event_stats(state: State<'_, AppState>) -> Result<serde_json::Value, String> {
    let store = {
        let guard = state.db.lock().map_err(|e| e.to_string())?;
        guard.as_ref().cloned().ok_or("Store not initialized")?
    };

    // Count actionable events
    let mut resp1 = store
        .get_db()
        .query(
            "SELECT count() as count FROM event
             WHERE actor = 'system' AND payload.type = 'goal_ready_to_complete'",
        )
        .await
        .map_err(|e| e.to_string())?;

    #[derive(serde::Deserialize)]
    struct Count {
        count: i64,
    }

    let goal_ready: Vec<Count> = resp1.take(0).map_err(|e| e.to_string())?;
    let goal_ready_count = goal_ready.first().map(|c| c.count).unwrap_or(0);

    let mut resp2 = store
        .get_db()
        .query(
            "SELECT count() as count FROM event
             WHERE actor = 'system' AND payload.type = 'phase_ready_to_close'",
        )
        .await
        .map_err(|e| e.to_string())?;

    let phase_ready: Vec<Count> = resp2.take(0).map_err(|e| e.to_string())?;
    let phase_ready_count = phase_ready.first().map(|c| c.count).unwrap_or(0);

    Ok(serde_json::json!({
        "goals_ready_to_complete": goal_ready_count,
        "phases_ready_to_close": phase_ready_count,
        "total_actionable": goal_ready_count + phase_ready_count
    }))
}

/// Run proactive consequence scans to detect issues/opportunities
#[tauri::command]
pub async fn run_consequence_scan(state: State<'_, AppState>) -> Result<serde_json::Value, String> {
    let store = {
        let guard = state.db.lock().map_err(|e| e.to_string())?;
        guard.as_ref().cloned().ok_or("Store not initialized")?
    };

    let engine = ConsequenceEngine { store };
    let report = engine.run_all_scans().await.map_err(|e| e.to_string())?;

    Ok(serde_json::to_value(report).map_err(|e| e.to_string())?)
}

// === Unified Shell Command Dispatcher ===

#[derive(Debug, Serialize, Deserialize)]
pub struct ShellResult {
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
    pub timestamp: DateTime<Utc>,
    pub command: String,
}

fn shell_commands() -> Vec<(&'static str, &'static str)> {
    vec![
        ("help", "List available shell commands"),
        ("doctor", "Show DB/phase/day diagnostics"),
        ("ingest_roadmap", "Ingest and enrich roadmap into DB"),
        (
            "update_all",
            "Recover/refresh DB state and set active phase",
        ),
        ("phase list", "List phases"),
        ("goal list", "List goals"),
        ("aequitas <cmd>", "Proxy to Aequitas CLI (not yet wired)"),
    ]
}

fn format_help() -> String {
    shell_commands()
        .into_iter()
        .map(|(cmd, desc)| format!("{:<18} {}", cmd, desc))
        .collect::<Vec<_>>()
        .join("\n")
}

async fn get_store(
    state: &State<'_, AppState>,
) -> Result<std::sync::Arc<metatheos_core::store::SurrealStore>, String> {
    let guard = state.db.lock().map_err(|e| e.to_string())?;
    guard
        .as_ref()
        .cloned()
        .ok_or("Store not initialized".to_string())
}

fn format_phase_list(phases: Vec<metatheos_core::Phase>) -> String {
    if phases.is_empty() {
        return "No phases found".to_string();
    }
    phases
        .into_iter()
        .map(|p| {
            let status = p.status;
            format!("{}: {} ({})", p.phase_id, p.title, status)
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn format_goal_list(goals: Vec<metatheos_core::Goal>) -> String {
    if goals.is_empty() {
        return "No goals found".to_string();
    }
    goals
        .into_iter()
        .map(|g| {
            let phase = g.phase.clone().unwrap_or_else(|| "n/a".to_string());
            format!("{} [{}] {}", g.goal_id, phase, g.title)
        })
        .collect::<Vec<_>>()
        .join("\n")
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DoctorSnapshot {
    pub governance_root: String,
    pub db_path: String,
    pub counts: std::collections::HashMap<String, usize>,
    pub active_phase: Option<String>,
    pub today_day: Option<String>,
    pub roadmap_exists: bool,
}

async fn run_doctor(state: &State<'_, AppState>) -> Result<(DoctorSnapshot, String), String> {
    let governance_root = state.governance_root.lock().unwrap().clone();
    let db_path = governance_root.join(".metatheos.db");
    let roadmap_exists = governance_root.join("aequitas_roadmap.md").exists()
        || std::path::Path::new("governance/aequitas_roadmap.md").exists();
    let legacy_dirs: Vec<String> = ["02_PHASES", "03_GOALS_EPICS", "04_DECISIONS"]
        .iter()
        .filter_map(|d| {
            let p = governance_root.join(d);
            if p.exists() {
                Some(p.to_string_lossy().to_string())
            } else {
                None
            }
        })
        .collect();

    let store = get_store(state).await?;
    let tables = vec!["phase", "goal", "work_item", "day", "event", "annotation"];
    let mut counts = std::collections::HashMap::new();
    for t in &tables {
        let query = format!("SELECT count() as count FROM {}", t);
        let mut resp = store.db.query(query).await.map_err(|e| e.to_string())?;
        #[derive(serde::Deserialize)]
        struct CountRow {
            count: i64,
        }
        let c = resp
            .take::<Vec<CountRow>>(0)
            .ok()
            .and_then(|rows| rows.first().map(|r| r.count as usize))
            .unwrap_or(0);
        counts.insert(t.to_string(), c);
    }

    let active_phase = store.get_meta("active_phase").await.ok().flatten();

    let today = Local::now()
        .naive_local()
        .date()
        .format("%Y-%m-%d")
        .to_string();
    let mut today_day: Option<String> = None;
    if let Ok(mut resp) = store
        .db
        .query("SELECT * FROM day WHERE id = $id")
        .bind(("id", today.clone()))
        .await
    {
        let rows: Result<Vec<serde_json::Value>, _> = resp.take(0);
        if rows.ok().map(|v| !v.is_empty()).unwrap_or(false) {
            today_day = Some(today.clone());
        }
    }

    let snapshot = DoctorSnapshot {
        governance_root: governance_root.to_string_lossy().to_string(),
        db_path: db_path.to_string_lossy().to_string(),
        counts,
        active_phase,
        today_day,
        roadmap_exists,
    };

    let mut lines = Vec::new();
    lines.push(format!("governance_root: {}", snapshot.governance_root));
    lines.push(format!("db_path: {}", snapshot.db_path));
    lines.push(format!(
        "counts: {:?}",
        snapshot
            .counts
            .iter()
            .map(|(k, v)| format!("{}={}", k, v))
            .collect::<Vec<_>>()
            .join(", ")
    ));
    lines.push(format!(
        "active_phase: {}",
        snapshot
            .active_phase
            .clone()
            .unwrap_or_else(|| "none".to_string())
    ));
    lines.push(format!(
        "today_day: {}",
        snapshot
            .today_day
            .clone()
            .unwrap_or_else(|| "none".to_string())
    ));
    lines.push(format!(
        "roadmap_file: {}",
        if snapshot.roadmap_exists {
            "present"
        } else {
            "missing"
        }
    ));
    lines.push("ingest_roadmap: available".to_string());
    lines.push(
        "data_sources: DB-backed for phases/goals/work_items/days/annotations/events".to_string(),
    );
    if !legacy_dirs.is_empty() {
        lines.push(format!(
            "legacy files detected (ignored): {}",
            legacy_dirs.join(", ")
        ));
    } else {
        lines.push("legacy files detected (ignored): none".to_string());
    }

    Ok((snapshot, lines.join("\n")))
}

async fn run_update_all(state: &State<'_, AppState>) -> Result<String, String> {
    let (before, before_text) = run_doctor(state).await?;
    let store = get_store(state).await?;
    let mut actions: Vec<String> = vec!["Ensured schema initialized".to_string()];

    // Re-run schema init (idempotent)
    store::schema::initialize_schema(store.get_db())
        .await
        .map_err(|e| e.to_string())?;

    // Ensure phases exist
    let mut phases = store.get_all_phases().await.map_err(|e| e.to_string())?;
    if phases.is_empty() {
        let rep = ingest_roadmap(state.clone()).await?;
        actions.push(format!(
            "ingest_roadmap ran: phases {}, goals {}, annotations {}",
            rep.phases_upserted, rep.goals_upserted, rep.annotations_added
        ));
        phases = store.get_all_phases().await.map_err(|e| e.to_string())?;
    }

    // Ensure active phase
    let active_phase = store.get_meta("active_phase").await.ok().flatten();
    if active_phase.is_none() && !phases.is_empty() {
        // Prefer active status first
        let chosen = phases
            .iter()
            .find(|p| p.status.eq_ignore_ascii_case("active"))
            .cloned()
            .unwrap_or_else(|| phases[0].clone());
        store
            .set_meta("active_phase", &chosen.phase_id)
            .await
            .map_err(|e| e.to_string())?;
        actions.push(format!("set active phase: {}", chosen.phase_id));
    }

    let (after, after_text) = run_doctor(state).await?;

    // Summarize counts delta for key tables
    let mut deltas = Vec::new();
    for key in ["phase", "goal", "work_item", "day", "event", "annotation"] {
        let b = *before.counts.get(key).unwrap_or(&0);
        let a = *after.counts.get(key).unwrap_or(&0);
        if a != b {
            deltas.push(format!("{}: {} -> {}", key, b, a));
        }
    }

    let mut output = Vec::new();
    output.push("=== Doctor (before) ===".to_string());
    output.push(before_text);
    output.push("\n=== Actions ===".to_string());
    output.extend(actions);
    if deltas.is_empty() {
        output.push("counts unchanged".to_string());
    } else {
        output.push(format!("counts diff: {}", deltas.join(", ")));
    }
    output.push("\n=== Doctor (after) ===".to_string());
    output.push(after_text);

    Ok(output.join("\n"))
}

#[tauri::command]
pub async fn execute_shell_command(
    input: String,
    state: State<'_, AppState>,
) -> Result<ShellResult, String> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Ok(ShellResult {
            success: false,
            output: "".to_string(),
            error: Some("Empty command".to_string()),
            timestamp: Utc::now(),
            command: input,
        });
    }

    let tokens: Vec<String> = trimmed.split_whitespace().map(|s| s.to_string()).collect();

    let command = tokens.get(0).cloned().unwrap_or_default();

    // Route to Aequitas CLI (Python) - not yet wired in-process
    if command.eq_ignore_ascii_case("aequitas") {
        return Ok(ShellResult {
            success: false,
            output: "".to_string(),
            error: Some("Aequitas CLI bridge is not yet available in the GUI shell; please run aequitas-cli directly.".to_string()),
            timestamp: Utc::now(),
            command: input,
        });
    }

    // Dispatch Metatheos commands (minimal routing)
    let result = match command.as_str() {
        "ingest_roadmap" => {
            let report = ingest_roadmap(state).await?;
            ShellResult {
                success: true,
                output: format!(
                    "Roadmap ingested (phases: {}, goals: {}, annotations: {}, event_logged: {})",
                    report.phases_upserted,
                    report.goals_upserted,
                    report.annotations_added,
                    report.event_logged
                ),
                error: None,
                timestamp: Utc::now(),
                command: input,
            }
        }
        "doctor" => {
            let (_, text) = run_doctor(&state).await?;
            ShellResult {
                success: true,
                output: text,
                error: None,
                timestamp: Utc::now(),
                command: input,
            }
        }
        "update_all" => {
            let text = run_update_all(&state).await?;
            ShellResult {
                success: true,
                output: text,
                error: None,
                timestamp: Utc::now(),
                command: input,
            }
        }
        "phase" => {
            if tokens.get(1).map(|s| s.as_str()) == Some("list") {
                let phases = get_store(&state)
                    .await?
                    .get_all_phases()
                    .await
                    .map_err(|e| e.to_string())?;
                ShellResult {
                    success: true,
                    output: format_phase_list(phases),
                    error: None,
                    timestamp: Utc::now(),
                    command: input,
                }
            } else {
                ShellResult {
                    success: false,
                    output: "".to_string(),
                    error: Some("Usage: phase list".to_string()),
                    timestamp: Utc::now(),
                    command: input,
                }
            }
        }
        "goal" => {
            if tokens.get(1).map(|s| s.as_str()) == Some("list") {
                let goals = get_store(&state)
                    .await?
                    .get_all_goals()
                    .await
                    .map_err(|e| e.to_string())?;
                ShellResult {
                    success: true,
                    output: format_goal_list(goals),
                    error: None,
                    timestamp: Utc::now(),
                    command: input,
                }
            } else {
                ShellResult {
                    success: false,
                    output: "".to_string(),
                    error: Some("Usage: goal list".to_string()),
                    timestamp: Utc::now(),
                    command: input,
                }
            }
        }
        "help" => ShellResult {
            success: true,
            output: format_help(),
            error: None,
            timestamp: Utc::now(),
            command: input,
        },
        _ => ShellResult {
            success: false,
            output: "".to_string(),
            error: Some(format!("Unknown command '{}'", command)),
            timestamp: Utc::now(),
            command: input,
        },
    };

    Ok(result)
}

// === Roadmap Ingestion & Enrichment (DB-first, idempotent) ===

#[derive(Debug, Serialize, Deserialize)]
pub struct RoadmapIngestReport {
    pub phases_upserted: usize,
    pub goals_upserted: usize,
    pub annotations_added: usize,
    pub annotations_skipped: usize,
    pub event_logged: bool,
    pub warnings: Vec<String>,
    pub fixed_items: usize,
}

/// Load and validate a roadmap file (returns normalized roadmap + warnings)
#[tauri::command]
pub async fn load_roadmap_from_file(
    state: State<'_, AppState>,
    file_path: Option<String>,
) -> Result<serde_json::Value, String> {
    use crate::roadmap_loader;

    let path = if let Some(p) = file_path {
        std::path::PathBuf::from(p)
    } else {
        let gov_root = state.governance_root.lock().map_err(|e| e.to_string())?.clone();
        gov_root.join("roadmap.golden.json")
    };

    log::info!("🔍 Loading roadmap from: {}", path.display());

    let result = roadmap_loader::load_roadmap_file(&path)?;

    log::info!(
        "✓ Roadmap loaded: {} phases, {} warnings, {} auto-fixed",
        result.roadmap.phases.len(),
        result.warnings.len(),
        result.fixed_items
    );

    Ok(serde_json::json!({
        "roadmap": result.roadmap,
        "warnings": result.warnings,
        "fixed_items": result.fixed_items,
    }))
}

/// Ingest a roadmap from JSON file (fail-safe, never crashes)
#[tauri::command]
pub async fn ingest_roadmap_from_file(
    state: State<'_, AppState>,
    file_path: Option<String>,
) -> Result<RoadmapIngestReport, String> {
    use crate::roadmap_loader;

    let path = if let Some(p) = file_path {
        std::path::PathBuf::from(p)
    } else {
        let gov_root = state.governance_root.lock().map_err(|e| e.to_string())?.clone();
        gov_root.join("roadmap.json")
    };

    log::info!("📥 Ingesting roadmap from: {}", path.display());

    // Load and normalize
    let load_result = roadmap_loader::load_roadmap_file(&path)?;
    let roadmap = load_result.roadmap;

    log::info!(
        "📊 Normalized roadmap: {} phases, {} warnings, {} fixed",
        roadmap.phases.len(),
        load_result.warnings.len(),
        load_result.fixed_items
    );

    // Get database
    let store = {
        let guard = state.db.lock().map_err(|e| e.to_string())?;
        guard.as_ref().cloned().ok_or("Store not initialized")?
    };
    let db = store.get_db();

    let mut report = RoadmapIngestReport {
        phases_upserted: 0,
        goals_upserted: 0,
        annotations_added: 0,
        annotations_skipped: 0,
        event_logged: false,
        warnings: load_result.warnings,
        fixed_items: load_result.fixed_items,
    };

    // Ingest phases (fail-safe - skip bad items)
    for (idx, phase_spec) in roadmap.phases.iter().enumerate() {
        let pointer = format!("/phases/{}", idx);
        log::debug!("  📍 Processing phase {}: {}", idx, phase_spec.phase_id);

        match ingest_phase_spec(&db, phase_spec, &pointer, &mut report).await {
            Ok(_) => {
                log::debug!("    ✓ Phase {} ingested", phase_spec.phase_id);
                report.phases_upserted += 1;
            }
            Err(e) => {
                let warn = format!("Failed to ingest phase at {}: {}", pointer, e);
                log::warn!("    ⚠️  {}", warn);
                report.warnings.push(warn);
            }
        }
    }

    // Log event
    if report.phases_upserted > 0 {
        let event = Event::new(
            "roadmap".to_string(),
            roadmap.roadmap_id.clone(),
            EventAction::Update,
            "system".to_string(),
            json!({
                "source": "file",
                "path": path.display().to_string(),
                "phases": report.phases_upserted,
                "goals": report.goals_upserted,
                "warnings": report.warnings.len(),
            }),
        );
        if let Err(e) = store.log_event(&event).await {
            log::warn!("Failed to log roadmap ingest event: {}", e);
        } else {
            report.event_logged = true;
        }
    }

    log::info!(
        "✅ Roadmap ingestion complete: {} phases, {} goals, {} warnings",
        report.phases_upserted,
        report.goals_upserted,
        report.warnings.len()
    );

    Ok(report)
}

/// Helper: Ingest a single phase spec (fail-safe)
async fn ingest_phase_spec(
    db: &surrealdb::Surreal<surrealdb::engine::local::Db>,
    phase: &crate::roadmap_loader::PhaseSpec,
    pointer: &str,
    report: &mut RoadmapIngestReport,
) -> Result<(), String> {
    // Check if phase exists
    let existing: Option<serde::de::IgnoredAny> = db
        .select(("phase", phase.phase_id.as_str()))
        .await
        .map_err(|e| e.to_string())?;

    let phase_payload = json!({
        "id": phase.phase_id,
        "phase_id": phase.phase_id,
        "title": phase.title,
        "description": phase.content,
        "content": phase.content,
        "status": phase.status,
        "order_index": phase.order_index,
        "start_date": phase.start_date,
        "target_date": phase.target_date,
        "dependencies": phase.dependencies,
    });

    if existing.is_some() {
        // Update existing
        let _: Option<serde::de::IgnoredAny> = db
            .update(("phase", phase.phase_id.as_str()))
            .merge(phase_payload)
            .await
            .map_err(|e| format!("Failed to update phase: {}", e))?;
    } else {
        // Create new
        let _: Option<serde::de::IgnoredAny> = db
            .create(("phase", phase.phase_id.as_str()))
            .content(phase_payload)
            .await
            .map_err(|e| format!("Failed to create phase: {}", e))?;
    }

    // Ingest goals
    for (goal_idx, goal_spec) in phase.goals.iter().enumerate() {
        let goal_pointer = format!("{}/goals/{}", pointer, goal_idx);
        match ingest_goal_spec(db, goal_spec, &phase.phase_id, &goal_pointer).await {
            Ok(_) => report.goals_upserted += 1,
            Err(e) => {
                let warn = format!("Failed to ingest goal at {}: {}", goal_pointer, e);
                log::warn!("      ⚠️  {}", warn);
                report.warnings.push(warn);
            }
        }
    }

    Ok(())
}

/// Helper: Ingest a single goal spec (fail-safe)
async fn ingest_goal_spec(
    db: &surrealdb::Surreal<surrealdb::engine::local::Db>,
    goal: &crate::roadmap_loader::GoalSpec,
    phase_id: &str,
    _pointer: &str,
) -> Result<(), String> {
    let existing: Option<serde::de::IgnoredAny> = db
        .select(("goal", goal.goal_id.as_str()))
        .await
        .map_err(|e| e.to_string())?;

    let goal_payload = json!({
        "id": goal.goal_id,
        "phase_id": phase_id,
        "title": goal.title,
        "description": goal.content,
        "status": goal.status,
        "priority": "normal",
        "dependencies": [],
        "tags": vec![format!("phase:{}", phase_id), "roadmap_ingest".to_string()],
    });

    if existing.is_some() {
        let _: Option<serde::de::IgnoredAny> = db
            .update(("goal", goal.goal_id.as_str()))
            .merge(goal_payload)
            .await
            .map_err(|e| format!("Failed to update goal: {}", e))?;
    } else {
        let _: Option<serde::de::IgnoredAny> = db
            .create(("goal", goal.goal_id.as_str()))
            .content(goal_payload)
            .await
            .map_err(|e| format!("Failed to create goal: {}", e))?;
    }

    Ok(())
}

#[derive(Clone)]
struct PhaseSeed {
    code: &'static str,
    title: &'static str,
    purpose: &'static str,
    why: &'static str,
    status: &'static str,
    order_index: i32,
    start_date: Option<&'static str>,
    target_date: Option<&'static str>,
    goals: &'static [&'static str],
    learning: &'static [&'static str],
    concepts: &'static [&'static str],
    prerequisites: &'static [&'static str],
    hard: &'static [&'static str],
    mental_models: &'static [&'static str],
}

fn roadmap_seeds() -> Vec<PhaseSeed> {
    vec![
        PhaseSeed {
            code: "P0",
            title: "Foundation Stone",
            purpose: "Governance, awareness, self-observation",
            why:
                "Visibility precedes correctness; we need observability of work before changing it.",
            status: "active",
            order_index: 0,
            start_date: Some("2025-11-20"),
            target_date: Some("2026-01-15"),
            goals: &[
                "Phases, goals, work items, days exist and are visible",
                "Events, annotations, decisions are captured",
                "Metatheos tracks Aequitas itself",
            ],
            learning: &[
                "Project governance basics (roadmaps vs backlogs)",
                "State and context framing",
                "Event thinking and change logging",
                "Single source of truth discipline",
            ],
            concepts: &[
                "roadmaps vs backlogs",
                "phase/goal/task boundaries",
                "event streams and append-only logs",
                "database as truth, not files",
            ],
            prerequisites: &[
                "Willingness to model work explicitly",
                "Basic comfort reading database records",
            ],
            hard: &[
                "Feels meta and abstract; easy to chase tooling instead of clarity",
                "Progress can feel invisible without instrumentation",
            ],
            mental_models: &[
                "Observer tower for the project",
                "Governance as instrumentation, not bureaucracy",
            ],
        },
        PhaseSeed {
            code: "P1",
            title: "Canon",
            purpose: "Definitions that cannot be negotiated",
            why: "Most bugs are definition problems; canon must be explicit and immutable.",
            status: "planned",
            order_index: 1,
            start_date: Some("2026-01-16"),
            target_date: Some("2026-02-28"),
            goals: &[
                "Canonical chart of accounts is defined",
                "Account types and normal balances are explicit",
                "Fiscal period rules are captured",
                "Currency and precision rules are enforced",
                "Canon is stored as data, not code paths",
            ],
            learning: &[
                "Deep accounting theory (not procedural)",
                "Domain modeling of financial primitives",
                "Immutability for shared definitions",
                "Separating rules from behaviors",
            ],
            concepts: &[
                "normal balances",
                "dimensional modeling of accounts",
                "immutable reference data",
                "data vs logic separation",
            ],
            prerequisites: &[
                "Basic debits/credits literacy",
                "Familiarity with financial statements structure",
            ],
            hard: &[
                "Definitions feel tedious but drive every downstream invariant",
                "Temptation to bake rules into code instead of data",
            ],
            mental_models: &[
                "Constitution for the system",
                "Ledger DNA that must not drift",
            ],
        },
        PhaseSeed {
            code: "P2",
            title: "The Engine",
            purpose: "Deterministic transaction processing",
            why: "Correctness is proven through enforced invariants and auditability.",
            status: "planned",
            order_index: 2,
            start_date: Some("2026-03-01"),
            target_date: Some("2026-04-15"),
            goals: &[
                "Journal entries exist and validate",
                "Double-entry enforcement is hard-guarded",
                "Ledger posting path is deterministic",
                "Trial balance is derivable anytime",
                "Full audit trail accompanies processing",
            ],
            learning: &[
                "Invariants and how to enforce them",
                "Transaction processing and rollback",
                "Idempotency and repeatability",
                "Pure vs impure computation boundaries",
            ],
            concepts: &[
                "ACID and transaction scopes",
                "idempotent handlers",
                "deterministic functions vs side effects",
                "audit trails and evidence",
            ],
            prerequisites: &[
                "Comfort with canonical chart of accounts",
                "Understanding of journal vs ledger",
            ],
            hard: &[
                "Edge cases around rollback/idempotency are easy to miss",
                "Testing invariants requires discipline and fixtures",
            ],
            mental_models: &[
                "Assembly line that must never skip a bolt",
                "Mathematical function plus durable log",
            ],
        },
        PhaseSeed {
            code: "P3",
            title: "Time & Events",
            purpose: "Reality as a sequence, not a snapshot",
            why: "You stop thinking in rows and start thinking in histories.",
            status: "planned",
            order_index: 3,
            start_date: Some("2026-04-16"),
            target_date: Some("2026-05-31"),
            goals: &[
                "Financial events are captured",
                "Event to journal transformation exists",
                "Event log is canonical",
                "Period lifecycle (open/close/lock) is defined",
                "Historical reconstruction is possible",
            ],
            learning: &[
                "Event sourcing fundamentals",
                "Temporal reasoning and point-in-time queries",
                "Causality chains",
                "State reconstruction from history",
            ],
            concepts: &[
                "event sourcing vs CRUD",
                "valid-time vs transaction-time",
                "event causality",
                "replay and rebuild",
            ],
            prerequisites: &[
                "Deterministic engine from P2",
                "Comfort with append-only logs",
            ],
            hard: &[
                "Temporal bugs are subtle and hard to test",
                "Mixing snapshot thinking with event thinking causes drift",
            ],
            mental_models: &[
                "Flight recorder for finances",
                "History-first, projections later",
            ],
        },
        PhaseSeed {
            code: "P4",
            title: "Materialization",
            purpose: "Derived truth",
            why: "Understanding arises from computed views, not stored reports.",
            status: "planned",
            order_index: 4,
            start_date: Some("2026-06-01"),
            target_date: Some("2026-07-15"),
            goals: &[
                "Balance Sheet materializes from data",
                "Income Statement materializes from data",
                "Cash Flow Statement is derived",
                "Reconciliation paths exist",
                "Computation audit trails are kept",
            ],
            learning: &[
                "Derived data vs stored reports",
                "Functional composition of computations",
                "Reconciliation logic to prove outputs",
                "Explainability and traceability",
            ],
            concepts: &[
                "materialized views vs authoritative tables",
                "functional pipelines",
                "reconciliation proofs",
                "numerical integrity (precision/rounding)",
            ],
            prerequisites: &[
                "Stable event and ledger history",
                "Known statements definitions from P1",
            ],
            hard: &[
                "Precision/rounding edge cases creep in silently",
                "Temptation to store reports instead of recomputing",
            ],
            mental_models: &[
                "Math workbook that shows every step",
                "Glass box calculations, not black box",
            ],
        },
        PhaseSeed {
            code: "P5",
            title: "Operational Modules",
            purpose: "Reality enters the system",
            why: "Clean theory meets messy operational data.",
            status: "planned",
            order_index: 5,
            start_date: Some("2026-07-16"),
            target_date: Some("2026-09-30"),
            goals: &[
                "AP, AR, assets, reconciliation flows connect to engine",
                "Master data for customers and vendors exists",
                "Operational workflows feed the engine without breaking rules",
            ],
            learning: &[
                "Workflow modeling (states, transitions, approvals)",
                "Boundary enforcement for accounting rules",
                "Data lifecycle from draft to posted",
                "Human error handling",
            ],
            concepts: &[
                "state machines for operations",
                "validation at boundaries",
                "lifecycle hooks",
                "error recovery paths",
            ],
            prerequisites: &[
                "Engine invariants from P2 are stable",
                "Basic UX of operational flows understood",
            ],
            hard: &[
                "Operational shortcuts tend to bypass invariants",
                "Real data is messy; needs resilient validation",
            ],
            mental_models: &[
                "Airlocks between operations and accounting core",
                "Safety rails over raw speed",
            ],
        },
        PhaseSeed {
            code: "P6",
            title: "The Observer",
            purpose: "Intelligence without authority",
            why: "AI assists but never controls; decision support only.",
            status: "planned",
            order_index: 6,
            start_date: Some("2026-10-01"),
            target_date: Some("2026-11-15"),
            goals: &[
                "Read-only AI layer exists",
                "Anomaly detection runs against ledger",
                "Natural language queries work without mutations",
                "AI annotations and audit trail exist",
            ],
            learning: &[
                "Decision support vs decision making",
                "Read-only system design",
                "Interpretability and bias awareness",
                "Human-in-the-loop protocols",
            ],
            concepts: &[
                "principle of least authority for AI",
                "explainable outputs",
                "audit trails for AI suggestions",
                "feedback loops with humans",
            ],
            prerequisites: &[
                "Stable materializations from P4",
                "Clear operational boundaries from P5",
            ],
            hard: &[
                "Pressure to let AI mutate state must be resisted",
                "Hallucinations must be bounded and labeled",
            ],
            mental_models: &[
                "Lens, not hands-on driver",
                "Read-only oracle with receipts",
            ],
        },
        PhaseSeed {
            code: "P7",
            title: "Verification",
            purpose: "Proof",
            why: "Trust becomes mathematical, not social.",
            status: "planned",
            order_index: 7,
            start_date: Some("2026-11-16"),
            target_date: Some("2027-01-15"),
            goals: &[
                "Continuous invariant checks exist",
                "Tamper-evident logs are in place",
                "Reproducibility is demonstrable",
                "Verification reports are produced",
            ],
            learning: &[
                "Verification vs testing",
                "Reproducibility strategies",
                "Cryptographic guarantees",
                "System self-validation",
            ],
            concepts: &[
                "formal checks vs unit tests",
                "deterministic replay",
                "hash chaining / tamper evidence",
                "verification report pipelines",
            ],
            prerequisites: &[
                "Complete event history from P3",
                "Materialized outputs from P4",
            ],
            hard: &[
                "Hard to scope verification without over-fitting",
                "Cryptographic tooling can be misapplied",
            ],
            mental_models: &[
                "Mathematical audit, not narrative audit",
                "Proving properties, not just hoping",
            ],
        },
        PhaseSeed {
            code: "P8",
            title: "Hardening",
            purpose: "Survival",
            why: "Correct systems still fail unless designed not to.",
            status: "planned",
            order_index: 8,
            start_date: Some("2027-01-16"),
            target_date: Some("2027-03-31"),
            goals: &[
                "Validation everywhere",
                "Backup and recovery exist",
                "Access control enforced",
                "Performance guarantees understood",
                "Migrations are safe",
            ],
            learning: &[
                "Failure modes and blast radius",
                "Defense in depth",
                "Operational safety",
                "Backward compatibility and migrations",
            ],
            concepts: &[
                "SLOs and error budgets",
                "least privilege access",
                "backup/restore drills",
                "rolling and reversible migrations",
            ],
            prerequisites: &[
                "Stable verification signals from P7",
                "Ops discipline baseline",
            ],
            hard: &[
                "Performance vs safety trade-offs are non-obvious",
                "Backwards compatibility is easy to break",
            ],
            mental_models: &[
                "Safety nets layered like armor",
                "Chaos engineering mindset",
            ],
        },
        PhaseSeed {
            code: "P9",
            title: "Horizon",
            purpose: "Optional expansion",
            why: "Extensions must not compromise invariants.",
            status: "planned",
            order_index: 9,
            start_date: Some("2027-04-01"),
            target_date: None, // May remain open; default placeholder applied downstream if required
            goals: &[
                "Carefully chosen extensions are identified",
                "Core invariants remain untouched",
            ],
            learning: &[
                "Architectural foresight",
                "Trade-off analysis",
                "Knowing when not to build",
            ],
            concepts: &[
                "expansion joints in architecture",
                "cost/benefit framing",
                "stopping rules",
            ],
            prerequisites: &[
                "Core spine is stable (P0-P8)",
                "Clear non-negotiables documented",
            ],
            hard: &[
                "Shiny-object bias invites scope creep",
                "Hard to say no when progress feels slow",
            ],
            mental_models: &["Guarded frontier", "Options, not obligations"],
        },
    ]
}

fn build_annotation_content(kind: &str, bullets: &[&str]) -> String {
    let body = bullets
        .iter()
        .map(|b| format!("- {}", b))
        .collect::<Vec<_>>()
        .join("\n");
    format!("type: {} (enrichment)\n{}", kind, body)
}

fn canonical_phase_dates(code: &str) -> (String, String) {
    match code {
        "P0" => ("2025-11-20".into(), "2026-01-15".into()),
        "P1" => ("2026-01-16".into(), "2026-02-28".into()),
        "P2" => ("2026-03-01".into(), "2026-04-15".into()),
        "P3" => ("2026-04-16".into(), "2026-05-31".into()),
        "P4" => ("2026-06-01".into(), "2026-07-15".into()),
        "P5" => ("2026-07-16".into(), "2026-09-30".into()),
        "P6" => ("2026-10-01".into(), "2026-11-15".into()),
        "P7" => ("2026-11-16".into(), "2027-01-15".into()),
        "P8" => ("2027-01-16".into(), "2027-03-31".into()),
        "P9" => ("2027-04-01".into(), "2099-12-31".into()),
        _ => ("2025-11-20".into(), "2099-12-31".into()),
    }
}

/// Seed default roadmap phases and goals into the database
/// This is called during startup if the phase table is empty
pub async fn seed_default_roadmap(store: &metatheos_core::store::SurrealStore) -> Result<usize, String> {
    let db = store.get_db();
    let seeds = roadmap_seeds();
    let mut phases_seeded = 0;

    for seed in &seeds {
        let description = format!(
            "Purpose: {}. Why it matters: {}. (created_from: roadmap_ingest, enrichment)",
            seed.purpose, seed.why
        );

        let (start_date, target_date) = if seed.start_date.is_some() || seed.target_date.is_some() {
            (
                seed.start_date.unwrap_or("2025-11-20").to_string(),
                seed.target_date.unwrap_or("2099-12-31").to_string(),
            )
        } else {
            canonical_phase_dates(seed.code)
        };


        // Phase doesn't exist - use CREATE (will apply defaults)
        let phase_payload = json!({
            "id": seed.code,
            "phase_id": seed.code,
            "title": seed.title,
            "description": description,
            "content": "",  // Required field, will be populated later
            "status": seed.status,
            "order_index": seed.order_index,
            "start_date": start_date,
            "target_date": target_date,
            "dependencies": [],  // Required field, empty by default
            "file_path": "",  // Required field, will be populated later
        });

        // Validate before writing to database
        metatheos_core::store::validation::validate_phase_input(&phase_payload)
            .map_err(|e| format!("Phase validation failed for {}: {}", seed.code, e))?;

        let _: Option<serde::de::IgnoredAny> = db
            .create(("phase", seed.code))
            .content(phase_payload)
            .await
            .map_err(|e| format!("Failed to seed phase {}: {}", seed.code, e))?;
        phases_seeded += 1;

        // Seed goals for this phase
        for (idx, goal_title) in seed.goals.iter().enumerate() {
            let goal_id = format!("G-{}-{:02}", seed.code, idx + 1);
            let goal_desc = format!(
                "What: {}. Why: {}. Learning focus: {}.",
                goal_title,
                seed.purpose,
                seed.learning.join("; ")
            );
            let tags = vec![
                "roadmap_ingest".to_string(),
                format!("phase:{}", seed.code),
                format!("order:{:02}", idx + 1),
            ];

            let goal_payload = json!({
                "id": goal_id,
                "phase_id": seed.code,
                "title": goal_title,
                "description": goal_desc,
                "status": "open",
                "priority": "normal",
                "dependencies": [],
                "tags": tags,
            });

            // Validate before writing to database
            metatheos_core::store::validation::validate_goal_input(&goal_payload)
                .map_err(|e| format!("Goal validation failed for {}: {}", goal_id, e))?;

            let _: Option<serde::de::IgnoredAny> = db
                .create(("goal", goal_id.as_str()))
                .content(goal_payload)
                .await
                .map_err(|e| format!("Failed to seed goal {}: {}", goal_id, e))?;
        }
    }

    println!("✓ Seeded {} default phases with goals", phases_seeded);

    // Now seed detailed work items based on actual Aequitas progress
    seed_aequitas_work_items(store).await?;

    Ok(phases_seeded)
}

/// Seed detailed work items based on actual Aequitas development progress
async fn seed_aequitas_work_items(store: &metatheos_core::store::SurrealStore) -> Result<(), String> {
    println!("🌱 [seed_aequitas_work_items] Starting detailed Aequitas seeding...");
    let db = store.get_db();

    // P0: Foundation Stone - What's been built in Aequitas
    println!("  → Seeding P0 goals...");
    let p0_goals = vec![
        ("G-P0-BACKEND", "Backend API Foundation", "done", vec![
            ("Database models and migrations", "done"),
            ("FastAPI application structure", "done"),
            ("Authentication and authorization", "done"),
            ("PostgreSQL integration", "done"),
            ("Alembic migration system", "done"),
        ]),
        ("G-P0-ACCOUNTING", "Core Accounting Entities", "done", vec![
            ("Chart of Accounts model", "done"),
            ("Journal Entries system", "done"),
            ("Fiscal Period management", "done"),
            ("Company and multi-tenant support", "done"),
            ("Account mapping framework", "done"),
        ]),
        ("G-P0-INTEGRATIONS", "QuickBooks Integration", "active", vec![
            ("OAuth2 authentication flow", "done"),
            ("QBO API client implementation", "done"),
            ("Data sync mechanisms", "done"),
            ("Mapping engine for QBO entities", "active"),
            ("Error handling and retry logic", "done"),
        ]),
        ("G-P0-FRONTEND", "Frontend Application", "active", vec![
            ("Svelte/SvelteKit setup", "done"),
            ("Athenaeum design system integration", "done"),
            ("Dashboard layouts", "done"),
            ("Company management UI", "done"),
            ("Chart of Accounts viewer", "active"),
            ("Journal Entry creation forms", "active"),
        ]),
        ("G-P0-GOVERNANCE", "Metatheos Governance Engine", "active", vec![
            ("SurrealDB integration", "done"),
            ("Phase management system", "done"),
            ("Goal tracking infrastructure", "done"),
            ("Work item hierarchy (goal/subgoal/task)", "active"),
            ("Event logging and audit trail", "done"),
            ("File watcher for markdown sync", "done"),
        ]),
    ];

    for (goal_id, title, status, tasks) in p0_goals {
        // Create goal
        println!("    ✓ Creating goal: {} - {}", goal_id, title);
        let goal_payload = json!({
            "id": goal_id,
            "phase_id": "P0",
            "title": title,
            "description": format!("Real progress on {}", title),
            "status": status,
            "priority": "high",
            "dependencies": [],
            "tags": vec!["aequitas", "foundation"],
        });

        // Validate before writing to database
        metatheos_core::store::validation::validate_goal_input(&goal_payload)
            .map_err(|e| format!("Goal validation failed for {}: {}", goal_id, e))?;

        let _: Option<serde::de::IgnoredAny> = db
            .create(("goal", goal_id))
            .content(goal_payload)
            .await
            .map_err(|e| format!("Failed to create goal {}: {}", goal_id, e))?;

        // Create work items (tasks) for this goal
        for (idx, (task_title, task_status)) in tasks.iter().enumerate() {
            let task_id = format!("{}-T{:02}", goal_id, idx + 1);
            let task_payload = json!({
                "id": task_id,
                "goal_id": goal_id,
                "parent_id": null,
                "level": "task",
                "title": task_title,
                "description": format!("Implementation: {}", task_title),
                "status": task_status,
                "order_index": idx,
            });

            // Validate before writing to database
            metatheos_core::store::validation::validate_work_item_input(&task_payload)
                .map_err(|e| format!("Work item validation failed for {}: {}", task_id, e))?;

            let _: Option<serde::de::IgnoredAny> = db
                .create(("work_item", task_id.as_str()))
                .content(task_payload)
                .await
                .map_err(|e| format!("Failed to create work item {}: {}", task_id, e))?;
        }
        println!("      └─ Created {} work items for {}", tasks.len(), goal_id);
    }
    println!("  ✓ P0 goals created");

    // P1: Canon - Schema and validation work
    println!("  → Seeding P1 goals...");
    let p1_goals = vec![
        ("G-P1-SCHEMA", "Database Schema Definition", "active", vec![
            ("Define SCHEMAFULL tables in SurrealDB", "done"),
            ("Canonical phase/goal/work_item models", "done"),
            ("Schema migration infrastructure", "done"),
            ("Field validation with ASSERT constraints", "active"),
        ]),
        ("G-P1-VALIDATION", "Input Validation Layer", "active", vec![
            ("Pydantic models for API validation", "done"),
            ("Request/response schemas", "active"),
            ("Error message standardization", "open"),
        ]),
    ];

    for (goal_id, title, status, tasks) in p1_goals {
        println!("    ✓ Creating goal: {} - {}", goal_id, title);
        let goal_payload = json!({
            "id": goal_id,
            "phase_id": "P1",
            "title": title,
            "description": format!("Canonical definitions: {}", title),
            "status": status,
            "priority": "high",
            "dependencies": [],
            "tags": vec!["canon", "schema"],
        });
        let _: Option<serde::de::IgnoredAny> = db
            .create(("goal", goal_id))
            .content(goal_payload)
            .await
            .map_err(|e| format!("Failed to create goal {}: {}", goal_id, e))?;

        for (idx, (task_title, task_status)) in tasks.iter().enumerate() {
            let task_id = format!("{}-T{:02}", goal_id, idx + 1);
            let task_payload = json!({
                "id": task_id,
                "goal_id": goal_id,
                "parent_id": null,
                "level": "task",
                "title": task_title,
                "description": format!("Implementation: {}", task_title),
                "status": task_status,
                "order_index": idx,
            });
            let _: Option<serde::de::IgnoredAny> = db
                .create(("work_item", task_id.as_str()))
                .content(task_payload)
                .await
                .map_err(|e| format!("Failed to create work item {}: {}", task_id, e))?;
        }
        println!("      └─ Created {} work items for {}", tasks.len(), goal_id);
    }
    println!("  ✓ P1 goals created");

    // P2: The Engine - Business logic and processing
    println!("  → Seeding P2 goals...");
    let p2_goals = vec![
        ("G-P2-LEDGER", "Ledger Posting Engine", "open", vec![
            ("Double-entry validation logic", "open"),
            ("Account balance calculation", "open"),
            ("Trial balance generation", "open"),
        ]),
        ("G-P2-MAPPINGS", "Mapping Engine", "active", vec![
            ("QBO to Aequitas mapping rules", "active"),
            ("Master chart to company chart mapping", "active"),
            ("Automated mapping suggestions", "open"),
        ]),
    ];

    for (goal_id, title, status, tasks) in p2_goals {
        println!("    ✓ Creating goal: {} - {}", goal_id, title);
        let goal_payload = json!({
            "id": goal_id,
            "phase_id": "P2",
            "title": title,
            "description": format!("Processing engine: {}", title),
            "status": status,
            "priority": "normal",
            "dependencies": [],
            "tags": vec!["engine", "processing"],
        });
        let _: Option<serde::de::IgnoredAny> = db
            .create(("goal", goal_id))
            .content(goal_payload)
            .await
            .map_err(|e| format!("Failed to create goal {}: {}", goal_id, e))?;

        for (idx, (task_title, task_status)) in tasks.iter().enumerate() {
            let task_id = format!("{}-T{:02}", goal_id, idx + 1);
            let task_payload = json!({
                "id": task_id,
                "goal_id": goal_id,
                "parent_id": null,
                "level": "task",
                "title": task_title,
                "description": format!("Implementation: {}", task_title),
                "status": task_status,
                "order_index": idx,
            });
            let _: Option<serde::de::IgnoredAny> = db
                .create(("work_item", task_id.as_str()))
                .content(task_payload)
                .await
                .map_err(|e| format!("Failed to create work item {}: {}", task_id, e))?;
        }
        println!("      └─ Created {} work items for {}", tasks.len(), goal_id);
    }
    println!("  ✓ P2 goals created");

    // Count what we created
    let mut goal_count_resp = db.query("SELECT count() FROM goal GROUP ALL").await.map_err(|e| e.to_string())?;
    let goal_count: usize = goal_count_resp.take::<Option<serde_json::Value>>(0)
        .ok()
        .and_then(|v| v)
        .and_then(|v| v.get("count").and_then(|c| c.as_u64()))
        .map(|c| c as usize)
        .unwrap_or(0);

    let mut wi_count_resp = db.query("SELECT count() FROM work_item GROUP ALL").await.map_err(|e| e.to_string())?;
    let wi_count: usize = wi_count_resp.take::<Option<serde_json::Value>>(0)
        .ok()
        .and_then(|v| v)
        .and_then(|v| v.get("count").and_then(|c| c.as_u64()))
        .map(|c| c as usize)
        .unwrap_or(0);

    println!("✓ Seeded detailed work items based on Aequitas progress");
    println!("  └─ Total: {} goals with {} work items (tasks) in database", goal_count, wi_count);
    Ok(())
}

#[tauri::command]
pub async fn ingest_roadmap(state: State<'_, AppState>) -> Result<RoadmapIngestReport, String> {
    let store = {
        let guard = state.db.lock().map_err(|e| e.to_string())?;
        guard.as_ref().cloned().ok_or("Store not initialized")?
    };

    let db = store.get_db();
    let seeds = roadmap_seeds();
    let mut report = RoadmapIngestReport {
        phases_upserted: 0,
        goals_upserted: 0,
        annotations_added: 0,
        annotations_skipped: 0,
        event_logged: false,
        warnings: Vec::new(),
        fixed_items: 0,
    };

    for seed in &seeds {
        let description = format!(
            "Purpose: {}. Why it matters: {}. (created_from: roadmap_ingest, enrichment)",
            seed.purpose, seed.why
        );

        // Use seed dates if provided, otherwise fall back to canonical dates
        // This ensures PhaseSeed.start_date and target_date fields are consumed
        let (start_date, target_date) = if seed.start_date.is_some() || seed.target_date.is_some() {
            (
                seed.start_date.unwrap_or("2025-11-20").to_string(),
                seed.target_date.unwrap_or("2099-12-31").to_string(),
            )
        } else {
            canonical_phase_dates(seed.code)
        };

        println!(
            "Ingesting phase {}: start_date={}, target_date={}",
            seed.code, start_date, target_date
        );

        // Check if phase exists
        // Check if phase exists - struct removed, using IgnoredAny below

        let existing: Option<serde::de::IgnoredAny> = db
            .select(("phase", seed.code))
            .await
            .map_err(|e| e.to_string())?;

        if existing.is_some() {
            // Phase exists - use MERGE to update only specified fields
            let phase_updates = json!({
                "phase_id": seed.code,
                "title": seed.title,
                "description": description,
                "status": seed.status,
                "order_index": seed.order_index,
                "start_date": start_date,
                "target_date": target_date,
            });
            let _: Option<serde::de::IgnoredAny> = db
                .update(("phase", seed.code))
                .merge(phase_updates)
                .await
                .map_err(|e| e.to_string())?;
        } else {
            // Phase doesn't exist - use CREATE (will apply defaults)
            let phase_payload = json!({
                "id": seed.code,
                "phase_id": seed.code,
                "title": seed.title,
                "description": description,
                "status": seed.status,
                "order_index": seed.order_index,
                "start_date": start_date,
                "target_date": target_date,
                // created_at will be set by schema default
            });
            let _: Option<serde::de::IgnoredAny> = db
                .create(("phase", seed.code))
                .content(phase_payload)
                .await
                .map_err(|e| e.to_string())?;
        }
        report.phases_upserted += 1;

        for (idx, goal_title) in seed.goals.iter().enumerate() {
            let goal_id = format!("G-{}-{:02}", seed.code, idx + 1);
            let goal_desc = format!(
                "What: {}. Why: {}. Learning focus: {}. Failure mode: definitions drift or remain implicit. (enrichment)",
                goal_title,
                seed.purpose,
                seed.learning.join("; ")
            );
            let tags = vec![
                "roadmap_ingest".to_string(),
                format!("phase:{}", seed.code),
                format!("order:{:02}", idx + 1),
            ];
            // Check if goal exists
            let existing_goal: Option<serde::de::IgnoredAny> = db
                .select(("goal", goal_id.as_str()))
                .await
                .map_err(|e| e.to_string())?;

            if existing_goal.is_some() {
                // Goal exists - use MERGE to update
                let goal_updates = json!({
                    "phase_id": seed.code,
                    "title": goal_title,
                    "description": goal_desc,
                    "tags": tags,
                });
                let _: Option<serde::de::IgnoredAny> = db
                    .update(("goal", goal_id.as_str()))
                    .merge(goal_updates)
                    .await
                    .map_err(|e| e.to_string())?;
            } else {
                // Goal doesn't exist - use CREATE
                let goal_payload = json!({
                    "id": goal_id,
                    "phase_id": seed.code,
                    "title": goal_title,
                    "description": goal_desc,
                    "status": "open",
                    "priority": "normal",
                    "dependencies": [],
                    "tags": tags,
                    // created_at will be set by schema default
                });
                let _: Option<serde::de::IgnoredAny> = db
                    .create(("goal", goal_id.as_str()))
                    .content(goal_payload)
                    .await
                    .map_err(|e| e.to_string())?;
            }
            report.goals_upserted += 1;
        }

        let existing_annotations = store
            .get_annotations("phase", seed.code)
            .await
            .unwrap_or_default();

        let annotations_to_add = vec![
            build_annotation_content("learning_objectives", seed.learning),
            build_annotation_content("concepts_to_study", seed.concepts),
            build_annotation_content("prerequisites", seed.prerequisites),
            build_annotation_content("why_this_is_hard", seed.hard),
            build_annotation_content("mental_models", seed.mental_models),
        ];

        for content in annotations_to_add {
            if existing_annotations.iter().any(|a| a.content == content) {
                report.annotations_skipped += 1;
                continue;
            }
            let ann_id = format!("ANN-{}", Uuid::new_v4());
            let ann_payload = json!({
                "id": ann_id,
                "entity_type": "phase",
                "entity_id": seed.code,
                "content": content,
                "author_type": "user",
                "author_ref": null,
            });
            let _: Option<serde::de::IgnoredAny> = db
                .create(("annotation", ann_id.as_str()))
                .content(ann_payload)
                .await
                .map_err(|e| e.to_string())?;
            report.annotations_added += 1;
        }
    }

    // Log a single event for the ingestion if it hasn't been logged before
    // Log a single event for the ingestion if it hasn't been logged before
    // We wrap this in a block to ensure that logging failures (e.g. strict type errors, deserialization)
    // do NOT fail the entire ingest process.
    let log_result: Result<bool, String> = async {
        let mut check = db
            .query("SELECT count() as count FROM event WHERE entity_type = 'roadmap' AND action = 'create' AND payload.philosophy = 'learning-first'")
            .await
            .map_err(|e| e.to_string())?;

        // We use IgnoredAny here too just in case, though we really want the count.
        // If count fails, we assume not logged.
        #[derive(Deserialize)]
        struct Cnt {
            count: i64,
        }
        let existing: Vec<Cnt> = check.take(0).map_err(|e| e.to_string())?;
        let already_logged = existing.first().map(|c| c.count > 0).unwrap_or(false);

        if !already_logged {
            let event = Event::new(
                "roadmap",
                "aequitas_roadmap.md",
                EventAction::Create,
                "system",
                json!({
                    "type": "roadmap_ingested_and_enriched",
                    "source": "aequitas_roadmap.md",
                    "enrichment": true,
                    "philosophy": "learning-first"
                }),
            );
            store.log_event(&event).await.map_err(|e| e.to_string())?;
            return Ok(true);
        }
        Ok(false)
    }.await;

    if let Ok(logged) = log_result {
        if logged {
            report.event_logged = true;
        }
    } else if let Err(e) = log_result {
        println!("Warning: Failed to log ingest event: {}", e);
    }

    Ok(report)
}

// ============================================================================
// DAY WIZARD COMMANDS - DB-First Day Flow
// ============================================================================

use metatheos_core::{Day, DayType};

#[derive(Debug, Serialize, Deserialize)]
pub struct DayDto {
    pub id: String,
    pub phase_id: String,
    pub day_type: String,
    pub created_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DayGoalDto {
    pub day_id: String,
    pub goal_id: String,
    pub required: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DayContextDto {
    pub day: DayDto,
    pub phase: PhaseDto,
    pub goals: Vec<GoalDto>,
    pub work_items: Vec<WorkItem>,
    pub annotations: Vec<Annotation>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateDayRequest {
    pub date: String, // "YYYY-MM-DD"
    pub phase_id: String,
    pub day_type: String, // "light", "heavy", "review", "rest"
    pub selected_goals: Vec<DayGoalDto>,
}

/// Get today's day record
#[tauri::command]
pub async fn get_today_day(state: State<'_, AppState>) -> Result<Option<DayDto>, String> {
    let today = Local::now()
        .naive_local()
        .date()
        .format("%Y-%m-%d")
        .to_string();
    get_day(state, today).await
}

/// Get a specific day by date
#[tauri::command]
pub async fn get_day(state: State<'_, AppState>, date: String) -> Result<Option<DayDto>, String> {
    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;

    let day_opt: Option<Day> = store
        .get_db()
        .select(("day", date.as_str()))
        .await
        .map_err(|e| e.to_string())?;

    Ok(day_opt.map(|d| DayDto {
        id: d.id,
        phase_id: d.phase_id,
        day_type: d.day_type.as_str().to_string(),
        created_at: d.created_at.to_rfc3339(),
    }))
}

/// Create a new day with atomic persistence (Wizard Step 5)
#[tauri::command]
pub async fn create_day(
    state: State<'_, AppState>,
    request: CreateDayRequest,
) -> Result<DayDto, String> {
    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;

    // Validate day type
    let day_type = match request.day_type.to_lowercase().as_str() {
        "light" => DayType::Light,
        "heavy" => DayType::Heavy,
        "review" => DayType::Review,
        "rest" => DayType::Rest,
        _ => return Err("Invalid day type".to_string()),
    };

    // Validate day type constraints
    match day_type {
        DayType::Heavy => {
            let required_count = request.selected_goals.iter().filter(|g| g.required).count();
            if required_count != 2 {
                return Err("Heavy day requires exactly 2 required goals".to_string());
            }
        }
        DayType::Rest => {
            if !request.selected_goals.is_empty() {
                return Err("Rest day cannot have goals".to_string());
            }
        }
        _ => {}
    }

    // Create Day record
    let day = Day {
        id: request.date.clone(),
        phase_id: request.phase_id.clone(),
        day_type: day_type.clone(),
        created_at: chrono::Utc::now(),
    };

    let day_payload = serde_json::json!({
        "id": day.id,
        "phase_id": day.phase_id,
        "day_type": day.day_type.as_str(),
        "created_at": day.created_at
    });

    let _: Option<serde_json::Value> = store
        .get_db()
        .create(("day", day.id.as_str()))
        .content(day_payload)
        .await
        .map_err(|e| format!("Failed to create day: {}", e))?;

    // Link goals to day
    for goal_link in &request.selected_goals {
        let day_goal_payload = serde_json::json!({
            "day_id": request.date,
            "goal_id": goal_link.goal_id,
            "required": goal_link.required
        });

        let link_id = format!("{}_{}", request.date, goal_link.goal_id);
        let _: Option<serde_json::Value> = store
            .get_db()
            .create(("day_goal", link_id.as_str()))
            .content(day_goal_payload)
            .await
            .map_err(|e| format!("Failed to link goal to day: {}", e))?;
    }

    // Emit event
    let event_payload = serde_json::json!({
        "day_type": day.day_type.as_str(),
        "phase_id": day.phase_id,
        "goals": request.selected_goals.iter().map(|g| &g.goal_id).collect::<Vec<_>>()
    });

    let event = Event::new("day", &day.id, EventAction::Create, "user", event_payload);
    let event_json = serde_json::json!({
        "id": event.id,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "action": event.action.as_str(),
        "actor": event.actor,
        "payload": event.payload,
        "created_at": event.created_at
    });

    let _: Option<serde_json::Value> = store
        .get_db()
        .create(("event", event.id.as_str()))
        .content(event_json)
        .await
        .map_err(|e| format!("Failed to create event: {}", e))?;

    let engine = ConsequenceEngine {
        store: store.clone(),
    };
    let _ = engine.on_day_goal_updated(&day.id).await;

    Ok(DayDto {
        id: day.id,
        phase_id: day.phase_id,
        day_type: day.day_type.as_str().to_string(),
        created_at: day.created_at.to_rfc3339(),
    })
}

/// Get full day context for dashboard (Day + Phase + Goals + WorkItems)
#[tauri::command]
pub async fn get_day_context(
    state: State<'_, AppState>,
    date: String,
) -> Result<DayContextDto, String> {
    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;

    // Get day
    let day: Day = store
        .get_db()
        .select(("day", date.as_str()))
        .await
        .map_err(|e| e.to_string())?
        .ok_or("Day not found")?;

    // Get phase
    let phase: metatheos_core::Phase = store
        .get_db()
        .select(("phase", day.phase_id.as_str()))
        .await
        .map_err(|e| e.to_string())?
        .ok_or("Phase not found")?;

    // Get day_goal links
    let mut day_goals_resp = store
        .get_db()
        .query("SELECT * FROM day_goal WHERE day_id = $day_id")
        .bind(("day_id", date.clone()))
        .await
        .map_err(|e| e.to_string())?;

    #[derive(serde::Deserialize)]
    #[allow(dead_code)]
    struct DayGoalDb {
        goal_id: String,
        required: bool,
    }

    let day_goals: Vec<DayGoalDb> = day_goals_resp.take(0).map_err(|e| e.to_string())?;
    let goal_ids: Vec<String> = day_goals.iter().map(|g| g.goal_id.clone()).collect();

    // Get goals
    let mut goals_vec = Vec::new();
    for goal_id in &goal_ids {
        if let Ok(Some(goal)) = store
            .get_db()
            .select::<Option<metatheos_core::Goal>>(("goal", goal_id.as_str()))
            .await
        {
            goals_vec.push(GoalDto::from(&goal));
        }
    }

    // Get work items for all goals
    let mut all_work_items = Vec::new();
    for goal_id in &goal_ids {
        if let Ok(items) = store.get_work_items_by_goal(goal_id).await {
            all_work_items.extend(items);
        }
    }

    // Get annotations for the day
    let annotations = store
        .get_annotations("day", &date)
        .await
        .unwrap_or_default();

    Ok(DayContextDto {
        day: DayDto {
            id: day.id,
            phase_id: day.phase_id,
            day_type: day.day_type.as_str().to_string(),
            created_at: day.created_at.to_rfc3339(),
        },
        phase: PhaseDto::from(&phase),
        goals: goals_vec,
        work_items: all_work_items,
        annotations,
    })
}

/// Get available goals for day wizard (filtered by phase and day type)
#[tauri::command]
pub async fn get_available_goals_for_day(
    state: State<'_, AppState>,
    phase_id: String,
    day_type: String,
) -> Result<Vec<GoalDto>, String> {
    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;

    let query = match day_type.to_lowercase().as_str() {
        "review" => {
            // Review day: only done or partial goals
            "SELECT * FROM goal WHERE phase_id = $phase_id AND status IN ['done', 'partial'] ORDER BY id"
        }
        "rest" => {
            // Rest day: no goals
            return Ok(Vec::new());
        }
        _ => {
            // Light/Heavy: open, active, planned, partial, or blocked goals
            "SELECT * FROM goal WHERE phase_id = $phase_id AND status IN ['open', 'active', 'planned', 'partial', 'blocked'] ORDER BY priority DESC, id"
        }
    };

    let mut resp = store
        .get_db()
        .query(query)
        .bind(("phase_id", phase_id))
        .await
        .map_err(|e| e.to_string())?;

    let goals: Vec<metatheos_core::Goal> = resp.take(0).map_err(|e| e.to_string())?;

    Ok(goals.iter().map(GoalDto::from).collect())
}

// ============================================================================
// TIMELINE VIEW COMMANDS - Read-only observational surface
// ============================================================================

/// Timeline item DTO - merges events and annotations into a chronological stream
#[derive(Debug, Serialize, Deserialize)]
pub struct TimelineItemDto {
    pub kind: String,      // "event" or "annotation"
    pub timestamp: String, // RFC3339 timestamp
    pub title: String,     // Summary for events, first line of content for annotations
    pub body: String,      // Empty for events (payload in title), full content for annotations
    pub entity_type: String,
    pub entity_id: String,
    pub author: Option<String>, // For annotations: "user" or "ai", for events: "user", "system", "ai"
}

/// Get timeline for a specific day (events + annotations)
#[tauri::command]
pub async fn get_timeline_for_day(
    state: State<'_, AppState>,
    day_id: String,
) -> Result<Vec<TimelineItemDto>, String> {
    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;

    let mut timeline_items = Vec::new();

    // Fetch events for this day
    let mut event_resp = store
        .get_db()
        .query("SELECT * FROM event WHERE entity_type = 'day' AND entity_id = $day_id ORDER BY created_at DESC")
        .bind(("day_id", day_id.clone()))
        .await
        .map_err(|e| e.to_string())?;

    let events: Vec<Event> = event_resp.take(0).map_err(|e| e.to_string())?;

    for event in events {
        let title = format!(
            "{} {} ({})",
            event.action.as_str(),
            event.entity_type,
            event.entity_id
        );
        timeline_items.push(TimelineItemDto {
            kind: "event".to_string(),
            timestamp: event.created_at.to_rfc3339(),
            title,
            body: event.payload.to_string(),
            entity_type: event.entity_type,
            entity_id: event.entity_id,
            author: Some(event.actor),
        });
    }

    // Fetch annotations for this day
    let annotations = store
        .get_annotations("day", &day_id)
        .await
        .map_err(|e| e.to_string())?;

    for annotation in annotations {
        let title = annotation
            .content
            .lines()
            .next()
            .unwrap_or("(no content)")
            .to_string();
        timeline_items.push(TimelineItemDto {
            kind: "annotation".to_string(),
            timestamp: annotation.created_at.to_rfc3339(),
            title,
            body: annotation.content,
            entity_type: annotation.entity_type.as_str().to_string(),
            entity_id: annotation.entity_id,
            author: Some(annotation.author_type.as_str().to_string()),
        });
    }

    // Sort by timestamp descending (newest first)
    timeline_items.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));

    Ok(timeline_items)
}

/// Get timeline for a specific goal (events + annotations)
#[tauri::command]
pub async fn get_timeline_for_goal(
    state: State<'_, AppState>,
    goal_id: String,
) -> Result<Vec<TimelineItemDto>, String> {
    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;

    let mut timeline_items = Vec::new();

    // Fetch events for this goal
    let mut event_resp = store
        .get_db()
        .query("SELECT * FROM event WHERE entity_type = 'goal' AND entity_id = $goal_id ORDER BY created_at DESC")
        .bind(("goal_id", goal_id.clone()))
        .await
        .map_err(|e| e.to_string())?;

    let events: Vec<Event> = event_resp.take(0).map_err(|e| e.to_string())?;

    for event in events {
        let title = format!(
            "{} {} ({})",
            event.action.as_str(),
            event.entity_type,
            event.entity_id
        );
        timeline_items.push(TimelineItemDto {
            kind: "event".to_string(),
            timestamp: event.created_at.to_rfc3339(),
            title,
            body: event.payload.to_string(),
            entity_type: event.entity_type,
            entity_id: event.entity_id,
            author: Some(event.actor),
        });
    }

    // Fetch annotations for this goal
    let annotations = store
        .get_annotations("goal", &goal_id)
        .await
        .map_err(|e| e.to_string())?;

    for annotation in annotations {
        let title = annotation
            .content
            .lines()
            .next()
            .unwrap_or("(no content)")
            .to_string();
        timeline_items.push(TimelineItemDto {
            kind: "annotation".to_string(),
            timestamp: annotation.created_at.to_rfc3339(),
            title,
            body: annotation.content,
            entity_type: annotation.entity_type.as_str().to_string(),
            entity_id: annotation.entity_id,
            author: Some(annotation.author_type.as_str().to_string()),
        });
    }

    // Sort by timestamp descending (newest first)
    timeline_items.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));

    Ok(timeline_items)
}

/// Get timeline for a specific work item (events + annotations)
#[tauri::command]
pub async fn get_timeline_for_work_item(
    state: State<'_, AppState>,
    work_item_id: String,
) -> Result<Vec<TimelineItemDto>, String> {
    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;

    let mut timeline_items = Vec::new();

    // Fetch events for this work item
    let mut event_resp = store
        .get_db()
        .query("SELECT * FROM event WHERE entity_type = 'work_item' AND entity_id = $work_item_id ORDER BY created_at DESC")
        .bind(("work_item_id", work_item_id.clone()))
        .await
        .map_err(|e| e.to_string())?;

    let events: Vec<Event> = event_resp.take(0).map_err(|e| e.to_string())?;

    for event in events {
        let title = format!(
            "{} {} ({})",
            event.action.as_str(),
            event.entity_type,
            event.entity_id
        );
        timeline_items.push(TimelineItemDto {
            kind: "event".to_string(),
            timestamp: event.created_at.to_rfc3339(),
            title,
            body: event.payload.to_string(),
            entity_type: event.entity_type,
            entity_id: event.entity_id,
            author: Some(event.actor),
        });
    }

    // Fetch annotations for this work item
    let annotations = store
        .get_annotations("work_item", &work_item_id)
        .await
        .map_err(|e| e.to_string())?;

    for annotation in annotations {
        let title = annotation
            .content
            .lines()
            .next()
            .unwrap_or("(no content)")
            .to_string();
        timeline_items.push(TimelineItemDto {
            kind: "annotation".to_string(),
            timestamp: annotation.created_at.to_rfc3339(),
            title,
            body: annotation.content,
            entity_type: annotation.entity_type.as_str().to_string(),
            entity_id: annotation.entity_id,
            author: Some(annotation.author_type.as_str().to_string()),
        });
    }

    // Sort by timestamp descending (newest first)
    timeline_items.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));

    Ok(timeline_items)
}

/// Get timeline for a specific phase (events + annotations)
#[tauri::command]
pub async fn get_timeline_for_phase(
    state: State<'_, AppState>,
    phase_id: String,
) -> Result<Vec<TimelineItemDto>, String> {
    let store_option = {
        let db_guard = state.db.lock().map_err(|e| e.to_string())?;
        db_guard.as_ref().map(|s| s.clone())
    };
    let store = store_option.ok_or("Store not initialized")?;

    let mut timeline_items = Vec::new();

    // Fetch events for this phase
    let mut event_resp = store
        .get_db()
        .query("SELECT * FROM event WHERE entity_type = 'phase' AND entity_id = $phase_id ORDER BY created_at DESC")
        .bind(("phase_id", phase_id.clone()))
        .await
        .map_err(|e| e.to_string())?;

    let events: Vec<Event> = event_resp.take(0).map_err(|e| e.to_string())?;

    for event in events {
        let title = format!(
            "{} {} ({})",
            event.action.as_str(),
            event.entity_type,
            event.entity_id
        );
        timeline_items.push(TimelineItemDto {
            kind: "event".to_string(),
            timestamp: event.created_at.to_rfc3339(),
            title,
            body: event.payload.to_string(),
            entity_type: event.entity_type,
            entity_id: event.entity_id,
            author: Some(event.actor),
        });
    }

    // Fetch annotations for this phase
    let annotations = store
        .get_annotations("phase", &phase_id)
        .await
        .map_err(|e| e.to_string())?;

    for annotation in annotations {
        let title = annotation
            .content
            .lines()
            .next()
            .unwrap_or("(no content)")
            .to_string();
        timeline_items.push(TimelineItemDto {
            kind: "annotation".to_string(),
            timestamp: annotation.created_at.to_rfc3339(),
            title,
            body: annotation.content,
            entity_type: annotation.entity_type.as_str().to_string(),
            entity_id: annotation.entity_id,
            author: Some(annotation.author_type.as_str().to_string()),
        });
    }

    // Sort by timestamp descending (newest first)
    timeline_items.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));

    Ok(timeline_items)
}
