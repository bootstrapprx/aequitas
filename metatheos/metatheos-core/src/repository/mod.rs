/// Repository layer for database access
///
/// Repositories handle CRUD operations and database interactions.
/// They use DTOs for serialization and return domain models.

pub mod goal_repository;
pub mod phase_repository;

pub use goal_repository::GoalRepository;
pub use phase_repository::PhaseRepository;
