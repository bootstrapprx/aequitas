use crate::domain::*;
use crate::errors::{MetaError, Result};
use crate::parser::LinkExtractor;
use chrono::{Duration, Local, NaiveDate};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::SystemTime;
use walkdir::WalkDir;

#[derive(Debug, Clone)]
pub struct CanonDoc {
    pub title: String,
    pub file_path: PathBuf,
}

#[derive(Debug, Clone)]
pub struct ProtocolDoc {
    pub title: String,
    pub file_path: PathBuf,
}

#[derive(Debug, Clone)]
pub struct GovernanceState {
    pub phases: Vec<Phase>,
    pub goals: Vec<Goal>,
    pub decisions: Vec<Decision>,
    pub daily_notes: Vec<DailyNote>,
    pub audits: Vec<AuditRecord>,
    pub prompts: Vec<Prompt>,
    pub canon_docs: Vec<CanonDoc>,
    pub protocols: Vec<ProtocolDoc>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct ReadOnlyPhase {
    pub id: String,
    pub title: String,
    pub start_date: Option<String>,
    pub target_date: Option<String>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct ReadOnlyGoal {
    pub id: String,
    pub title: String,
    pub status: String,
    pub phase: Option<String>,
    pub parent_id: Option<String>,
    pub is_blocked: bool,
    pub level: Option<String>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct ReadOnlyGovernanceContext {
    pub date: String,
    pub active_phase: Option<ReadOnlyPhase>,
    pub active_goals: Vec<ReadOnlyGoal>,
    pub blocked_goals: Vec<ReadOnlyGoal>,
    pub recent_work: Vec<String>,
}

pub use GovernanceWarningKind::*; // Re-export warning kind if used externally usually but not needed here

/// Phase is the canonical scope root for all governance state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GovernanceWarningKind {
    MissingDailyNote,
    GoalMissingPhase,
    GoalMissingStatus,
    GoalMissingRecentDaily,
    DecisionUnlinked,
    PhaseWithoutActiveGoals,
}

#[derive(Debug, Clone)]
pub struct GovernanceWarning {
    pub kind: GovernanceWarningKind,
    pub message: String,
    pub related: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct DependencyGap {
    pub goal_id: String,
    pub missing: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct GoalRelations {
    pub goal: Goal,
    pub decisions: Vec<Decision>,
    pub audits: Vec<AuditRecord>,
    pub daily_refs: Vec<DailyNote>,
    pub missing_dependencies: Vec<String>,
    pub out_of_phase: bool,
}

#[derive(Debug, Clone)]
pub struct DailyContext {
    pub date: NaiveDate,
    pub note: Option<DailyNote>,
    pub active_phase: Option<Phase>,
    pub phase_defined: bool,
    pub in_phase_goals: Vec<Goal>,
    pub out_of_phase_goals: Vec<Goal>,
    pub goal_relations: HashMap<String, GoalRelations>,
    pub recent_decisions: Vec<Decision>,
    pub linked_decisions: Vec<Decision>,
    pub linked_audits: Vec<AuditRecord>,
    pub blocked_goals: Vec<Goal>,
    pub dependency_gaps: Vec<DependencyGap>,
    pub active_goal_count: usize,
    pub blocked_goal_count: usize,
}

#[derive(Debug, Clone)]
pub struct PhaseGoalBreakdown {
    pub phase: Phase,
    pub active_goals: Vec<Goal>,
}

#[derive(Debug, Clone)]
pub struct GovernanceSummary {
    pub current_phase: Option<Phase>,
    pub active_goals: Vec<Goal>,
    pub blocked_goals: Vec<Goal>,
    pub total_goals: usize,
    pub today_exists: bool,
    pub today_path: PathBuf,
    pub today_mode: Option<String>,
    pub today_goals: Vec<String>,
    pub today_blockers: Vec<String>,
    pub today_decisions: Vec<String>,
    pub today_divergences: Vec<String>,
    pub latest_daily: Option<DailyNote>,
    pub recent_decisions: Vec<Decision>,
    pub canon_docs: Vec<CanonDoc>,
    pub protocols: Vec<ProtocolDoc>,
    pub active_by_phase: Vec<PhaseGoalBreakdown>,
    pub orphaned_goals: Vec<Goal>,
    pub stale_goals: Vec<Goal>,
    pub top_blocked: Vec<Goal>,
    pub warnings: Vec<GovernanceWarning>,
}

#[derive(Debug, Clone)]
pub struct PhaseMetrics {
    pub phase_id: Option<String>,
    pub total_goals: usize,
    pub active: usize,
    pub blocked: usize,
    pub done: usize,
    pub completion_pct: f64,
}

#[derive(Debug, Clone)]
pub struct PhaseScope {
    pub active_phase: Option<Phase>,
    pub goals: Vec<Goal>,
    pub metrics: PhaseMetrics,
    pub phase_defined: bool,
}

impl std::fmt::Display for GovernanceWarningKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let label = match self {
            GovernanceWarningKind::MissingDailyNote => "missing_daily_note",
            GovernanceWarningKind::GoalMissingPhase => "goal_missing_phase",
            GovernanceWarningKind::GoalMissingStatus => "goal_missing_status",
            GovernanceWarningKind::GoalMissingRecentDaily => "goal_missing_recent_daily",
            GovernanceWarningKind::DecisionUnlinked => "decision_unlinked",
            GovernanceWarningKind::PhaseWithoutActiveGoals => "phase_without_active_goals",
        };
        write!(f, "{}", label)
    }
}

pub struct GovernanceScanner {
    pub root: PathBuf,
}

impl GovernanceScanner {
    pub fn new<P: AsRef<Path>>(root: P) -> Self {
        Self {
            root: root.as_ref().to_path_buf(),
        }
    }

    // NOTE: scan() removed - use from_store() instead (DB-only architecture)

    // NOTE: scan_markdown() removed - DB is source of truth for entities

    fn scan_canon(&self) -> Result<Vec<CanonDoc>> {
        let canon_root = self.root.join("canon");
        if !canon_root.exists() {
            return Ok(Vec::new());
        }

        let mut docs = Vec::new();
        for entry in WalkDir::new(&canon_root)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.path().is_file())
        {
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) != Some("md") {
                continue;
            }
            let title = path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or_default()
                .replace('_', " ");
            docs.push(CanonDoc {
                title,
                file_path: path.to_path_buf(),
            });
        }

        Ok(docs)
    }

    fn scan_protocols(&self) -> Result<Vec<ProtocolDoc>> {
        let master_root = self.root.join("00_MASTER");
        if !master_root.exists() {
            return Ok(Vec::new());
        }

        let mut docs = Vec::new();
        for entry in WalkDir::new(&master_root)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.path().is_file())
        {
            let path = entry.path();
            let name = path
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or_default();
            if !name.to_ascii_uppercase().contains("PROTOCOL") {
                continue;
            }
            if path.extension().and_then(|s| s.to_str()) != Some("md") {
                continue;
            }

            let title = path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or_default()
                .replace('_', " ");
            docs.push(ProtocolDoc {
                title,
                file_path: path.to_path_buf(),
            });
        }

        Ok(docs)
    }
}

/// Main governance context - loads and manages all governance data
pub struct GovernanceContext {
    pub root: PathBuf,
    pub state: GovernanceState,
    goals_index: HashMap<String, usize>,
    decisions_index: HashMap<String, usize>,
}

impl GovernanceContext {
    /// DEPRECATED: Sync wrapper causes tokio runtime panic when called from async context.
    /// Use `load_async()` or `from_store()` instead.
    ///
    /// This method is kept ONLY for CLI usage where we're not in an async context.
    /// For Tauri commands (async), use `load_async()`.
    #[deprecated(since = "2.1.0", note = "Use `load_async()` to avoid runtime panic")]
    pub fn load<P: AsRef<Path>>(root: P) -> Result<Self> {
        let root_path = root.as_ref().to_path_buf();
        let db_path = root_path.join(".metatheos.db");

        // Create a new runtime ONLY if we're not already in one
        // This is safe only for CLI usage
        let rt = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .map_err(|e| crate::errors::MetaError::SystemError(format!("Runtime error: {}", e)))?;

        rt.block_on(async {
            let store = crate::store::SurrealStore::init(db_path).await?;
            Self::from_store(&store, root_path).await
        })
    }

    /// Async load method - safe to call from Tauri commands and other async contexts
    /// This is the RECOMMENDED method for all new code.
    pub async fn load_async<P: AsRef<Path>>(root: P) -> Result<Self> {
        let root_path = root.as_ref().to_path_buf();
        let db_path = root_path.join(".metatheos.db");

        let store = crate::store::SurrealStore::init(db_path).await?;
        Self::from_store(&store, root_path).await
    }

    /// Load context from SurrealStore (hybrid DB + FS for Canon/Protocols)
    pub async fn from_store(store: &crate::store::SurrealStore, root: PathBuf) -> Result<Self> {
        // Fetch DB data with graceful degradation - deserialization errors should not crash UI
        let goals = match store.get_all_goals().await {
            Ok(data) => data,
            Err(e) => {
                eprintln!("GovernanceContext: failed to load goals from DB: {}", e);
                Vec::new()
            }
        };
        let phases = match store.get_all_phases().await {
            Ok(data) => data,
            Err(e) => {
                eprintln!("GovernanceContext: failed to load phases from DB: {}", e);
                Vec::new()
            }
        };
        let decisions = match store.get_all_decisions().await {
            Ok(data) => data,
            Err(e) => {
                eprintln!("GovernanceContext: failed to load decisions from DB: {}", e);
                Vec::new()
            }
        };
        let audits = match store.get_all_audits().await {
            Ok(data) => data,
            Err(e) => {
                eprintln!("GovernanceContext: failed to load audits from DB: {}", e);
                Vec::new()
            }
        };
        let prompts = match store.get_all_prompts().await {
            Ok(data) => data,
            Err(e) => {
                eprintln!("GovernanceContext: failed to load prompts from DB: {}", e);
                Vec::new()
            }
        };
        let daily_notes = match store.get_all_daily_notes().await {
            Ok(data) => data,
            Err(e) => {
                eprintln!(
                    "GovernanceContext: failed to load daily notes from DB: {}",
                    e
                );
                Vec::new()
            }
        };

        // Fetch FS data (Canon + Protocols) via Scanner
        let scanner = GovernanceScanner::new(&root);
        let canon_docs = scanner.scan_canon()?;
        let protocols = scanner.scan_protocols()?;

        let state = GovernanceState {
            goals,
            phases,
            decisions,
            audits,
            prompts,
            daily_notes,
            canon_docs,
            protocols,
        };

        let mut ctx = Self {
            root,
            state,
            goals_index: HashMap::new(),
            decisions_index: HashMap::new(),
        };

        ctx.build_indexes();
        Ok(ctx)
    }

    fn build_indexes(&mut self) {
        for (idx, goal) in self.state.goals.iter().enumerate() {
            self.goals_index.insert(goal.goal_id.to_lowercase(), idx);
        }

        for (idx, decision) in self.state.decisions.iter().enumerate() {
            self.decisions_index
                .insert(decision.decision_id.to_lowercase(), idx);
        }
    }

    fn normalize_id(value: &str) -> String {
        value.trim().to_lowercase()
    }

    fn goal_match(link: &str, goal_id: &str) -> bool {
        let link_norm = Self::normalize_id(link);
        let goal_norm = Self::normalize_id(goal_id);
        link_norm.contains(&goal_norm) || goal_norm.contains(&link_norm)
    }

    fn decision_match(link: &str, decision_id: &str) -> bool {
        let link_norm = Self::normalize_id(link);
        let dec_norm = Self::normalize_id(decision_id);
        link_norm.contains(&dec_norm) || dec_norm.contains(&link_norm)
    }

    fn resolve_goal_phase_with_seen(
        &self,
        goal: &Goal,
        seen: &mut HashSet<String>,
    ) -> Option<String> {
        if let Some(phase) = goal.phase.as_ref().filter(|p| !p.trim().is_empty()) {
            return Some(phase.clone());
        }

        if let Some(parent_id) = &goal.parent_id {
            let key = parent_id.to_lowercase();
            if !seen.insert(key) {
                // Prevent cycles
                return None;
            }
            if let Some(parent) = self.get_goal(parent_id) {
                return self.resolve_goal_phase_with_seen(parent, seen);
            }
        }

        None
    }

    pub fn resolve_goal_phase(&self, goal: &Goal) -> Option<String> {
        let mut seen = HashSet::new();
        self.resolve_goal_phase_with_seen(goal, &mut seen)
    }

    pub fn goal_with_effective_phase(&self, goal: &Goal) -> Goal {
        let mut cloned = goal.clone();
        cloned.phase = self.resolve_goal_phase(goal);
        cloned
    }

    #[allow(dead_code)]
    fn resolve_goal_links(&self, link: &str) -> Option<Goal> {
        self.state
            .goals
            .iter()
            .find(|g| Self::goal_match(link, &g.goal_id))
            .cloned()
    }

    fn resolve_decision_links(&self, link: &str) -> Option<Decision> {
        self.state
            .decisions
            .iter()
            .find(|d| Self::decision_match(link, &d.decision_id))
            .cloned()
    }

    fn goal_relations_map(&self, active_phase: Option<&str>) -> HashMap<String, GoalRelations> {
        let mut map = HashMap::new();

        for goal in &self.state.goals {
            let goal_with_phase = self.goal_with_effective_phase(goal);
            let mut decisions = Vec::new();
            let mut audits = Vec::new();
            let mut daily_refs = Vec::new();

            for link in LinkExtractor::extract_decision_links(&goal_with_phase.content) {
                if let Some(decision) = self.resolve_decision_links(&link) {
                    if !decisions.iter().any(|d: &Decision| {
                        d.decision_id.eq_ignore_ascii_case(&decision.decision_id)
                    }) {
                        decisions.push(decision);
                    }
                }
            }

            for decision in &self.state.decisions {
                let goal_links = LinkExtractor::extract_goal_links(&decision.content);
                if goal_links
                    .iter()
                    .any(|link| Self::goal_match(link, &goal_with_phase.goal_id))
                {
                    if !decisions
                        .iter()
                        .any(|d| d.decision_id.eq_ignore_ascii_case(&decision.decision_id))
                    {
                        decisions.push(decision.clone());
                    }
                }
            }

            for audit in &self.state.audits {
                let goal_links = LinkExtractor::extract_goal_links(&audit.content);
                if goal_links
                    .iter()
                    .any(|link| Self::goal_match(link, &goal_with_phase.goal_id))
                {
                    if !audits
                        .iter()
                        .any(|a: &AuditRecord| a.file_path == audit.file_path)
                    {
                        audits.push(audit.clone());
                    }
                }
            }

            for daily in &self.state.daily_notes {
                let linked = daily
                    .linked_goals
                    .iter()
                    .any(|g| Self::goal_match(g, &goal_with_phase.goal_id));
                let in_frontmatter = daily
                    .goals
                    .iter()
                    .any(|g| Self::goal_match(g, &goal_with_phase.goal_id))
                    || daily
                        .goals_worked
                        .iter()
                        .any(|g| Self::goal_match(g, &goal_with_phase.goal_id));
                if linked || in_frontmatter {
                    if !daily_refs.iter().any(|d: &DailyNote| d.date == daily.date) {
                        daily_refs.push(daily.clone());
                    }
                }
            }

            let missing_dependencies: Vec<String> = goal_with_phase
                .dependencies
                .iter()
                .filter(|dep| self.get_goal(dep).is_none())
                .cloned()
                .collect();

            let mut is_in_phase = false;
            if let Some(active) = active_phase {
                // 1. Direct phase match
                if let Some(p) = &goal_with_phase.phase {
                    if p.eq_ignore_ascii_case(active) {
                        is_in_phase = true;
                    }
                }
                // 2. Hierarchy Check
                if !is_in_phase {
                    let mut current = &goal_with_phase;
                    while let Some(parent_id) = &current.parent_id {
                        let mut found_parent = None;
                        for pg in &self.state.goals {
                            if pg.goal_id == *parent_id {
                                found_parent = Some(pg);
                                break;
                            }
                        }
                        if let Some(parent) = found_parent {
                            if let Some(pp) = &parent.phase {
                                if pp.eq_ignore_ascii_case(active) {
                                    is_in_phase = true;
                                    break;
                                }
                            }
                            current = parent;
                        } else {
                            break;
                        }
                    }
                }
            } else {
                is_in_phase = true;
            }

            let out_of_phase = !is_in_phase;

            map.insert(
                goal_with_phase.goal_id.to_lowercase(),
                GoalRelations {
                    goal: goal_with_phase,
                    decisions,
                    audits,
                    daily_refs,
                    missing_dependencies,
                    out_of_phase,
                },
            );
        }

        map
    }

    pub fn get_goal(&self, id: &str) -> Option<&Goal> {
        self.goals_index
            .get(&id.to_lowercase())
            .and_then(|idx| self.state.goals.get(*idx))
    }

    pub fn get_decision(&self, id: &str) -> Option<&Decision> {
        self.decisions_index
            .get(&id.to_lowercase())
            .and_then(|idx| self.state.decisions.get(*idx))
    }

    pub fn all_goals(&self) -> Vec<&Goal> {
        self.state.goals.iter().collect()
    }

    pub fn all_decisions(&self) -> Vec<&Decision> {
        self.state.decisions.iter().collect()
    }

    pub fn all_phases(&self) -> Vec<&Phase> {
        self.state.phases.iter().collect()
    }

    pub fn all_audits(&self) -> Vec<&AuditRecord> {
        self.state.audits.iter().collect()
    }

    pub fn all_daily_notes(&self) -> Vec<DailyNote> {
        self.state.daily_notes.clone()
    }

    pub fn goals_by_phase(&self) -> HashMap<String, Vec<Goal>> {
        let mut grouped: HashMap<String, Vec<Goal>> = HashMap::new();
        for goal in &self.state.goals {
            if let Some(phase) = goal.phase.as_ref() {
                grouped
                    .entry(phase.to_string())
                    .or_default()
                    .push(goal.clone());
            } else {
                grouped
                    .entry("".to_string())
                    .or_default()
                    .push(goal.clone());
            }
        }
        grouped
    }

    pub fn orphaned_goals(&self) -> Vec<Goal> {
        self.state
            .goals
            .iter()
            .filter(|g| {
                g.phase.is_none()
                    || g.phase
                        .as_ref()
                        .map(|p| p.trim().is_empty())
                        .unwrap_or(true)
            })
            .cloned()
            .collect()
    }

    pub fn stale_goals(&self, stale_after_days: i64) -> Vec<Goal> {
        let cutoff = Local::now().naive_local().date() - Duration::days(stale_after_days);

        let mut stale: Vec<Goal> = self
            .state
            .goals
            .iter()
            .filter(|g| {
                if let Some(updated) = g.updated {
                    updated < cutoff
                } else {
                    true
                }
            })
            .cloned()
            .collect();

        stale.sort_by(|a, b| a.goal_id.cmp(&b.goal_id));
        stale
    }

    pub fn count_files(&self) -> usize {
        self.state.goals.len()
            + self.state.decisions.len()
            + self.state.daily_notes.len()
            + self.state.phases.len()
    }

    pub fn active_phase(&self) -> Option<Phase> {
        self.resolve_active_phase(chrono::Local::now().date_naive(), None)
    }

    pub fn resolve_active_phase(
        &self,
        date: NaiveDate,
        explicit_phase_id: Option<&str>,
    ) -> Option<Phase> {
        // 0. Use explicit phase ID if provided and valid
        if let Some(phase_id) = explicit_phase_id {
            if let Some(phase) = self.state.phases.iter().find(|p| p.phase_id == phase_id) {
                return Some(phase.clone());
            }
        }

        // 1. Try to find a phase that strictly covers this date
        let date_match = self
            .state
            .phases
            .iter()
            .find(|p| {
                if let (Some(start), Some(target)) = (p.start_date, p.target_date) {
                    date >= start && date <= target
                } else {
                    false
                }
            })
            .cloned();

        if date_match.is_some() {
            return date_match;
        }

        // 2. Fallback: Priority checking
        fn phase_priority(status: &str) -> u8 {
            let s = status.to_lowercase();
            if s.contains("active") || s.contains("in-progress") {
                0
            } else if s.contains("partial") {
                1
            } else if s.contains("planned") {
                2
            } else if s.contains("done") || s.contains("completed") {
                3
            } else if s.contains("archived") || s.contains("inactive") {
                4
            } else {
                5
            }
        }

        let mut phases = self.state.phases.clone();
        phases.sort_by(|a, b| {
            phase_priority(&a.status)
                .cmp(&phase_priority(&b.status))
                .then_with(|| Self::mtime(&b.file_path).cmp(&Self::mtime(&a.file_path)))
                .then_with(|| b.number().cmp(&a.number()))
        });
        phases.into_iter().next()
    }

    pub fn phase_scope(&self, date: NaiveDate, explicit_phase_id: Option<&str>) -> PhaseScope {
        let active_phase = self.resolve_active_phase(date, explicit_phase_id);
        let active_phase_id = active_phase.as_ref().map(|p| p.phase_id.clone());

        let goals_with_phase: Vec<Goal> = self
            .state
            .goals
            .iter()
            .map(|g| self.goal_with_effective_phase(g))
            .collect();

        let phase_goals: Vec<Goal> = goals_with_phase
            .iter()
            .cloned()
            .filter(|g| {
                active_phase_id
                    .as_ref()
                    .map(|pid| {
                        g.phase
                            .as_ref()
                            .map(|p| p.eq_ignore_ascii_case(pid))
                            .unwrap_or(false)
                    })
                    .unwrap_or(false)
            })
            .collect();

        let total_goals = phase_goals.len();
        let active = phase_goals.iter().filter(|g| g.is_active()).count();
        let blocked = phase_goals.iter().filter(|g| g.is_blocked()).count();
        let done = phase_goals.iter().filter(|g| g.is_done()).count();

        let metrics = PhaseMetrics {
            phase_id: active_phase_id.clone(),
            total_goals,
            active,
            blocked,
            done,
            completion_pct: if total_goals > 0 {
                (done as f64 / total_goals as f64) * 100.0
            } else {
                0.0
            },
        };

        PhaseScope {
            active_phase,
            goals: phase_goals,
            metrics,
            phase_defined: active_phase_id.is_some(),
        }
    }

    pub fn active_goals(&self) -> Vec<Goal> {
        let scope = self.phase_scope(chrono::Local::now().date_naive(), None);
        let mut goals: Vec<Goal> = scope
            .goals
            .iter()
            .filter(|g| g.is_active())
            .cloned()
            .collect();

        goals.sort_by(|a, b| b.updated.cmp(&a.updated));
        goals
    }

    pub fn blocked_goals(&self) -> Vec<Goal> {
        let scope = self.phase_scope(chrono::Local::now().date_naive(), None);
        let mut goals: Vec<Goal> = scope
            .goals
            .iter()
            .filter(|g| g.is_blocked())
            .cloned()
            .collect();
        goals.sort_by(|a, b| b.updated.cmp(&a.updated));
        goals
    }

    pub fn decisions_within_days(&self, days: i64) -> Vec<Decision> {
        let cutoff = Local::now().naive_local().date() - Duration::days(days);
        let mut decisions: Vec<Decision> = self
            .state
            .decisions
            .iter()
            .filter(|d| {
                let relevant_date = d.updated.or(d.date);
                relevant_date.map(|dt| dt >= cutoff).unwrap_or(true)
            })
            .cloned()
            .collect();
        decisions.sort_by(|a, b| {
            let a_date = a.updated.or(a.date);
            let b_date = b.updated.or(b.date);
            b_date.cmp(&a_date).then_with(|| {
                Self::mtime(b.file_path.as_path()).cmp(&Self::mtime(a.file_path.as_path()))
            })
        });
        decisions
    }

    pub fn daily_context(&self, date: NaiveDate) -> DailyContext {
        let note = self.get_daily(date);

        // Allow the daily note to pin a phase; otherwise fall back to the inferred active phase
        // Default to phase active on that date
        // Resolve active phase (Explicit > Date > Priority)
        let phase_override = note.as_ref().and_then(|n| n.phase.as_deref());
        let scope = self.phase_scope(date, phase_override);
        let active_phase = scope.active_phase.clone();
        let active_phase_id = scope.active_phase.as_ref().map(|p| p.phase_id.clone());

        // Work with phase-resolved goals so children inherit their parent's phase
        let goals_with_phase: Vec<Goal> = self
            .state
            .goals
            .iter()
            .map(|g| self.goal_with_effective_phase(g))
            .collect();

        let relations = if scope.phase_defined {
            self.goal_relations_map(active_phase_id.as_deref())
        } else {
            HashMap::new()
        };
        let mut in_phase_goals = Vec::new();
        let mut out_of_phase_goals = Vec::new();

        if let Some(active) = active_phase_id.as_deref() {
            for g in &goals_with_phase {
                let mut is_in_phase = false;
                if let Some(p) = &g.phase {
                    if p.eq_ignore_ascii_case(active) {
                        is_in_phase = true;
                    }
                }
                if !is_in_phase {
                    let mut current = g;
                    while let Some(parent_id) = &current.parent_id {
                        if let Some(parent) =
                            goals_with_phase.iter().find(|pg| pg.goal_id == *parent_id)
                        {
                            if let Some(pp) = &parent.phase {
                                if pp.eq_ignore_ascii_case(active) {
                                    is_in_phase = true;
                                    break;
                                }
                            }
                            current = parent;
                        } else {
                            break;
                        }
                    }
                }

                if is_in_phase {
                    in_phase_goals.push(g.clone());
                } else {
                    out_of_phase_goals.push(g.clone());
                }
            }
        }

        let selected_goals: Vec<String> = note
            .as_ref()
            .map(|n| {
                if n.goals.is_empty() {
                    n.linked_goals.clone()
                } else {
                    n.goals.clone()
                }
            })
            .unwrap_or_default();

        let mut linked_decisions = Vec::new();
        let mut linked_audits = Vec::new();
        let mut dependency_gaps = Vec::new();

        for goal_id in &selected_goals {
            if let Some(rel) = relations.get(&goal_id.to_lowercase()).cloned() {
                for decision in rel.decisions {
                    if !linked_decisions.iter().any(|d: &Decision| {
                        d.decision_id.eq_ignore_ascii_case(&decision.decision_id)
                    }) {
                        linked_decisions.push(decision);
                    }
                }
                for audit in rel.audits {
                    if !linked_audits.iter().any(|a: &AuditRecord| {
                        a.title == audit.title && a.file_path == audit.file_path
                    }) {
                        linked_audits.push(audit);
                    }
                }
                if !rel.missing_dependencies.is_empty() {
                    dependency_gaps.push(DependencyGap {
                        goal_id: rel.goal.goal_id.clone(),
                        missing: rel.missing_dependencies.clone(),
                    });
                }
            }
        }

        DailyContext {
            date,
            note,
            active_phase,
            phase_defined: scope.phase_defined,
            in_phase_goals,
            out_of_phase_goals,
            goal_relations: relations,
            recent_decisions: self.decisions_within_days(30),
            linked_decisions,
            linked_audits,
            blocked_goals: scope
                .goals
                .iter()
                .filter(|g| g.is_blocked())
                .cloned()
                .collect(),
            dependency_gaps,
            active_goal_count: scope.metrics.active,
            blocked_goal_count: scope.metrics.blocked,
        }
    }

    pub fn get_read_only_context(&self, date: NaiveDate) -> ReadOnlyGovernanceContext {
        let ctx = self.daily_context(date);

        ReadOnlyGovernanceContext {
            date: ctx.date.to_string(),
            active_phase: ctx.active_phase.map(|p| ReadOnlyPhase {
                id: p.phase_id,
                title: p.title,
                start_date: p.start_date.map(|d| d.to_string()),
                target_date: p.target_date.map(|d| d.to_string()),
            }),
            active_goals: ctx
                .in_phase_goals
                .iter()
                .map(|g| ReadOnlyGoal {
                    id: g.goal_id.clone(),
                    title: g.title.clone(),
                    status: g.status.to_string(),
                    phase: g.phase.clone(),
                    parent_id: g.parent_id.clone(),
                    is_blocked: g.is_blocked(),
                    level: g.level.clone(),
                })
                .collect(),
            blocked_goals: ctx
                .blocked_goals
                .iter()
                .map(|g| ReadOnlyGoal {
                    id: g.goal_id.clone(),
                    title: g.title.clone(),
                    status: g.status.to_string(),
                    phase: g.phase.clone(),
                    parent_id: g.parent_id.clone(),
                    is_blocked: true,
                    level: g.level.clone(),
                })
                .collect(),
            recent_work: ctx.note.map(|n| n.goals_worked).unwrap_or_default(),
        }
    }

    pub fn summary(&self) -> GovernanceSummary {
        let today = Local::now().naive_local().date();
        let today_path = self
            .root
            .join("01_DAILY")
            .join(DailyNote::file_name(&today));
        let today_exists = today_path.exists();
        let today_mode = self
            .state
            .daily_notes
            .iter()
            .find(|d| d.date == today)
            .and_then(|d| d.mode.clone());
        let today_goals = self
            .state
            .daily_notes
            .iter()
            .find(|d| d.date == today)
            .map(|d| d.goals.clone())
            .unwrap_or_default();
        let today_blockers = self
            .state
            .daily_notes
            .iter()
            .find(|d| d.date == today)
            .map(|d| d.blockers.clone())
            .unwrap_or_default();
        let today_decisions = self
            .state
            .daily_notes
            .iter()
            .find(|d| d.date == today)
            .map(|d| d.decisions.clone())
            .unwrap_or_default();
        let today_divergences = self
            .state
            .daily_notes
            .iter()
            .find(|d| d.date == today)
            .map(|d| d.divergences.clone())
            .unwrap_or_default();

        let scope = self.phase_scope(today, None);
        let current_phase = scope.active_phase.clone();
        let recent_decisions = self.recent_decisions(5);
        let warnings = self.compute_warnings();
        let mut canon_docs = self.state.canon_docs.clone();
        canon_docs.sort_by(|a, b| a.title.cmp(&b.title));
        let mut protocols = self.state.protocols.clone();
        protocols.sort_by(|a, b| a.title.cmp(&b.title));

        let mut active_by_phase: Vec<PhaseGoalBreakdown> = Vec::new();
        if let Some(phase) = &scope.active_phase {
            let active_goals: Vec<Goal> = scope
                .goals
                .iter()
                .filter(|g| g.is_active())
                .cloned()
                .collect();
            active_by_phase.push(PhaseGoalBreakdown {
                phase: phase.clone(),
                active_goals,
            });
        }

        let mut blocked_top = self.blocked_goals();
        blocked_top.truncate(3);

        let latest_daily = self
            .state
            .daily_notes
            .iter()
            .max_by(|a, b| a.date.cmp(&b.date))
            .cloned();

        GovernanceSummary {
            current_phase,
            active_goals: self.active_goals(),
            blocked_goals: self.blocked_goals(),
            total_goals: scope.metrics.total_goals,
            today_exists,
            today_path,
            today_mode,
            today_goals,
            today_blockers,
            today_decisions,
            today_divergences,
            latest_daily,
            recent_decisions,
            canon_docs,
            protocols,
            active_by_phase,
            orphaned_goals: self.orphaned_goals(),
            stale_goals: self.stale_goals(30),
            top_blocked: blocked_top,
            warnings,
        }
    }

    pub fn recent_decisions(&self, count: usize) -> Vec<Decision> {
        let mut decisions = self.state.decisions.clone();
        decisions.sort_by(|a, b| {
            let a_date = a.updated.or(a.date);
            let b_date = b.updated.or(b.date);
            b_date.cmp(&a_date).then_with(|| {
                Self::mtime(b.file_path.as_path()).cmp(&Self::mtime(a.file_path.as_path()))
            })
        });
        decisions.into_iter().take(count).collect()
    }

    pub fn ensure_daily_note(&self, date: NaiveDate) -> Result<PathBuf> {
        let daily_dir = self.root.join("01_DAILY");
        if !daily_dir.exists() {
            fs::create_dir_all(&daily_dir)?;
        }

        let filename = DailyNote::file_name(&date);
        let file_path = daily_dir.join(&filename);
        if file_path.exists() {
            return Ok(file_path);
        }

        let template = format!(
            r#"---
type: daily
date: {}
phase:
mode:
protocol:
goals: []
blockers: []
decisions: []
agent:
updated:
---

# Daily Focus ({})

## Daily Context
- Mode:
- Focus Axis:
- Calendar Reference: [[CALENDAR]]
- Protocol: [[LIGHT_DAY_PROTOCOL]] / [[HEAVY_DAY_PROTOCOL]] / [[REVIEW_DAY_PROTOCOL]]

## Today’s intended goal(s)
- Link 1–3 goal notes: [[GOAL — …]]
- If none, link [[Aequitas Roadmap Master]]

## Blockers & Unknowns
- Bullet list
- Each blocker gets a link to a GOAL or an AUDIT note

## Decisions made today
- Link or create [[DECISION — {} — …]]

## Evidence / Verification
- What was verified (tests, screenshots, queries, etc.)

## Next actions (tomorrow seed)
- [ ] tasks
"#,
            date.format("%Y-%m-%d"),
            date.format("%Y-%m-%d"),
            date.format("%Y-%m-%d")
        );

        fs::write(&file_path, template)?;
        Ok(file_path)
    }

    pub fn set_daily_mode(&self, date: NaiveDate, mode: Option<String>) -> Result<PathBuf> {
        let path = self.ensure_daily_note(date)?;
        let content = fs::read_to_string(&path)?;
        let (mut frontmatter, body) =
            crate::parser::frontmatter::FrontmatterParser::parse(&content)?;
        if let Some(mode_value) = mode {
            frontmatter.insert("mode".to_string(), serde_json::Value::String(mode_value));
        } else {
            frontmatter.remove("mode");
        }

        let updated_frontmatter = serde_yaml::to_string(&frontmatter).map_err(MetaError::Yaml)?;
        let new_content = format!("---\n{}---\n\n{}", updated_frontmatter, body);
        fs::write(&path, new_content)?;

        Ok(path)
    }

    pub fn update_daily(
        &self,
        date: NaiveDate,
        mode: Option<String>,
        protocol: Option<String>,
        goals: Option<Vec<String>>,
        blockers: Option<Vec<String>>,
        decisions: Option<Vec<String>>,
        divergences: Option<Vec<String>>,
        content_override: Option<String>,
    ) -> Result<PathBuf> {
        let path = self.ensure_daily_note(date)?;
        let content = fs::read_to_string(&path)?;
        let (mut frontmatter, body) =
            crate::parser::frontmatter::FrontmatterParser::parse(&content)?;

        if let Some(mode_value) = mode {
            if mode_value.is_empty() {
                frontmatter.remove("mode");
            } else {
                frontmatter.insert("mode".to_string(), serde_json::Value::String(mode_value));
            }
        }

        if let Some(protocol_value) = protocol {
            if protocol_value.is_empty() {
                frontmatter.remove("protocol");
            } else {
                frontmatter.insert(
                    "protocol".to_string(),
                    serde_json::Value::String(protocol_value),
                );
            }
        }

        if let Some(goals_value) = goals {
            frontmatter.insert(
                "goals".to_string(),
                serde_json::Value::Array(
                    goals_value
                        .into_iter()
                        .map(|g| serde_json::Value::String(g))
                        .collect(),
                ),
            );
        }

        if let Some(blockers_value) = blockers {
            frontmatter.insert(
                "blockers".to_string(),
                serde_json::Value::Array(
                    blockers_value
                        .into_iter()
                        .map(|b| serde_json::Value::String(b))
                        .collect(),
                ),
            );
        }

        if let Some(decisions_value) = decisions {
            frontmatter.insert(
                "decisions".to_string(),
                serde_json::Value::Array(
                    decisions_value
                        .into_iter()
                        .map(|d| serde_json::Value::String(d))
                        .collect(),
                ),
            );
        }

        if let Some(divergences_value) = divergences {
            frontmatter.insert(
                "divergences".to_string(),
                serde_json::Value::Array(
                    divergences_value
                        .into_iter()
                        .map(|d| serde_json::Value::String(d))
                        .collect(),
                ),
            );
        }

        let updated_frontmatter = serde_yaml::to_string(&frontmatter).map_err(MetaError::Yaml)?;
        let body_to_write = content_override.unwrap_or_else(|| body);
        let new_content = format!("---\n{}---\n\n{}", updated_frontmatter, body_to_write);
        fs::write(&path, new_content)?;

        Ok(path)
    }

    pub fn get_daily(&self, date: NaiveDate) -> Option<DailyNote> {
        self.state
            .daily_notes
            .iter()
            .find(|d| d.date == date)
            .cloned()
    }

    pub fn list_daily(&self) -> Vec<DailyNote> {
        let mut notes = self.state.daily_notes.clone();
        notes.sort_by(|a, b| b.date.cmp(&a.date));
        notes
    }

    pub fn update_goal_status(&self, goal_id: &str, new_status: GoalStatus) -> Result<()> {
        let goal = self
            .get_goal(goal_id)
            .ok_or_else(|| MetaError::GoalNotFound(goal_id.to_string()))?;

        if !goal.status.can_transition_to(&new_status) {
            return Err(MetaError::InvalidTransition {
                from: goal.status.to_string(),
                to: new_status.to_string(),
            });
        }

        let content = fs::read_to_string(&goal.file_path)?;
        let (mut frontmatter, body) =
            crate::parser::frontmatter::FrontmatterParser::parse(&content)?;
        frontmatter.insert(
            "status".to_string(),
            serde_json::Value::String(new_status.to_string()),
        );

        let updated_frontmatter = serde_yaml::to_string(&frontmatter).map_err(MetaError::Yaml)?;
        let new_content = format!("---\n{}---\n\n{}", updated_frontmatter, body);
        fs::write(&goal.file_path, new_content)?;

        Ok(())
    }

    pub fn compute_warnings(&self) -> Vec<GovernanceWarning> {
        let mut warnings = Vec::new();
        let today = Local::now().naive_local().date();
        let today_path = self
            .root
            .join("01_DAILY")
            .join(DailyNote::file_name(&today));
        if !today_path.exists() {
            warnings.push(GovernanceWarning {
                kind: GovernanceWarningKind::MissingDailyNote,
                message: format!("Missing daily note for {}", today.format("%Y-%m-%d")),
                related: vec![today_path.to_string_lossy().to_string()],
            });
        }

        for goal in &self.state.goals {
            if goal
                .phase
                .as_ref()
                .map(|p| p.trim().is_empty())
                .unwrap_or(true)
            {
                warnings.push(GovernanceWarning {
                    kind: GovernanceWarningKind::GoalMissingPhase,
                    message: format!("{} has no phase assigned", goal.title),
                    related: vec![goal.goal_id.clone()],
                });
            }

            if matches!(goal.status, GoalStatus::Unknown(_)) {
                warnings.push(GovernanceWarning {
                    kind: GovernanceWarningKind::GoalMissingStatus,
                    message: format!("{} has an unrecognized status", goal.title),
                    related: vec![goal.goal_id.clone()],
                });
            }
        }

        // Active goals not referenced recently in daily notes
        let mut referenced_goals: HashSet<String> = HashSet::new();
        let cutoff = today - Duration::days(7);
        for daily in &self.state.daily_notes {
            if daily.date < cutoff {
                continue;
            }

            for goal_id in daily.goals_worked.iter().chain(daily.linked_goals.iter()) {
                referenced_goals.insert(goal_id.to_lowercase());
            }
        }

        for goal in self.state.goals.iter().filter(|g| g.is_active()) {
            if !referenced_goals
                .iter()
                .any(|ref_id| ref_id == &goal.goal_id.to_lowercase())
            {
                warnings.push(GovernanceWarning {
                    kind: GovernanceWarningKind::GoalMissingRecentDaily,
                    message: format!(
                        "{} has no daily note references in the last 7 days",
                        goal.title
                    ),
                    related: vec![goal.goal_id.clone()],
                });
            }
        }

        // Decisions not referenced by any goal
        let mut decision_refs: HashSet<String> = HashSet::new();
        for goal in &self.state.goals {
            for link in LinkExtractor::extract_decision_links(&goal.content) {
                decision_refs.insert(link.to_lowercase());
            }
        }

        for decision in &self.state.decisions {
            let id_lower = decision.decision_id.to_lowercase();
            if !decision_refs
                .iter()
                .any(|link| link.contains(&id_lower) || id_lower.contains(link))
            {
                warnings.push(GovernanceWarning {
                    kind: GovernanceWarningKind::DecisionUnlinked,
                    message: format!("{} is not referenced by any goal", decision.title),
                    related: vec![decision.decision_id.clone()],
                });
            }
        }

        // Phases with zero active goals
        for phase in &self.state.phases {
            let active_count = self
                .state
                .goals
                .iter()
                .filter(|g| g.status == GoalStatus::Active)
                .filter(|g| {
                    g.phase
                        .as_ref()
                        .map(|p| p.eq_ignore_ascii_case(&phase.phase_id))
                        .unwrap_or(false)
                })
                .count();
            if active_count == 0 {
                warnings.push(GovernanceWarning {
                    kind: GovernanceWarningKind::PhaseWithoutActiveGoals,
                    message: format!("Phase {} has no active goals", phase.title),
                    related: vec![phase.phase_id.clone()],
                });
            }
        }

        warnings
    }

    fn mtime(path: &Path) -> SystemTime {
        fs::metadata(path)
            .and_then(|m| m.modified())
            .unwrap_or(SystemTime::UNIX_EPOCH)
    }
}
