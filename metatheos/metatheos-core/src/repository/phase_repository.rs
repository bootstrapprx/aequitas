/// Phase Repository - Database access layer for phases
///
/// Handles all CRUD operations for phases.

use crate::errors::{MetaError, Result};
use crate::store::dto::PhaseDto;
use crate::store::SurrealStore;
use crate::Phase;
use std::sync::Arc;

/// Repository for phase database operations
pub struct PhaseRepository {
    store: Arc<SurrealStore>,
}

impl PhaseRepository {
    pub fn new(store: Arc<SurrealStore>) -> Self {
        Self { store }
    }

    /// Create a new phase
    pub async fn create(&self, phase: Phase) -> Result<String> {
        let phase_id = phase.phase_id.clone();
        let dto = PhaseDto::from(phase);

        let _: Option<serde_json::Value> = self.store
            .get_db()
            .create(("phase", phase_id.as_str()))
            .content(dto)
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!("Failed to create phase {}: {}", phase_id, e))
            })?;

        Ok(phase_id)
    }

    /// Get a phase by ID
    pub async fn get_by_id(&self, phase_id: &str) -> Result<Option<Phase>> {
        let dto: Option<PhaseDto> = self
            .store
            .get_db()
            .select(("phase", phase_id))
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!("Failed to get phase {}: {}", phase_id, e))
            })?;

        Ok(dto.map(|d| d.into_phase()))
    }

    /// Get a phase by ID (returns error if not found)
    pub async fn get_by_id_or_error(&self, phase_id: &str) -> Result<Phase> {
        self.get_by_id(phase_id)
            .await?
            .ok_or_else(|| MetaError::PhaseNotFound(phase_id.to_string()))
    }

    /// Update an existing phase
    pub async fn update(&self, phase: Phase) -> Result<()> {
        let phase_id = phase.phase_id.clone();
        let dto = PhaseDto::from(phase);

        self.store
            .get_db()
            .update::<Option<serde_json::Value>>(("phase", phase_id.as_str()))
            .content(dto)
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!("Failed to update phase {}: {}", phase_id, e))
            })?;

        Ok(())
    }

    /// Delete a phase (sets status to archived)
    pub async fn delete(&self, phase_id: &str) -> Result<()> {
        let mut phase = self.get_by_id_or_error(phase_id).await?;
        phase.status = "archived".to_string();
        self.update(phase).await
    }

    /// Get all phases
    pub async fn get_all(&self) -> Result<Vec<Phase>> {
        self.store.get_all_phases().await
    }

    /// Get active phase
    pub async fn get_active(&self) -> Result<Option<Phase>> {
        if let Some(phase_id) = self.store.get_meta("active_phase").await? {
            self.get_by_id(&phase_id).await
        } else {
            Ok(None)
        }
    }

    /// Set active phase
    pub async fn set_active(&self, phase_id: &str) -> Result<()> {
        // Verify phase exists
        self.get_by_id_or_error(phase_id).await?;

        // Set as active
        self.store
            .set_meta("active_phase", phase_id)
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!("Failed to set active phase: {}", e))
            })
    }
}
