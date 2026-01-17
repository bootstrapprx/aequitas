pub mod api;
pub mod canon;
pub mod dashboard;
pub mod domain;
pub mod dto;
pub mod errors;
pub mod governance;
pub mod llm;
pub mod parser;
pub mod query;
pub mod reasoner;
pub mod repository;
pub mod service;
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
pub use repository::{GoalRepository, PhaseRepository};
pub use service::{GoalService, PhaseService};
pub use validator::GovernanceValidator;
pub use watcher::{
    ChangeKind, EntityType, FileChangeEvent, FileWatcher, GovernanceUpdateEvent, WatcherService,
};
pub use writer::{DailyWriter, GoalWriter, PhaseWriter};
pub use dto::{
    ApiErrorDto, AuditDto, AuthStatusDto, ContextOverviewDto, CountsDto, DayDto,
    DayTypeDto, DbStatusDto, GoalDto, GoalPriorityDto, GoalStatusDto, PhaseDto,
    PhaseStatus, PromptDto, ReadMode, TimelineItemDto, TimelineKind,
};

use std::path::PathBuf;
use std::sync::Arc;
use crate::store::SurrealStore;

#[derive(Debug, Clone, Default)]
pub struct Config {
    // Add fields if needed later
}

#[derive(Debug, Clone)]
pub struct AppState {
    pub store: Arc<SurrealStore>,
    pub config: Config,
    pub root_path: PathBuf,
}
