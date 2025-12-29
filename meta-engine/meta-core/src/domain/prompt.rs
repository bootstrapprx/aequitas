use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Prompt {
    pub prompt_id: String,
    pub agent: String,
    pub purpose: String,
    pub timestamp: DateTime<Utc>,
    pub prompt_text: String,
    pub response_text: Option<String>,
    pub file_path: PathBuf,
}

impl Prompt {
    pub fn validate_id(id: &str) -> bool {
        id.starts_with("PROMPT_")
    }
}
