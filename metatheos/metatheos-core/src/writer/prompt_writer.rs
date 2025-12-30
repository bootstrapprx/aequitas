use crate::domain::Prompt;
use crate::errors::{MetaError, Result};
use crate::writer::MarkdownWriter;
use chrono::Utc;
use std::fs;
use std::path::{Path, PathBuf};

pub struct PromptWriter {
    governance_root: PathBuf,
}

impl PromptWriter {
    pub fn new(governance_root: PathBuf) -> Self {
        Self { governance_root }
    }

    /// Create a new prompt
    pub fn create_prompt(&self, prompt: &Prompt) -> Result<PathBuf> {
        // Generate file path
        let prompts_dir = self.governance_root.join("06_PROMPTS");
        fs::create_dir_all(&prompts_dir)?;

        // Generate filename from prompt_id or title
        let file_name = if let Some(prompt_id) = &prompt.prompt_id {
            format!("{}.md", prompt_id)
        } else {
            let sanitized_title = prompt
                .title
                .chars()
                .filter(|c| c.is_alphanumeric() || *c == ' ' || *c == '-')
                .collect::<String>()
                .replace(' ', "-")
                .to_lowercase();
            format!("PROMPT-{}.md", sanitized_title)
        };

        let file_path = prompts_dir.join(&file_name);

        if file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "Prompt file already exists: {}",
                file_path.display()
            )));
        }

        // Generate markdown content
        let markdown = self.to_markdown(prompt)?;

        // Validate before writing
        self.validate(&markdown)?;

        // Write file
        self.write(&file_path, &markdown)?;

        Ok(file_path)
    }

    /// Update an existing prompt
    pub fn update_prompt(&self, prompt: &Prompt) -> Result<()> {
        let file_path = &prompt.file_path;

        if !file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "Prompt file does not exist: {}",
                file_path.display()
            )));
        }

        // Backup existing file
        self.backup(file_path)?;

        // Generate markdown content
        let markdown = self.to_markdown(prompt)?;

        // Validate before writing
        self.validate(&markdown)?;

        // Write file
        self.write(file_path, &markdown)?;

        Ok(())
    }

    /// Delete a prompt (archives it)
    pub fn delete_prompt(&self, file_path: &Path) -> Result<()> {
        if !file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "Prompt file does not exist: {}",
                file_path.display()
            )));
        }

        // Create archive directory
        let archive_dir = self.governance_root.join("06_PROMPTS").join("_archive");
        fs::create_dir_all(&archive_dir)?;

        // Move to archive
        let file_name = file_path
            .file_name()
            .ok_or_else(|| MetaError::ValidationError("Invalid file path".to_string()))?;
        let archive_path = archive_dir.join(file_name);

        fs::rename(file_path, &archive_path)?;

        Ok(())
    }

    /// Convert Prompt to markdown format
    fn to_markdown(&self, prompt: &Prompt) -> Result<String> {
        let mut frontmatter = serde_yaml::Mapping::new();

        // Add frontmatter fields
        frontmatter.insert(
            serde_yaml::Value::String("type".to_string()),
            serde_yaml::Value::String("prompt".to_string()),
        );

        if let Some(prompt_id) = &prompt.prompt_id {
            frontmatter.insert(
                serde_yaml::Value::String("id".to_string()),
                serde_yaml::Value::String(prompt_id.clone()),
            );
        }

        if let Some(agent) = &prompt.agent {
            frontmatter.insert(
                serde_yaml::Value::String("agent".to_string()),
                serde_yaml::Value::String(agent.clone()),
            );
        }

        if let Some(purpose) = &prompt.purpose {
            frontmatter.insert(
                serde_yaml::Value::String("purpose".to_string()),
                serde_yaml::Value::String(purpose.clone()),
            );
        }

        if let Some(timestamp) = prompt.timestamp {
            frontmatter.insert(
                serde_yaml::Value::String("timestamp".to_string()),
                serde_yaml::Value::String(timestamp.to_rfc3339()),
            );
        }

        if let Some(prompt_text) = &prompt.prompt_text {
            frontmatter.insert(
                serde_yaml::Value::String("prompt_text".to_string()),
                serde_yaml::Value::String(prompt_text.clone()),
            );
        }

        // Serialize frontmatter
        let fm_str = serde_yaml::to_string(&frontmatter)
            .map_err(|e| MetaError::ValidationError(format!("Failed to serialize frontmatter: {}", e)))?;

        // Build full markdown
        let markdown = format!("---\n{}---\n\n# {}\n\n{}", fm_str, prompt.title, prompt.content);

        Ok(markdown)
    }
}

impl MarkdownWriter for PromptWriter {
    fn write(&self, path: &Path, content: &str) -> Result<()> {
        // Atomic write: write to temp file then rename
        let temp_path = path.with_extension("tmp");
        fs::write(&temp_path, content)?;
        fs::rename(&temp_path, path)?;
        Ok(())
    }

    fn backup(&self, path: &Path) -> Result<Option<PathBuf>> {
        if !path.exists() {
            return Ok(None);
        }

        let backup_dir = path.parent().unwrap().join(".backup");
        fs::create_dir_all(&backup_dir)?;

        let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
        let file_name = path.file_name().unwrap();
        let backup_path = backup_dir.join(format!("{}.{}.bak", file_name.to_string_lossy(), timestamp));

        fs::copy(path, &backup_path)?;
        Ok(Some(backup_path))
    }

    fn validate(&self, content: &str) -> Result<()> {
        if content.trim().is_empty() {
            return Err(MetaError::ValidationError(
                "Prompt content cannot be empty".to_string(),
            ));
        }

        if !content.starts_with("---") {
            return Err(MetaError::ValidationError(
                "Prompt must have frontmatter".to_string(),
            ));
        }

        Ok(())
    }
}
