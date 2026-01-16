use crate::args::PhaseAction;
use anyhow::Result;
use metatheos_core::{GoalStatus, GovernanceContext};

pub fn run_phase(root: &str, action: &PhaseAction) -> Result<()> {
    let ctx = GovernanceContext::load(root)?;

    match action {
        PhaseAction::Current => {
            if let Some(phase) = ctx.active_phase() {
                println!("Current Phase: {} — {}", phase.phase_id, phase.title);
            } else {
                println!("No active goals with phase information");
            }
        }

        PhaseAction::List => {
            let mut phases = ctx.state.phases.clone();
            phases.sort_by(|a, b| a.phase_id.cmp(&b.phase_id));
            println!("Phases found:");
            for phase in phases {
                let goal_count = ctx
                    .state
                    .goals
                    .iter()
                    .filter(|g| {
                        g.phase
                            .as_ref()
                            .map(|p| p.eq_ignore_ascii_case(&phase.phase_id))
                            .unwrap_or(false)
                    })
                    .count();

                println!("  {} ({} goals)", phase.phase_id, goal_count);
            }
        }

        PhaseAction::Validate => {
            let Some(curr_phase) = ctx.active_phase() else {
                println!("No active goals with phase information");
                return Ok(());
            };

            let all_goals = ctx.all_goals();
            let mismatched: Vec<_> = all_goals
                .iter()
                .filter(|g| g.status == GoalStatus::Active)
                .filter(|g| {
                    g.phase
                        .as_ref()
                        .map(|p| !p.eq_ignore_ascii_case(&curr_phase.phase_id))
                        .unwrap_or(true)
                })
                .collect();

            if mismatched.is_empty() {
                println!(
                    "✓ Phase coherence validated: all active goals are in Phase {}",
                    curr_phase.phase_id
                );
            } else {
                println!(
                    "⚠ Warning: {} active goals are not in current Phase {}",
                    mismatched.len(),
                    curr_phase.phase_id
                );
                for goal in mismatched {
                    println!(
                        "  {} (Phase {:?}): {}",
                        goal.goal_id, goal.phase, goal.title
                    );
                }
            }
        }
    }

    Ok(())
}
