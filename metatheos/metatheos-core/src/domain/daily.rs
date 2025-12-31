use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DailyNote {
    pub date: NaiveDate,
    pub phase: Option<u32>,
    pub mode: Option<String>,
    pub protocol: Option<String>,
    pub goals_worked: Vec<String>,
    pub decisions_made: Vec<String>,
    pub divergences: Vec<String>,
    pub goals: Vec<String>,
    pub blockers: Vec<String>,
    pub decisions: Vec<String>,
    pub linked_goals: Vec<String>,
    pub file_path: PathBuf,
    pub content: String,
    #[serde(flatten)]
    pub extra: std::collections::HashMap<String, serde_json::Value>,
}

impl DailyNote {
    pub fn file_name(date: &NaiveDate) -> String {
        format!("{}.md", date.format("%Y-%m-%d"))
    }

    pub fn validate_file_name(name: &str) -> bool {
        name.ends_with(".md")
            && NaiveDate::parse_from_str(&name[..10], "%Y-%m-%d").is_ok()
    }
}
