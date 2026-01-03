// Phase Writer - Stub for DB-only architecture
// Original file-based methods replaced with placeholders
// TODO: Replace with SurrealStore calls

use crate::domain::Phase;
use crate::errors::{MetaError, Result};
use std::path::PathBuf;

pub struct PhaseWriter {
    #[allow(dead_code)]
    governance_root: PathBuf,
}

impl PhaseWriter {
    pub fn new(governance_root: PathBuf) -> Self {
        Self { governance_root }
    }

    /// Create a new phase
    pub fn create_phase(&self, _phase: &Phase) -> Result<PathBuf> {
        Err(MetaError::SystemError(
            "PhaseWriter deprecated: use SurrealStore.save_phase() instead".to_string(),
        ))
    }

    /// Update an existing phase
    pub fn update_phase(&self, _phase: &Phase) -> Result<()> {
        Err(MetaError::SystemError(
            "PhaseWriter deprecated: use SurrealStore.save_phase() instead".to_string(),
        ))
    }

    /// Delete a phase
    pub fn delete_phase(&self, _phase_id: &str) -> Result<()> {
        Err(MetaError::SystemError(
            "PhaseWriter deprecated: use SurrealStore directly".to_string(),
        ))
    }

    /// Set active phase (Stub)
    pub fn set_active_phase(&self, _phase_id: &str) -> Result<()> {
        Err(MetaError::SystemError(
            "PhaseWriter deprecated: use SurrealStore directly".to_string(),
        ))
    }
}
