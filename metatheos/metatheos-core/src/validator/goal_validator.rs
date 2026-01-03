use crate::domain::*;
use crate::governance::GovernanceContext;

pub struct GoalValidator;

impl GoalValidator {
    pub fn validate_dependencies(goal: &Goal, ctx: &GovernanceContext) -> Vec<ValidationResult> {
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
        ctx: &GovernanceContext,
        active_phase: Option<&str>,
    ) -> Vec<ValidationResult> {
        let mut results = Vec::new();
        let resolved = ctx.goal_with_effective_phase(goal);

        if resolved.phase.is_none() {
            results.push(ValidationResult::error(
                resolved.file_path.clone(),
                "Goal must belong to a phase (phase is the canonical scope root)",
            ));
        }

        if let Some(parent_id) = &resolved.parent_id {
            if let Some(parent) = ctx.get_goal(parent_id) {
                let parent_resolved = ctx.goal_with_effective_phase(parent);
                if let (Some(child_phase), Some(parent_phase)) =
                    (resolved.phase.as_ref(), parent_resolved.phase.as_ref())
                {
                    if !child_phase.eq_ignore_ascii_case(parent_phase) {
                        results.push(ValidationResult::error(
                            resolved.file_path.clone(),
                            format!(
                                "Parent-child phase mismatch: {} is in {}, parent {} is in {}",
                                resolved.goal_id, child_phase, parent.goal_id, parent_phase
                            ),
                        ));
                    }
                }
            }
        }

        if resolved.is_active() {
            if let Some(active) = active_phase {
                if resolved
                    .phase
                    .as_ref()
                    .map(|p| !p.eq_ignore_ascii_case(active))
                    .unwrap_or(true)
                {
                    results.push(ValidationResult::error(
                        resolved.file_path.clone(),
                        format!(
                            "Active goal is outside the active phase {} (phase is the canonical scope root)",
                            active
                        ),
                    ));
                }
            }
        }

        results
    }
}
