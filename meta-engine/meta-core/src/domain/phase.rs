use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Phase {
    pub phase_number: u32,
    pub title: String,
    pub description: String,
    pub file_path: PathBuf,
}

impl Phase {
    pub fn number(&self) -> u32 {
        self.phase_number
    }
}
