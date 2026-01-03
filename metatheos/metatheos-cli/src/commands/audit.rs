use crate::output::{JsonFormatter, MarkdownFormatter, TableFormatter};
use anyhow::Result;
use metatheos_core::GovernanceContext;

pub fn run_audit(root: &str, format: &str) -> Result<i32> {
    let ctx = GovernanceContext::load(root)?;
    let audits = ctx.all_audits();

    let output = match format {
        "json" => JsonFormatter::format_audit_records(&audits),
        "markdown" => MarkdownFormatter::format_audit_records(&audits),
        _ => TableFormatter::format_audit_records(&audits),
    };

    println!("{}", output);

    Ok(0)
}
