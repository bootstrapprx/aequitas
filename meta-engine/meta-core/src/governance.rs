use crate::domain::*;
use crate::errors::{MetaError, Result};
use crate::parser::{LinkExtractor, MarkdownParser};
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
pub struct GovernanceState {
    pub phases: Vec<Phase>,
    pub goals: Vec<Goal>,
    pub decisions: Vec<Decision>,
    pub daily_notes: Vec<DailyNote>,
    pub audits: Vec<AuditRecord>,
    pub prompts: Vec<Prompt>,
    pub canon_docs: Vec<CanonDoc>,
}

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
    pub recent_decisions: Vec<Decision>,
    pub canon_docs: Vec<CanonDoc>,
    pub warnings: Vec<GovernanceWarning>,
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

    pub fn scan(&self) -> Result<GovernanceState> {
        if !self.root.exists() {
            return Err(MetaError::GovernanceFolderNotFound(
                self.root.to_string_lossy().to_string(),
            ));
        }

        let phases = self.scan_markdown("02_PHASES", |p| MarkdownParser::parse_phase(p))?;
        let goals = self.scan_markdown("03_GOALS_EPICS", |p| MarkdownParser::parse_goal(p))?;
        let decisions = self.scan_markdown("04_DECISIONS", |p| MarkdownParser::parse_decision(p))?;
        let daily_notes = self.scan_markdown("01_DAILY", |p| MarkdownParser::parse_daily(p))?;
        let audits = self.scan_markdown("05_AUDITS", |p| MarkdownParser::parse_audit(p))?;
        let prompts = self.scan_markdown("06_PROMPTS", |p| MarkdownParser::parse_prompt(p))?;
        let canon_docs = self.scan_canon()?;

        Ok(GovernanceState {
            phases,
            goals,
            decisions,
            daily_notes,
            audits,
            prompts,
            canon_docs,
        })
    }

    fn scan_markdown<T, F>(&self, folder: &str, parser: F) -> Result<Vec<T>>
    where
        F: Fn(&Path) -> Result<T>,
    {
        let dir = self.root.join(folder);
        if !dir.exists() {
            return Ok(Vec::new());
        }

        let mut items = Vec::new();
        for entry in WalkDir::new(&dir)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.path().is_file())
        {
            let path = entry.path();
            if path
                .file_name()
                .and_then(|n| n.to_str())
                .map(|name| name.starts_with('_'))
                .unwrap_or(false)
            {
                continue;
            }

            if path.extension().and_then(|s| s.to_str()) != Some("md") {
                continue;
            }

            match parser(path) {
                Ok(item) => items.push(item),
                Err(err) => {
                    eprintln!("Warning: failed to parse {:?}: {}", path, err);
                }
            }
        }

        Ok(items)
    }

    fn scan_canon(&self) -> Result<Vec<CanonDoc>> {
        let canon_root = self.root.join("CONSTITUTION");
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
}

/// Main governance context - loads and manages all governance data
pub struct GovernanceContext {
    pub root: PathBuf,
    pub state: GovernanceState,
    goals_index: HashMap<String, usize>,
    decisions_index: HashMap<String, usize>,
}

impl GovernanceContext {
    pub fn load<P: AsRef<Path>>(root: P) -> Result<Self> {
        let scanner = GovernanceScanner::new(root);
        let root = scanner.root.clone();
        let state = scanner.scan()?;

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
            self.goals_index
                .insert(goal.goal_id.to_lowercase(), idx);
        }

        for (idx, decision) in self.state.decisions.iter().enumerate() {
            self.decisions_index
                .insert(decision.decision_id.to_lowercase(), idx);
        }
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

    pub fn count_files(&self) -> usize {
        self.state.goals.len()
            + self.state.decisions.len()
            + self.state.daily_notes.len()
            + self.state.phases.len()
    }

    pub fn active_phase(&self) -> Option<Phase> {
        // Prefer explicit active/in-progress status if present
        if let Some(found) = self
            .state
            .phases
            .iter()
            .find(|p| p
                .status
                .as_ref()
                .map(|s| s.to_lowercase().contains("active"))
                .unwrap_or(false))
        {
            return Some(found.clone());
        }

        let mut phases = self.state.phases.clone();
        phases.sort_by(|a, b| {
            b.updated
                .cmp(&a.updated)
                .then_with(|| b.number().cmp(&a.number()))
        });
        phases.into_iter().next()
    }

    pub fn active_goals(&self) -> Vec<Goal> {
        let mut goals: Vec<Goal> = self
            .state
            .goals
            .iter()
            .filter(|g| g.is_active())
            .cloned()
            .collect();

        goals.sort_by(|a, b| b.updated.cmp(&a.updated));
        goals
    }

    pub fn blocked_goals(&self) -> Vec<Goal> {
        let mut goals: Vec<Goal> = self
            .state
            .goals
            .iter()
            .filter(|g| g.status == GoalStatus::Blocked)
            .cloned()
            .collect();
        goals.sort_by(|a, b| b.updated.cmp(&a.updated));
        goals
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

        let current_phase = self.active_phase();
        let recent_decisions = self.recent_decisions(5);
        let warnings = self.compute_warnings();
        let mut canon_docs = self.state.canon_docs.clone();
        canon_docs.sort_by(|a, b| a.title.cmp(&b.title));

        GovernanceSummary {
            current_phase,
            active_goals: self.active_goals(),
            blocked_goals: self.blocked_goals(),
            total_goals: self.state.goals.len(),
            today_exists,
            today_path,
            today_mode,
            today_goals,
            today_blockers,
            today_decisions,
            today_divergences,
            recent_decisions,
            canon_docs,
            warnings,
        }
    }

    pub fn recent_decisions(&self, count: usize) -> Vec<Decision> {
        let mut decisions = self.state.decisions.clone();
        decisions.sort_by(|a, b| {
            let a_date = a.updated.or(a.date);
            let b_date = b.updated.or(b.date);
            b_date
                .cmp(&a_date)
                .then_with(|| Self::mtime(b.file_path.as_path()).cmp(&Self::mtime(a.file_path.as_path())))
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
        let (mut frontmatter, body) = crate::parser::frontmatter::FrontmatterParser::parse(&content)?;
        if let Some(mode_value) = mode {
            frontmatter.insert(
                "mode".to_string(),
                serde_json::Value::String(mode_value),
            );
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
                frontmatter.insert(
                    "mode".to_string(),
                    serde_json::Value::String(mode_value),
                );
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
        self.state.daily_notes.iter().find(|d| d.date == date).cloned()
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
        let (mut frontmatter, body) = crate::parser::frontmatter::FrontmatterParser::parse(&content)?;
        frontmatter.insert(
            "status".to_string(),
            serde_json::Value::String(new_status.to_string()),
        );

        let updated_frontmatter =
            serde_yaml::to_string(&frontmatter).map_err(MetaError::Yaml)?;
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
            if goal.phase.as_ref().map(|p| p.trim().is_empty()).unwrap_or(true) {
                warnings.push(GovernanceWarning {
                    kind: GovernanceWarningKind::GoalMissingPhase,
                    message: format!("{} has no phase assigned", goal.goal_id),
                    related: vec![goal.goal_id.clone()],
                });
            }

            if matches!(goal.status, GoalStatus::Unknown(_)) {
                warnings.push(GovernanceWarning {
                    kind: GovernanceWarningKind::GoalMissingStatus,
                    message: format!("{} has an unrecognized status", goal.goal_id),
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

            for goal_id in daily
                .goals_worked
                .iter()
                .chain(daily.linked_goals.iter())
            {
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
                        goal.goal_id
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
                    message: format!(
                        "{} is not referenced by any goal",
                        decision.decision_id
                    ),
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
                    message: format!(
                        "Phase {} has no active goals",
                        phase.phase_id
                    ),
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
