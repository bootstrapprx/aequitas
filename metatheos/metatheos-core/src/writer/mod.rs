pub mod frontmatter;
pub mod goal_writer;
pub mod phase_writer;
pub mod daily_writer;
pub mod audit_writer;
pub mod prompt_writer;

pub use frontmatter::FrontmatterSerializer;
pub use goal_writer::GoalWriter;
pub use phase_writer::PhaseWriter;
pub use daily_writer::DailyWriter;
pub use audit_writer::AuditWriter;
pub use prompt_writer::PromptWriter;

use crate::errors::Result;
use crate::errors::MetaError;
use std::path::Path;

/// Core trait for markdown writers
pub trait MarkdownWriter {
    /// Write content to a markdown file
    fn write(&self, path: &Path, content: &str) -> Result<()>;

    /// Create a backup of an existing file before modification
    fn backup(&self, path: &Path) -> Result<Option<std::path::PathBuf>>;

    /// Validate content before writing
    fn validate(&self, content: &str) -> Result<()>;
}

/// Ensure the governance root matches the expected on-disk layout.
/// This guard prevents writes from drifting into incorrect folders.
pub fn ensure_governance_layout(root: &Path) -> Result<()> {
    let expected = [
        "01_DAILY",
        "02_PHASES",
        "03_GOALS_EPICS",
        "04_DECISIONS",
        "05_AUDITS",
        "06_PROMPTS",
    ];

    let missing: Vec<&str> = expected
        .iter()
        .copied()
        .filter(|dir| !root.join(dir).exists())
        .collect();

    if !missing.is_empty() {
        return Err(MetaError::ValidationError(format!(
            "Governance layout incomplete. Missing: {}",
            missing.join(", ")
        )));
    }

    Ok(())
}
