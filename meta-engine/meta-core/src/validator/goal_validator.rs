use crate::domain::*;
use crate::governance::GovernanceContext;

pub struct GoalValidator;

impl GoalValidator {
    pub fn validate_dependencies(
        goal: &Goal,
        ctx: &GovernanceContext,
    ) -> Vec<ValidationResult> {
        let mut results = Vec::new();

        for dep_id in &goal.dependencies {
            if ctx.get_goal(dep_id).is_none() {
                results.push(ValidationResult::warning(
                    goal.file_path.clone(),
                    format!("Referenced goal `{}` does not exist", dep_id),
                ));
            }
        }

        results
    }

    pub fn validate_phase_coherence(
        goal: &Goal,
        current_phase: Option<u32>,
    ) -> Vec<ValidationResult> {
        let mut results = Vec::new();

        if goal.is_active() {
            if let (Some(goal_phase), Some(curr_phase)) = (goal.phase, current_phase) {
                if goal_phase != curr_phase {
                    results.push(ValidationResult::warning(
                        goal.file_path.clone(),
                        format!(
                            "Active goal is in Phase {}, but current phase is {}",
                            goal_phase, curr_phase
                        ),
                    ));
                }
            }
        }

        results
    }
}
