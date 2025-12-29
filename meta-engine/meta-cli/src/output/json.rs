use meta_core::{Audit, Goal};
use serde_json;

pub struct JsonFormatter;

impl JsonFormatter {
    pub fn format_audit(audit: &Audit) -> String {
        serde_json::to_string_pretty(audit).unwrap_or_else(|_| "{}".to_string())
    }

    pub fn format_goals(goals: &[&Goal]) -> String {
        serde_json::to_string_pretty(&goals).unwrap_or_else(|_| "[]".to_string())
    }
}
