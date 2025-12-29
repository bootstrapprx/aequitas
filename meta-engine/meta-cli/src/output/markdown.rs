use meta_core::{Audit, AuditRecord, Goal, ValidationSeverity};

pub struct MarkdownFormatter;

impl MarkdownFormatter {
    #[allow(dead_code)]
    pub fn format_audit(audit: &Audit) -> String {
        let mut output = String::new();

        output.push_str(&format!("# Governance Audit — {}\n\n", chrono::Local::now().format("%Y-%m-%d")));

        let errors: Vec<_> = audit
            .results
            .iter()
            .filter(|r| r.severity == ValidationSeverity::Error)
            .collect();

        let warnings: Vec<_> = audit
            .results
            .iter()
            .filter(|r| r.severity == ValidationSeverity::Warning)
            .collect();

        let infos: Vec<_> = audit
            .results
            .iter()
            .filter(|r| r.severity == ValidationSeverity::Info)
            .collect();

        if !errors.is_empty() {
            output.push_str(&format!("## Errors ({})\n\n", errors.len()));
            for result in errors {
                let line_info = result
                    .line
                    .map(|l| format!(":{}",  l))
                    .unwrap_or_default();
                output.push_str(&format!(
                    "- {}{}  \n  {}\n\n",
                    result.file.display(),
                    line_info,
                    result.message
                ));
            }
        }

        if !warnings.is_empty() {
            output.push_str(&format!("## Warnings ({})\n\n", warnings.len()));
            for result in warnings {
                let line_info = result
                    .line
                    .map(|l| format!(":{}", l))
                    .unwrap_or_default();
                output.push_str(&format!(
                    "- {}{}  \n  {}\n\n",
                    result.file.display(),
                    line_info,
                    result.message
                ));
            }
        }

        if !infos.is_empty() {
            output.push_str(&format!("## Info ({})\n\n", infos.len()));
            for result in infos {
                output.push_str(&format!(
                    "- {}  \n  {}\n\n",
                    result.file.display(),
                    result.message
                ));
            }
        }

        output.push_str("## Summary\n\n");
        output.push_str(&format!("Total files: {}\n", audit.total_files));
        output.push_str(&format!("Errors: {}\n", audit.error_count()));
        output.push_str(&format!("Warnings: {}\n", audit.warning_count()));
        output.push_str(&format!("Info: {}\n", audit.info_count()));

        output
    }

    pub fn format_goals(goals: &[&Goal]) -> String {
        let mut output = String::new();

        output.push_str("# Goals\n\n");

        for goal in goals {
            let phase = goal
                .phase
                .as_ref()
                .map(|p| format!("Phase {}", p))
                .unwrap_or_else(|| "No phase".to_string());
            let owner = goal.owner.as_deref().unwrap_or("Unassigned");

            output.push_str(&format!(
                "- **{}**: {}  \n  Status: {} | {} | Owner: {}\n\n",
                goal.goal_id,
                goal.title,
                goal.status,
                phase,
                owner
            ));
        }

        output
    }

    pub fn format_audit_records(audits: &[&AuditRecord]) -> String {
        let mut output = String::new();
        output.push_str("# Governance Audits\n\n");

        if audits.is_empty() {
            output.push_str("- No audits found\n");
            return output;
        }

        for audit in audits {
            output.push_str(&format!("## {}\n", audit.title));
            if let Some(date) = audit.date {
                output.push_str(&format!("- Date: {}\n", date));
            }
            if let Some(scope) = &audit.scope {
                output.push_str(&format!("- Scope: {}\n", scope));
            }
            if let Some(risk) = &audit.risk {
                output.push_str(&format!("- Risk: {}\n", risk));
            }
            if let Some(auditor) = &audit.auditor {
                output.push_str(&format!("- Auditor: {}\n", auditor));
            }
            if let Some(summary) = &audit.summary {
                output.push_str(&format!("- Summary: {}\n", summary));
            }
            output.push_str(&format!(
                "- File: {}\n\n",
                audit.file_path.display()
            ));
        }

        output
    }
}
