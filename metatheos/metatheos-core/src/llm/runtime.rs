use crate::errors::{MetaError, Result};
use reqwest::StatusCode;
use serde::Deserialize;
use std::time::Duration;
use url::Url;

#[derive(Debug, Clone, Deserialize)]
pub struct ModelInfo {
    pub name: String,
    #[serde(default)]
    pub size: Option<u64>,
}

#[derive(Debug, Clone)]
pub struct OllamaStatus {
    pub reachable: bool,
    pub default_model_ready: bool,
    pub models: Vec<ModelInfo>,
    pub message: String,
}

#[derive(Debug, Clone)]
pub struct OllamaRuntimeController {
    base_url: Url,
    default_model: String,
    client: reqwest::Client,
}

impl OllamaRuntimeController {
    pub fn new(model: Option<String>, base_url: Option<String>) -> Result<Self> {
        let base = base_url
            .or_else(|| std::env::var("OLLAMA_BASE_URL").ok())
            .unwrap_or_else(|| "http://127.0.0.1:11435".to_string());
        let parsed = Url::parse(&base)
            .map_err(|e| MetaError::ConfigError(format!("Invalid OLLAMA_BASE_URL: {}", e)))?;

        let model = model
            .or_else(|| std::env::var("OLLAMA_MODEL").ok())
            .unwrap_or_else(|| "qwen2.5:7b-instruct".to_string());

        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(8))
            .build()
            .map_err(|e| MetaError::ConfigError(format!("Failed to build HTTP client: {}", e)))?;

        Ok(Self {
            base_url: parsed,
            default_model: model,
            client,
        })
    }

    pub fn model_name(&self) -> &str {
        &self.default_model
    }

    pub fn base_url(&self) -> &Url {
        &self.base_url
    }

    /// Health check: reachable + model availability
    pub async fn ollama_health(&self) -> Result<OllamaStatus> {
        let models = match self.ollama_models().await {
            Ok(list) => list,
            Err(err) => {
                return Ok(OllamaStatus {
                    reachable: false,
                    default_model_ready: false,
                    models: Vec::new(),
                    message: format!("Ollama unreachable: {}", err),
                });
            }
        };

        let default_model_ready = models
            .iter()
            .any(|m| m.name.eq_ignore_ascii_case(&self.default_model));

        Ok(OllamaStatus {
            reachable: true,
            default_model_ready,
            models,
            message: if default_model_ready {
                "ok".to_string()
            } else {
                format!("Model {} missing; pull manually on {}", self.default_model, self.base_url)
            },
        })
    }

    /// List available models via /api/tags
    pub async fn ollama_models(&self) -> Result<Vec<ModelInfo>> {
        let url = self
            .base_url
            .join("/api/tags")
            .map_err(|e| MetaError::ConfigError(format!("Invalid Ollama tags URL: {}", e)))?;

        let resp = self
            .client
            .get(url)
            .send()
            .await
            .map_err(|e| MetaError::NetworkError(format!("Ollama tags request failed: {}", e)))?;

        if resp.status() == StatusCode::NOT_FOUND {
            return Err(MetaError::NetworkError(
                "Ollama responded 404; is the base URL correct?".to_string(),
            ));
        }

        if !resp.status().is_success() {
            return Err(MetaError::NetworkError(format!(
                "Ollama responded with status {}",
                resp.status()
            )));
        }

        let json: serde_json::Value = resp
            .json()
            .await
            .map_err(|e| MetaError::NetworkError(format!("Failed to parse Ollama tags: {}", e)))?;

        let models = json["models"]
            .as_array()
            .unwrap_or(&Vec::new())
            .iter()
            .filter_map(|m| serde_json::from_value::<ModelInfo>(m.clone()).ok())
            .collect();

        Ok(models)
    }
}
