# Ollama Reasoning Subsystem — Private-GPT Pattern

## Architecture Diagram
`User NL → IntentRouter → GovernanceIngestion (summaries only) → PromptAssembler (contract-per-intent) → OllamaRuntime (reasoning only) → StructuredOutput Parser → ValidationLayer (IDs, schema, canon) → MarkdownMaterializer (draft) → Preview UI → SafeWrite → Git Commit`

## Components & Responsibilities
- **OllamaRuntimeController** (metatheos-core/src/llm/runtime.rs): single-instance guard on 127.0.0.1:11435, default model `qwen2.5:7b-instruct`, fail-fast if missing, exposes `ollama_health()` + `ollama_models()`.
- **GovernanceIngestion** (metatheos-core/src/reasoner/ingestion.rs): typed loaders `load_goals|phases|decisions|audits|daily_notes(limit)` returning minimal structs `{id,status,phase,path,summary}`; no full text to avoid prompt bloat.
- **IntentRouter** (metatheos-core/src/reasoner/intent.rs): rule-first, Ollama-second classifier producing intents `CreateGoal|UpdateGoal|CreateDecision|CreateAudit|WriteDailyNote|AnalyzeGovernance|AskQuestion`; carries rationale + confidence.
- **PromptContracts** (metatheos-core/src/reasoner/prompts.rs): contract registry per intent, builds system/user prompts with strict schemas and “INVALID_OUTPUT” escape hatch.
- **ReasoningEngine** (metatheos-core/src/reasoner/engine.rs): orchestrates pipeline, enforces “Ollama writes nothing”, emits `StructuredResult` for validation/materialization only.
- **ValidationLayer** (metatheos-core/src/reasoner/validation.rs): ID format/uniqueness checks, reference existence, canon reference whitelist, schema compliance; blocks before UI.
- **MarkdownMaterializer** (metatheos-core/src/reasoner/materializer.rs): maps validated structured output to draft markdown (frontmatter + body) and target paths; no filesystem writes—hands off to Safe Write (existing Phase 2 flow).
- **UI Adapter** (metatheos-gui): Assistant tab updates to surface intent, context counts, structured output preview, and Safe Write/commit buttons labeled “Local Model (Ollama) — Reasoning Only”.

## Rust Module Skeletons
```rust
// metatheos-core/src/llm/runtime.rs
use serde::Deserialize;
use url::Url;
use crate::errors::Result;

#[derive(Debug, Clone)]
pub struct OllamaRuntimeController {
    base_url: Url,
    default_model: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ModelInfo { pub name: String, pub size: Option<u64> }

#[derive(Debug, Clone)]
pub struct OllamaStatus {
    pub reachable: bool,
    pub default_model_ready: bool,
    pub models: Vec<ModelInfo>,
    pub message: String,
}

impl OllamaRuntimeController {
    pub fn new(model: Option<String>, base_url: Option<String>) -> Result<Self> { /* set defaults, parse URL */ todo!() }
    pub async fn ollama_health(&self) -> Result<OllamaStatus> { /* GET /api/tags, check default model present */ todo!() }
    pub async fn ollama_models(&self) -> Result<Vec<ModelInfo>> { /* reuse tags list */ todo!() }
    pub fn model_name(&self) -> &str { &self.default_model }
}
```
```rust
// metatheos-core/src/reasoner/ingestion.rs
use crate::errors::Result;
use crate::governance::GovernanceContext;
use chrono::NaiveDate;
use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct SummaryItem {
    pub id: String,
    pub status: Option<String>,
    pub phase: Option<String>,
    pub path: PathBuf,
    pub summary: String,       // 1–2 sentences max
    pub updated: Option<NaiveDate>,
}

pub struct GovernanceIngestion;
impl GovernanceIngestion {
    pub fn load_goals(ctx: &GovernanceContext) -> Result<Vec<SummaryItem>> { todo!() }
    pub fn load_phases(ctx: &GovernanceContext) -> Result<Vec<SummaryItem>> { todo!() }
    pub fn load_decisions(ctx: &GovernanceContext) -> Result<Vec<SummaryItem>> { todo!() }
    pub fn load_audits(ctx: &GovernanceContext) -> Result<Vec<SummaryItem>> { todo!() }
    pub fn load_daily_notes(ctx: &GovernanceContext, limit: usize) -> Result<Vec<SummaryItem>> { todo!() }
}
```
```rust
// metatheos-core/src/reasoner/intent.rs
#[derive(Debug, Clone)]
pub enum Intent {
    CreateGoal,
    UpdateGoal,
    CreateDecision,
    CreateAudit,
    WriteDailyNote,
    AnalyzeGovernance,
    AskQuestion,
}

#[derive(Debug, Clone)]
pub struct IntentGuess {
    pub intent: Intent,
    pub confidence: f32,
    pub rationale: String,
    pub used_rules: Vec<String>,
}

pub struct IntentRouter;
impl IntentRouter {
    pub fn classify_rule_based(query: &str) -> Option<IntentGuess> { todo!() }
    pub async fn classify_with_ollama(query: &str, runtime: &crate::llm::runtime::OllamaRuntimeController) -> Result<IntentGuess> { todo!() }
    pub async fn classify(query: &str, runtime: &crate::llm::runtime::OllamaRuntimeController) -> Result<IntentGuess> {
        if let Some(rule) = Self::classify_rule_based(query) { return Ok(rule); }
        Self::classify_with_ollama(query, runtime).await
    }
}
```
```rust
// metatheos-core/src/reasoner/prompts.rs
use crate::reasoner::intent::Intent;

#[derive(Debug, Clone)]
pub struct PromptContract {
    pub intent: Intent,
    pub system_preamble: String,
    pub user_instruction: String,
    pub schema: String, // YAML/JSON schema text echoed to model
}

pub struct PromptAssembler;
impl PromptAssembler {
    pub fn contract(intent: &Intent) -> PromptContract { todo!() }
    pub fn build_messages(intent: &Intent, context: &str, user_input: &str) -> Vec<crate::llm::Message> { todo!() }
}
```
```rust
// metatheos-core/src/reasoner/validation.rs
use crate::errors::Result;
use serde_json::Value;

#[derive(Debug, Clone)]
pub struct ValidationReport {
    pub valid: bool,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}

pub struct ValidationLayer;
impl ValidationLayer {
    pub fn validate_ids(doc: &Value, ctx: &crate::governance::GovernanceContext) -> ValidationReport { todo!() }
    pub fn validate_schema(doc: &Value, expected_intent: &crate::reasoner::intent::Intent) -> ValidationReport { todo!() }
    pub fn enforce_canon_refs(doc: &Value, allowed: &[String]) -> ValidationReport { todo!() }
    pub fn merge(reports: Vec<ValidationReport>) -> ValidationReport { todo!() }
}
```
```rust
// metatheos-core/src/reasoner/materializer.rs
use std::path::PathBuf;
use serde_json::Value;
use crate::errors::Result;

#[derive(Debug, Clone)]
pub struct DraftArtifact {
    pub intent: crate::reasoner::intent::Intent,
    pub target_path: PathBuf,
    pub frontmatter: String,
    pub body: String,
}

pub struct MarkdownMaterializer;
impl MarkdownMaterializer {
    pub fn to_draft(doc: &Value, governance_root: &PathBuf) -> Result<DraftArtifact> {
        // derive folder/filename from validated IDs; do not write to disk
        todo!()
    }
}
```
```rust
// metatheos-core/src/reasoner/engine.rs
use crate::{governance::GovernanceContext, llm::runtime::OllamaRuntimeController};
use crate::errors::Result;
use serde_json::Value;

pub struct StructuredResult {
    pub intent: crate::reasoner::intent::Intent,
    pub raw: String,
    pub parsed: Value,
    pub validation: crate::reasoner::validation::ValidationReport,
    pub draft: Option<crate::reasoner::materializer::DraftArtifact>,
}

pub struct ReasoningEngine {
    runtime: OllamaRuntimeController,
}

impl ReasoningEngine {
    pub fn new(runtime: OllamaRuntimeController) -> Self { Self { runtime } }
    pub async fn run(&self, query: &str, ctx: &GovernanceContext) -> Result<StructuredResult> {
        // 1) classify intent, 2) ingest summaries, 3) assemble prompt, 4) call Ollama chat,
        // 5) parse JSON/YAML, 6) validate, 7) materialize draft (no write)
        todo!()
    }
}
```

## Prompt Contracts (YAML, model sees schema + INVALID_OUTPUT guard)
```yaml
intent: CreateGoal
required_output:
  id: "G-###"
  title: string
  phase: "P#"
  status: planned|active|blocked|partial|done
  depends_on: ["G-###"]
  canon_refs: []
  rationale: string
  body: markdown
if_invalid: "INVALID_OUTPUT"
```
```yaml
intent: UpdateGoal
required_output:
  id: existing "G-###"
  status: planned|active|blocked|partial|done|archived
  phase: "P#" | same
  changes: [summary_of_change]
  depends_on: ["G-###"]
  canon_refs: []
  body_patch: markdown delta (no file paths)
if_invalid: "INVALID_OUTPUT"
```
```yaml
intent: CreateDecision
required_output:
  id: "D-###"
  title: string
  status: draft|proposed|implemented|active|superseded|abandoned
  phase: "P#"
  canon_refs: []
  rationale: string
  impacts: ["G-###"]
  body: markdown
if_invalid: "INVALID_OUTPUT"
```
```yaml
intent: CreateAudit
required_output:
  id: "AUD-YYYYMMDD-##"
  target: ["G-###"|"D-###"]
  severity: info|warn|fail
  findings: [string]
  canon_refs: []
  remediation: string
if_invalid: "INVALID_OUTPUT"
```
```yaml
intent: WriteDailyNote
required_output:
  date: YYYY-MM-DD
  mode: focus|retro|sync
  goals_worked: ["G-###"]
  blockers: [string]
  decisions_made: ["D-###"]
  summary: string
  body: markdown
if_invalid: "INVALID_OUTPUT"
```
```yaml
intent: AnalyzeGovernance
required_output:
  insights: [string]
  risks: [string]
  blocked_goals: ["G-###"]
  decision_gaps: ["G-###"]
  canon_refs: []
if_invalid: "INVALID_OUTPUT"
```
```yaml
intent: AskQuestion
required_output:
  answer: string
  references: ["G-###"|"D-###"|"AUD-*"]
if_invalid: "INVALID_OUTPUT"
```

## Validation Rules
- **ID format**: Goal `G-###` only; Decision `D-###`; Audit `AUD-YYYYMMDD-##`; Phase `P#`; Daily `YYYY-MM-DD`. Reject anything else before draft creation.
- **Uniqueness**: Check against `GovernanceContext` indexes; new IDs must not exist; updates must exist.
- **Reference existence**: `depends_on`, `impacts`, `goals_worked`, `decisions_made` must resolve in context; otherwise reject as hallucination.
- **Canon references**: Only allow references present in `ctx.canon_docs`; reject free-text canon names.
- **Schema compliance**: Output must parse as JSON/YAML, include all required keys, no extra file paths, no absolute paths, no executable content; enforce `INVALID_OUTPUT` fallback.
- **Governance layout**: Materializer validates target folder names and file extensions; never let Ollama propose paths/filenames.

## Minimal UI Changes (Assistant Tab)
- Switch default mode to “Local Model (Ollama) — Reasoning Only”; remove web iframe from primary path.
- Display detected intent, model health (11435 + model), context counts (goals/decisions/audits/dailies loaded), and structured output JSON.
- Buttons: `Preview as Governance` (renders markdown draft in-panel), `Edit Draft` (opens textarea/local modal), `Commit via Safe Write` (calls existing `safe_write_file` + git commit action).
- Show explicit banner: “Ollama reasons; Metatheos validates and writes. No direct file writes by model.”
- Expose error states: missing model, validation failures, ID collisions, unknown references.

## Phase 5 (Embeddings/Later) TODOs
- Plug optional embedding store (no-DB first; file-based index) behind feature flag.
- Add retrieval hooks to `GovernanceIngestion` for curated context slices (no chat history).
- Introduce evaluation harness for schema adherence + hallucination rate.
- Expand Safe Write flow with diff preview + signature of validated schema used.
