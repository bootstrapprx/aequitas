use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum MetaError {
    // ============================================================================
    // I/O and Parsing Errors
    // ============================================================================
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("YAML parsing error: {0}")]
    Yaml(#[from] serde_yaml::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    // ============================================================================
    // Database Errors
    // ============================================================================
    #[error("Database connection error: {0}")]
    DatabaseConnection(String),

    #[error("Database query error: {0}")]
    DatabaseQuery(String),

    #[error("Database serialization error: {0}")]
    DatabaseSerialization(String),

    #[error("Database constraint violation: {0}")]
    DatabaseConstraint(String),

    #[error("Database migration error: {0}")]
    DatabaseMigration(String),

    // ============================================================================
    // Resource Not Found Errors
    // ============================================================================
    #[error("Phase not found: {0}")]
    PhaseNotFound(String),

    #[error("Goal not found: {0}")]
    GoalNotFound(String),

    #[error("Work item not found: {0}")]
    WorkItemNotFound(String),

    #[error("Day not found: {0}")]
    DayNotFound(String),

    #[error("Annotation not found: {0}")]
    AnnotationNotFound(String),

    #[error("Event not found: {0}")]
    EventNotFound(String),

    #[error("Governance folder not found: {0}")]
    GovernanceFolderNotFound(String),

    // ============================================================================
    // Validation and Business Logic Errors
    // ============================================================================
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

    #[error("Validation error: {0}")]
    ValidationError(String),

    #[error("Canon boundary violation: {0}")]
    CanonViolation(String),

    // ============================================================================
    // State and Conflict Errors
    // ============================================================================
    #[error("Resource already exists: {resource_type} with ID {id}")]
    AlreadyExists { resource_type: String, id: String },

    #[error("Invalid state for operation: {0}")]
    InvalidState(String),

    #[error("Operation not permitted: {0}")]
    OperationNotPermitted(String),

    #[error("Dependency not satisfied: {0}")]
    DependencyNotSatisfied(String),

    // ============================================================================
    // External Service Errors
    // ============================================================================
    #[error("Network error: {0}")]
    NetworkError(String),

    #[error("AI service error: {0}")]
    AiServiceError(String),

    #[error("Git operation error: {0}")]
    GitError(String),

    // ============================================================================
    // Configuration and System Errors
    // ============================================================================
    #[error("Configuration error: {0}")]
    ConfigError(String),

    #[error("Parse error: {0}")]
    ParseError(String),

    #[error("System error: {0}")]
    SystemError(String),

    #[error("Timeout error: {0}")]
    TimeoutError(String),

    #[error("Internal error: {0}")]
    InternalError(String),
}

impl From<anyhow::Error> for MetaError {
    fn from(err: anyhow::Error) -> Self {
        MetaError::SystemError(err.to_string())
    }
}

impl MetaError {
    /// Get error code for categorization
    pub fn error_code(&self) -> &'static str {
        match self {
            // I/O and Parsing
            MetaError::Io(_) => "ERR_IO",
            MetaError::Yaml(_) => "ERR_YAML_PARSE",
            MetaError::Json(_) => "ERR_JSON_PARSE",

            // Database
            MetaError::DatabaseConnection(_) => "ERR_DB_CONNECTION",
            MetaError::DatabaseQuery(_) => "ERR_DB_QUERY",
            MetaError::DatabaseSerialization(_) => "ERR_DB_SERIALIZATION",
            MetaError::DatabaseConstraint(_) => "ERR_DB_CONSTRAINT",
            MetaError::DatabaseMigration(_) => "ERR_DB_MIGRATION",

            // Not Found
            MetaError::PhaseNotFound(_) => "ERR_PHASE_NOT_FOUND",
            MetaError::GoalNotFound(_) => "ERR_GOAL_NOT_FOUND",
            MetaError::WorkItemNotFound(_) => "ERR_WORK_ITEM_NOT_FOUND",
            MetaError::DayNotFound(_) => "ERR_DAY_NOT_FOUND",
            MetaError::AnnotationNotFound(_) => "ERR_ANNOTATION_NOT_FOUND",
            MetaError::EventNotFound(_) => "ERR_EVENT_NOT_FOUND",
            MetaError::GovernanceFolderNotFound(_) => "ERR_FOLDER_NOT_FOUND",

            // Validation
            MetaError::MissingFrontmatter { .. } => "ERR_MISSING_FIELD",
            MetaError::InvalidField { .. } => "ERR_INVALID_FIELD",
            MetaError::InvalidTransition { .. } => "ERR_INVALID_TRANSITION",
            MetaError::InvalidGoalId(_) => "ERR_INVALID_GOAL_ID",
            MetaError::InvalidDecisionId(_) => "ERR_INVALID_DECISION_ID",
            MetaError::Validation { .. } => "ERR_VALIDATION",
            MetaError::ValidationError(_) => "ERR_VALIDATION",
            MetaError::CanonViolation(_) => "ERR_CANON_VIOLATION",

            // State and Conflicts
            MetaError::AlreadyExists { .. } => "ERR_ALREADY_EXISTS",
            MetaError::InvalidState(_) => "ERR_INVALID_STATE",
            MetaError::OperationNotPermitted(_) => "ERR_OPERATION_NOT_PERMITTED",
            MetaError::DependencyNotSatisfied(_) => "ERR_DEPENDENCY_NOT_SATISFIED",

            // External Services
            MetaError::NetworkError(_) => "ERR_NETWORK",
            MetaError::AiServiceError(_) => "ERR_AI_SERVICE",
            MetaError::GitError(_) => "ERR_GIT",

            // System
            MetaError::ConfigError(_) => "ERR_CONFIG",
            MetaError::ParseError(_) => "ERR_PARSE",
            MetaError::SystemError(_) => "ERR_SYSTEM",
            MetaError::TimeoutError(_) => "ERR_TIMEOUT",
            MetaError::InternalError(_) => "ERR_INTERNAL",
        }
    }

    /// Get HTTP status code equivalent
    pub fn http_status(&self) -> u16 {
        match self {
            // 400 - Bad Request
            MetaError::Yaml(_)
            | MetaError::Json(_)
            | MetaError::InvalidField { .. }
            | MetaError::InvalidGoalId(_)
            | MetaError::InvalidDecisionId(_)
            | MetaError::Validation { .. }
            | MetaError::ValidationError(_)
            | MetaError::ParseError(_) => 400,

            // 403 - Forbidden
            MetaError::CanonViolation(_) | MetaError::OperationNotPermitted(_) => 403,

            // 404 - Not Found
            MetaError::PhaseNotFound(_)
            | MetaError::GoalNotFound(_)
            | MetaError::WorkItemNotFound(_)
            | MetaError::DayNotFound(_)
            | MetaError::AnnotationNotFound(_)
            | MetaError::EventNotFound(_)
            | MetaError::GovernanceFolderNotFound(_) => 404,

            // 409 - Conflict
            MetaError::AlreadyExists { .. }
            | MetaError::InvalidTransition { .. }
            | MetaError::DatabaseConstraint(_) => 409,

            // 422 - Unprocessable Entity
            MetaError::MissingFrontmatter { .. }
            | MetaError::InvalidState(_)
            | MetaError::DependencyNotSatisfied(_) => 422,

            // 500 - Internal Server Error
            MetaError::Io(_)
            | MetaError::DatabaseConnection(_)
            | MetaError::DatabaseQuery(_)
            | MetaError::DatabaseSerialization(_)
            | MetaError::DatabaseMigration(_)
            | MetaError::ConfigError(_)
            | MetaError::SystemError(_)
            | MetaError::InternalError(_) => 500,

            // 502 - Bad Gateway (external services)
            MetaError::AiServiceError(_) => 502,

            // 503 - Service Unavailable
            MetaError::NetworkError(_) | MetaError::GitError(_) => 503,

            // 504 - Gateway Timeout
            MetaError::TimeoutError(_) => 504,
        }
    }

    /// Convert to frontend-friendly error response
    pub fn to_response(&self) -> ErrorResponse {
        ErrorResponse {
            error: true,
            code: self.error_code().to_string(),
            message: self.to_string(),
            status: self.http_status(),
        }
    }
}

/// Frontend-friendly error response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub error: bool,
    pub code: String,
    pub message: String,
    pub status: u16,
}

pub type Result<T> = std::result::Result<T, MetaError>;
