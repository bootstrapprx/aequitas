use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum GoalStatus {
    Active,
    Blocked,
    Completed,
    Archived,
}

impl GoalStatus {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "active" => Some(Self::Active),
            "blocked" => Some(Self::Blocked),
            "completed" => Some(Self::Completed),
            "archived" => Some(Self::Archived),
            _ => None,
        }
    }

    pub fn can_transition_to(&self, target: &GoalStatus) -> bool {
        match (self, target) {
            (GoalStatus::Active, GoalStatus::Blocked)
            | (GoalStatus::Active, GoalStatus::Completed)
            | (GoalStatus::Active, GoalStatus::Archived)
            | (GoalStatus::Blocked, GoalStatus::Active)
            | (GoalStatus::Blocked, GoalStatus::Archived)
            | (GoalStatus::Completed, GoalStatus::Archived) => true,
            _ => false,
        }
    }
}

impl std::fmt::Display for GoalStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            GoalStatus::Active => write!(f, "active"),
            GoalStatus::Blocked => write!(f, "blocked"),
            GoalStatus::Completed => write!(f, "completed"),
            GoalStatus::Archived => write!(f, "archived"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Goal {
    pub goal_id: String,
    pub title: String,
    pub status: GoalStatus,
    pub phase: Option<u32>,
    pub owner: Option<String>,
    pub dependencies: Vec<String>,
    pub tags: Vec<String>,
    pub file_path: PathBuf,
    pub content: String,
}

impl Goal {
    pub fn validate_id(id: &str) -> bool {
        id.starts_with("G-") && id.len() > 2 && id[2..].chars().all(|c| c.is_ascii_digit())
    }

    pub fn id(&self) -> &str {
        &self.goal_id
    }

    pub fn is_active(&self) -> bool {
        self.status == GoalStatus::Active
    }

    pub fn is_blocked(&self) -> bool {
        self.status == GoalStatus::Blocked
    }

    pub fn has_dependency(&self, goal_id: &str) -> bool {
        self.dependencies.iter().any(|dep| dep == goal_id)
    }
}
