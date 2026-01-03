use crate::errors::Result;
use crate::store::SurrealStore;
use crate::watcher::{FileChangeEvent, FileWatcher};
use std::path::Path;
use std::sync::Arc;
use tokio::sync::broadcast;

#[derive(Debug, Clone, serde::Serialize)]
pub struct GovernanceUpdateEvent {
    pub entity_type: String,
    pub id: String,
    pub operation: String,
}

pub struct WatcherService {
    #[allow(dead_code)]
    store: Arc<SurrealStore>,
    tx_events: broadcast::Sender<GovernanceUpdateEvent>,
}

impl WatcherService {
    pub fn new(
        governance_root: &Path,
        store: Arc<SurrealStore>,
    ) -> Result<(
        Self,
        FileWatcher,
        broadcast::Receiver<GovernanceUpdateEvent>,
    )> {
        let watcher = FileWatcher::new(governance_root)?;
        let (tx, rx) = broadcast::channel(100);

        Ok((
            Self {
                store,
                tx_events: tx,
            },
            watcher,
            rx,
        ))
    }

    /// Run the watcher loop - currently a no-op since DB is the source of truth
    /// Future: could watch for manual markdown exports or daily note sync
    pub async fn run(self, mut watcher: FileWatcher) {
        println!("WatcherService started (DB-only mode - file watching disabled).");
        loop {
            // Consume events but ignore them - DB is canonical
            if let Some(_event) = watcher.next_event() {
                // In DB-only mode, we don't process file changes
                // All entity modifications go through the GUI/CLI -> DB
            } else {
                tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
            }
        }
    }

    /// Broadcast an update event (called from GUI commands after DB modification)
    #[allow(dead_code)]
    pub fn broadcast(&self, update: GovernanceUpdateEvent) {
        let _ = self.tx_events.send(update);
    }
}
