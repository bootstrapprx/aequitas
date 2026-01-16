use crate::args::parse_goal_status;
use crate::output::{JsonFormatter, MarkdownFormatter, TableFormatter};
use anyhow::{anyhow, Result};
use metatheos_core::{GoalQuery, GovernanceContext};

pub fn run_goals(
    root: &str,
    status: Option<String>,
    active: bool,
    phase: Option<String>,
    tag: Option<String>,
    format: &str,
) -> Result<()> {
    let ctx = GovernanceContext::load(root)?;
    let mut query = GoalQuery::new(&ctx);

    if let Some(status_str) = status {
        let status = parse_goal_status(&status_str).map_err(|e| anyhow!(e))?;
        query = query.with_status(status);
    }

    if let Some(p) = phase {
        query = query.with_phase(p);
    }

    if let Some(t) = tag {
        query = query.with_tag(t);
    }

    let mut goals = query.execute();

    if active {
        goals.retain(|g| g.is_active());
    }

    let output = match format {
        "json" => JsonFormatter::format_goals(&goals),
        "markdown" => MarkdownFormatter::format_goals(&goals),
        _ => TableFormatter::format_goals(&goals),
    };

    println!("{}", output);

    Ok(())
}
