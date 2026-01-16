// Goal Writer - Stub for DB-only architecture
// Original file-based methods replaced with placeholders
// TODO: Replace with SurrealStore calls

use crate::domain::Goal;
use crate::errors::{MetaError, Result};
use std::path::PathBuf;

pub struct GoalWriter {
    #[allow(dead_code)]
    governance_root: PathBuf,
}

impl GoalWriter {
    pub fn new(governance_root: PathBuf) -> Self {
        Self { governance_root }
    }

    /// Create a new goal - NOW USES DB VIA FROM CALLER
    pub fn create_goal(&self, _goal: &Goal) -> Result<PathBuf> {
        Err(MetaError::SystemError(
            "GoalWriter deprecated: use SurrealStore.save_goal() instead".to_string(),
        ))
    }

    /// Update an existing goal
    pub fn update_goal(&self, _goal: &Goal) -> Result<()> {
        Err(MetaError::SystemError(
            "GoalWriter deprecated: use SurrealStore.save_goal() instead".to_string(),
        ))
    }

    /// Delete a goal
    pub fn delete_goal(&self, _goal_id: &str) -> Result<()> {
        Err(MetaError::SystemError(
            "GoalWriter deprecated: use SurrealStore directly".to_string(),
        ))
    }
}
