use crate::domain::AuditRecord;
use crate::errors::{MetaError, Result};
use crate::writer::{ensure_governance_layout, MarkdownWriter};
use chrono::{Utc, Datelike};
use std::fs;
use std::path::{Path, PathBuf};

pub struct AuditWriter {
    governance_root: PathBuf,
}

impl AuditWriter {
    pub fn new(governance_root: PathBuf) -> Self {
        Self { governance_root }
    }

    /// Create a new audit record
    pub fn create_audit(&self, audit: &AuditRecord) -> Result<PathBuf> {
        ensure_governance_layout(&self.governance_root)?;
        // Generate file path based on date and title
        let audits_dir = self.governance_root.join("05_AUDITS");
        fs::create_dir_all(&audits_dir)?;

        // Generate filename from date and title
        let date_str = audit
            .date
            .map(|d| format!("{}-{:02}-{:02}", d.year(), d.month(), d.day()))
            .unwrap_or_else(|| {
                let now = Utc::now();
                format!("{}-{:02}-{:02}", now.year(), now.month(), now.day())
            });

        let sanitized_title = audit
            .title
            .chars()
            .filter(|c| c.is_alphanumeric() || *c == ' ' || *c == '-')
            .collect::<String>()
            .replace(' ', "-")
            .to_lowercase();

        let file_path = audits_dir.join(format!("AUDIT-{}-{}.md", date_str, sanitized_title));

        if file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "Audit file already exists: {}",
                file_path.display()
            )));
        }

        // Generate markdown content
        let markdown = self.to_markdown(audit)?;

        // Validate before writing
        self.validate(&markdown)?;

        // Write file
        self.write(&file_path, &markdown)?;

        Ok(file_path)
    }

    /// Update an existing audit record
    pub fn update_audit(&self, audit: &AuditRecord) -> Result<()> {
        ensure_governance_layout(&self.governance_root)?;
        let file_path = &audit.file_path;

        if !file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "Audit file does not exist: {}",
                file_path.display()
            )));
        }

        // Backup existing file
        self.backup(file_path)?;

        // Generate markdown content
        let markdown = self.to_markdown(audit)?;

        // Validate before writing
        self.validate(&markdown)?;

        // Write file
        self.write(file_path, &markdown)?;

        Ok(())
    }

    /// Delete an audit record (archives it)
    pub fn delete_audit(&self, file_path: &Path) -> Result<()> {
        ensure_governance_layout(&self.governance_root)?;
        if !file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "Audit file does not exist: {}",
                file_path.display()
            )));
        }

        // Create archive directory
        let archive_dir = self.governance_root.join("05_AUDITS").join("_archive");
        fs::create_dir_all(&archive_dir)?;

        // Move to archive
        let file_name = file_path
            .file_name()
            .ok_or_else(|| MetaError::ValidationError("Invalid file path".to_string()))?;
        let archive_path = archive_dir.join(file_name);

        fs::rename(file_path, &archive_path)?;

        Ok(())
    }

    /// Convert AuditRecord to markdown format
    fn to_markdown(&self, audit: &AuditRecord) -> Result<String> {
        let mut frontmatter = serde_yaml::Mapping::new();

        // Add frontmatter fields
        frontmatter.insert(
            serde_yaml::Value::String("type".to_string()),
            serde_yaml::Value::String("audit".to_string()),
        );

        if let Some(date) = audit.date {
            frontmatter.insert(
                serde_yaml::Value::String("date".to_string()),
                serde_yaml::Value::String(date.format("%Y-%m-%d").to_string()),
            );
        }

        if let Some(scope) = &audit.scope {
            frontmatter.insert(
                serde_yaml::Value::String("scope".to_string()),
                serde_yaml::Value::String(scope.clone()),
            );
        }

        if let Some(risk) = &audit.risk {
            frontmatter.insert(
                serde_yaml::Value::String("risk".to_string()),
                serde_yaml::Value::String(risk.clone()),
            );
        }

        if let Some(auditor) = &audit.auditor {
            frontmatter.insert(
                serde_yaml::Value::String("auditor".to_string()),
                serde_yaml::Value::String(auditor.clone()),
            );
        }

        if let Some(status) = &audit.status {
            frontmatter.insert(
                serde_yaml::Value::String("status".to_string()),
                serde_yaml::Value::String(status.clone()),
            );
        }

        if let Some(evidence) = &audit.evidence {
            frontmatter.insert(
                serde_yaml::Value::String("evidence".to_string()),
                serde_yaml::Value::String(evidence.clone()),
            );
        }

        if let Some(summary) = &audit.summary {
            frontmatter.insert(
                serde_yaml::Value::String("summary".to_string()),
                serde_yaml::Value::String(summary.clone()),
            );
        }

        // Serialize frontmatter
        let fm_str = serde_yaml::to_string(&frontmatter)
            .map_err(|e| MetaError::ValidationError(format!("Failed to serialize frontmatter: {}", e)))?;

        // Build full markdown
        let markdown = format!("---\n{}---\n\n# {}\n\n{}", fm_str, audit.title, audit.content);

        Ok(markdown)
    }
}

impl MarkdownWriter for AuditWriter {
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
                "Audit content cannot be empty".to_string(),
            ));
        }

        if !content.starts_with("---") {
            return Err(MetaError::ValidationError(
                "Audit must have frontmatter".to_string(),
            ));
        }

        Ok(())
    }
}
