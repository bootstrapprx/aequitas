pub mod canon;
pub mod dashboard;
pub mod domain;
pub mod errors;
pub mod governance;
pub mod llm;
pub mod parser;
pub mod query;
pub mod reasoner;
pub mod store;
pub mod validator;
pub mod watcher;
pub mod writer;

pub use dashboard::{AequitasDashboard, DashboardCalculator};
pub use domain::*;
pub use errors::{MetaError, Result};
pub use governance::{
    CanonDoc, DailyContext, DependencyGap, GoalRelations, GovernanceContext, GovernanceState,
    GovernanceSummary, GovernanceWarning, GovernanceWarningKind, PhaseGoalBreakdown, ProtocolDoc,
    ReadOnlyGoal, ReadOnlyGovernanceContext, ReadOnlyPhase,
};
pub use llm::{
    AIResponse, AIService, ClaudeClient, ContextBuilder, PromptLogger, StatusSuggestion,
};
pub use query::GoalQuery;
pub use reasoner::{ReasoningEngine, StructuredResult};
pub use validator::GovernanceValidator;
pub use watcher::{
    ChangeKind, EntityType, FileChangeEvent, FileWatcher, GovernanceUpdateEvent, WatcherService,
};
pub use writer::{DailyWriter, GoalWriter, PhaseWriter};
