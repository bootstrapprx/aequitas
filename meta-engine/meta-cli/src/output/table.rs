use comfy_table::{Table, Cell, Color, Attribute, ContentArrangement};
use meta_core::{Audit, Goal, ValidationSeverity};

pub struct TableFormatter;

impl TableFormatter {
    pub fn format_audit(audit: &Audit) -> String {
        let mut table = Table::new();
        table.set_content_arrangement(ContentArrangement::Dynamic);
        table.set_header(vec!["Severity", "File", "Line", "Message"]);

        for result in &audit.results {
            let severity = match result.severity {
                ValidationSeverity::Error => Cell::new("Error").fg(Color::Red),
                ValidationSeverity::Warning => Cell::new("Warning").fg(Color::Yellow),
                ValidationSeverity::Info => Cell::new("Info").fg(Color::Blue),
            };

            let line = result
                .line
                .map(|l| l.to_string())
                .unwrap_or_else(|| "-".to_string());

            table.add_row(vec![
                severity,
                Cell::new(result.file.display().to_string()),
                Cell::new(line),
                Cell::new(&result.message),
            ]);
        }

        let mut output = table.to_string();
        output.push_str("\n\n");
        output.push_str(&format!("Total files: {}\n", audit.total_files));
        output.push_str(&format!("Errors: {}, Warnings: {}, Info: {}\n",
            audit.error_count(),
            audit.warning_count(),
            audit.info_count()
        ));

        output
    }

    pub fn format_goals(goals: &[&Goal]) -> String {
        let mut table = Table::new();
        table.set_content_arrangement(ContentArrangement::Dynamic);
        table.set_header(vec!["Goal ID", "Title", "Status", "Phase", "Owner"]);

        for goal in goals {
            let status_cell = match goal.status.to_string().as_str() {
                "active" => Cell::new("active").fg(Color::Green),
                "blocked" => Cell::new("blocked").fg(Color::Red),
                "completed" => Cell::new("completed").fg(Color::Blue),
                "archived" => Cell::new("archived").fg(Color::DarkGrey),
                _ => Cell::new(goal.status.to_string()),
            };

            let phase = goal.phase.map(|p| p.to_string()).unwrap_or_else(|| "-".to_string());
            let owner = goal.owner.as_deref().unwrap_or("-");

            table.add_row(vec![
                Cell::new(&goal.goal_id).add_attribute(Attribute::Bold),
                Cell::new(&goal.title),
                status_cell,
                Cell::new(phase),
                Cell::new(owner),
            ]);
        }

        table.to_string()
    }
}
