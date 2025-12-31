use crate::governance::GovernanceContext;
use crate::domain::{Goal, GoalStatus, DailyNote};
use chrono::{Utc, Duration};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AequitasDashboard {
    pub completion: CompletionMetrics,
    pub current_phase: PhaseStatus,
    pub blockers: Vec<Blocker>,
    pub critical_path: Vec<CriticalGoal>,
    pub recent_activity: RecentActivity,
    pub health: HealthMetrics,
    pub generated_at: String,
    pub governance_root: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompletionMetrics {
    pub percentage: f64,
    pub total_goals: usize,
    pub done_goals: usize,
    pub active_goals: usize,
    pub blocked_goals: usize,
    pub planned_goals: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseStatus {
    pub phase_number: Option<u8>,
    pub phase_title: Option<String>,
    pub phase_status: Option<String>,
    pub goals_in_phase: usize,
    pub done_in_phase: usize,
    pub phase_completion: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Blocker {
    pub goal_id: String,
    pub title: String,
    pub reason: Option<String>,
    pub blocked_since: Option<String>,
    pub blocking_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CriticalGoal {
    pub goal_id: String,
    pub title: String,
    pub status: String,
    pub reverse_dependencies: usize,
    pub phase: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecentActivity {
    pub days_tracked: usize,
    pub goals_completed: usize,
    pub goals_started: usize,
    pub velocity: f64,
    pub daily_notes: Vec<DailyNoteInfo>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DailyNoteInfo {
    pub date: String,
    pub goals_worked: Vec<String>,
    pub decisions_made: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthMetrics {
    pub blocked_percentage: f64,
    pub orphaned_goals: usize,
    pub missing_dependencies: usize,
    pub audit_errors: usize,
}

pub struct DashboardCalculator<'a> {
    ctx: &'a GovernanceContext,
}

impl<'a> DashboardCalculator<'a> {
    pub fn new(ctx: &'a GovernanceContext) -> Self {
        Self { ctx }
    }

    pub fn calculate(&self) -> AequitasDashboard {
        AequitasDashboard {
            completion: self.calculate_completion(),
            current_phase: self.detect_current_phase(),
            blockers: self.find_blockers(),
            critical_path: self.build_critical_path(),
            recent_activity: self.analyze_recent_activity(),
            health: self.calculate_health(),
            generated_at: Utc::now().to_rfc3339(),
            governance_root: self.ctx.root.to_string_lossy().to_string(),
        }
    }

    fn calculate_completion(&self) -> CompletionMetrics {
        let all_goals = self.ctx.all_goals();
        let total_goals = all_goals.len();

        let done_goals = all_goals.iter().filter(|g| g.status == GoalStatus::Done).count();
        let active_goals = all_goals.iter().filter(|g| g.status == GoalStatus::Active).count();
        let blocked_goals = all_goals.iter().filter(|g| g.status == GoalStatus::Blocked).count();
        let planned_goals = all_goals.iter().filter(|g| g.status == GoalStatus::Planned).count();

        let percentage = if total_goals > 0 {
            (done_goals as f64 / total_goals as f64) * 100.0
        } else {
            0.0
        };

        CompletionMetrics {
            percentage,
            total_goals,
            done_goals,
            active_goals,
            blocked_goals,
            planned_goals,
        }
    }

    fn detect_current_phase(&self) -> PhaseStatus {
        let phases = self.ctx.all_phases();
        let all_goals = self.ctx.all_goals();

        // Helper: parse phase number from phase_id (e.g., "P4" → 4)
        let parse_phase_num = |phase_id: &str| -> Option<u8> {
            phase_id.trim_start_matches('P').parse().ok()
        };

        // Find active phase or highest phase with goals
        let current_phase = phases.iter()
            .filter(|p| p.status.as_str() == "active")
            .max_by_key(|p| parse_phase_num(&p.phase_id))
            .or_else(|| {
                // Find highest phase that has goals
                phases.iter()
                    .filter(|p| {
                        let phase_num = parse_phase_num(&p.phase_id);
                        all_goals.iter().any(|g| {
                            g.phase.as_ref().and_then(|ph| ph.parse::<u8>().ok()) == phase_num
                        })
                    })
                    .max_by_key(|p| parse_phase_num(&p.phase_id))
            });

        if let Some(phase) = current_phase {
            let phase_num = parse_phase_num(&phase.phase_id);
            let phase_goals: Vec<_> = all_goals.iter()
                .filter(|g| {
                    g.phase.as_ref().and_then(|ph| ph.parse::<u8>().ok()) == phase_num
                })
                .collect();

            let goals_in_phase = phase_goals.len();
            let done_in_phase = phase_goals.iter().filter(|g| g.status == GoalStatus::Done).count();
            let phase_completion = if goals_in_phase > 0 {
                (done_in_phase as f64 / goals_in_phase as f64) * 100.0
            } else {
                0.0
            };

            PhaseStatus {
                phase_number: phase_num,
                phase_title: Some(phase.title.clone()),
                phase_status: Some(phase.status.clone()),
                goals_in_phase,
                done_in_phase,
                phase_completion,
            }
        } else {
            PhaseStatus {
                phase_number: None,
                phase_title: None,
                phase_status: None,
                goals_in_phase: 0,
                done_in_phase: 0,
                phase_completion: 0.0,
            }
        }
    }

    fn find_blockers(&self) -> Vec<Blocker> {
        let all_goals = self.ctx.all_goals();
        let blocked_goals: Vec<_> = all_goals.iter()
            .filter(|g| g.status == GoalStatus::Blocked)
            .collect();

        // Build reverse dependency map
        let reverse_deps = self.build_reverse_dependencies();

        let mut blockers: Vec<Blocker> = blocked_goals.iter()
            .map(|goal| {
                let blocking_count = reverse_deps.get(&goal.goal_id).map(|v| v.len()).unwrap_or(0);

                // Try to extract reason from content (look for common patterns)
                let reason = self.extract_blocker_reason(goal);

                Blocker {
                    goal_id: goal.goal_id.clone(),
                    title: goal.title.clone(),
                    reason,
                    blocked_since: goal.updated.map(|d| d.to_string()),
                    blocking_count,
                }
            })
            .collect();

        // Sort by blocking_count descending (most critical first)
        blockers.sort_by(|a, b| b.blocking_count.cmp(&a.blocking_count));

        blockers
    }

    fn extract_blocker_reason(&self, goal: &Goal) -> Option<String> {
        // Simple heuristic: look for "Blocked by:" or similar patterns in content
        let content = &goal.content;

        if content.contains("Blocked by:") {
            content.lines()
                .find(|line| line.contains("Blocked by:"))
                .and_then(|line| line.split("Blocked by:").nth(1))
                .map(|reason| reason.trim().to_string())
        } else if content.contains("Blocker:") {
            content.lines()
                .find(|line| line.contains("Blocker:"))
                .and_then(|line| line.split("Blocker:").nth(1))
                .map(|reason| reason.trim().to_string())
        } else {
            None
        }
    }

    fn build_critical_path(&self) -> Vec<CriticalGoal> {
        let reverse_deps = self.build_reverse_dependencies();
        let all_goals = self.ctx.all_goals();

        let mut critical_goals: Vec<CriticalGoal> = all_goals.iter()
            .filter_map(|goal| {
                let reverse_count = reverse_deps.get(&goal.goal_id).map(|v| v.len()).unwrap_or(0);
                if reverse_count > 0 {
                    Some(CriticalGoal {
                        goal_id: goal.goal_id.clone(),
                        title: goal.title.clone(),
                        status: goal.status.to_string(),
                        reverse_dependencies: reverse_count,
                        phase: goal.phase.clone(),
                    })
                } else {
                    None
                }
            })
            .collect();

        // Sort by reverse_dependencies descending
        critical_goals.sort_by(|a, b| b.reverse_dependencies.cmp(&a.reverse_dependencies));

        // Return top 10
        critical_goals.into_iter().take(10).collect()
    }

    fn build_reverse_dependencies(&self) -> HashMap<String, Vec<String>> {
        let all_goals = self.ctx.all_goals();
        let mut reverse_deps: HashMap<String, Vec<String>> = HashMap::new();

        for goal in all_goals {
            for dep_id in &goal.dependencies {
                reverse_deps.entry(dep_id.clone())
                    .or_insert_with(Vec::new)
                    .push(goal.goal_id.clone());
            }
        }

        reverse_deps
    }

    fn analyze_recent_activity(&self) -> RecentActivity {
        let today = Utc::now().naive_utc().date();
        let seven_days_ago = today - Duration::days(7);

        let all_daily_notes = self.ctx.all_daily_notes();
        let all_goals = self.ctx.all_goals();

        // Filter daily notes from last 7 days
        let recent_notes: Vec<&DailyNote> = all_daily_notes.iter()
            .filter(|note| note.date >= seven_days_ago && note.date <= today)
            .collect();

        let days_tracked = recent_notes.len();

        // Extract goals worked from daily notes
        let mut all_goals_worked: HashSet<String> = HashSet::new();
        let mut all_decisions_made: HashSet<String> = HashSet::new();

        for note in &recent_notes {
            for goal_id in &note.goals_worked {
                all_goals_worked.insert(goal_id.clone());
            }
            for decision_id in &note.decisions_made {
                all_decisions_made.insert(decision_id.clone());
            }
        }

        // Count goals completed in last 7 days (updated field >= 7 days ago AND status = done)
        let goals_completed = all_goals.iter()
            .filter(|g| {
                g.status == GoalStatus::Done &&
                g.updated.map(|d| d >= seven_days_ago && d <= today).unwrap_or(false)
            })
            .count();

        // Count goals started in last 7 days (updated field >= 7 days ago AND status = active)
        let goals_started = all_goals.iter()
            .filter(|g| {
                g.status == GoalStatus::Active &&
                g.updated.map(|d| d >= seven_days_ago && d <= today).unwrap_or(false)
            })
            .count();

        // Calculate velocity
        let velocity = if days_tracked > 0 {
            goals_completed as f64 / 7.0
        } else {
            0.0
        };

        // Build daily note info
        let daily_notes = recent_notes.iter()
            .map(|note| DailyNoteInfo {
                date: note.date.to_string(),
                goals_worked: note.goals_worked.clone(),
                decisions_made: note.decisions_made.clone(),
            })
            .collect();

        RecentActivity {
            days_tracked,
            goals_completed,
            goals_started,
            velocity,
            daily_notes,
        }
    }

    fn calculate_health(&self) -> HealthMetrics {
        let all_goals = self.ctx.all_goals();
        let total_goals = all_goals.len();

        let blocked_goals = all_goals.iter().filter(|g| g.status == GoalStatus::Blocked).count();
        let blocked_percentage = if total_goals > 0 {
            (blocked_goals as f64 / total_goals as f64) * 100.0
        } else {
            0.0
        };

        // Count orphaned goals (no phase AND no canon)
        let orphaned_goals = all_goals.iter()
            .filter(|g| g.phase.is_none() && g.canon.is_empty())
            .count();

        // Count missing dependencies
        let all_goal_ids: HashSet<String> = all_goals.iter()
            .map(|g| g.goal_id.clone())
            .collect();

        let missing_dependencies = all_goals.iter()
            .flat_map(|g| &g.dependencies)
            .filter(|dep_id| !all_goal_ids.contains(*dep_id))
            .count();

        // Count audit errors (run validator)
        let audit = crate::validator::GovernanceValidator::validate(self.ctx);
        let audit_errors = audit.error_count();

        HealthMetrics {
            blocked_percentage,
            orphaned_goals,
            missing_dependencies,
            audit_errors,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::GovernanceContext;
    use std::path::PathBuf;

    #[test]
    fn test_dashboard_calculator_basic() {
        // This test requires a valid governance folder
        // In a real test, we'd use a fixture or mock
        let gov_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .parent()
            .unwrap()
            .join("governance");

        if gov_root.exists() {
            let ctx = GovernanceContext::load(&gov_root).expect("Failed to load governance context");
            let calculator = DashboardCalculator::new(&ctx);
            let dashboard = calculator.calculate();

            // Basic assertions
            assert!(dashboard.completion.percentage >= 0.0 && dashboard.completion.percentage <= 100.0);
            assert!(dashboard.completion.total_goals > 0);
            assert!(!dashboard.generated_at.is_empty());
        }
    }
}
