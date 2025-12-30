use crate::errors::Result;
use crate::governance::GovernanceContext;
use crate::llm::runtime::OllamaRuntimeController;
use crate::llm::{LLMClient, OllamaClient};
use crate::reasoner::ingestion::{GovernanceIngestion, SummaryItem};
use crate::reasoner::intent::{Intent, IntentGuess, IntentRouter};
use crate::reasoner::materializer::{DraftArtifact, MarkdownMaterializer};
use crate::reasoner::prompts::PromptAssembler;
use crate::reasoner::validation::{ValidationLayer, ValidationReport};
use serde_json::Value;
use regex::Regex;

#[derive(Debug, Clone)]
pub struct ReasonerContextUsed {
    pub goals: Vec<SummaryItem>,
    pub decisions: Vec<SummaryItem>,
    pub audits: Vec<SummaryItem>,
    pub daily_notes: Vec<SummaryItem>,
    pub phase: Option<SummaryItem>,
}

#[derive(Debug, Clone)]
pub struct StructuredResult {
    pub intent: Intent,
    pub intent_guess: IntentGuess,
    pub context_used: ReasonerContextUsed,
    pub raw_model_output: String,
    pub parsed: Option<Value>,
    pub validation: ValidationReport,
    pub draft: Option<DraftArtifact>,
    pub next_actions: Vec<String>,
    pub required_inputs: Vec<String>,
}

pub struct ReasoningEngine {
    runtime: OllamaRuntimeController,
}

impl ReasoningEngine {
    pub fn new(runtime: OllamaRuntimeController) -> Self {
        Self { runtime }
    }

    pub async fn run(
        &self,
        query: &str,
        ctx: &GovernanceContext,
        override_intent: Option<Intent>,
    ) -> Result<StructuredResult> {
        let guess = if let Some(intent) = override_intent {
            IntentGuess {
                intent,
                confidence: 1.0,
                rationale: "User override".to_string(),
                used_rules: vec!["user_override".to_string()],
                required_inputs: Vec::new(),
            }
        } else {
            IntentRouter::classify(query, &self.runtime).await?
        };

        if guess.confidence < 0.4 {
            return Ok(StructuredResult {
                intent: guess.intent.clone(),
                intent_guess: guess.clone(),
                context_used: ReasonerContextUsed { goals: vec![], decisions: vec![], audits: vec![], daily_notes: vec![], phase: None },
                raw_model_output: "".to_string(),
                parsed: None,
                validation: ValidationReport {
                    valid: false,
                    errors: vec!["Low intent confidence; please clarify your request.".to_string()],
                    warnings: vec![],
                },
                draft: None,
                next_actions: vec!["clarify".to_string()],
                required_inputs: guess.required_inputs.clone(),
            });
        }

        // Ingest summaries
        let refs = self.extract_refs(query);
        let context_used = ReasonerContextUsed {
            phase: GovernanceIngestion::active_phase_summary(ctx),
            goals: if refs.goals.is_empty() {
                GovernanceIngestion::load_goals(ctx)?.into_iter().take(5).collect()
            } else {
                GovernanceIngestion::filter_goals_by_ids(ctx, &refs.goals)?
            },
            decisions: if refs.decisions.is_empty() {
                Vec::new()
            } else {
                GovernanceIngestion::filter_decisions_by_ids(ctx, &refs.decisions)?
            },
            audits: if refs.audits.is_empty() {
                Vec::new()
            } else {
                GovernanceIngestion::filter_audits_by_ids(ctx, &refs.audits)?
            },
            daily_notes: GovernanceIngestion::load_daily_notes(ctx, 3)?,
        };

        let context_str = self.render_context(&context_used);
        let messages = PromptAssembler::build_messages(&guess.intent, &context_str, query);

        let client = OllamaClient::with_base(
            Some(self.runtime.model_name().to_string()),
            Some(self.runtime.base_url().to_string()),
        );

        let raw_output = client.chat(messages).await?;

        // Parse JSON
        let parsed = serde_json::from_str::<Value>(&raw_output).ok();

        // Validate
        let validation = if let Some(json) = &parsed {
            ValidationLayer::validate(json, &guess.intent, ctx)
        } else {
            ValidationReport::error("Model output was not valid JSON; expected schema.")
        };

        // Draft
        let draft = if validation.errors.is_empty() {
            if let Some(json) = &parsed {
                Some(MarkdownMaterializer::to_draft(json, &ctx.root, ctx)?)
            } else {
                None
            }
        } else {
            None
        };

        // Next actions
        let mut next_actions = vec![
            "preview".to_string(),
            "edit_draft".to_string(),
            "safe_write".to_string(),
        ];
        if draft.is_some() {
            next_actions.push("commit".to_string());
        }

        let required_inputs = guess.required_inputs.clone();

        Ok(StructuredResult {
            intent: guess.intent.clone(),
            intent_guess: guess,
            context_used,
            raw_model_output: raw_output,
            parsed,
            validation,
            draft,
            next_actions,
            required_inputs,
        })
    }

    fn render_context(&self, ctx: &ReasonerContextUsed) -> String {
        let mut out = String::new();
        if let Some(phase) = &ctx.phase {
            out.push_str(&format!("## Active Phase\n{} [{}]\n", phase.id, phase.status.clone().unwrap_or_default()));
        }
        if !ctx.goals.is_empty() {
            out.push_str("## Goals (summary)\n");
            for g in &ctx.goals {
                out.push_str(&format!(
                    "- {} [{}] ({:?}) — {}\n",
                    g.id,
                    g.status.clone().unwrap_or_else(|| "unknown".to_string()),
                    g.phase,
                    g.summary
                ));
            }
        }
        if !ctx.decisions.is_empty() {
            out.push_str("\n## Decisions (summary)\n");
            for d in &ctx.decisions {
                out.push_str(&format!(
                    "- {} [{}] ({:?}) — {}\n",
                    d.id,
                    d.status.clone().unwrap_or_else(|| "unknown".to_string()),
                    d.phase,
                    d.summary
                ));
            }
        }
        if !ctx.audits.is_empty() {
            out.push_str("\n## Audits (summary)\n");
            for a in &ctx.audits {
                out.push_str(&format!(
                    "- {} [{}] — {}\n",
                    a.id,
                    a.status.clone().unwrap_or_else(|| "unknown".to_string()),
                    a.summary
                ));
            }
        }
        if !ctx.daily_notes.is_empty() {
            out.push_str("\n## Daily Notes\n");
            for d in &ctx.daily_notes {
                out.push_str(&format!(
                    "- {} [{}] — {}\n",
                    d.id,
                    d.status.clone().unwrap_or_else(|| "n/a".to_string()),
                    d.summary
                ));
            }
        }
        out
    }

    fn extract_refs(&self, query: &str) -> RefCapture {
        let goal_re = Regex::new(r"\bG-\d{2,}\b").unwrap();
        let dec_re = Regex::new(r"\bD-\d{2,}\b").unwrap();
        let aud_re = Regex::new(r"\bAUD-\d{8}-\d{2}\b").unwrap();

        let goals = goal_re
            .find_iter(query)
            .map(|m| m.as_str().to_string())
            .collect::<Vec<_>>();
        let decisions = dec_re
            .find_iter(query)
            .map(|m| m.as_str().to_string())
            .collect::<Vec<_>>();
        let audits = aud_re
            .find_iter(query)
            .map(|m| m.as_str().to_string())
            .collect::<Vec<_>>();

        RefCapture {
            goals,
            decisions,
            audits,
        }
    }
}

#[derive(Default)]
struct RefCapture {
    goals: Vec<String>,
    decisions: Vec<String>,
    audits: Vec<String>,
}
