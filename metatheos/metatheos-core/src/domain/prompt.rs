use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Prompt {
    pub prompt_id: Option<String>,
    pub agent: Option<String>,
    pub purpose: Option<String>,
    pub origin: Option<String>,
    pub status: Option<String>,
    pub timestamp: Option<DateTime<Utc>>,
    pub prompt_text: Option<String>,
    pub response_text: Option<String>,
    pub title: String,
    pub file_path: PathBuf,
    pub content: String,
}

impl Prompt {
    pub fn validate_id(id: &str) -> bool {
        id.starts_with("PROMPT_")
    }
}
