pub mod client;
pub mod context;
pub mod logger;
pub mod service;
pub mod runtime;

pub use client::{LLMClient, ClaudeClient, OllamaClient, Message};
pub use context::ContextBuilder;
pub use logger::PromptLogger;
pub use service::{AIService, AIResponse, StatusSuggestion};
pub use runtime::{OllamaRuntimeController, OllamaStatus, ModelInfo};
