use std::path::{Path, PathBuf};

/// Canon boundary - read-only Canon access
pub struct CanonReader {
    canon_root: PathBuf,
}

impl CanonReader {
    pub fn new<P: AsRef<Path>>(governance_root: P) -> Self {
        let canon_root = governance_root.as_ref().join("canon");
        Self { canon_root }
    }

    pub fn exists(&self) -> bool {
        self.canon_root.exists()
    }

    pub fn list_canon_files(&self) -> Vec<PathBuf> {
        if !self.exists() {
            return Vec::new();
        }

        walkdir::WalkDir::new(&self.canon_root)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.path().is_file())
            .filter(|e| e.path().extension().and_then(|s| s.to_str()) == Some("md"))
            .map(|e| e.path().to_path_buf())
            .collect()
    }

    pub fn validate_reference<P: AsRef<Path>>(&self, reference: P) -> bool {
        self.canon_root.join(reference).exists()
    }
}
