use anyhow::{Result, bail, anyhow};
use meta_core::{GovernanceContext, MetaError};
use crate::args::{GoalAction, parse_goal_status};
use std::fs;

pub fn run_goal(root: &str, action: &GoalAction) -> Result<()> {
    let ctx = GovernanceContext::load(root)?;

    match action {
        GoalAction::Show { goal_id } => {
            let goal = ctx.get_goal(goal_id)
                .ok_or_else(|| MetaError::GoalNotFound(goal_id.clone()))?;

            println!("Goal: {}", goal.goal_id);
            println!("Title: {}", goal.title);
            println!("Status: {}", goal.status);
            println!("Phase: {}", goal.phase.map(|p| p.to_string()).unwrap_or_else(|| "None".to_string()));
            println!("Owner: {}", goal.owner.as_deref().unwrap_or("Unassigned"));
            println!("Dependencies: {:?}", goal.dependencies);
            println!("Tags: {:?}", goal.tags);
            println!("\nFile: {}", goal.file_path.display());
        }

        GoalAction::Set { goal_id, status } => {
            let goal = ctx.get_goal(goal_id)
                .ok_or_else(|| MetaError::GoalNotFound(goal_id.clone()))?;

            let new_status = parse_goal_status(status).map_err(|e| anyhow!(e))?;

            if !goal.status.can_transition_to(&new_status) {
                bail!(MetaError::InvalidTransition {
                    from: goal.status.to_string(),
                    to: new_status.to_string(),
                });
            }

            // Read the file
            let content = fs::read_to_string(&goal.file_path)?;

            // Replace the status in the frontmatter
            let updated = content.replace(
                &format!("status: {}", goal.status),
                &format!("status: {}", new_status),
            );

            // Write back
            fs::write(&goal.file_path, updated)?;

            println!("Updated {} → {}", goal_id, new_status);
        }

        GoalAction::Deps { goal_id } => {
            let goal = ctx.get_goal(goal_id)
                .ok_or_else(|| MetaError::GoalNotFound(goal_id.clone()))?;

            if goal.dependencies.is_empty() {
                println!("{} has no dependencies", goal_id);
            } else {
                println!("{} depends on:", goal_id);
                for dep_id in &goal.dependencies {
                    if let Some(dep) = ctx.get_goal(dep_id) {
                        println!("  → {} ({}) - {}", dep.goal_id, dep.status, dep.title);
                    } else {
                        println!("  → {} (not found)", dep_id);
                    }
                }
            }
        }
    }

    Ok(())
}
