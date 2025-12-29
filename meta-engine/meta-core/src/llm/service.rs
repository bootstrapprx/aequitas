use crate::errors::Result;
use crate::governance::GovernanceContext;
use crate::llm::{LLMClient, ContextBuilder, PromptLogger, InteractionMetadata};
use crate::domain::GoalStatus;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::Instant;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIResponse {
    pub text: String,
    pub context: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusSuggestion {
    pub goal_id: String,
    pub current_status: String,
    pub suggested_status: String,
    pub reasoning: String,
    pub confidence: String, // "high", "medium", "low"
}

pub struct AIService {
    client: Arc<dyn LLMClient>,
    context_builder: ContextBuilder,
    logger: PromptLogger,
}

impl AIService {
    pub fn new(
        client: Arc<dyn LLMClient>,
        context_builder: ContextBuilder,
        logger: PromptLogger,
    ) -> Self {
        Self {
            client,
            context_builder,
            logger,
        }
    }

    /// Ask a general question about governance
    pub async fn ask(&self, query: &str, ctx: &GovernanceContext) -> Result<AIResponse> {
        let start = Instant::now();

        // Build context
        let context = self.context_builder.for_query(ctx, query);

        // Build system prompt
        let system_prompt = self.build_system_prompt();

        // Build full prompt
        let full_prompt = format!(
            "{}\n\n# Governance Context\n{}\n\n# User Question\n{}\n\nProvide a concise, actionable response. Reference specific goal IDs when relevant.",
            system_prompt,
            context,
            query
        );

        // Get AI response
        let response_text = self.client.complete(&full_prompt).await?;

        let duration_ms = start.elapsed().as_millis() as u64;

        // Log interaction
        let metadata = InteractionMetadata {
            model: self.client.model_name().to_string(),
            tokens_in: None, // TODO: estimate tokens
            tokens_out: None,
            duration_ms: Some(duration_ms),
        };

        self.logger.log_interaction(query, &context, &response_text, metadata)?;

        Ok(AIResponse {
            text: response_text,
            context,
        })
    }

    /// Suggest next status for a goal
    pub async fn suggest_status(
        &self,
        goal_id: &str,
        ctx: &GovernanceContext,
    ) -> Result<StatusSuggestion> {
        let goal = ctx.get_goal(goal_id)
            .ok_or_else(|| crate::errors::MetaError::InvalidGoalId(goal_id.to_string()))?;

        // Build context for this specific goal
        let context = self.context_builder.for_goal(ctx, goal_id)
            .ok_or_else(|| crate::errors::MetaError::InvalidGoalId(goal_id.to_string()))?;

        // Get allowed transitions
        let current_status = &goal.status;
        let allowed_transitions: Vec<String> = vec![
            GoalStatus::Planned,
            GoalStatus::Active,
            GoalStatus::Blocked,
            GoalStatus::Partial,
            GoalStatus::Done,
            GoalStatus::Archived,
        ]
        .into_iter()
        .filter(|s| current_status.can_transition_to(s))
        .map(|s| s.to_string())
        .collect();

        // Build prompt
        let prompt = format!(
            "Analyze this goal and suggest the most appropriate next status.\n\n{}\n\n\
            Current Status: {}\n\
            Allowed transitions: {}\n\n\
            Provide your response in this exact format:\n\
            SUGGESTED_STATUS: <status>\n\
            REASONING: <brief explanation>\n\
            CONFIDENCE: <high|medium|low>\n",
            context,
            current_status,
            allowed_transitions.join(", ")
        );

        let response_text = self.client.complete(&prompt).await?;

        // Parse response
        let suggestion = self.parse_status_suggestion(goal_id, &goal.status.to_string(), &response_text);

        Ok(suggestion)
    }

    fn build_system_prompt(&self) -> String {
        r#"You are an AI assistant for the Aequitas governance system.
You help architects manage goals, decisions, and phases.

Your responses should:
- Be concise and actionable (2-3 paragraphs maximum)
- Reference specific goal IDs when relevant
- Explain your reasoning clearly
- Never suggest modifying Canon documents
- Respect phase boundaries and dependencies

Remember: You suggest, the human decides. Never be prescriptive."#.to_string()
    }

    fn parse_status_suggestion(&self, goal_id: &str, current_status: &str, response: &str) -> StatusSuggestion {
        let mut suggested_status = current_status.to_string();
        let mut reasoning = "No clear suggestion provided".to_string();
        let mut confidence = "low".to_string();

        for line in response.lines() {
            if line.starts_with("SUGGESTED_STATUS:") {
                suggested_status = line.replace("SUGGESTED_STATUS:", "").trim().to_lowercase();
            } else if line.starts_with("REASONING:") {
                reasoning = line.replace("REASONING:", "").trim().to_string();
            } else if line.starts_with("CONFIDENCE:") {
                confidence = line.replace("CONFIDENCE:", "").trim().to_lowercase();
            }
        }

        StatusSuggestion {
            goal_id: goal_id.to_string(),
            current_status: current_status.to_string(),
            suggested_status,
            reasoning,
            confidence,
        }
    }
}
