use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum DayType {
    Light,
    Heavy,
    Review,
    Rest,
}

impl DayType {
    pub fn as_str(&self) -> &str {
        match self {
            DayType::Light => "light",
            DayType::Heavy => "heavy",
            DayType::Review => "review",
            DayType::Rest => "rest",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "light" => Some(Self::Light),
            "heavy" => Some(Self::Heavy),
            "review" => Some(Self::Review),
            "rest" => Some(Self::Rest),
            _ => None,
        }
    }
}

/// Represents a single calendar day in the daily workflow
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Day {
    pub id: String,        // Format: "YYYY-MM-DD"
    pub phase_id: String,  // Phase this day belongs to
    pub day_type: DayType, // Type of day (light/heavy/review/rest)
    pub created_at: DateTime<Utc>,
}

/// Link table between days and goals
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DayGoal {
    pub day_id: String,  // Foreign key to Day
    pub goal_id: String, // Foreign key to Goal
    pub required: bool,  // Whether this goal is required for the day
}

/// Daily log entry - narrative and telemetry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DayLog {
    pub id: String,
    pub day_id: String,  // Foreign key to Day
    pub content: String, // Markdown content
    pub created_at: DateTime<Utc>,
}

impl Day {
    pub fn validate_id(id: &str) -> bool {
        // Format: YYYY-MM-DD
        if id.len() != 10 {
            return false;
        }
        let parts: Vec<&str> = id.split('-').collect();
        if parts.len() != 3 {
            return false;
        }
        parts[0].len() == 4 && parts[1].len() == 2 && parts[2].len() == 2
    }
}
