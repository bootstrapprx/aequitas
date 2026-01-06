/// Service layer for business logic
///
/// Services orchestrate business operations, coordinate between repositories,
/// handle validation, and enforce business rules.

pub mod goal_service;
pub mod phase_service;

pub use goal_service::GoalService;
pub use phase_service::PhaseService;
