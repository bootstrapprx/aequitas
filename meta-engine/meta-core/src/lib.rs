pub mod domain;
pub mod parser;
pub mod validator;
pub mod query;
pub mod canon;
pub mod governance;
pub mod errors;
pub mod llm;

pub use domain::*;
pub use governance::{
    CanonDoc, GovernanceContext, GovernanceState, GovernanceSummary, GovernanceWarning,
    GovernanceWarningKind,
};
pub use validator::GovernanceValidator;
pub use query::GoalQuery;
pub use errors::{MetaError, Result};
pub use llm::{AIService, AIResponse, StatusSuggestion, ClaudeClient, ContextBuilder, PromptLogger};
