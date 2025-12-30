use crate::domain::Prompt;
use crate::errors::{MetaError, Result};
use crate::writer::{ensure_governance_layout, MarkdownWriter};
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
        ensure_governance_layout(&self.governance_root)?;
        self.validate_metadata(prompt)?;
        // Generate file path
        let prompts_dir = self.governance_root.join("06_PROMPTS").join("library");
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
        ensure_governance_layout(&self.governance_root)?;
        self.validate_metadata(prompt)?;
        let file_path = &prompt.file_path;

        if !file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "Prompt file does not exist: {}",
                file_path.display()
            )));
        }
        self.ensure_library_path(file_path)?;

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
        ensure_governance_layout(&self.governance_root)?;
        if !file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "Prompt file does not exist: {}",
                file_path.display()
            )));
        }
        self.ensure_library_path(file_path)?;

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

        if let Some(origin) = &prompt.origin {
            frontmatter.insert(
                serde_yaml::Value::String("origin".to_string()),
                serde_yaml::Value::String(origin.clone()),
            );
        }

        if let Some(status) = &prompt.status {
            frontmatter.insert(
                serde_yaml::Value::String("status".to_string()),
                serde_yaml::Value::String(status.clone()),
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

    fn validate_metadata(&self, prompt: &Prompt) -> Result<()> {
        // Require core governance fields for curated prompts
        let mut missing = Vec::new();
        if prompt.prompt_id.as_ref().map(|id| id.trim().is_empty()).unwrap_or(true) {
            missing.push("id");
        }
        if prompt.agent.as_ref().map(|id| id.trim().is_empty()).unwrap_or(true) {
            missing.push("agent");
        }
        if prompt.purpose.as_ref().map(|id| id.trim().is_empty()).unwrap_or(true) {
            missing.push("purpose");
        }
        if prompt.origin.as_ref().map(|id| id.trim().is_empty()).unwrap_or(true) {
            missing.push("origin");
        }
        if prompt.status.as_ref().map(|id| id.trim().is_empty()).unwrap_or(true) {
            missing.push("status");
        }

        if !missing.is_empty() {
            return Err(MetaError::ValidationError(format!(
                "Prompt is missing required metadata: {}",
                missing.join(", ")
            )));
        }

        if let Some(status) = &prompt.status {
            let allowed = ["draft", "active", "deprecated"];
            if !allowed.contains(&status.to_lowercase().as_str()) {
                return Err(MetaError::ValidationError(format!(
                    "Invalid prompt status '{}'. Use draft|active|deprecated",
                    status
                )));
            }
        }

        Ok(())
    }

    fn ensure_library_path(&self, path: &Path) -> Result<()> {
        let library_root = self.governance_root.join("06_PROMPTS").join("library");
        if !path.starts_with(&library_root) {
            return Err(MetaError::ValidationError(
                "Prompts must live under 06_PROMPTS/library (logs are excluded)".to_string(),
            ));
        }
        Ok(())
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

        // Basic YAML validation and required fields
        let end = content[4..]
            .find("---")
            .ok_or_else(|| MetaError::ValidationError("Prompt frontmatter must end with ---".to_string()))?
            + 4;
        let yaml_part = &content[4..end];

        let value: serde_yaml::Value = serde_yaml::from_str(yaml_part).map_err(|e| {
            MetaError::ValidationError(format!("Invalid YAML frontmatter: {}", e))
        })?;

        let mapping = value.as_mapping().ok_or_else(|| {
            MetaError::ValidationError("Prompt frontmatter must be a mapping".to_string())
        })?;

        let required = ["id", "agent", "purpose", "origin", "status"];
        let mut missing = Vec::new();
        for key in &required {
            if !mapping.contains_key(&serde_yaml::Value::String(key.to_string())) {
                missing.push(*key);
            }
        }
        if !missing.is_empty() {
            return Err(MetaError::ValidationError(format!(
                "Prompt missing required metadata: {}",
                missing.join(", ")
            )));
        }

        if let Some(status_value) = mapping
            .get(&serde_yaml::Value::String("status".to_string()))
            .and_then(|v| v.as_str())
        {
            let allowed = ["draft", "active", "deprecated"];
            if !allowed.contains(&status_value.to_lowercase().as_str()) {
                return Err(MetaError::ValidationError(format!(
                    "Invalid prompt status '{}'. Use draft|active|deprecated",
                    status_value
                )));
            }
        }

        Ok(())
    }
}
