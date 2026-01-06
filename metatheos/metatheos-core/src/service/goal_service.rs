/// Goal Service - Business logic for goal operations
///
/// Handles goal lifecycle, status transitions, dependency validation,
/// and business rules enforcement.

use crate::errors::{MetaError, Result};
use crate::repository::GoalRepository;
use crate::store::consequences::ConsequenceEngine;
use crate::store::SurrealStore;
use crate::{Event, EventAction, Goal, GoalStatus};
use chrono::Utc;
use std::sync::Arc;

/// Service for goal business operations
pub struct GoalService {
    repository: GoalRepository,
    store: Arc<SurrealStore>,
}

impl GoalService {
    pub fn new(store: Arc<SurrealStore>) -> Self {
        Self {
            repository: GoalRepository::new(store.clone()),
            store,
        }
    }

    /// Create a new goal with validation
    pub async fn create_goal(&self, mut goal: Goal) -> Result<String> {
        // Validate phase exists
        if let Some(phase_id) = &goal.phase {
            self.validate_phase_exists(phase_id).await?;
        } else {
            return Err(MetaError::ValidationError(
                "Goal must belong to a phase".to_string(),
            ));
        }

        // Validate dependencies exist
        self.validate_dependencies(&goal.dependencies).await?;

        // Set creation timestamp
        goal.updated = Some(Utc::now().naive_utc().date());

        // Create goal
        let goal_id = self.repository.create(goal.clone()).await?;

        // Log event
        let event = Event::new(
            "goal",
            &goal_id,
            EventAction::Create,
            "user",
            serde_json::json!({
                "title": goal.title,
                "status": goal.status.as_str(),
                "phase": goal.phase,
            }),
        );
        let _ = self.store.log_event(&event).await;

        Ok(goal_id)
    }

    /// Update an existing goal with validation
    pub async fn update_goal(&self, mut goal: Goal) -> Result<()> {
        // Verify goal exists
        let existing = self.repository.get_by_id_or_error(&goal.goal_id).await?;

        // Validate phase change
        if goal.phase != existing.phase {
            if let Some(phase_id) = &goal.phase {
                self.validate_phase_exists(phase_id).await?;
            }
        }

        // Validate dependencies
        self.validate_dependencies(&goal.dependencies).await?;

        // Validate parent-child phase consistency
        if let Some(parent_id) = &goal.parent_id {
            let parent = self.repository.get_by_id_or_error(parent_id).await?;
            if parent.phase != goal.phase {
                return Err(MetaError::ValidationError(
                    "Goal phase must match parent goal phase".to_string(),
                ));
            }
        }

        // Check children phase consistency
        let all_goals = self.repository.get_all().await?;
        for child in all_goals.iter() {
            if child.parent_id.as_ref() == Some(&goal.goal_id) {
                if child.phase != goal.phase {
                    return Err(MetaError::ValidationError(format!(
                        "Cannot change phase - child goal {} is in different phase",
                        child.goal_id
                    )));
                }
            }
        }

        // Update timestamp
        goal.updated = Some(Utc::now().naive_utc().date());

        // Perform update
        self.repository.update(goal.clone()).await?;

        // Log event
        let event = Event::new(
            "goal",
            &goal.goal_id,
            EventAction::Update,
            "user",
            serde_json::json!({
                "title": goal.title,
                "status": goal.status.as_str(),
            }),
        );
        let _ = self.store.log_event(&event).await;

        Ok(())
    }

    /// Update goal status with transition validation
    pub async fn update_status(&self, goal_id: &str, new_status: GoalStatus) -> Result<()> {
        let mut goal = self.repository.get_by_id_or_error(goal_id).await?;

        // Validate status transition
        if !goal.status.can_transition_to(&new_status) {
            return Err(MetaError::InvalidTransition {
                from: goal.status.as_str().to_string(),
                to: new_status.as_str().to_string(),
            });
        }

        // Update status
        goal.status = new_status.clone();
        goal.updated = Some(Utc::now().naive_utc().date());

        self.repository.update(goal.clone()).await?;

        // Trigger consequence detection
        let engine = ConsequenceEngine {
            store: self.store.clone(),
        };
        let _ = engine.on_goal_status_changed(&goal.goal_id).await;

        // Log event
        let event = Event::new(
            "goal",
            goal_id,
            EventAction::Update,
            "user",
            serde_json::json!({
                "status_changed": new_status.as_str(),
            }),
        );
        let _ = self.store.log_event(&event).await;

        Ok(())
    }

    /// Delete (archive) a goal
    pub async fn delete_goal(&self, goal_id: &str) -> Result<()> {
        // Check if goal has active children
        let all_goals = self.repository.get_all().await?;
        let active_children: Vec<_> = all_goals
            .iter()
            .filter(|g| {
                g.parent_id.as_ref() == Some(&goal_id.to_string())
                    && g.status != GoalStatus::Done
                    && g.status != GoalStatus::Archived
            })
            .collect();

        if !active_children.is_empty() {
            return Err(MetaError::OperationNotPermitted(
                "Cannot archive goal with active children. Archive children first.".to_string(),
            ));
        }

        // Archive the goal
        self.repository.delete(goal_id).await?;

        // Log event
        let event = Event::new(
            "goal",
            goal_id,
            EventAction::Delete,
            "user",
            serde_json::json!({}),
        );
        let _ = self.store.log_event(&event).await;

        Ok(())
    }

    /// Get goal by ID
    pub async fn get_goal(&self, goal_id: &str) -> Result<Option<Goal>> {
        self.repository.get_by_id(goal_id).await
    }

    /// Get all goals
    pub async fn get_all_goals(&self) -> Result<Vec<Goal>> {
        self.repository.get_all().await
    }

    /// Get goals by phase
    pub async fn get_goals_by_phase(&self, phase_id: &str) -> Result<Vec<Goal>> {
        self.repository.get_by_phase(phase_id).await
    }

    /// Get goals by status
    pub async fn get_goals_by_status(&self, status: &str) -> Result<Vec<Goal>> {
        self.repository.get_by_status(status).await
    }

    // Private validation helpers

    async fn validate_phase_exists(&self, phase_id: &str) -> Result<()> {
        let phase: Option<crate::Phase> = self
            .store
            .get_db()
            .select(("phase", phase_id))
            .await
            .map_err(|e| MetaError::DatabaseQuery(format!("Failed to validate phase: {}", e)))?;

        if phase.is_none() {
            return Err(MetaError::PhaseNotFound(phase_id.to_string()));
        }

        Ok(())
    }

    async fn validate_dependencies(&self, dep_ids: &[String]) -> Result<()> {
        for dep_id in dep_ids {
            let dep = self.repository.get_by_id(dep_id).await?;
            if dep.is_none() {
                return Err(MetaError::GoalNotFound(dep_id.clone()));
            }
        }
        Ok(())
    }
}
