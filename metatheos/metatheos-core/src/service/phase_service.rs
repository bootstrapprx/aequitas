/// Phase Service - Business logic for phase operations
///
/// Handles phase lifecycle, activation, and business rules.

use crate::errors::{MetaError, Result};
use crate::repository::PhaseRepository;
use crate::store::SurrealStore;
use crate::{Event, EventAction, Phase};
use std::sync::Arc;

/// Service for phase business operations
pub struct PhaseService {
    repository: PhaseRepository,
    store: Arc<SurrealStore>,
}

impl PhaseService {
    pub fn new(store: Arc<SurrealStore>) -> Self {
        Self {
            repository: PhaseRepository::new(store.clone()),
            store,
        }
    }

    /// Create a new phase
    pub async fn create_phase(&self, phase: Phase) -> Result<String> {
        // Validate phase_id is unique
        if self.repository.get_by_id(&phase.phase_id).await?.is_some() {
            return Err(MetaError::AlreadyExists {
                resource_type: "Phase".to_string(),
                id: phase.phase_id.clone(),
            });
        }

        // Create phase
        let phase_id = self.repository.create(phase.clone()).await?;

        // Log event
        let event = Event::new(
            "phase",
            &phase_id,
            EventAction::Create,
            "user",
            serde_json::json!({
                "title": phase.title,
                "status": phase.status,
            }),
        );
        let _ = self.store.log_event(&event).await;

        Ok(phase_id)
    }

    /// Update an existing phase
    pub async fn update_phase(&self, phase: Phase) -> Result<()> {
        // Verify phase exists
        self.repository.get_by_id_or_error(&phase.phase_id).await?;

        // Validate dependencies exist
        for dep_id in &phase.dependencies {
            self.repository.get_by_id_or_error(dep_id).await?;
        }

        // Perform update
        self.repository.update(phase.clone()).await?;

        // Log event
        let event = Event::new(
            "phase",
            &phase.phase_id,
            EventAction::Update,
            "user",
            serde_json::json!({
                "title": phase.title,
                "status": phase.status,
            }),
        );
        let _ = self.store.log_event(&event).await;

        Ok(())
    }

    /// Set a phase as active
    pub async fn set_active_phase(&self, phase_id: &str) -> Result<()> {
        // Verify phase exists
        self.repository.get_by_id_or_error(phase_id).await?;

        // Set as active
        self.repository.set_active(phase_id).await?;

        // Log event
        let event = Event::new(
            "phase",
            phase_id,
            EventAction::Update,
            "system",
            serde_json::json!({
                "set_active": true,
            }),
        );
        let _ = self.store.log_event(&event).await;

        Ok(())
    }

    /// Get active phase
    pub async fn get_active_phase(&self) -> Result<Option<Phase>> {
        self.repository.get_active().await
    }

    /// Get phase by ID
    pub async fn get_phase(&self, phase_id: &str) -> Result<Option<Phase>> {
        self.repository.get_by_id(phase_id).await
    }

    /// Get all phases
    pub async fn get_all_phases(&self) -> Result<Vec<Phase>> {
        self.repository.get_all().await
    }

    /// Delete (archive) a phase
    pub async fn delete_phase(&self, phase_id: &str) -> Result<()> {
        // Check if phase has active goals
        let phase_id_owned = phase_id.to_string();
        let mut response = self
            .store
            .get_db()
            .query("SELECT * FROM goal WHERE phase_id = $phase_id AND status != 'archived'")
            .bind(("phase_id", phase_id_owned.clone()))
            .await
            .map_err(|e| MetaError::DatabaseQuery(format!("Failed to check phase goals: {}", e)))?;

        let goals: Vec<crate::Goal> = response.take(0)
            .map_err(|e| {
                MetaError::DatabaseSerialization(format!("Failed to parse goals: {}", e))
            })?;

        if !goals.is_empty() {
            return Err(MetaError::OperationNotPermitted(format!(
                "Cannot archive phase {} - it has {} active goals",
                phase_id,
                goals.len()
            )));
        }

        // Archive the phase
        self.repository.delete(phase_id).await?;

        // Log event
        let event = Event::new(
            "phase",
            phase_id,
            EventAction::Delete,
            "user",
            serde_json::json!({}),
        );
        let _ = self.store.log_event(&event).await;

        Ok(())
    }
}
