/// Goal Repository - Database access layer for goals
///
/// Handles all CRUD operations for goals, using DTOs for database serialization
/// and returning domain Goal models.

use crate::errors::{MetaError, Result};
use crate::store::dto::GoalDbDto;
use crate::store::SurrealStore;
use crate::{Goal, GoalStatus};
use std::sync::Arc;

/// Repository for goal database operations
pub struct GoalRepository {
    store: Arc<SurrealStore>,
}

impl GoalRepository {
    pub fn new(store: Arc<SurrealStore>) -> Self {
        Self { store }
    }

    /// Create a new goal
    pub async fn create(&self, goal: Goal) -> Result<String> {
        let goal_id = goal.goal_id.clone();
        let dto = GoalDbDto::from(goal);

        let _: Option<serde_json::Value> = self.store
            .get_db()
            .create(("goal", goal_id.as_str()))
            .content(dto)
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!("Failed to create goal {}: {}", goal_id, e))
            })?;

        Ok(goal_id)
    }

    /// Get a goal by ID
    pub async fn get_by_id(&self, goal_id: &str) -> Result<Option<Goal>> {
        let dto: Option<GoalDbDto> = self
            .store
            .get_db()
            .select(("goal", goal_id))
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!("Failed to get goal {}: {}", goal_id, e))
            })?;

        Ok(dto.map(|d| d.into_goal()))
    }

    /// Get a goal by ID (returns error if not found)
    pub async fn get_by_id_or_error(&self, goal_id: &str) -> Result<Goal> {
        self.get_by_id(goal_id)
            .await?
            .ok_or_else(|| MetaError::GoalNotFound(goal_id.to_string()))
    }

    /// Update an existing goal
    pub async fn update(&self, goal: Goal) -> Result<()> {
        let goal_id = goal.goal_id.clone();
        let dto = GoalDbDto::from(goal);

        self.store
            .get_db()
            .update::<Option<serde_json::Value>>(("goal", goal_id.as_str()))
            .content(dto)
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!("Failed to update goal {}: {}", goal_id, e))
            })?;

        Ok(())
    }

    /// Delete a goal (sets status to archived)
    pub async fn delete(&self, goal_id: &str) -> Result<()> {
        let mut goal = self.get_by_id_or_error(goal_id).await?;
        goal.status = GoalStatus::Archived;
        self.update(goal).await
    }

    /// Get all goals
    pub async fn get_all(&self) -> Result<Vec<Goal>> {
        let query = "SELECT * FROM goal ORDER BY created_at DESC";
        let mut response = self
            .store
            .get_db()
            .query(query)
            .await
            .map_err(|e| MetaError::DatabaseQuery(format!("Failed to query all goals: {}", e)))?;

        let dtos: Vec<GoalDbDto> = response.take(0).map_err(|e| {
            MetaError::DatabaseSerialization(format!("Failed to parse goals: {}", e))
        })?;

        Ok(dtos.into_iter().map(|d| d.into_goal()).collect())
    }

    /// Get goals by phase
    pub async fn get_by_phase(&self, phase_id: &str) -> Result<Vec<Goal>> {
        let query = "SELECT * FROM goal WHERE phase_id = $phase_id ORDER BY created_at DESC";
        let phase_id_owned = phase_id.to_string();
        let mut response = self
            .store
            .get_db()
            .query(query)
            .bind(("phase_id", phase_id_owned))
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!(
                    "Failed to query goals for phase {}: {}",
                    phase_id, e
                ))
            })?;

        let dtos: Vec<GoalDbDto> = response.take(0).map_err(|e| {
            MetaError::DatabaseSerialization(format!("Failed to parse goals: {}", e))
        })?;

        Ok(dtos.into_iter().map(|d| d.into_goal()).collect())
    }

    /// Get goals by status
    pub async fn get_by_status(&self, status: &str) -> Result<Vec<Goal>> {
        let query = "SELECT * FROM goal WHERE status = $status ORDER BY created_at DESC";
        let status_owned = status.to_string();
        let mut response = self
            .store
            .get_db()
            .query(query)
            .bind(("status", status_owned))
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!(
                    "Failed to query goals with status {}: {}",
                    status, e
                ))
            })?;

        let dtos: Vec<GoalDbDto> = response.take(0).map_err(|e| {
            MetaError::DatabaseSerialization(format!("Failed to parse goals: {}", e))
        })?;

        Ok(dtos.into_iter().map(|d| d.into_goal()).collect())
    }

    /// Count goals by status
    pub async fn count_by_status(&self) -> Result<std::collections::HashMap<String, usize>> {
        self.store.count_goals_by_status().await
    }
}
