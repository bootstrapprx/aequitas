use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum DecisionStatus {
    Active,
    Superseded,
    Abandoned,
}

impl DecisionStatus {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "active" => Some(Self::Active),
            "superseded" => Some(Self::Superseded),
            "abandoned" => Some(Self::Abandoned),
            _ => None,
        }
    }
}

impl std::fmt::Display for DecisionStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DecisionStatus::Active => write!(f, "active"),
            DecisionStatus::Superseded => write!(f, "superseded"),
            DecisionStatus::Abandoned => write!(f, "abandoned"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Decision {
    pub decision_id: String,
    pub title: String,
    pub status: DecisionStatus,
    pub date: NaiveDate,
    pub rationale: Option<String>,
    pub file_path: PathBuf,
    pub content: String,
}

impl Decision {
    pub fn validate_id(id: &str) -> bool {
        id.starts_with("D-") && id.len() > 2 && id[2..].chars().all(|c| c.is_ascii_digit())
    }

    pub fn id(&self) -> &str {
        &self.decision_id
    }
}
