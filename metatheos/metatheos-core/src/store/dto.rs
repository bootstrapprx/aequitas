/// Data Transfer Objects for SurrealDB serialization
///
/// This module provides DTO (Data Transfer Object) types that bridge the gap
/// between Rust domain models and SurrealDB's schema expectations.
///
/// Domain models use rich types (NaiveDate, PathBuf, custom enums) optimized
/// for business logic. DTOs use simple types (String, etc.) that serialize
/// cleanly to JSON for database storage.

use serde::{Deserialize, Serialize};

/// Goal Database DTO for SurrealDB serialization
///
/// Maps between domain Goal struct and SurrealDB goal table schema:
/// - goal_id → id
/// - phase → phase_id
/// - content → description
/// - PathBuf → String
/// - NaiveDate → String
/// - GoalStatus enum → String (via custom serialization)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GoalDbDto {
    /// Primary key (matches goal_id from domain)
    pub id: String,

    /// Phase this goal belongs to
    pub phase_id: String,

    /// Goal title
    pub title: String,

    /// Goal description (maps to content in domain)
    pub description: String,

    /// Status as string
    pub status: String,

    /// Priority level
    pub priority: String,

    /// Optional owner
    #[serde(skip_serializing_if = "Option::is_none")]
    pub owner: Option<String>,

    /// Goal dependencies
    #[serde(default)]
    pub dependencies: Vec<String>,

    /// Tags
    #[serde(default)]
    pub tags: Vec<String>,

    /// Last updated (ISO 8601 date string)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub updated: Option<String>,
}

impl From<crate::Goal> for GoalDbDto {
    fn from(goal: crate::Goal) -> Self {
        Self {
            id: goal.goal_id,
            phase_id: goal.phase.unwrap_or_default(),
            title: goal.title,
            description: goal.content,
            status: goal.status.as_str().to_string(),
            priority: "normal".to_string(), // Default priority
            owner: goal.owner,
            dependencies: goal.dependencies,
            tags: goal.tags,
            updated: goal.updated.map(|d| d.to_string()),
        }
    }
}

impl GoalDbDto {
    /// Convert DTO back to domain Goal
    pub fn into_goal(self) -> crate::Goal {
        crate::Goal {
            goal_id: self.id.clone(),
            title: self.title,
            content: self.description,
            status: crate::GoalStatus::from_str(&self.status)
                .unwrap_or(crate::GoalStatus::Unknown(self.status)),
            phase: Some(self.phase_id),
            owner: self.owner,
            parent_id: None,
            level: None,
            dependencies: self.dependencies,
            canon: vec![],
            tags: self.tags,
            updated: self.updated.and_then(|s| {
                use std::str::FromStr;
                chrono::NaiveDate::from_str(&s).ok()
            }),
            file_path: std::path::PathBuf::from(format!("goals/{}.md", self.id)),
        }
    }
}

/// Phase DTO for database operations
///
/// Handles conversions for Phase struct:
/// - NaiveDate → String
/// - PathBuf → String
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseDto {
    pub id: String,
    pub phase_id: String,
    pub title: String,
    pub description: String,
    pub content: String,
    pub status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub start_date: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub target_date: Option<String>,
    #[serde(default)]
    pub dependencies: Vec<String>,
    pub file_path: String,
}

impl From<crate::Phase> for PhaseDto {
    fn from(phase: crate::Phase) -> Self {
        Self {
            id: phase.phase_id.clone(),
            phase_id: phase.phase_id,
            title: phase.title,
            description: String::new(), // Phase doesn't have separate description
            content: phase.content,
            status: phase.status,
            start_date: phase.start_date.map(|d| d.to_string()),
            target_date: phase.target_date.map(|d| d.to_string()),
            dependencies: phase.dependencies,
            file_path: phase.file_path.to_string_lossy().to_string(),
        }
    }
}

impl PhaseDto {
    /// Convert DTO back to domain Phase
    pub fn into_phase(self) -> crate::Phase {
        crate::Phase {
            phase_id: self.phase_id,
            title: self.title,
            status: self.status,
            start_date: self.start_date.and_then(|s| {
                use std::str::FromStr;
                chrono::NaiveDate::from_str(&s).ok()
            }),
            target_date: self.target_date.and_then(|s| {
                use std::str::FromStr;
                chrono::NaiveDate::from_str(&s).ok()
            }),
            dependencies: self.dependencies,
            file_path: std::path::PathBuf::from(self.file_path),
            content: self.content,
        }
    }
}
