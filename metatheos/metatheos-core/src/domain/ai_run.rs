use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum AIProvider {
    Ollama,
    OpenAI,
    Anthropic,
    Mistral,
}

impl AIProvider {
    pub fn as_str(&self) -> &str {
        match self {
            AIProvider::Ollama => "ollama",
            AIProvider::OpenAI => "openai",
            AIProvider::Anthropic => "anthropic",
            AIProvider::Mistral => "mistral",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "ollama" => Some(Self::Ollama),
            "openai" => Some(Self::OpenAI),
            "anthropic" => Some(Self::Anthropic),
            "mistral" => Some(Self::Mistral),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum AIIntent {
    Summarize,
    Expand,
    Critique,
    Plan,
    Refine,
    Validate,
    Chat,
}

impl AIIntent {
    pub fn as_str(&self) -> &str {
        match self {
            AIIntent::Summarize => "summarize",
            AIIntent::Expand => "expand",
            AIIntent::Critique => "critique",
            AIIntent::Plan => "plan",
            AIIntent::Refine => "refine",
            AIIntent::Validate => "validate",
            AIIntent::Chat => "chat",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "summarize" => Some(Self::Summarize),
            "expand" => Some(Self::Expand),
            "critique" => Some(Self::Critique),
            "plan" => Some(Self::Plan),
            "refine" => Some(Self::Refine),
            "validate" => Some(Self::Validate),
            "chat" => Some(Self::Chat),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum AIRunStatus {
    Draft,    // AI generated but not yet applied
    Applied,  // User confirmed and changes applied
    Rejected, // User rejected the draft
}

impl AIRunStatus {
    pub fn as_str(&self) -> &str {
        match self {
            AIRunStatus::Draft => "draft",
            AIRunStatus::Applied => "applied",
            AIRunStatus::Rejected => "rejected",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "draft" => Some(Self::Draft),
            "applied" => Some(Self::Applied),
            "rejected" => Some(Self::Rejected),
            _ => None,
        }
    }
}

/// AI Run record - every AI interaction logged for safety and auditability
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIRun {
    pub id: String,
    pub provider: AIProvider,
    pub model: String,
    pub intent: AIIntent,
    pub context_ref: JsonValue, // JSON with phase_id, goal_id, work_item_id, etc.
    pub prompt: String,
    pub response: String,
    pub status: AIRunStatus,
    pub created_at: DateTime<Utc>,
}

impl AIRun {
    /// Create a new AI run in draft status
    pub fn new(
        provider: AIProvider,
        model: impl Into<String>,
        intent: AIIntent,
        context_ref: JsonValue,
        prompt: impl Into<String>,
        response: impl Into<String>,
    ) -> Self {
        use uuid::Uuid;
        Self {
            id: format!("AI-{}", Uuid::new_v4()),
            provider,
            model: model.into(),
            intent,
            context_ref,
            prompt: prompt.into(),
            response: response.into(),
            status: AIRunStatus::Draft,
            created_at: Utc::now(),
        }
    }

    /// Mark this run as applied
    pub fn apply(&mut self) {
        self.status = AIRunStatus::Applied;
    }

    /// Mark this run as rejected
    pub fn reject(&mut self) {
        self.status = AIRunStatus::Rejected;
    }

    /// Check if this run is still a draft
    pub fn is_draft(&self) -> bool {
        self.status == AIRunStatus::Draft
    }
}

/// Prompt template for reusable prompts
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptTemplate {
    pub id: String,
    pub name: String,
    pub intent: AIIntent,
    pub template: String,
    pub output_schema: Option<JsonValue>, // JSON schema for expected output
    pub created_at: DateTime<Utc>,
}

impl PromptTemplate {
    pub fn new(
        name: impl Into<String>,
        intent: AIIntent,
        template: impl Into<String>,
        output_schema: Option<JsonValue>,
    ) -> Self {
        use uuid::Uuid;
        Self {
            id: format!("TEMPLATE-{}", Uuid::new_v4()),
            name: name.into(),
            intent,
            template: template.into(),
            output_schema,
            created_at: Utc::now(),
        }
    }
}
