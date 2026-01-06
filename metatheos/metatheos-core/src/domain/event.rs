use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum EventAction {
    Create,
    Update,
    Complete,
    Reopen,
    Link,
    Delete,
}

impl EventAction {
    pub fn as_str(&self) -> &str {
        match self {
            EventAction::Create => "create",
            EventAction::Update => "update",
            EventAction::Complete => "complete",
            EventAction::Reopen => "reopen",
            EventAction::Link => "link",
            EventAction::Delete => "delete",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "create" => Some(Self::Create),
            "update" => Some(Self::Update),
            "complete" => Some(Self::Complete),
            "reopen" => Some(Self::Reopen),
            "link" => Some(Self::Link),
            "delete" => Some(Self::Delete),
            _ => None,
        }
    }
}

/// Event record for audit trail - nothing is silent
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub id: String,
    pub entity_type: String, // Table name (phase, goal, work_item, etc.)
    pub entity_id: String,   // ID of the entity
    pub action: EventAction, // What happened
    pub actor: String,       // Who/what caused this event ('user', 'system', 'ai')
    pub payload: JsonValue,  // JSON object with change details
    pub created_at: DateTime<Utc>,
}

impl Event {
    /// Create a new event
    pub fn new(
        entity_type: impl Into<String>,
        entity_id: impl Into<String>,
        action: EventAction,
        actor: impl Into<String>,
        payload: JsonValue,
    ) -> Self {
        use uuid::Uuid;
        Self {
            id: format!("EVENT-{}", Uuid::new_v4()),
            entity_type: entity_type.into(),
            entity_id: entity_id.into(),
            action,
            actor: actor.into(),
            payload,
            created_at: Utc::now(),
        }
    }

    /// Create a simple event with minimal payload
    pub fn simple(
        entity_type: impl Into<String>,
        entity_id: impl Into<String>,
        action: EventAction,
    ) -> Self {
        Self::new(
            entity_type,
            entity_id,
            action,
            "user",
            serde_json::json!({}),
        )
    }
}
