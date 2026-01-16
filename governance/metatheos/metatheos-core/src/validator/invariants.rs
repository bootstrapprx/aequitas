use crate::domain::*;
use crate::governance::GovernanceContext;
use crate::validator::GoalValidator;

pub struct GovernanceValidator;

impl GovernanceValidator {
    pub fn validate(ctx: &GovernanceContext) -> Audit {
        let mut audit = Audit::new();
        audit.total_files = ctx.count_files();

        // Validate all goals
        for goal in ctx.all_goals() {
            // Validate dependencies
            let dep_results = GoalValidator::validate_dependencies(goal, ctx);
            for result in dep_results {
                audit.add_result(result);
            }

            // Phase coherence (phase is canonical scope root)
            let active_phase = ctx.active_phase().map(|p| p.phase_id);
            let phase_results =
                GoalValidator::validate_phase_coherence(goal, ctx, active_phase.as_deref());
            for result in phase_results {
                audit.add_result(result);
            }
        }

        // Validate all decisions
        for decision in ctx.all_decisions() {
            // Basic validation - decisions are already validated during parsing
            if decision.rationale.is_none() {
                audit.add_result(ValidationResult::info(
                    decision.file_path.clone(),
                    "Decision has no rationale".to_string(),
                ));
            }
        }

        audit
    }
}
