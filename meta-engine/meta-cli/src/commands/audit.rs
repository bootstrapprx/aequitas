use anyhow::Result;
use meta_core::{GovernanceContext, GovernanceValidator};
use crate::output::{MarkdownFormatter, JsonFormatter, TableFormatter};

pub fn run_audit(root: &str, format: &str, strict: bool) -> Result<i32> {
    let ctx = GovernanceContext::load(root)?;
    let audit = GovernanceValidator::validate(&ctx);

    let output = match format {
        "json" => JsonFormatter::format_audit(&audit),
        "table" => TableFormatter::format_audit(&audit),
        _ => MarkdownFormatter::format_audit(&audit),
    };

    println!("{}", output);

    // Exit code: 0 if valid, 1 if errors (or warnings in strict mode)
    let exit_code = if audit.has_errors() || (strict && audit.warning_count() > 0) {
        1
    } else {
        0
    };

    Ok(exit_code)
}
