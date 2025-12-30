use crate::errors::Result;
use crate::llm::runtime::OllamaRuntimeController;
use crate::llm::{LLMClient, Message, OllamaClient};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum Intent {
    DraftGoal,
    UpdateGoal,
    DraftDecision,
    DraftAudit,
    SummarizeState,
    AnalyzeBlockers,
    ExplainPhase,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntentGuess {
    pub intent: Intent,
    pub confidence: f32,
    pub rationale: String,
    pub used_rules: Vec<String>,
    pub required_inputs: Vec<String>,
}

pub struct IntentRouter;

impl IntentRouter {
    pub fn classify_rule_based(query: &str) -> Option<IntentGuess> {
        let lower = query.to_lowercase();
        let mut rules = Vec::new();

        let intent = if lower.contains("update goal") || lower.contains("edit goal") {
            rules.push("keyword:update_goal".to_string());
            Some(Intent::UpdateGoal)
        } else if lower.contains("new goal") || lower.contains("create goal") || lower.contains("goal draft") {
            rules.push("keyword:draft_goal".to_string());
            Some(Intent::DraftGoal)
        } else if lower.contains("audit") {
            rules.push("keyword:audit".to_string());
            Some(Intent::DraftAudit)
        } else if lower.contains("decision") || lower.contains("adr") || lower.contains("rfc") {
            rules.push("keyword:decision".to_string());
            Some(Intent::DraftDecision)
        } else if lower.contains("blocker") || lower.contains("blocked") {
            rules.push("keyword:blocker".to_string());
            Some(Intent::AnalyzeBlockers)
        } else if lower.contains("phase") || lower.contains("milestone") || lower.contains("timeline") {
            rules.push("keyword:phase".to_string());
            Some(Intent::ExplainPhase)
        } else if lower.contains("summarize") || lower.contains("overview") || lower.contains("state") {
            rules.push("keyword:summarize".to_string());
            Some(Intent::SummarizeState)
        } else {
            None
        };

        intent.map(|i| {
            let intent_clone = i.clone();
            IntentGuess {
                intent: intent_clone.clone(),
                confidence: 0.72,
                rationale: "Matched rule-based keyword heuristic".to_string(),
                used_rules: rules,
                required_inputs: default_required_inputs(&intent_clone),
            }
        })
    }

    pub async fn classify_with_ollama(
        query: &str,
        runtime: &OllamaRuntimeController,
    ) -> Result<IntentGuess> {
        let prompt = format!(
            "Classify the user's governance request into one of: \
draft_goal, update_goal, draft_decision, draft_audit, summarize_state, analyze_blockers, explain_phase. \
Reply ONLY with JSON: {{\"intent\":\"...\",\"confidence\":0-1,\"rationale\":\"...\"}}. \
If unsure, choose summarize_state.\n\nUser: {}",
            query
        );

        let client = OllamaClient::with_base(
            Some(runtime.model_name().to_string()),
            Some(runtime.base_url().to_string()),
        );

        let messages = vec![Message {
            role: "user".to_string(),
            content: prompt,
        }];

        let raw = client.chat(messages).await?;
        let parsed: serde_json::Value = serde_json::from_str(&raw).unwrap_or_else(|_| serde_json::json!({}));
        let intent_str = parsed["intent"].as_str().unwrap_or("summarize_state");
        let intent = match intent_str {
            "draft_goal" => Intent::DraftGoal,
            "update_goal" => Intent::UpdateGoal,
            "draft_decision" => Intent::DraftDecision,
            "draft_audit" => Intent::DraftAudit,
            "analyze_blockers" => Intent::AnalyzeBlockers,
            "explain_phase" => Intent::ExplainPhase,
            _ => Intent::SummarizeState,
        };

        let confidence = parsed["confidence"].as_f64().unwrap_or(0.4) as f32;
        let rationale = parsed["rationale"]
            .as_str()
            .unwrap_or("Defaulted after model classification.")
            .to_string();

        Ok(IntentGuess {
            intent: intent.clone(),
            confidence,
            rationale,
            used_rules: vec!["ollama:classifier".to_string()],
            required_inputs: default_required_inputs(&intent),
        })
    }

    pub async fn classify(query: &str, runtime: &OllamaRuntimeController) -> Result<IntentGuess> {
        if let Some(rule) = Self::classify_rule_based(query) {
            return Ok(rule);
        }
        Self::classify_with_ollama(query, runtime).await
    }
}

fn default_required_inputs(intent: &Intent) -> Vec<String> {
    match intent {
        Intent::DraftGoal => vec!["goal title", "phase", "status"].into_iter().map(|s| s.to_string()).collect(),
        Intent::UpdateGoal => vec!["goal id"].into_iter().map(|s| s.to_string()).collect(),
        Intent::DraftDecision => vec!["decision title", "scope"].into_iter().map(|s| s.to_string()).collect(),
        Intent::DraftAudit => vec!["targets", "scope"].into_iter().map(|s| s.to_string()).collect(),
        Intent::AnalyzeBlockers => vec!["scope or goals"].into_iter().map(|s| s.to_string()).collect(),
        Intent::ExplainPhase => vec!["phase id"].into_iter().map(|s| s.to_string()).collect(),
        Intent::SummarizeState => Vec::new(),
    }
}
