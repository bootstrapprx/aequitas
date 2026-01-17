//! Data Transfer Objects for UI Contract
//!
//! This module is the SINGLE SOURCE OF TRUTH for all UI-facing types.
//! All conversions from domain types happen here. No SurrealDB records
//! should leak directly to the UI.
//!
//! Design principles:
//! - Enums are normalized to lowercase strings
//! - Dates are ISO-8601 strings
//! - Optional fields are explicit
//! - IDs are stable and explicit

use chrono::{DateTime, NaiveDate, Utc};
use serde::{Deserialize, Serialize};

// ============================================================================
// ENUMS - Normalized lowercase strings for UI
// ============================================================================

/// Phase status enum - normalized for UI
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum PhaseStatus {
    Planned,
    Active,
    Closed,
    Archived,
}

impl PhaseStatus {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "active" | "in-progress" => Self::Active,
            "closed" | "done" | "completed" => Self::Closed,
            "archived" | "inactive" => Self::Archived,
            _ => Self::Planned,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Planned => "planned",
            Self::Active => "active",
            Self::Closed => "closed",
            Self::Archived => "archived",
        }
    }
}

/// Day type enum - normalized for UI
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum DayTypeDto {
    Light,
    Heavy,
    Review,
    Rest,
}

impl DayTypeDto {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "heavy" => Self::Heavy,
            "review" => Self::Review,
            "rest" => Self::Rest,
            _ => Self::Light,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Light => "light",
            Self::Heavy => "heavy",
            Self::Review => "review",
            Self::Rest => "rest",
        }
    }
}

/// Timeline item kind - for merged events + annotations
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum TimelineKind {
    Event,
    Annotation,
}

impl TimelineKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Event => "event",
            Self::Annotation => "annotation",
        }
    }
}

/// Goal status enum - normalized for UI
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum GoalStatusDto {
    Open,
    Active,
    Blocked,
    Partial,
    Done,
    Archived,
    Unknown,
}

impl GoalStatusDto {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "open" | "planned" => Self::Open,
            "active" | "in-progress" => Self::Active,
            "blocked" => Self::Blocked,
            "partial" => Self::Partial,
            "done" | "completed" => Self::Done,
            "archived" => Self::Archived,
            _ => Self::Unknown,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Open => "open",
            Self::Active => "active",
            Self::Blocked => "blocked",
            Self::Partial => "partial",
            Self::Done => "done",
            Self::Archived => "archived",
            Self::Unknown => "unknown",
        }
    }
}

/// Goal priority enum - normalized for UI
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum GoalPriorityDto {
    Low,
    Normal,
    High,
    Critical,
}

impl Default for GoalPriorityDto {
    fn default() -> Self {
        Self::Normal
    }
}

impl GoalPriorityDto {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "low" => Self::Low,
            "high" => Self::High,
            "critical" => Self::Critical,
            _ => Self::Normal,
        }
    }
}

// ============================================================================
// DTOs - UI Contract Types
// ============================================================================

/// Phase DTO - UI contract for phases
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseDto {
    pub id: String,
    pub title: String,
    pub status: PhaseStatus,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub start_date: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub target_date: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

impl From<&crate::Phase> for PhaseDto {
    fn from(phase: &crate::Phase) -> Self {
        Self {
            id: phase.phase_id.clone(),
            title: phase.title.clone(),
            status: PhaseStatus::from_str(&phase.status),
            start_date: phase.start_date.map(|d| d.format("%Y-%m-%d").to_string()),
            target_date: phase.target_date.map(|d| d.format("%Y-%m-%d").to_string()),
            description: if phase.content.is_empty() {
                None
            } else {
                Some(phase.content.clone())
            },
        }
    }
}

/// Goal DTO - UI contract for goals
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GoalDto {
    pub id: String,
    pub phase_id: String,
    pub title: String,
    pub status: GoalStatusDto,
    pub priority: GoalPriorityDto,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub owner: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub updated: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

impl From<&crate::Goal> for GoalDto {
    fn from(goal: &crate::Goal) -> Self {
        Self {
            id: goal.goal_id.clone(),
            phase_id: goal.phase.clone().unwrap_or_default(),
            title: goal.title.clone(),
            status: GoalStatusDto::from_str(goal.status.as_str()),
            priority: GoalPriorityDto::default(),
            owner: goal.owner.clone(),
            tags: goal.tags.clone(),
            updated: goal.updated.map(|d| d.format("%Y-%m-%d").to_string()),
            description: if goal.content.is_empty() {
                None
            } else {
                Some(goal.content.clone())
            },
        }
    }
}

/// Day DTO - UI contract for days
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DayDto {
    pub id: String,
    pub phase_id: String,
    pub day_type: DayTypeDto,
    pub created_at: String,
}

impl From<&crate::Day> for DayDto {
    fn from(day: &crate::Day) -> Self {
        Self {
            id: day.id.clone(),
            phase_id: day.phase_id.clone(),
            day_type: DayTypeDto::from_str(day.day_type.as_str()),
            created_at: day.created_at.to_rfc3339(),
        }
    }
}

/// Timeline item DTO - merged events + annotations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimelineItemDto {
    pub kind: TimelineKind,
    pub ts: String, // ISO-8601
    pub id: String,
    pub summary: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub phase_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub goal_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub work_item_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub day_id: Option<String>,
}

impl TimelineItemDto {
    /// Create from Event
    pub fn from_event(event: &crate::Event) -> Self {
        let summary = format!(
            "{} {} on {}",
            event.action.as_str(),
            event.entity_type,
            event.entity_id
        );

        let (phase_id, goal_id, work_item_id, day_id) = match event.entity_type.as_str() {
            "phase" => (Some(event.entity_id.clone()), None, None, None),
            "goal" => (None, Some(event.entity_id.clone()), None, None),
            "work_item" => (None, None, Some(event.entity_id.clone()), None),
            "day" => (None, None, None, Some(event.entity_id.clone())),
            _ => (None, None, None, None),
        };

        Self {
            kind: TimelineKind::Event,
            ts: event.created_at.to_rfc3339(),
            id: event.id.clone(),
            summary,
            phase_id,
            goal_id,
            work_item_id,
            day_id,
        }
    }

    /// Create from Annotation
    pub fn from_annotation(annotation: &crate::Annotation) -> Self {
        let summary = annotation.content.chars().take(100).collect::<String>();

        let (phase_id, goal_id, work_item_id, day_id) = match annotation.entity_type.as_str() {
            "phase" => (Some(annotation.entity_id.clone()), None, None, None),
            "goal" => (None, Some(annotation.entity_id.clone()), None, None),
            "work_item" => (None, None, Some(annotation.entity_id.clone()), None),
            "day" => (None, None, None, Some(annotation.entity_id.clone())),
            _ => (None, None, None, None),
        };

        Self {
            kind: TimelineKind::Annotation,
            ts: annotation.created_at.to_rfc3339(),
            id: annotation.id.clone(),
            summary,
            phase_id,
            goal_id,
            work_item_id,
            day_id,
        }
    }

    /// Stable sort key: (ts DESC, kind, id)
    pub fn sort_key(&self) -> impl Ord {
        // Negate timestamp for DESC order
        let ts_key = self.ts.clone();
        let kind_key = match self.kind {
            TimelineKind::Event => 0,
            TimelineKind::Annotation => 1,
        };
        // Reverse ts for DESC, then kind ASC, then id ASC
        (std::cmp::Reverse(ts_key), kind_key, self.id.clone())
    }
}

/// Audit DTO - read-only audit representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditDto {
    pub id: String,
    pub title: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub origin: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub created_at: Option<String>,
}

impl From<&crate::AuditRecord> for AuditDto {
    fn from(audit: &crate::AuditRecord) -> Self {
        Self {
            id: audit.title.replace(" ", "_").to_lowercase(),
            title: audit.title.clone(),
            status: audit.status.clone(),
            origin: audit.scope.clone(),
            created_at: audit.date.map(|d| d.format("%Y-%m-%d").to_string()),
        }
    }
}

/// Prompt DTO - read-only prompt representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptDto {
    pub id: String,
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub intent: Option<String>,
    pub template: String,
}

impl From<&crate::Prompt> for PromptDto {
    fn from(prompt: &crate::Prompt) -> Self {
        Self {
            id: prompt.prompt_id.clone().unwrap_or_else(|| prompt.title.replace(" ", "_").to_lowercase()),
            name: prompt.title.clone(),
            intent: prompt.purpose.clone(),
            template: prompt.content.clone(),
        }
    }
}

/// Auth status DTO - authentication state for UI
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthStatusDto {
    pub authenticated: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user: Option<AuthUserDto>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthUserDto {
    pub role: String,
}

impl AuthStatusDto {
    pub fn unauthenticated() -> Self {
        Self {
            authenticated: false,
            user: None,
        }
    }

    pub fn admin() -> Self {
        Self {
            authenticated: true,
            user: Some(AuthUserDto {
                role: "admin".to_string(),
            }),
        }
    }
}

/// Database status for context overview
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DbStatusDto {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub path: Option<String>,
    pub mode: String,
    pub healthy: bool,
}

/// Counts for context overview
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CountsDto {
    pub phases: usize,
    pub goals: usize,
    pub work_items: usize,
    pub events: usize,
    pub annotations: usize,
}

/// Context overview DTO - dashboard summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextOverviewDto {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub active_phase: Option<PhaseDto>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub current_day: Option<DayDto>,
    pub counts: CountsDto,
    pub db: DbStatusDto,
}

// ============================================================================
// API Error Type
// ============================================================================

/// API error response - structured error for UI
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiErrorDto {
    pub error_code: String,
    pub message: String,
}

impl ApiErrorDto {
    pub fn new(code: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            error_code: code.into(),
            message: message.into(),
        }
    }

    pub fn database_error(message: impl Into<String>) -> Self {
        Self::new("DATABASE_ERROR", message)
    }

    pub fn not_found(entity: impl Into<String>) -> Self {
        Self::new("NOT_FOUND", format!("{} not found", entity.into()))
    }

    pub fn unauthorized() -> Self {
        Self::new("UNAUTHORIZED", "Authentication required")
    }

    pub fn invalid_credentials() -> Self {
        Self::new("INVALID_CREDENTIALS", "Invalid username or password")
    }
}

// ============================================================================
// Read Mode Enum (for store kill-switch)
// ============================================================================

/// Read mode for store - controls canonical vs legacy table reads
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ReadMode {
    CanonicalOnly,
    #[default]
    DualRead,
    LegacyOnly,
}

impl ReadMode {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "canonical_only" | "canonical" => Self::CanonicalOnly,
            "legacy_only" | "legacy" => Self::LegacyOnly,
            _ => Self::DualRead,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Self::CanonicalOnly => "canonical_only",
            Self::DualRead => "dual_read",
            Self::LegacyOnly => "legacy_only",
        }
    }
}

impl std::fmt::Display for ReadMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.as_str())
    }
}
