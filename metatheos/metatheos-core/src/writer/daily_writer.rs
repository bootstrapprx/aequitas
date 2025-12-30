use crate::errors::{MetaError, Result};
use crate::writer::{ensure_governance_layout, MarkdownWriter};
use chrono::{NaiveDate, Utc};
use std::fs;
use std::path::{Path, PathBuf};

pub struct DailyWriter {
    governance_root: PathBuf,
}

impl DailyWriter {
    pub fn new(governance_root: PathBuf) -> Self {
        Self { governance_root }
    }

    /// Create or update a daily note
    /// This combines create and update since daily notes don't have complex frontmatter
    pub fn write_daily_note(&self, date: NaiveDate, content: &str) -> Result<PathBuf> {
        ensure_governance_layout(&self.governance_root)?;
        let daily_dir = self.governance_root.join("01_DAILY");
        fs::create_dir_all(&daily_dir)?;

        let filename = format!("{}.md", date.format("%Y-%m-%d"));
        let file_path = daily_dir.join(filename);

        // Backup if exists
        if file_path.exists() {
            self.backup(&file_path)?;
        }

        // Validate content
        self.validate(content)?;

        // Write file
        self.write(&file_path, content)?;

        // Create audit entry
        let action = if file_path.exists() {
            "daily_note_updated"
        } else {
            "daily_note_created"
        };
        self.create_audit_entry(action, &date.to_string())?;

        Ok(file_path)
    }

    /// Delete a daily note (archives it)
    pub fn delete_daily_note(&self, date: NaiveDate) -> Result<()> {
        ensure_governance_layout(&self.governance_root)?;
        let daily_dir = self.governance_root.join("01_DAILY");
        let filename = format!("{}.md", date.format("%Y-%m-%d"));
        let file_path = daily_dir.join(&filename);

        if !file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "Daily note for {} does not exist",
                date
            )));
        }

        // Create archive directory
        let archive_dir = daily_dir.join(".archive");
        fs::create_dir_all(&archive_dir)?;

        // Move file to archive
        let archived_name = format!(
            "{}-{}.md",
            date.format("%Y-%m-%d"),
            Utc::now().format("%Y%m%d-%H%M%S")
        );
        let archive_path = archive_dir.join(archived_name);

        fs::rename(&file_path, &archive_path)?;

        // Create audit entry
        self.create_audit_entry(
            "daily_note_deleted",
            &format!("Archived note for {} to {}", date, archive_path.display()),
        )?;

        Ok(())
    }

    /// Create audit entry for daily note operation
    fn create_audit_entry(&self, action: &str, details: &str) -> Result<()> {
        let audit_dir = self.governance_root.join("05_AUDITS");
        fs::create_dir_all(&audit_dir)?;

        let timestamp = Utc::now();
        let filename = format!("{}.md", timestamp.format("%Y-%m-%d-%H%M%S"));
        let audit_path = audit_dir.join(filename);

        let content = format!(
            "---\ntimestamp: {}\naction: {}\nuser: system\n---\n\n# {}\n\n{}",
            timestamp.to_rfc3339(),
            action,
            action.replace('_', " ").to_uppercase(),
            details
        );

        fs::write(&audit_path, content)?;

        Ok(())
    }
}

impl MarkdownWriter for DailyWriter {
    fn write(&self, path: &Path, content: &str) -> Result<()> {
        // Atomic write: write to temp file, then rename
        let temp_path = path.with_extension("md.tmp");
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

        let filename = path.file_name().unwrap();
        let backup_name = format!(
            "{}-{}",
            Utc::now().format("%Y%m%d-%H%M%S"),
            filename.to_string_lossy()
        );
        let backup_path = backup_dir.join(backup_name);

        fs::copy(path, &backup_path)?;

        Ok(Some(backup_path))
    }

    fn validate(&self, content: &str) -> Result<()> {
        // Daily notes have simpler validation - just check it's not empty
        if content.trim().is_empty() {
            return Err(MetaError::ValidationError(
                "Daily note content cannot be empty".to_string(),
            ));
        }

        // Basic markdown check - should have at least one heading or paragraph
        if !content.contains('#') && !content.contains('\n') {
            return Err(MetaError::ValidationError(
                "Daily note should contain markdown content".to_string(),
            ));
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_daily_writer_validation() {
        let writer = DailyWriter::new(PathBuf::from("/tmp"));

        // Valid content
        let valid = "# Daily Note\n\nSome content here.";
        assert!(writer.validate(valid).is_ok());

        // Empty content
        let empty = "";
        assert!(writer.validate(empty).is_err());

        // Only whitespace
        let whitespace = "   \n\n  ";
        assert!(writer.validate(whitespace).is_err());
    }
}
