use crate::governance::GovernanceContext;
use crate::domain::Goal;

pub struct ContextBuilder {
    #[allow(dead_code)]
    max_tokens: usize,
}

impl ContextBuilder {
    pub fn new(max_tokens: usize) -> Self {
        Self { max_tokens }
    }

    /// Build context for a general query
    pub fn for_query(&self, ctx: &GovernanceContext, _query: &str) -> String {
        let mut context = String::new();

        // Current phase
        if let Some(current_phase) = ctx.active_phase() {
            context.push_str(&format!("## Current Phase\n{}\n\n", current_phase.phase_id));
        }

        // Active goals
        let active_goals: Vec<&Goal> = ctx.all_goals()
            .into_iter()
            .filter(|g| g.is_active())
            .take(10)
            .collect();

        if !active_goals.is_empty() {
            context.push_str("## Active Goals\n");
            for goal in active_goals {
                context.push_str(&format!("- {} ({}): {}\n",
                    goal.goal_id,
                    goal.status,
                    goal.title
                ));
            }
            context.push_str("\n");
        }

        // Blocked goals
        let blocked_goals: Vec<&Goal> = ctx.all_goals()
            .into_iter()
            .filter(|g| g.is_blocked())
            .take(5)
            .collect();

        if !blocked_goals.is_empty() {
            context.push_str("## Blocked Goals\n");
            for goal in blocked_goals {
                context.push_str(&format!("- {} ({}): {}\n",
                    goal.goal_id,
                    goal.status,
                    goal.title
                ));
            }
            context.push_str("\n");
        }

        // Recently completed
        let done_goals: Vec<&Goal> = ctx.all_goals()
            .into_iter()
            .filter(|g| g.is_done())
            .take(5)
            .collect();

        if !done_goals.is_empty() {
            context.push_str("## Recently Completed\n");
            for goal in done_goals {
                context.push_str(&format!("- {}: {}\n", goal.goal_id, goal.title));
            }
            context.push_str("\n");
        }

        // Statistics
        let all_goals = ctx.all_goals();
        let status_counts = self.count_by_status(&all_goals);

        context.push_str("## Statistics\n");
        context.push_str(&format!("- Total Goals: {}\n", all_goals.len()));
        for (status, count) in status_counts {
            context.push_str(&format!("- {}: {}\n", status, count));
        }

        context
    }

    /// Build context for a specific goal
    pub fn for_goal(&self, ctx: &GovernanceContext, goal_id: &str) -> Option<String> {
        let goal = ctx.get_goal(goal_id)?;

        let mut context = String::new();

        context.push_str(&format!("# Goal: {}\n\n", goal.goal_id));
        context.push_str(&format!("**Title:** {}\n", goal.title));
        context.push_str(&format!("**Status:** {}\n", goal.status));

        if let Some(phase) = &goal.phase {
            context.push_str(&format!("**Phase:** {}\n", phase));
        }

        if let Some(owner) = &goal.owner {
            context.push_str(&format!("**Owner:** {}\n", owner));
        }

        if let Some(updated) = &goal.updated {
            context.push_str(&format!("**Updated:** {}\n", updated));
        }

        if !goal.dependencies.is_empty() {
            context.push_str("\n## Dependencies\n");
            for dep in &goal.dependencies {
                if let Some(dep_goal) = ctx.get_goal(dep) {
                    context.push_str(&format!("- {} ({}): {}\n",
                        dep_goal.goal_id,
                        dep_goal.status,
                        dep_goal.title
                    ));
                } else {
                    context.push_str(&format!("- {} (not found)\n", dep));
                }
            }
        }

        // Check for reverse dependencies (what depends on this goal)
        let dependents: Vec<&Goal> = ctx.all_goals()
            .into_iter()
            .filter(|g| g.has_dependency(goal_id))
            .collect();

        if !dependents.is_empty() {
            context.push_str("\n## Blocked By This Goal\n");
            for dependent in dependents {
                context.push_str(&format!("- {} ({}): {}\n",
                    dependent.goal_id,
                    dependent.status,
                    dependent.title
                ));
            }
        }

        if !goal.content.is_empty() {
            let preview = goal.content.lines().take(10).collect::<Vec<_>>().join("\n");
            context.push_str(&format!("\n## Content Preview\n{}\n", preview));
        }

        Some(context)
    }

    fn count_by_status(&self, goals: &[&Goal]) -> Vec<(String, usize)> {
        let mut counts = std::collections::HashMap::new();

        for goal in goals {
            *counts.entry(goal.status.to_string()).or_insert(0) += 1;
        }

        let mut result: Vec<(String, usize)> = counts.into_iter().collect();
        result.sort_by(|a, b| b.1.cmp(&a.1)); // Sort by count descending
        result
    }
}
