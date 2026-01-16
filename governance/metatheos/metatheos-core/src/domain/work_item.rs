use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Canonical work item level (matches SCHEMAFULL `work_item.level`)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum WorkItemLevel {
    Goal,
    Subgoal,
    Task,
}

impl WorkItemLevel {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "goal" => Some(Self::Goal),
            "subgoal" => Some(Self::Subgoal),
            "task" => Some(Self::Task),
            _ => None,
        }
    }
}

/// Canonical work item status (matches SCHEMAFULL `work_item.status`)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum WorkItemStatus {
    Open,
    Active,
    Blocked,
    Done,
}

impl WorkItemStatus {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "open" => Some(Self::Open),
            "active" => Some(Self::Active),
            "blocked" => Some(Self::Blocked),
            "done" => Some(Self::Done),
            _ => None,
        }
    }
}

/// Canonical work item record (SCHEMAFULL `work_item` table)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkItem {
    pub id: String,
    pub goal_id: String, // Root goal this item belongs to
    pub parent_id: Option<String>,
    pub level: WorkItemLevel, // goal | subgoal | task
    pub title: String,
    #[serde(default)]
    pub description: String,
    pub status: WorkItemStatus, // open | active | blocked | done
    #[serde(default)]
    pub order_index: i32,
    pub created_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
}
