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
        let api_key = std::env::var("ANTHROPIC_API_KEY").map_err(|_| {
            crate::errors::MetaError::ConfigError("ANTHROPIC_API_KEY not set".to_string())
        })?;
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
            let error_text = response
                .text()
                .await
                .unwrap_or_else(|_| "Unknown error".to_string());
            return Err(crate::errors::MetaError::NetworkError(format!(
                "Claude API error: {}",
                error_text
            )));
        }

        let response_json: serde_json::Value = response
            .json()
            .await
            .map_err(|e| crate::errors::MetaError::NetworkError(e.to_string()))?;

        // Extract text from response
        let text = response_json["content"][0]["text"]
            .as_str()
            .ok_or_else(|| {
                crate::errors::MetaError::NetworkError("Invalid response format".to_string())
            })?;

        Ok(text.to_string())
    }

    fn model_name(&self) -> &str {
        &self.model
    }
}

/// Ollama client for local LLM inference
pub struct OllamaClient {
    base_url: String,
    model: String,
}

impl OllamaClient {
    pub fn new(model: Option<String>) -> Self {
        let base_url = std::env::var("OLLAMA_BASE_URL")
            .unwrap_or_else(|_| "http://127.0.0.1:11435".to_string());
        Self {
            base_url,
            model: model.unwrap_or_else(|| "qwen2.5:7b-instruct".to_string()),
        }
    }

    pub fn with_base(model: Option<String>, base_url: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| {
                std::env::var("OLLAMA_BASE_URL")
                    .unwrap_or_else(|_| "http://127.0.0.1:11435".to_string())
            }),
            model: model.unwrap_or_else(|| {
                std::env::var("OLLAMA_MODEL").unwrap_or_else(|_| "qwen2.5:7b-instruct".to_string())
            }),
        }
    }

    pub fn from_env() -> Result<Self> {
        let model = std::env::var("OLLAMA_MODEL").ok();
        let base_url = std::env::var("OLLAMA_BASE_URL").ok();
        Ok(Self::with_base(model, base_url))
    }
}

#[async_trait::async_trait]
impl LLMClient for OllamaClient {
    async fn complete(&self, prompt: &str) -> Result<String> {
        let client = reqwest::Client::new();

        let body = serde_json::json!({
            "model": self.model,
            "prompt": prompt,
            "stream": false,
        });

        let url = format!("{}/api/generate", self.base_url);
        let response = client.post(&url).json(&body).send().await.map_err(|e| {
            crate::errors::MetaError::NetworkError(format!("Ollama request failed: {}", e))
        })?;

        if !response.status().is_success() {
            let error_text = response
                .text()
                .await
                .unwrap_or_else(|_| "Unknown error".to_string());
            return Err(crate::errors::MetaError::NetworkError(format!(
                "Ollama API error: {}",
                error_text
            )));
        }

        let response_json: serde_json::Value = response
            .json()
            .await
            .map_err(|e| crate::errors::MetaError::NetworkError(e.to_string()))?;

        let text = response_json["response"].as_str().ok_or_else(|| {
            crate::errors::MetaError::NetworkError("Invalid response format".to_string())
        })?;

        Ok(text.to_string())
    }

    async fn chat(&self, messages: Vec<Message>) -> Result<String> {
        let client = reqwest::Client::new();

        let body = serde_json::json!({
            "model": self.model,
            "messages": messages,
            "stream": false,
        });

        let url = format!("{}/api/chat", self.base_url);
        let response = client.post(&url).json(&body).send().await.map_err(|e| {
            crate::errors::MetaError::NetworkError(format!("Ollama chat failed: {}", e))
        })?;

        if !response.status().is_success() {
            let error_text = response
                .text()
                .await
                .unwrap_or_else(|_| "Unknown error".to_string());
            return Err(crate::errors::MetaError::NetworkError(format!(
                "Ollama API error: {}",
                error_text
            )));
        }

        let response_json: serde_json::Value = response
            .json()
            .await
            .map_err(|e| crate::errors::MetaError::NetworkError(e.to_string()))?;

        let text = response_json["message"]["content"]
            .as_str()
            .ok_or_else(|| {
                crate::errors::MetaError::NetworkError("Invalid chat response format".to_string())
            })?;

        Ok(text.to_string())
    }

    fn model_name(&self) -> &str {
        &self.model
    }
}
