use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Canonical scope for annotations (DB-first, matches SCHEMAFULL `annotation` table)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum AnnotationScope {
    #[serde(alias = "Phase")]
    Phase,
    #[serde(alias = "Goal")]
    Goal,
    #[serde(
        alias = "WorkItem",
        alias = "workitem",
        alias = "Task",
        alias = "task",
        alias = "Subgoal",
        alias = "subgoal"
    )]
    WorkItem,
    #[serde(alias = "Day")]
    Day,
    #[serde(alias = "Event")]
    Event,
    #[serde(alias = "AiRun", alias = "ai", alias = "AI")]
    AiRun,
}

impl AnnotationScope {
    pub fn as_str(&self) -> &'static str {
        match self {
            AnnotationScope::Phase => "phase",
            AnnotationScope::Goal => "goal",
            AnnotationScope::WorkItem => "work_item",
            AnnotationScope::Day => "day",
            AnnotationScope::Event => "event",
            AnnotationScope::AiRun => "ai_run",
        }
    }
}

/// Author type for annotations
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum AnnotationAuthor {
    #[serde(alias = "user", alias = "system")]
    User,
    #[serde(alias = "ai")]
    Ai,
}

impl AnnotationAuthor {
    pub fn as_str(&self) -> &'static str {
        match self {
            AnnotationAuthor::User => "user",
            AnnotationAuthor::Ai => "ai",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Annotation {
    pub id: String,
    #[serde(alias = "scope_type", alias = "target_type")]
    pub entity_type: AnnotationScope,
    #[serde(alias = "scope_id", alias = "target_id")]
    pub entity_id: String,
    #[serde(alias = "body")]
    pub content: String,
    #[serde(alias = "author", alias = "author_type")]
    pub author_type: AnnotationAuthor, // "user" or "ai"
    #[serde(alias = "author_ref")]
    pub author_ref: Option<String>,
    #[serde(default = "Utc::now")]
    pub created_at: DateTime<Utc>,
}
