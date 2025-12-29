use crate::domain::*;
use crate::governance::GovernanceContext;

pub struct GoalQuery<'a> {
    ctx: &'a GovernanceContext,
    status_filter: Option<GoalStatus>,
    phase_filter: Option<String>,
    tag_filter: Option<String>,
}

impl<'a> GoalQuery<'a> {
    pub fn new(ctx: &'a GovernanceContext) -> Self {
        Self {
            ctx,
            status_filter: None,
            phase_filter: None,
            tag_filter: None,
        }
    }

    pub fn with_status(mut self, status: GoalStatus) -> Self {
        self.status_filter = Some(status);
        self
    }

    pub fn with_phase(mut self, phase: impl Into<String>) -> Self {
        self.phase_filter = Some(phase.into());
        self
    }

    pub fn with_tag(mut self, tag: impl Into<String>) -> Self {
        self.tag_filter = Some(tag.into());
        self
    }

    pub fn execute(&self) -> Vec<&Goal> {
        let mut results: Vec<&Goal> = self.ctx.all_goals();

        if let Some(ref status) = self.status_filter {
            results.retain(|g| &g.status == status);
        }

        if let Some(ref phase) = self.phase_filter {
            results.retain(|g| {
                g.phase
                    .as_ref()
                    .map(|p| p.eq_ignore_ascii_case(&phase))
                    .unwrap_or(false)
            });
        }

        if let Some(ref tag) = self.tag_filter {
            results.retain(|g| g.tags.contains(tag));
        }

        // Sort by goal_id
        results.sort_by(|a, b| a.goal_id.cmp(&b.goal_id));

        results
    }
}
