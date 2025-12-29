use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ValidationSeverity {
    Error,
    Warning,
    Info,
}

impl std::fmt::Display for ValidationSeverity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ValidationSeverity::Error => write!(f, "❌ Error"),
            ValidationSeverity::Warning => write!(f, "⚠ Warning"),
            ValidationSeverity::Info => write!(f, "ℹ Info"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub severity: ValidationSeverity,
    pub file: PathBuf,
    pub line: Option<usize>,
    pub message: String,
}

impl ValidationResult {
    pub fn error<P: Into<PathBuf>>(file: P, message: impl Into<String>) -> Self {
        Self {
            severity: ValidationSeverity::Error,
            file: file.into(),
            line: Some(1),
            message: message.into(),
        }
    }

    pub fn warning<P: Into<PathBuf>>(file: P, message: impl Into<String>) -> Self {
        Self {
            severity: ValidationSeverity::Warning,
            file: file.into(),
            line: None,
            message: message.into(),
        }
    }

    pub fn info<P: Into<PathBuf>>(file: P, message: impl Into<String>) -> Self {
        Self {
            severity: ValidationSeverity::Info,
            file: file.into(),
            line: None,
            message: message.into(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Audit {
    pub results: Vec<ValidationResult>,
    pub total_files: usize,
}

impl Audit {
    pub fn new() -> Self {
        Self {
            results: Vec::new(),
            total_files: 0,
        }
    }

    pub fn add_result(&mut self, result: ValidationResult) {
        self.results.push(result);
    }

    pub fn error_count(&self) -> usize {
        self.results
            .iter()
            .filter(|r| r.severity == ValidationSeverity::Error)
            .count()
    }

    pub fn warning_count(&self) -> usize {
        self.results
            .iter()
            .filter(|r| r.severity == ValidationSeverity::Warning)
            .count()
    }

    pub fn info_count(&self) -> usize {
        self.results
            .iter()
            .filter(|r| r.severity == ValidationSeverity::Info)
            .count()
    }

    pub fn has_errors(&self) -> bool {
        self.error_count() > 0
    }
}

impl Default for Audit {
    fn default() -> Self {
        Self::new()
    }
}

/// Governance audit document (05_AUDITS)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditRecord {
    pub title: String,
    pub date: Option<NaiveDate>,
    pub scope: Option<String>,
    pub risk: Option<String>,
    pub auditor: Option<String>,
    pub file_path: PathBuf,
    pub summary: Option<String>,
    pub content: String,
}
