use crate::domain::Phase;
use crate::errors::{MetaError, Result};
use crate::governance::GovernanceContext;
use crate::writer::{ensure_governance_layout, FrontmatterSerializer, MarkdownWriter};
use chrono::Utc;
use std::fs;
use std::path::{Path, PathBuf};

pub struct PhaseWriter {
    governance_root: PathBuf,
}

impl PhaseWriter {
    pub fn new(governance_root: PathBuf) -> Self {
        Self { governance_root }
    }

    /// Create a new phase
    pub fn create_phase(&self, phase: &Phase) -> Result<PathBuf> {
        ensure_governance_layout(&self.governance_root)?;
        // Validate phase ID is unique
        let ctx = GovernanceContext::load(&self.governance_root)?;
        if ctx.all_phases().iter().any(|p| p.phase_id == phase.phase_id) {
            return Err(MetaError::ValidationError(format!(
                "Phase with ID '{}' already exists",
                phase.phase_id
            )));
        }

        // Validate dependencies exist
        for dep_id in &phase.dependencies {
            if !ctx.all_phases().iter().any(|p| p.phase_id == *dep_id) {
                return Err(MetaError::ValidationError(format!(
                    "Phase dependency '{}' does not exist",
                    dep_id
                )));
            }
        }

        // Generate file path
        let phases_dir = self.governance_root.join("02_PHASES");
        fs::create_dir_all(&phases_dir)?;

        let file_path = phases_dir.join(format!("{}.md", phase.phase_id));

        if file_path.exists() {
            return Err(MetaError::ValidationError(format!(
                "File already exists: {}",
                file_path.display()
            )));
        }

        // Generate markdown content
        let markdown = self.to_markdown(phase)?;

        // Validate before writing
        self.validate(&markdown)?;

        // Write file
        self.write(&file_path, &markdown)?;

        // Create audit entry
        self.create_audit_entry("phase_created", &phase.phase_id, "Created new phase")?;

        Ok(file_path)
    }

    /// Update an existing phase
    pub fn update_phase(&self, phase: &Phase) -> Result<()> {
        ensure_governance_layout(&self.governance_root)?;
        // Validate phase exists
        let ctx = GovernanceContext::load(&self.governance_root)?;
        let existing = ctx
            .all_phases()
            .iter()
            .find(|p| p.phase_id == phase.phase_id)
            .cloned()
            .ok_or_else(|| {
                MetaError::ValidationError(format!("Phase '{}' does not exist", phase.phase_id))
            })?;

        // Validate dependencies exist
        for dep_id in &phase.dependencies {
            if !ctx.all_phases().iter().any(|p| p.phase_id == *dep_id) {
                return Err(MetaError::ValidationError(format!(
                    "Phase dependency '{}' does not exist",
                    dep_id
                )));
            }
        }

        let file_path = &existing.file_path;

        // Backup existing file
        self.backup(file_path)?;

        // Generate markdown content
        let markdown = self.to_markdown(phase)?;

        // Validate before writing
        self.validate(&markdown)?;

        // Write file
        self.write(file_path, &markdown)?;

        // Create audit entry
        self.create_audit_entry(
            "phase_updated",
            &phase.phase_id,
            &format!("Updated phase (status: {})", phase.status),
        )?;

        Ok(())
    }

    /// Set a phase as active (deactivates others)
    pub fn set_active_phase(&self, phase_id: &str) -> Result<()> {
        ensure_governance_layout(&self.governance_root)?;
        let ctx = GovernanceContext::load(&self.governance_root)?;

        // Validate phase exists
        let target_phase = ctx
            .all_phases()
            .iter()
            .find(|p| p.phase_id == phase_id)
            .cloned()
            .ok_or_else(|| {
                MetaError::ValidationError(format!("Phase '{}' does not exist", phase_id))
            })?;

        // Find currently active phase
        let currently_active = ctx.active_phase();

        // If already active, nothing to do
        if let Some(active) = currently_active {
            if active.phase_id == phase_id {
                return Ok(());
            }

            // Deactivate current phase
            let mut deactivated = active.clone();
            deactivated.status = "inactive".to_string();
            self.update_phase(&deactivated)?;
        }

        // Activate target phase
        let mut activated = target_phase.clone();
        activated.status = "active".to_string();
        self.update_phase(&activated)?;

        // Create audit entry
        self.create_audit_entry(
            "phase_activated",
            phase_id,
            &format!("Activated phase '{}'", phase_id),
        )?;

        Ok(())
    }

    /// Convert phase to markdown format
    fn to_markdown(&self, phase: &Phase) -> Result<String> {
        // Generate frontmatter
        let frontmatter = FrontmatterSerializer::phase_to_yaml(phase)?;

        // Build complete document
        Ok(FrontmatterSerializer::build_document(&frontmatter, &phase.content))
    }

    /// Create audit entry for phase operation
    fn create_audit_entry(&self, action: &str, phase_id: &str, details: &str) -> Result<()> {
        let audit_dir = self.governance_root.join("05_AUDITS");
        fs::create_dir_all(&audit_dir)?;

        let timestamp = Utc::now();
        let filename = format!("{}.md", timestamp.format("%Y-%m-%d-%H%M%S"));
        let audit_path = audit_dir.join(filename);

        let frontmatter = format!(
            "timestamp: {}\naction: {}\nphase_id: {}\nuser: system\n",
            timestamp.to_rfc3339(),
            action,
            phase_id
        );

        let content = format!("# {}\n\n{}", action.replace('_', " ").to_uppercase(), details);

        let markdown = FrontmatterSerializer::build_document(&frontmatter, &content);

        fs::write(&audit_path, markdown)?;

        Ok(())
    }
}

impl MarkdownWriter for PhaseWriter {
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

        // Basic YAML validation
        let end = content[4..].find("---\n").unwrap() + 4;
        let yaml_part = &content[4..end];

        serde_yaml::from_str::<serde_yaml::Value>(yaml_part).map_err(|e| {
            MetaError::ParseError(format!("Invalid YAML frontmatter: {}", e))
        })?;

        Ok(())
    }
}
