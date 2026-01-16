use anyhow::{Context, Result};
use notify::{Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::mpsc::{channel, Receiver, TryRecvError};
use std::time::{Duration, SystemTime};

pub mod service;
pub use service::{GovernanceUpdateEvent, WatcherService};

/// Type of entity that changed
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EntityType {
    Goal,
    Phase,
    Decision,
    Audit,
    DailyNote,
    Prompt,
    Canon,
    Unknown,
}

/// Kind of file system event
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ChangeKind {
    Create,
    Modify,
    Delete,
}

/// Represents a file change event with metadata
#[derive(Debug, Clone)]
pub struct FileChangeEvent {
    pub kind: ChangeKind,
    pub path: PathBuf,
    pub entity_type: EntityType,
    pub timestamp: SystemTime,
}

impl FileChangeEvent {
    /// Detect entity type from file path
    fn detect_entity_type(path: &Path) -> EntityType {
        let path_str = path.to_string_lossy();

        // Check if it's a canon file
        if path_str.contains("docs/canonical")
            || path_str.contains("CANON_")
            || path_str.contains("KERNEL_")
        {
            return EntityType::Canon;
        }

        // Check directory structure
        if path_str.contains("01_DAILY") {
            return EntityType::DailyNote;
        }
        if path_str.contains("02_PHASES") {
            return EntityType::Phase;
        }
        if path_str.contains("03_GOALS_EPICS") {
            return EntityType::Goal;
        }
        if path_str.contains("04_DECISIONS") {
            return EntityType::Decision;
        }
        if path_str.contains("05_AUDITS") {
            return EntityType::Audit;
        }
        if path_str.contains("06_PROMPTS") {
            return EntityType::Prompt;
        }

        // Check filename patterns
        if let Some(filename) = path.file_name() {
            let filename_str = filename.to_string_lossy();
            if filename_str.starts_with("G-") {
                return EntityType::Goal;
            }
            if filename_str.starts_with("PHASE_") {
                return EntityType::Phase;
            }
            if filename_str.starts_with("D-") {
                return EntityType::Decision;
            }
            if filename_str.starts_with("AUDIT_") {
                return EntityType::Audit;
            }
        }

        EntityType::Unknown
    }
}

/// Debouncer to prevent excessive events from rapid file changes
struct Debouncer {
    last_events: HashMap<PathBuf, SystemTime>,
    debounce_duration: Duration,
}

impl Debouncer {
    fn new(debounce_ms: u64) -> Self {
        Self {
            last_events: HashMap::new(),
            debounce_duration: Duration::from_millis(debounce_ms),
        }
    }

    /// Check if event should be processed (returns true if enough time has passed)
    fn should_process(&mut self, path: &Path, now: SystemTime) -> bool {
        if let Some(&last_time) = self.last_events.get(path) {
            if let Ok(elapsed) = now.duration_since(last_time) {
                if elapsed < self.debounce_duration {
                    return false; // Too soon, skip this event
                }
            }
        }

        // Update timestamp
        self.last_events.insert(path.to_path_buf(), now);
        true
    }

    /// Clean up old entries to prevent unbounded growth
    fn cleanup(&mut self, now: SystemTime) {
        let cutoff = now - Duration::from_secs(60); // Remove entries older than 1 minute
        self.last_events.retain(|_, &mut time| time > cutoff);
    }
}

/// File watcher for governance folder
pub struct FileWatcher {
    _watcher: RecommendedWatcher,
    receiver: Receiver<notify::Result<Event>>,
    debouncer: Debouncer,
}

impl FileWatcher {
    /// Create a new file watcher for the governance root directory
    pub fn new(governance_root: &Path) -> Result<Self> {
        let (tx, rx) = channel();

        let mut watcher = RecommendedWatcher::new(
            tx,
            notify::Config::default().with_poll_interval(Duration::from_millis(100)),
        )
        .context("Failed to create file watcher")?;

        watcher
            .watch(governance_root, RecursiveMode::Recursive)
            .context("Failed to watch governance directory")?;

        Ok(Self {
            _watcher: watcher,
            receiver: rx,
            debouncer: Debouncer::new(100), // 100ms debounce window
        })
    }

    /// Get next file change event (non-blocking)
    /// Returns None if no events are available or if event should be filtered
    pub fn next_event(&mut self) -> Option<FileChangeEvent> {
        // Clean up old debouncer entries periodically
        let now = SystemTime::now();
        self.debouncer.cleanup(now);

        loop {
            match self.receiver.try_recv() {
                Ok(Ok(event)) => {
                    // Filter and convert the event
                    if let Some(change_event) = self.process_event(event, now) {
                        return Some(change_event);
                    }
                    // Continue loop to check for more events
                }
                Ok(Err(e)) => {
                    eprintln!("File watcher error: {}", e);
                    // Continue loop to check for more events
                }
                Err(TryRecvError::Empty) => {
                    // No more events available
                    return None;
                }
                Err(TryRecvError::Disconnected) => {
                    eprintln!("File watcher channel disconnected");
                    return None;
                }
            }
        }
    }

    /// Process a raw notify event into a FileChangeEvent (if relevant)
    fn process_event(&mut self, event: Event, now: SystemTime) -> Option<FileChangeEvent> {
        // Determine change kind
        let change_kind = match event.kind {
            EventKind::Create(_) => ChangeKind::Create,
            EventKind::Modify(_) => ChangeKind::Modify,
            EventKind::Remove(_) => ChangeKind::Delete,
            _ => return None, // Ignore other event types
        };

        // Process each path in the event
        for path in event.paths {
            // Only process markdown files
            if !path.extension().map_or(false, |ext| ext == "md") {
                continue;
            }

            // Skip temporary files and swap files
            if let Some(filename) = path.file_name() {
                let filename_str = filename.to_string_lossy();
                if filename_str.starts_with('.')
                    || filename_str.ends_with('~')
                    || filename_str.contains(".swp")
                {
                    continue;
                }
            }

            // Apply debouncing
            if !self.debouncer.should_process(&path, now) {
                continue;
            }

            // Detect entity type
            let entity_type = FileChangeEvent::detect_entity_type(&path);

            // Skip unknown entity types
            if entity_type == EntityType::Unknown {
                continue;
            }

            // Create and return the event
            return Some(FileChangeEvent {
                kind: change_kind.clone(),
                path,
                entity_type,
                timestamp: now,
            });
        }

        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn test_entity_type_detection_by_directory() {
        let test_cases = vec![
            ("governance/01_DAILY/2025-12-31.md", EntityType::DailyNote),
            ("governance/02_PHASES/PHASE_1.md", EntityType::Phase),
            ("governance/03_GOALS_EPICS/G-042_test.md", EntityType::Goal),
            (
                "governance/04_DECISIONS/D-001_arch.md",
                EntityType::Decision,
            ),
            ("governance/05_AUDITS/AUDIT_001.md", EntityType::Audit),
            ("governance/06_PROMPTS/test.md", EntityType::Prompt),
            ("governance/docs/canonical/CANON_I.md", EntityType::Canon),
        ];

        for (path_str, expected) in test_cases {
            let path = PathBuf::from(path_str);
            let result = FileChangeEvent::detect_entity_type(&path);
            assert_eq!(result, expected, "Failed for path: {}", path_str);
        }
    }

    #[test]
    fn test_entity_type_detection_by_filename() {
        let test_cases = vec![
            ("G-042_test.md", EntityType::Goal),
            ("PHASE_3_TEST.md", EntityType::Phase),
            ("D-001_decision.md", EntityType::Decision),
            ("AUDIT_TEST.md", EntityType::Audit),
        ];

        for (filename, expected) in test_cases {
            let path = PathBuf::from(filename);
            let result = FileChangeEvent::detect_entity_type(&path);
            assert_eq!(result, expected, "Failed for filename: {}", filename);
        }
    }

    #[test]
    fn test_debouncer() {
        let mut debouncer = Debouncer::new(100); // 100ms debounce
        let path = PathBuf::from("test.md");
        let now = SystemTime::now();

        // First event should be processed
        assert!(debouncer.should_process(&path, now));

        // Immediate second event should be skipped
        assert!(!debouncer.should_process(&path, now));

        // Event after debounce period should be processed
        let later = now + Duration::from_millis(150);
        assert!(debouncer.should_process(&path, later));
    }

    #[test]
    fn test_file_watcher_creation() {
        let temp_dir = TempDir::new().unwrap();
        let result = FileWatcher::new(temp_dir.path());
        assert!(result.is_ok(), "FileWatcher creation should succeed");
    }

    #[test]
    fn test_file_watcher_detects_markdown_changes() {
        let temp_dir = TempDir::new().unwrap();
        let governance_path = temp_dir.path();

        // Create governance structure
        let goals_dir = governance_path.join("03_GOALS_EPICS");
        fs::create_dir_all(&goals_dir).unwrap();

        // Create watcher before file changes
        let mut watcher = FileWatcher::new(governance_path).unwrap();

        // Give watcher time to initialize
        std::thread::sleep(Duration::from_millis(200));

        // Create a goal file
        let goal_file = goals_dir.join("G-001_test.md");
        fs::write(&goal_file, "# Test Goal\n").unwrap();

        // Give watcher time to detect the change
        std::thread::sleep(Duration::from_millis(300));

        // Check for event
        let event = watcher.next_event();
        assert!(event.is_some(), "Should detect file creation");

        if let Some(evt) = event {
            assert_eq!(evt.kind, ChangeKind::Create);
            assert_eq!(evt.entity_type, EntityType::Goal);
        }
    }

    #[test]
    fn test_file_watcher_ignores_non_markdown() {
        let temp_dir = TempDir::new().unwrap();
        let governance_path = temp_dir.path();

        let mut watcher = FileWatcher::new(governance_path).unwrap();

        // Give watcher time to initialize
        std::thread::sleep(Duration::from_millis(200));

        // Create a non-markdown file
        let txt_file = governance_path.join("test.txt");
        fs::write(&txt_file, "Test content\n").unwrap();

        // Give watcher time to process
        std::thread::sleep(Duration::from_millis(300));

        // Should not detect .txt file
        let event = watcher.next_event();
        assert!(event.is_none(), "Should ignore non-markdown files");
    }
}
