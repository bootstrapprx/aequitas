pub mod frontmatter;
pub mod goal_writer;
pub mod phase_writer;
pub mod daily_writer;

pub use frontmatter::FrontmatterSerializer;
pub use goal_writer::GoalWriter;
pub use phase_writer::PhaseWriter;
pub use daily_writer::DailyWriter;

use crate::errors::Result;
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
