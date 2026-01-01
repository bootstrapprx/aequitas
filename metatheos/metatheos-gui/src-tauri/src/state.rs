use std::sync::Mutex;
use std::path::PathBuf;
use std::sync::Arc;
use metatheos_core::store::SurrealStore;
use metatheos_core::FileWatcher;

pub struct AppState {
    pub governance_root: Mutex<PathBuf>,
    pub repo_root: Mutex<PathBuf>,
    pub db: Mutex<Option<Arc<SurrealStore>>>,
    pub watcher: Mutex<Option<FileWatcher>>,
}

impl AppState {
    pub fn new(governance_root: PathBuf, repo_root: PathBuf) -> Self {
        Self {
            governance_root: Mutex::new(governance_root),
            repo_root: Mutex::new(repo_root),
            db: Mutex::new(None),
            watcher: Mutex::new(None),
        }
    }
}
