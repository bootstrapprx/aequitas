use crate::llm::Message;
use crate::reasoner::intent::Intent;

#[derive(Debug, Clone)]
pub struct PromptContract {
    pub intent: Intent,
    pub system_preamble: String,
    pub user_instruction: String,
    pub schema: String,
}

pub struct PromptAssembler;

impl PromptAssembler {
    pub fn contract(intent: &Intent) -> PromptContract {
        match intent {
            Intent::DraftGoal => PromptContract {
                intent: intent.clone(),
                system_preamble: base_preamble(),
                user_instruction: "Draft a governance-compliant goal. Respond ONLY in JSON.".to_string(),
                schema: r#"{
  "intent": "draft_goal",
  "id": "G-###",
  "title": "string",
  "phase": "P#",
  "status": "planned|active|blocked|partial|done",
  "depends_on": ["G-###"],
  "canon_refs": [],
  "rationale": "string",
  "body": "markdown"
}"#.to_string(),
            },
            Intent::UpdateGoal => PromptContract {
                intent: intent.clone(),
                system_preamble: base_preamble(),
                user_instruction: "Update an existing goal. Do not invent IDs. Respond ONLY in JSON.".to_string(),
                schema: r#"{
  "intent": "update_goal",
  "id": "G-###",
  "status": "planned|active|blocked|partial|done|archived",
  "phase": "P#",
  "depends_on": ["G-###"],
  "canon_refs": [],
  "rationale": "string",
  "body": "markdown"
}"#.to_string(),
            },
            Intent::DraftAudit => PromptContract {
                intent: intent.clone(),
                system_preamble: base_preamble(),
                user_instruction: "Draft an audit record referencing existing goals/decisions only. Respond ONLY in JSON.".to_string(),
                schema: r#"{
  "intent": "draft_audit",
  "id": "AUD-YYYYMMDD-##",
  "target": ["G-###"|"D-###"],
  "severity": "info|warn|fail",
  "findings": ["string"],
  "canon_refs": [],
  "remediation": "string",
  "body": "markdown"
}"#.to_string(),
            },
            Intent::DraftDecision => PromptContract {
                intent: intent.clone(),
                system_preamble: base_preamble(),
                user_instruction: "Draft a decision (ADR) with strict references. Respond ONLY in JSON.".to_string(),
                schema: r#"{
  "intent": "draft_decision",
  "id": "D-###",
  "title": "string",
  "status": "draft|proposed|implemented|active|superseded|abandoned",
  "phase": "P#",
  "canon_refs": [],
  "impacts": ["G-###"],
  "rationale": "string",
  "body": "markdown"
}"#.to_string(),
            },
            Intent::SummarizeState => PromptContract {
                intent: intent.clone(),
                system_preamble: base_preamble(),
                user_instruction: "Provide a concise governance summary. Respond ONLY in JSON.".to_string(),
                schema: r#"{
  "intent": "summarize_state",
  "insights": ["string"],
  "risks": ["string"],
  "blocked_goals": ["G-###"],
  "open_decisions": ["D-###"]
}"#.to_string(),
            },
            Intent::AnalyzeBlockers => PromptContract {
                intent: intent.clone(),
                system_preamble: base_preamble(),
                user_instruction: "Analyze blockers and propose mitigations. Respond ONLY in JSON.".to_string(),
                schema: r#"{
  "intent": "analyze_blockers",
  "blocked_goals": ["G-###"],
  "causes": ["string"],
  "actions": ["string"]
}"#.to_string(),
            },
            Intent::ExplainPhase => PromptContract {
                intent: intent.clone(),
                system_preamble: base_preamble(),
                user_instruction: "Explain current phase, constraints, and next moves. Respond ONLY in JSON.".to_string(),
                schema: r#"{
  "intent": "explain_phase",
  "phase": "P#",
  "summary": "string",
  "risks": ["string"],
  "next_steps": ["string"]
}"#.to_string(),
            },
        }
    }

    pub fn build_messages(intent: &Intent, context: &str, user_input: &str) -> Vec<Message> {
        let contract = Self::contract(intent);
        let mut messages = Vec::new();

        let system = format!(
            "{preamble}\nSTRICT OUTPUT: JSON only matching this schema:\n{schema}\nIf you cannot comply, reply exactly with INVALID_OUTPUT.",
            preamble = contract.system_preamble,
            schema = contract.schema
        );
        messages.push(Message {
            role: "system".to_string(),
            content: system,
        });

        let user = format!(
            "Intent: {intent:?}\nInstruction: {instruction}\n\nContext:\n{ctx}\n\nUser request:\n{req}",
            intent = intent,
            instruction = contract.user_instruction,
            ctx = context,
            req = user_input
        );
        messages.push(Message {
            role: "user".to_string(),
            content: user,
        });

        messages
    }
}

fn base_preamble() -> String {
    r#"You are Metatheos reasoning layer. You DO NOT write files. You must respect governance IDs, phases, and canon references. Do not invent IDs or file paths. Never mention paths. Output JSON only. If unsure, reply INVALID_OUTPUT."#.to_string()
}
