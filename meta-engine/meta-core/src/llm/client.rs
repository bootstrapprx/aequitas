use crate::errors::Result;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: String,
    pub content: String,
}

/// Trait for LLM client implementations
#[async_trait::async_trait]
pub trait LLMClient: Send + Sync {
    async fn complete(&self, prompt: &str) -> Result<String>;
    async fn chat(&self, messages: Vec<Message>) -> Result<String>;
    fn model_name(&self) -> &str;
}

/// Claude API client
pub struct ClaudeClient {
    api_key: String,
    model: String,
    max_tokens: usize,
}

impl ClaudeClient {
    pub fn new(api_key: String, model: Option<String>) -> Self {
        Self {
            api_key,
            model: model.unwrap_or_else(|| "claude-3-5-sonnet-20241022".to_string()),
            max_tokens: 4096,
        }
    }

    pub fn from_env() -> Result<Self> {
        let api_key = std::env::var("ANTHROPIC_API_KEY")
            .map_err(|_| crate::errors::MetaError::ConfigError("ANTHROPIC_API_KEY not set".to_string()))?;
        Ok(Self::new(api_key, None))
    }
}

#[async_trait::async_trait]
impl LLMClient for ClaudeClient {
    async fn complete(&self, prompt: &str) -> Result<String> {
        // Convert single prompt to message format
        let messages = vec![Message {
            role: "user".to_string(),
            content: prompt.to_string(),
        }];
        self.chat(messages).await
    }

    async fn chat(&self, messages: Vec<Message>) -> Result<String> {
        let client = reqwest::Client::new();

        let body = serde_json::json!({
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        });

        let response = client
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&body)
            .send()
            .await
            .map_err(|e| crate::errors::MetaError::NetworkError(e.to_string()))?;

        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(crate::errors::MetaError::NetworkError(format!("Claude API error: {}", error_text)));
        }

        let response_json: serde_json::Value = response
            .json()
            .await
            .map_err(|e| crate::errors::MetaError::NetworkError(e.to_string()))?;

        // Extract text from response
        let text = response_json["content"][0]["text"]
            .as_str()
            .ok_or_else(|| crate::errors::MetaError::NetworkError("Invalid response format".to_string()))?;

        Ok(text.to_string())
    }

    fn model_name(&self) -> &str {
        &self.model
    }
}
