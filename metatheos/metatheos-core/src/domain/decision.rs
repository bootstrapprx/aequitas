use chrono::NaiveDate;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::path::PathBuf;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DecisionStatus {
    Draft,
    Proposed,
    Implemented,
    Active,
    Superseded,
    Abandoned,
    Unknown(String),
}

// Custom serialization to always produce a string (not an object)
impl Serialize for DecisionStatus {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(self.as_str())
    }
}

// Custom deserialization from string
impl<'de> Deserialize<'de> for DecisionStatus {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        Ok(DecisionStatus::from_str(&s).unwrap_or_else(|| DecisionStatus::Unknown(s)))
    }
}

impl DecisionStatus {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "draft" => Some(Self::Draft),
            "proposed" => Some(Self::Proposed),
            "implemented" => Some(Self::Implemented),
            "active" => Some(Self::Active),
            "superseded" => Some(Self::Superseded),
            "abandoned" => Some(Self::Abandoned),
            other => Some(Self::Unknown(other.to_string())),
        }
    }

    pub fn as_str(&self) -> &str {
        match self {
            DecisionStatus::Draft => "draft",
            DecisionStatus::Proposed => "proposed",
            DecisionStatus::Implemented => "implemented",
            DecisionStatus::Active => "active",
            DecisionStatus::Superseded => "superseded",
            DecisionStatus::Abandoned => "abandoned",
            DecisionStatus::Unknown(value) => value.as_str(),
        }
    }
}

impl std::fmt::Display for DecisionStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DecisionStatus::Draft => write!(f, "draft"),
            DecisionStatus::Proposed => write!(f, "proposed"),
            DecisionStatus::Implemented => write!(f, "implemented"),
            DecisionStatus::Active => write!(f, "active"),
            DecisionStatus::Superseded => write!(f, "superseded"),
            DecisionStatus::Abandoned => write!(f, "abandoned"),
            DecisionStatus::Unknown(value) => write!(f, "{}", value),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Decision {
    pub decision_id: String,
    pub title: String,
    pub status: Option<DecisionStatus>,
    pub date: Option<NaiveDate>,
    pub updated: Option<NaiveDate>,
    pub canon: Vec<String>,
    pub phase: Option<String>,
    pub rationale: Option<String>,
    pub file_path: PathBuf,
    pub content: String,
}

impl Decision {
    pub fn validate_id(id: &str) -> bool {
        // Accept formats: "D-###" (numeric), "decision-*", "###" (legacy), or descriptive titles
        if id.starts_with("D-") && id.len() > 2 && id[2..].chars().all(|c| c.is_ascii_digit()) {
            return true;
        }
        if id.starts_with("decision-") && id.len() > 9 {
            return true;
        }
        if id.len() >= 3 && id.chars().take(3).all(|c| c.is_ascii_digit()) {
            return true;
        }
        !id.trim().is_empty()
    }

    pub fn id(&self) -> &str {
        &self.decision_id
    }
}
