pub mod client;
pub mod context;
pub mod logger;
pub mod runtime;
pub mod service;

pub use client::{ClaudeClient, LLMClient, Message, OllamaClient};
pub use context::ContextBuilder;
pub use logger::PromptLogger;
pub use runtime::{ModelInfo, OllamaRuntimeController, OllamaStatus};
pub use service::{AIResponse, AIService, StatusSuggestion};
