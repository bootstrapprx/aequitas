pub mod ingestion;
pub mod intent;
pub mod prompts;
pub mod validation;
pub mod materializer;
pub mod engine;

pub use engine::{ReasoningEngine, StructuredResult, ReasonerContextUsed};
pub use intent::{Intent, IntentGuess};
pub use validation::ValidationReport;
pub use materializer::DraftArtifact;
