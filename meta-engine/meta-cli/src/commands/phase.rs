use anyhow::Result;
use meta_core::{GovernanceContext, GoalStatus};
use crate::args::PhaseAction;

pub fn run_phase(root: &str, action: &PhaseAction) -> Result<()> {
    let ctx = GovernanceContext::load(root)?;

    match action {
        PhaseAction::Current => {
            let current_phase = ctx
                .all_goals()
                .iter()
                .filter(|g| g.status == GoalStatus::Active)
                .filter_map(|g| g.phase)
                .max();

            if let Some(phase) = current_phase {
                println!("Current Phase: {}", phase);
            } else {
                println!("No active goals with phase information");
            }
        }

        PhaseAction::List => {
            let mut phases: Vec<u32> = ctx
                .all_goals()
                .iter()
                .filter_map(|g| g.phase)
                .collect();

            phases.sort();
            phases.dedup();

            println!("Phases found:");
            for phase in phases {
                let goal_count = ctx
                    .all_goals()
                    .iter()
                    .filter(|g| g.phase == Some(phase))
                    .count();

                println!("  Phase {}: {} goals", phase, goal_count);
            }
        }

        PhaseAction::Validate => {
            let current_phase = ctx
                .all_goals()
                .iter()
                .filter(|g| g.status == GoalStatus::Active)
                .filter_map(|g| g.phase)
                .max();

            if let Some(curr_phase) = current_phase {
                let all_goals = ctx.all_goals();
                let mismatched: Vec<_> = all_goals
                    .iter()
                    .filter(|g| g.status == GoalStatus::Active)
                    .filter(|g| g.phase.is_some() && g.phase != Some(curr_phase))
                    .collect();

                if mismatched.is_empty() {
                    println!("✓ Phase coherence validated: all active goals are in Phase {}", curr_phase);
                } else {
                    println!("⚠ Warning: {} active goals are not in current Phase {}",
                        mismatched.len(), curr_phase);
                    for goal in mismatched {
                        println!("  {} (Phase {}): {}",
                            goal.goal_id,
                            goal.phase.unwrap(),
                            goal.title
                        );
                    }
                }
            } else {
                println!("No active goals with phase information");
            }
        }
    }

    Ok(())
}
