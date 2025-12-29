use thiserror::Error;

#[derive(Error, Debug)]
pub enum MetaError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("YAML parsing error: {0}")]
    Yaml(#[from] serde_yaml::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("Missing required frontmatter field: {field} in {file}")]
    MissingFrontmatter { field: String, file: String },

    #[error("Invalid {field} value: {value} in {file}")]
    InvalidField {
        field: String,
        value: String,
        file: String,
    },

    #[error("Invalid goal status transition: {from} -> {to}")]
    InvalidTransition { from: String, to: String },

    #[error("Goal not found: {0}")]
    GoalNotFound(String),

    #[error("Invalid goal ID format: {0}")]
    InvalidGoalId(String),

    #[error("Invalid decision ID format: {0}")]
    InvalidDecisionId(String),

    #[error("Validation error in {file}:{line} - {message}")]
    Validation {
        file: String,
        line: usize,
        message: String,
    },

    #[error("Canon boundary violation: {0}")]
    CanonViolation(String),

    #[error("Governance folder not found: {0}")]
    GovernanceFolderNotFound(String),
}

pub type Result<T> = std::result::Result<T, MetaError>;
