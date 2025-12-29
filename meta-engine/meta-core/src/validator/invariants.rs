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

            // Phase coherence (assume current phase is max active goal phase)
            let current_phase = ctx
                .all_goals()
                .iter()
                .filter(|g| g.is_active())
                .filter_map(|g| {
                    g.phase
                        .as_ref()
                        .and_then(|p| p.trim_start_matches('P').parse::<u32>().ok())
                })
                .max();

            let phase_results = GoalValidator::validate_phase_coherence(goal, current_phase);
            for result in phase_results {
                audit.add_result(result);
            }

            // Validate required fields presence (already done in parsing, but double-check)
            if goal.phase.is_none() {
                audit.add_result(ValidationResult::warning(
                    goal.file_path.clone(),
                    "Missing optional field: phase".to_string(),
                ));
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
