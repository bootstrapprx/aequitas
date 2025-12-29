use metatheos_core::{
    AIService, ClaudeClient, ContextBuilder, GovernanceContext, PromptLogger,
};
use metatheos_core::llm::LLMClient;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tauri::State;

use crate::state::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct AIAskRequest {
    pub query: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AIAskResponse {
    pub text: String,
    pub context: String,
    pub model: String,
    pub has_api_key: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AIStatusSuggestionResponse {
    pub goal_id: String,
    pub current_status: String,
    pub suggested_status: String,
    pub reasoning: String,
    pub confidence: String,
}

/// Check if API key is configured
#[tauri::command]
pub fn ai_check_config() -> Result<bool, String> {
    Ok(std::env::var("ANTHROPIC_API_KEY").is_ok())
}

/// Ask AI a question about governance
#[tauri::command]
pub async fn ai_ask(query: String, state: State<'_, AppState>) -> Result<AIAskResponse, String> {
    // Check if API key is available
    let has_api_key = std::env::var("ANTHROPIC_API_KEY").is_ok();

    if !has_api_key {
        return Ok(AIAskResponse {
            text: "⚠️ **No API Key Configured**\n\nTo use AI assistance, please set your ANTHROPIC_API_KEY environment variable.\n\nAlternatively, use the built-in chatbot interface for basic assistance.".to_string(),
            context: String::new(),
            model: "none".to_string(),
            has_api_key: false,
        });
    }

    // Load governance context - clone path before async
    let root = {
        let guard = state.governance_root.lock().unwrap();
        guard.clone()
    };
    let ctx = GovernanceContext::load(&root).map_err(|e| e.to_string())?;

    // Create AI service
    let client = Arc::new(ClaudeClient::from_env().map_err(|e| e.to_string())?);
    let context_builder = ContextBuilder::new(50000);
    let logger = PromptLogger::new(&root);
    let ai_service = AIService::new(client.clone(), context_builder, logger);

    // Ask question
    let response = ai_service
        .ask(&query, &ctx)
        .await
        .map_err(|e| e.to_string())?;

    Ok(AIAskResponse {
        text: response.text,
        context: response.context,
        model: client.model_name().to_string(),
        has_api_key: true,
    })
}

/// Get AI suggestion for goal status
#[tauri::command]
pub async fn ai_suggest_status(
    goal_id: String,
    state: State<'_, AppState>,
) -> Result<AIStatusSuggestionResponse, String> {
    // Check if API key is available
    let has_api_key = std::env::var("ANTHROPIC_API_KEY").is_ok();

    if !has_api_key {
        return Err("No API key configured. Please set ANTHROPIC_API_KEY environment variable.".to_string());
    }

    // Load governance context - clone path before async
    let root = {
        let guard = state.governance_root.lock().unwrap();
        guard.clone()
    };
    let ctx = GovernanceContext::load(&root).map_err(|e| e.to_string())?;

    // Create AI service
    let client = Arc::new(ClaudeClient::from_env().map_err(|e| e.to_string())?);
    let context_builder = ContextBuilder::new(50000);
    let logger = PromptLogger::new(&root);
    let ai_service = AIService::new(client, context_builder, logger);

    // Get suggestion
    let suggestion = ai_service
        .suggest_status(&goal_id, &ctx)
        .await
        .map_err(|e| e.to_string())?;

    Ok(AIStatusSuggestionResponse {
        goal_id: suggestion.goal_id,
        current_status: suggestion.current_status,
        suggested_status: suggestion.suggested_status,
        reasoning: suggestion.reasoning,
        confidence: suggestion.confidence,
    })
}

/// Get conversation starters / example questions
#[tauri::command]
pub fn ai_get_examples(state: State<'_, AppState>) -> Result<Vec<String>, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let current_phase = ctx
        .active_phase()
        .map(|p| p.phase_id.clone())
        .unwrap_or_else(|| "unknown".to_string());

    let active_count = ctx.all_goals().iter().filter(|g| g.is_active()).count();
    let blocked_count = ctx.all_goals().iter().filter(|g| g.is_blocked()).count();

    let mut examples = vec![
        "What should I work on next?".to_string(),
        format!("Why do I have {} blocked goals?", blocked_count),
        format!("What's the status of Phase {}?", current_phase),
        "What are the dependencies for goal-onboarding-flow?".to_string(),
        "Are there any goals with no dependencies?".to_string(),
    ];

    if active_count > 0 {
        examples.insert(
            1,
            format!("Summarize my {} active goals", active_count),
        );
    }

    Ok(examples)
}
