use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum GoalStatus {
    Planned,
    Active,
    Blocked,
    Partial,
    Done,
    Archived,
    /// Fallback for legacy/unknown statuses so we don't drop data
    Unknown(String),
}

impl GoalStatus {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "planned" => Some(Self::Planned),
            "active" => Some(Self::Active),
            "blocked" => Some(Self::Blocked),
            "partial" => Some(Self::Partial),
            "done" | "completed" => Some(Self::Done),
            "archived" => Some(Self::Archived),
            other => Some(Self::Unknown(other.to_string())),
        }
    }

    pub fn can_transition_to(&self, target: &GoalStatus) -> bool {
        match (self, target) {
            (GoalStatus::Planned, GoalStatus::Active)
            | (GoalStatus::Planned, GoalStatus::Blocked)
            | (GoalStatus::Planned, GoalStatus::Partial)
            | (GoalStatus::Planned, GoalStatus::Done)
            | (GoalStatus::Active, GoalStatus::Blocked)
            | (GoalStatus::Active, GoalStatus::Partial)
            | (GoalStatus::Active, GoalStatus::Done)
            | (GoalStatus::Blocked, GoalStatus::Active)
            | (GoalStatus::Blocked, GoalStatus::Partial)
            | (GoalStatus::Blocked, GoalStatus::Done)
            | (GoalStatus::Partial, GoalStatus::Active)
            | (GoalStatus::Partial, GoalStatus::Blocked)
            | (GoalStatus::Partial, GoalStatus::Done)
            | (GoalStatus::Done, GoalStatus::Active)
            | (GoalStatus::Done, GoalStatus::Partial)
            | (GoalStatus::Done, GoalStatus::Blocked)
            | (GoalStatus::Done, GoalStatus::Archived)
            | (GoalStatus::Archived, GoalStatus::Done) => true,
            (GoalStatus::Unknown(_), _) | (_, GoalStatus::Unknown(_)) => true,
            _ => false,
        }
    }

    pub fn as_str(&self) -> &str {
        match self {
            GoalStatus::Planned => "planned",
            GoalStatus::Active => "active",
            GoalStatus::Blocked => "blocked",
            GoalStatus::Partial => "partial",
            GoalStatus::Done => "done",
            GoalStatus::Archived => "archived",
            GoalStatus::Unknown(value) => value.as_str(),
        }
    }
}

impl std::fmt::Display for GoalStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            GoalStatus::Planned => write!(f, "planned"),
            GoalStatus::Active => write!(f, "active"),
            GoalStatus::Blocked => write!(f, "blocked"),
            GoalStatus::Archived => write!(f, "archived"),
            GoalStatus::Partial => write!(f, "partial"),
            GoalStatus::Done => write!(f, "done"),
            GoalStatus::Unknown(value) => write!(f, "{}", value),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Goal {
    pub goal_id: String,
    pub title: String,
    pub status: GoalStatus,
    pub phase: Option<String>,
    pub owner: Option<String>,
    pub parent_id: Option<String>,
    #[serde(default = "default_level")]
    pub level: Option<String>,
    pub dependencies: Vec<String>,
    pub canon: Vec<String>,
    pub updated: Option<NaiveDate>,
    pub tags: Vec<String>,
    pub file_path: PathBuf,
    pub content: String,
}

fn default_level() -> Option<String> {
    Some("goal".to_string())
}

impl Goal {
    pub fn validate_id(id: &str) -> bool {
        // Accept both formats: "G-###" (numeric) or "goal-*" (descriptive)
        if id.starts_with("G-") && id.len() > 2 && id[2..].chars().all(|c| c.is_ascii_digit()) {
            return true;
        }
        if id.starts_with("goal-") && id.len() > 5 {
            return true;
        }
        false
    }

    pub fn id(&self) -> &str {
        &self.goal_id
    }

    pub fn is_active(&self) -> bool {
        matches!(self.status, GoalStatus::Active | GoalStatus::Partial)
    }

    pub fn is_done(&self) -> bool {
        matches!(self.status, GoalStatus::Done)
    }

    pub fn is_blocked(&self) -> bool {
        self.status == GoalStatus::Blocked
    }

    pub fn has_dependency(&self, goal_id: &str) -> bool {
        self.dependencies.iter().any(|dep| dep == goal_id)
    }
}
