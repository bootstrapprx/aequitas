pub mod domain;
pub mod parser;
pub mod validator;
pub mod query;
pub mod canon;
pub mod governance;
pub mod errors;

pub use domain::*;
pub use governance::GovernanceContext;
pub use validator::GovernanceValidator;
pub use query::GoalQuery;
pub use errors::{MetaError, Result};
