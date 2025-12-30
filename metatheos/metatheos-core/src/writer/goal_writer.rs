use crate::domain::Goal;
use crate::errors::{MetaError, Result};
use crate::governance::GovernanceContext;
use crate::writer::{ensure_governance_layout, FrontmatterSerializer, MarkdownWriter};
use chrono::Utc;
use std::fs;
use std::path::{Path, PathBuf};

pub struct GoalWriter {
    governance_root: PathBuf,
}

impl GoalWriter {
    pub fn new(governance_root: PathBuf) -> Self {
        Self { governance_root }
    }

    /// Create a new goal
    pub fn create_goal(&self, goal: &Goal) -> Result<PathBuf> {
        ensure_governance_layout(&self.governance_root)?;
        // Validate goal ID is unique
        let ctx = GovernanceContext::load(&self.governance_root)?;
        if ctx.all_goals().iter().any(|g| g.goal_id == goal.goal_id) {
            return Err(MetaError::ValidationError(format!(
                "Goal with ID '{}' already exists",
                goal.goal_id
            )));
        }

        // Validate dependencies exist
        for dep_id in &goal.dependencies {
            if !ctx.all_goals().iter().any(|g| g.goal_id == *dep_id) {
                return Err(MetaError::ValidationError(format!(
                    "Dependency '{}' does not exist",
                    dep_id
                )));
            }
        }

        // Generate file path
        let goals_dir = self.governance_root.join("03_GOALS_EPICS");
        fs::create_dir_all(&goals_dir)?;

        let file_path = goals_dir.join(format!("{}.md", goal.goal_id));

        if file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "File already exists: {}",
                file_path.display()
            )));
        }

        // Generate markdown content
        let markdown = self.to_markdown(goal)?;

        // Validate before writing
        self.validate(&markdown)?;

        // Write file
        self.write(&file_path, &markdown)?;

        // Create audit entry
        self.create_audit_entry("goal_created", &goal.goal_id, "Created new goal")?;

        Ok(file_path)
    }

    /// Update an existing goal
    pub fn update_goal(&self, goal: &Goal) -> Result<()> {
        ensure_governance_layout(&self.governance_root)?;
        // Validate goal exists
        let ctx = GovernanceContext::load(&self.governance_root)?;
        let existing = ctx
            .all_goals()
            .iter()
            .find(|g| g.goal_id == goal.goal_id)
            .cloned()
            .ok_or_else(|| {
                MetaError::ValidationError(format!("Goal '{}' does not exist", goal.goal_id))
            })?;

        // Validate status transition
        if !existing.status.can_transition_to(&goal.status) {
            return Err(MetaError::ValidationError(format!(
                "Cannot transition from '{}' to '{}'",
                existing.status, goal.status
            )));
        }

        // Validate dependencies exist
        for dep_id in &goal.dependencies {
            if !ctx.all_goals().iter().any(|g| g.goal_id == *dep_id) {
                return Err(MetaError::ValidationError(format!(
                    "Dependency '{}' does not exist",
                    dep_id
                )));
            }
        }

        let file_path = &existing.file_path;

        // Backup existing file
        self.backup(file_path)?;

        // Generate markdown content
        let markdown = self.to_markdown(goal)?;

        // Validate before writing
        self.validate(&markdown)?;

        // Write file
        self.write(file_path, &markdown)?;

        // Create audit entry
        self.create_audit_entry(
            "goal_updated",
            &goal.goal_id,
            &format!("Updated goal (status: {})", goal.status.as_str()),
        )?;

        Ok(())
    }

    /// Delete a goal (archives it)
    pub fn delete_goal(&self, goal_id: &str) -> Result<()> {
        ensure_governance_layout(&self.governance_root)?;
        // Load context to check dependencies
        let ctx = GovernanceContext::load(&self.governance_root)?;

        let goal = ctx
            .all_goals()
            .iter()
            .find(|g| g.goal_id == goal_id)
            .cloned()
            .ok_or_else(|| MetaError::ValidationError(format!("Goal '{}' does not exist", goal_id)))?;

        // Check if any other goals depend on this one
        let dependents: Vec<String> = ctx
            .all_goals()
            .iter()
            .filter(|g| g.dependencies.contains(&goal_id.to_string()))
            .map(|g| g.goal_id.clone())
            .collect();

        if !dependents.is_empty() {
            return Err(MetaError::ValidationError(format!(
                "Cannot delete goal '{}': it is depended on by: {}",
                goal_id,
                dependents.join(", ")
            )));
        }

        // Create archive directory
        let archive_dir = self.governance_root.join("03_GOALS_EPICS").join(".archive");
        fs::create_dir_all(&archive_dir)?;

        // Move file to archive
        let archived_name = format!(
            "{}-{}.md",
            goal_id,
            Utc::now().format("%Y%m%d-%H%M%S")
        );
        let archive_path = archive_dir.join(archived_name);

        fs::rename(&goal.file_path, &archive_path)?;

        // Create audit entry
        self.create_audit_entry(
            "goal_deleted",
            goal_id,
            &format!("Archived goal to {}", archive_path.display()),
        )?;

        Ok(())
    }

    /// Convert goal to markdown format
    fn to_markdown(&self, goal: &Goal) -> Result<String> {
        // Generate frontmatter
        let frontmatter = FrontmatterSerializer::goal_to_yaml(goal)?;

        // Build complete document
        Ok(FrontmatterSerializer::build_document(&frontmatter, &goal.content))
    }

    /// Create audit entry for goal operation
    fn create_audit_entry(&self, action: &str, goal_id: &str, details: &str) -> Result<()> {
        let audit_dir = self.governance_root.join("05_AUDITS");
        fs::create_dir_all(&audit_dir)?;

        let timestamp = Utc::now();
        let filename = format!("{}.md", timestamp.format("%Y-%m-%d-%H%M%S"));
        let audit_path = audit_dir.join(filename);

        let frontmatter = format!(
            "timestamp: {}\naction: {}\ngoal_id: {}\nuser: system\n",
            timestamp.to_rfc3339(),
            action,
            goal_id
        );

        let content = format!("# {}\n\n{}", action.replace('_', " ").to_uppercase(), details);

        let markdown = FrontmatterSerializer::build_document(&frontmatter, &content);

        fs::write(&audit_path, markdown)?;

        Ok(())
    }
}

impl MarkdownWriter for GoalWriter {
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
        // Check has frontmatter delimiters
        if !content.starts_with("---\n") {
            return Err(MetaError::ValidationError(
                "Content must start with YAML frontmatter (---)".to_string(),
            ));
        }

        // Check has ending delimiter
        if !content[4..].contains("---\n") {
            return Err(MetaError::ValidationError(
                "Frontmatter must end with --- delimiter".to_string(),
            ));
        }

        // Basic YAML validation (try to parse)
        let end = content[4..].find("---\n").unwrap() + 4;
        let yaml_part = &content[4..end];

        serde_yaml::from_str::<serde_yaml::Value>(yaml_part).map_err(|e| {
            MetaError::ParseError(format!("Invalid YAML frontmatter: {}", e))
        })?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::GoalStatus;
    use std::path::PathBuf;

    #[test]
    fn test_goal_writer_validation() {
        let writer = GoalWriter::new(PathBuf::from("/tmp"));

        // Valid content
        let valid = "---\ngoal_id: test\n---\n\n# Content";
        assert!(writer.validate(valid).is_ok());

        // Missing frontmatter
        let invalid = "# Content without frontmatter";
        assert!(writer.validate(invalid).is_err());
    }

    #[test]
    fn test_to_markdown() {
        let writer = GoalWriter::new(PathBuf::from("/tmp"));
        let goal = Goal {
            goal_id: "goal-test".to_string(),
            title: "Test Goal".to_string(),
            status: GoalStatus::Active,
            phase: Some("P1".to_string()),
            owner: None,
            dependencies: vec![],
            canon: vec![],
            tags: vec![],
            updated: None,
            file_path: PathBuf::from("test.md"),
            content: "# Test Goal\n\nThis is the content.".to_string(),
        };

        let markdown = writer.to_markdown(&goal).unwrap();

        assert!(markdown.starts_with("---\n"));
        assert!(markdown.contains("goal_id: goal-test"));
        assert!(markdown.contains("# Test Goal"));
        assert!(markdown.contains("This is the content."));
    }
}
