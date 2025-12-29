use std::sync::Mutex;
use std::path::PathBuf;

pub struct AppState {
    pub governance_root: Mutex<PathBuf>,
}

impl AppState {
    pub fn new(root: PathBuf) -> Self {
        Self {
            governance_root: Mutex::new(root),
        }
    }
}
