use std::sync::Mutex;
use std::path::PathBuf;

pub struct AppState {
    pub governance_root: Mutex<PathBuf>,
    pub repo_root: Mutex<PathBuf>,
}

impl AppState {
    pub fn new(governance_root: PathBuf, repo_root: PathBuf) -> Self {
        Self {
            governance_root: Mutex::new(governance_root),
            repo_root: Mutex::new(repo_root),
        }
    }
}
