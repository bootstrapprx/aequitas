use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Phase {
    pub phase_id: String,
    pub title: String,
    pub status: String,
    pub start_date: Option<NaiveDate>,
    pub target_date: Option<NaiveDate>,
    pub dependencies: Vec<String>,
    pub file_path: PathBuf,
    pub content: String,
}

impl Phase {
    pub fn number(&self) -> Option<u32> {
        self.phase_id.trim_start_matches('P').parse::<u32>().ok()
    }
}
