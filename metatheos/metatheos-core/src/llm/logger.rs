use crate::errors::Result;
use chrono::Utc;
use std::fs;
use std::path::{Path, PathBuf};

pub struct PromptLogger {
    log_dir: PathBuf,
}

#[derive(Debug)]
pub struct InteractionMetadata {
    pub model: String,
    pub tokens_in: Option<usize>,
    pub tokens_out: Option<usize>,
    pub duration_ms: Option<u64>,
}

impl PromptLogger {
    pub fn new<P: AsRef<Path>>(governance_root: P) -> Self {
        let log_dir = governance_root.as_ref().join("06_PROMPTS").join("logs");
        Self { log_dir }
    }

    pub fn log_interaction(
        &self,
        query: &str,
        context: &str,
        response: &str,
        metadata: InteractionMetadata,
    ) -> Result<PathBuf> {
        // Ensure log directory exists
        fs::create_dir_all(&self.log_dir)?;

        // Generate filename with timestamp
        let timestamp = Utc::now();
        let filename = format!("{}.md", timestamp.format("%Y-%m-%d-%H%M%S"));
        let file_path = self.log_dir.join(filename);

        // Build frontmatter
        let mut frontmatter = format!(
            "---\ntimestamp: {}\nuser_query: \"{}\"\nmodel: {}\n",
            timestamp.to_rfc3339(),
            query.replace('"', "\\\""),
            metadata.model
        );

        if let Some(tokens_in) = metadata.tokens_in {
            frontmatter.push_str(&format!("tokens_in: {}\n", tokens_in));
        }

        if let Some(tokens_out) = metadata.tokens_out {
            frontmatter.push_str(&format!("tokens_out: {}\n", tokens_out));
        }

        if let Some(duration_ms) = metadata.duration_ms {
            frontmatter.push_str(&format!("duration_ms: {}\n", duration_ms));
        }

        frontmatter.push_str("---\n\n");

        // Build content
        let content = format!(
            "{}# AI Interaction Log\n\n## User Query\n{}\n\n## Context Provided\n```\n{}\n```\n\n## AI Response\n{}\n\n## Actions Taken\n- Viewed response\n- No automated actions taken\n",
            frontmatter,
            query,
            context.lines().take(20).collect::<Vec<_>>().join("\n"), // Limit context preview
            response
        );

        // Write to file
        fs::write(&file_path, content)?;

        Ok(file_path)
    }
}
