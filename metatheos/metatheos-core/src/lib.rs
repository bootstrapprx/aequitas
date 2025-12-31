pub mod domain;
pub mod parser;
pub mod validator;
pub mod query;
pub mod canon;
pub mod governance;
pub mod errors;
pub mod llm;
pub mod writer;
pub mod reasoner;
pub mod store;
pub mod dashboard;

pub use domain::*;
pub use governance::{
    CanonDoc, DailyContext, DependencyGap, GovernanceContext, GovernanceState,
    GovernanceSummary, GovernanceWarning, GovernanceWarningKind, GoalRelations, PhaseGoalBreakdown,
    ProtocolDoc,
};
pub use validator::GovernanceValidator;
pub use query::GoalQuery;
pub use errors::{MetaError, Result};
pub use llm::{AIService, AIResponse, StatusSuggestion, ClaudeClient, ContextBuilder, PromptLogger};
pub use writer::{GoalWriter, PhaseWriter, DailyWriter};
pub use reasoner::{ReasoningEngine, StructuredResult};
pub use dashboard::{AequitasDashboard, DashboardCalculator};
