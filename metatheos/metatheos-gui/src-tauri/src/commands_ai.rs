use metatheos_core::{
    AIService, ClaudeClient, ContextBuilder, GovernanceContext, PromptLogger,
};
use metatheos_core::reasoner::{ReasoningEngine, ReasonerContextUsed, Intent};
use metatheos_core::llm::runtime::OllamaRuntimeController;
use metatheos_core::reasoner::DraftArtifact;
use metatheos_core::llm::LLMClient;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use tauri::State;

use crate::state::AppState;

#[derive(Debug, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct AIAskRequest {
    pub query: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AIAskResponse {
    pub text: String,
    pub context: String,
    pub model: String,
    pub has_api_key: bool,
    pub context_descriptor: AIContextDescriptor,
    pub rejected: bool,
    pub unknown_references: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AIStatusSuggestionResponse {
    pub goal_id: String,
    pub current_status: String,
    pub suggested_status: String,
    pub reasoning: String,
    pub confidence: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct AIContextDescriptor {
    pub phase: Option<String>,
    pub included_goals: Vec<String>,
    pub status_counts: HashMap<String, usize>,
    pub decisions_loaded: bool,
    pub audits_loaded: bool,
    pub mode: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ReasonerContextSummary {
    pub phase: Option<ReasonerItem>,
    pub goals: Vec<ReasonerItem>,
    pub decisions: Vec<ReasonerItem>,
    pub audits: Vec<ReasonerItem>,
    pub daily_notes: Vec<ReasonerItem>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ReasonerItem {
    pub id: String,
    pub status: Option<String>,
    pub phase: Option<String>,
    pub path: String,
    pub summary: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ReasonerValidation {
    pub valid: bool,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ReasonerResponse {
    pub intent: String,
    pub confidence: f32,
    pub rationale: String,
    pub required_inputs: Vec<String>,
    pub context_used: ReasonerContextSummary,
    pub draft_path: Option<String>,
    pub draft_frontmatter: Option<String>,
    pub draft_body: Option<String>,
    pub draft_markdown: Option<String>,
    pub validation: ReasonerValidation,
    pub raw_model_output: String,
    pub model: String,
    pub base_url: String,
    pub next_actions: Vec<String>,
    pub message: Option<String>,
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
            context_descriptor: AIContextDescriptor {
                mode: "stateless".to_string(),
                ..Default::default()
            },
            rejected: false,
            unknown_references: Vec::new(),
        });
    }

    // Load governance context - clone path before async
    let root = {
        let guard = state.governance_root.lock().unwrap();
        guard.clone()
    };
    let ctx = GovernanceContext::load(&root).map_err(|e| e.to_string())?;
    let descriptor = build_context_descriptor(&ctx);

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

    let unknown_refs = find_unknown_references(&response.text, &ctx);
    let rejected = !unknown_refs.is_empty();
    let safe_text = if rejected {
        format!(
            "Response rejected: referenced unknown or unmapped IDs: {}",
            unknown_refs.join(", ")
        )
    } else {
        response.text.clone()
    };

    Ok(AIAskResponse {
        text: safe_text,
        context: response.context,
        model: client.model_name().to_string(),
        has_api_key: true,
        context_descriptor: descriptor,
        rejected,
        unknown_references: unknown_refs,
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

/// Build a short manual context snippet for copy/paste into web chats (no auto injection)
#[tauri::command]
pub fn get_context_clipboard_payload(
    selected_goals: Option<Vec<String>>,
    current_path: Option<String>,
    state: State<'_, AppState>,
) -> Result<String, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;

    let phase = ctx.active_phase().map(|p| p.phase_id.clone()).unwrap_or_else(|| "unknown".to_string());
    let goals = selected_goals.unwrap_or_default();
    let mut lines = Vec::new();
    lines.push("Metatheos Governance Context (manual paste)".to_string());
    lines.push(format!("Active phase: {}", phase));
    if !goals.is_empty() {
        lines.push(format!("Goals: {}", goals.join(", ")));
    } else {
        lines.push("Goals: (none selected)".to_string());
    }
    if let Some(path) = current_path {
        if !path.is_empty() {
            lines.push(format!("Last file: {}", path));
        }
    }
    lines.push("Warning: No vault context here. Do not request auto-writes; drafts only.".to_string());

    Ok(lines.join("\n"))
}

/// Local Ollama reasoning pipeline (reason-only, returns drafts)
#[tauri::command]
pub async fn ollama_reason(
    query: String,
    intent_override: Option<String>,
    state: State<'_, AppState>,
) -> Result<ReasonerResponse, String> {
    let root = {
        let guard = state.governance_root.lock().unwrap();
        guard.clone()
    };

    let ctx = GovernanceContext::load(&root).map_err(|e| e.to_string())?;
    let runtime = OllamaRuntimeController::new(None, None).map_err(|e| e.to_string())?;
    let health = runtime
        .ollama_health()
        .await
        .map_err(|e| e.to_string())?;

    if !health.reachable {
        return Err(health.message);
    }
    if !health.default_model_ready {
        return Err(format!("Model {} not available: {}", runtime.model_name(), health.message));
    }

    let engine = ReasoningEngine::new(runtime.clone());
    let override_intent = intent_override
        .as_deref()
        .and_then(|s| match s {
            "draft_goal" => Some(Intent::DraftGoal),
            "update_goal" => Some(Intent::UpdateGoal),
            "draft_decision" => Some(Intent::DraftDecision),
            "draft_audit" => Some(Intent::DraftAudit),
            "summarize_state" => Some(Intent::SummarizeState),
            "analyze_blockers" => Some(Intent::AnalyzeBlockers),
            "explain_phase" => Some(Intent::ExplainPhase),
            _ => None,
        });

    let result = engine
        .run(&query, &ctx, override_intent)
        .await
        .map_err(|e| e.to_string())?;

    let draft_markdown = result.draft.as_ref().map(|d| {
        format!("---\n{}---\n\n{}", d.frontmatter, d.body)
    });

    Ok(ReasonerResponse {
        intent: format!("{:?}", result.intent),
        confidence: result.intent_guess.confidence,
        rationale: result.intent_guess.rationale,
        required_inputs: result.required_inputs.clone(),
        context_used: to_summary(&result.context_used),
        draft_path: result.draft.as_ref().map(|d| d.target_path.to_string_lossy().to_string()),
        draft_frontmatter: result.draft.as_ref().map(|d| d.frontmatter.clone()),
        draft_body: result.draft.as_ref().map(|d| d.body.clone()),
        draft_markdown,
        validation: ReasonerValidation {
            valid: result.validation.errors.is_empty(),
            errors: result.validation.errors.clone(),
            warnings: result.validation.warnings.clone(),
        },
        raw_model_output: result.raw_model_output,
        model: runtime.model_name().to_string(),
        base_url: runtime.base_url().to_string(),
        next_actions: result.next_actions,
        message: None,
    })
}

fn build_context_descriptor(ctx: &GovernanceContext) -> AIContextDescriptor {
    let phase = ctx.active_phase().map(|p| p.phase_id);
    let included_goals = collect_included_goals(ctx);
    let status_counts = collect_status_counts(ctx);

    AIContextDescriptor {
        phase,
        included_goals,
        status_counts,
        decisions_loaded: false,
        audits_loaded: false,
        mode: "stateless".to_string(),
    }
}

fn collect_included_goals(ctx: &GovernanceContext) -> Vec<String> {
    let mut ids: Vec<String> = Vec::new();
    let mut push_unique = |value: String| {
        if !ids.iter().any(|existing| existing.eq_ignore_ascii_case(&value)) {
            ids.push(value);
        }
    };

    for goal in ctx
        .all_goals()
        .iter()
        .filter(|g| g.is_active())
        .take(10)
    {
        push_unique(goal.goal_id.clone());
    }

    for goal in ctx
        .all_goals()
        .iter()
        .filter(|g| g.is_blocked())
        .take(5)
    {
        push_unique(goal.goal_id.clone());
    }

    for goal in ctx
        .all_goals()
        .iter()
        .filter(|g| g.is_done())
        .take(5)
    {
        push_unique(goal.goal_id.clone());
    }

    ids
}

fn collect_status_counts(ctx: &GovernanceContext) -> HashMap<String, usize> {
    let mut counts: HashMap<String, usize> = HashMap::new();
    for goal in ctx.all_goals() {
        *counts.entry(goal.status.to_string()).or_insert(0) += 1;
    }
    counts
}

fn find_unknown_references(text: &str, ctx: &GovernanceContext) -> Vec<String> {
    let known_goals: HashSet<String> = ctx
        .all_goals()
        .iter()
        .map(|g| g.goal_id.to_lowercase())
        .collect();
    let known_decisions: HashSet<String> = ctx
        .all_decisions()
        .iter()
        .map(|d| d.decision_id.to_lowercase())
        .collect();
    let known_audits: HashSet<String> = ctx
        .all_audits()
        .iter()
        .filter_map(|a| a.file_path.file_stem())
        .filter_map(|s| s.to_str())
        .map(|s| s.to_lowercase())
        .collect();

    let mut unknown: Vec<String> = Vec::new();

    for token in text
        .split(|c: char| !c.is_alphanumeric() && c != '-' && c != '_')
        .filter(|t| !t.is_empty())
    {
        let lower = token.to_lowercase();
        let mut is_goal_like = lower.starts_with("goal-") || lower.starts_with("g-");
        is_goal_like = is_goal_like || lower.starts_with("goal_") || lower.starts_with("g_");
        let is_decision_like = lower.starts_with("decision-") || lower.starts_with("dec-");
        let is_audit_like = lower.starts_with("audit-") || lower.starts_with("audit_");

        if is_goal_like && !known_goals.contains(&lower) {
            if !unknown.iter().any(|u| u.eq_ignore_ascii_case(token)) {
                unknown.push(token.to_string());
            }
        } else if is_decision_like && !known_decisions.contains(&lower) {
            if !unknown.iter().any(|u| u.eq_ignore_ascii_case(token)) {
                unknown.push(token.to_string());
            }
        } else if is_audit_like && !known_audits.contains(&lower) {
            if !unknown.iter().any(|u| u.eq_ignore_ascii_case(token)) {
                unknown.push(token.to_string());
            }
        }
    }

    unknown
}

fn to_summary(ctx: &ReasonerContextUsed) -> ReasonerContextSummary {
    ReasonerContextSummary {
        phase: ctx.phase.as_ref().map(to_item),
        goals: ctx.goals.iter().map(to_item).collect(),
        decisions: ctx.decisions.iter().map(to_item).collect(),
        audits: ctx.audits.iter().map(to_item).collect(),
        daily_notes: ctx.daily_notes.iter().map(to_item).collect(),
    }
}

fn to_item(item: &metatheos_core::reasoner::ingestion::SummaryItem) -> ReasonerItem {
    ReasonerItem {
        id: item.id.clone(),
        status: item.status.clone(),
        phase: item.phase.clone(),
        path: item.path.to_string_lossy().to_string(),
        summary: item.summary.clone(),
    }
}
