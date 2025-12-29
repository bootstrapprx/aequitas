# Phase 4: LLM Integration - Design Specification

## Status: Planning

## Overview

Phase 4 adds AI-assisted governance capabilities to the Meta Engine while maintaining strict guardrails and human oversight. The system will provide contextual assistance for goal management, decision-making, and governance health, but will **never** autonomously modify files or make decisions.

## Core Principles

1. **Human in the Loop** - AI suggests, human decides and executes
2. **Transparency** - All prompts and responses logged to governance folder
3. **Context-Aware** - AI receives full governance context (goals, decisions, phases, canon)
4. **Read-Only AI** - LLM never writes files directly, only suggests changes
5. **Privacy-First** - Option for local LLM (Ollama) or API-based (Claude, OpenAI)
6. **Audit Trail** - Every AI interaction logged with timestamp and context

## Features

### 1. Governance Assistant Chat

**Location:** New "Assistant" tab in GUI

**Capabilities:**
- Answer questions about current governance state
- Explain goal dependencies and blockers
- Suggest status transitions based on context
- Identify gaps or inconsistencies
- Recommend next steps for current phase

**Examples:**
- "What goals are blocking the completion of Phase 3?"
- "Why is goal-fiscal-engine marked as partial?"
- "What should I work on next to progress Phase 7?"
- "Are there any orphaned goals with no dependencies?"

**UI:**
- Chat interface (similar to ChatGPT)
- Context panel showing what data was sent to AI
- Prompt/response history
- Copy/paste suggestions to apply manually

### 2. Smart Status Suggestions

**Location:** Goal Explorer (enhanced)

**Functionality:**
- When viewing a goal, AI suggests appropriate next status
- Based on: dependencies, current phase, timeline, blockers
- Shows reasoning for suggestion
- User can accept (updates status) or ignore

**Example:**
```
Goal: goal-fiscal-engine
Current Status: partial
Dependencies: All completed ✅
Blockers: None

AI Suggestion: Change status to "done"
Reasoning: All dependencies are met, no blockers reported,
and the goal deliverables appear complete based on the
goal description checklist.

[Accept] [Ignore] [Explain More]
```

### 3. Daily Note Prompts

**Location:** Dashboard (enhanced)

**Functionality:**
- When creating daily note, AI suggests:
  - Goals to focus on today based on priority/phase
  - Potential blockers to watch for
  - Related decisions that might need review
- Pre-fills daily note template with suggestions
- User edits before saving

**Example:**
```
Creating Daily Note for 2025-12-30

AI Suggestions:

Goals to work on:
- goal-onboarding-flow (active, Phase 7, high priority)
- goal-testing-baseline (blocked → active transition ready)

Potential blockers:
- goal-onboarding-flow depends on goal-authentication (done)
- No blockers detected for today's suggested goals

Related decisions:
- decision-004-dexter-observer (relevant to onboarding UX)

[Use Suggestions] [Edit Manually]
```

### 4. Context Assembly Engine

**Backend Service**

**Purpose:** Intelligently gather relevant context for AI prompts

**Capabilities:**
- Determine which governance files are relevant to a query
- Extract key facts (goal statuses, dependencies, dates)
- Build canonical context (include relevant Canon documents)
- Respect token limits (prioritize most relevant data)
- Cache frequently accessed contexts

**Example Context for "What should I work on next?"**
```yaml
Current Phase: P7
Active Goals: 3
Blocked Goals: 1
Recent Daily Notes: Last 3 days
Relevant Decisions: 2
Canon Documents: Phase transition rules
```

### 5. Prompt Logging & Audit Trail

**Location:** `/governance/06_PROMPTS/logs/`

**Format:**
```markdown
---
timestamp: 2025-12-30T15:30:00Z
user_query: "What should I work on next?"
model: claude-3-5-sonnet-20241022
tokens_in: 2450
tokens_out: 380
duration_ms: 1850
---

# AI Interaction Log

## User Query
What should I work on next?

## Context Provided
- Current Phase: P7
- Active Goals: goal-onboarding-flow, goal-sandbox-ui, goal-testing-baseline
- Blocked Goals: goal-integrations-foundation
- Recent Activity: Last daily note 2025-12-29

## AI Response
Based on your current phase (P7) and active goals, I recommend...

## Actions Taken
- Viewed suggestion
- No status changes made
```

**Benefits:**
- Full audit trail of AI interactions
- Can replay/review past suggestions
- Identify patterns in AI assistance usage
- Debug issues with context assembly

### 6. Goal Dependency Analyzer

**Location:** Goal Explorer (new feature)

**Functionality:**
- Visualize goal dependency graph
- AI suggests optimal work order
- Identifies circular dependencies
- Highlights critical path to phase completion

**Example:**
```
Goal Dependency Chain:

goal-authentication (done)
  ↓
goal-multi-tenancy (active) ← YOU ARE HERE
  ↓
goal-onboarding-flow (planned)
  ↓
goal-sandbox-ui (planned)

AI Recommendation: Complete goal-multi-tenancy first.
It's blocking 2 downstream goals and is 80% complete
based on checklist analysis.

Critical Path: 3 goals remaining to complete Phase 7
Estimated Completion: Based on recent velocity, 2-3 weeks
```

### 7. Decision Support

**Location:** New "Decisions" tab

**Functionality:**
- List all decisions with AI-generated summaries
- Suggest when decisions need review/update
- Identify superseded or conflicting decisions
- Recommend new decisions based on patterns

**Example:**
```
Decision: decision-001-stack-choices
Status: implemented
Date: 2024-06-15
Last Review: 6 months ago

AI Analysis:
This decision is stable and still valid. The stack
(Python/FastAPI + React) continues to serve the project well.
No changes recommended.

---

Decision: decision-003-accounting-orm
Status: active
Date: 2024-08-20

AI Analysis:
⚠️ This decision should be reviewed. There are 3 new
accounting modules that were built after this decision,
and they may have introduced variations that should be
documented.

[Review Decision] [Mark Reviewed] [Ignore]
```

## Technical Architecture

### Backend Components

**1. LLM Client Abstraction**
```rust
// meta-core/src/llm/mod.rs
pub trait LLMClient {
    async fn complete(&self, prompt: &str) -> Result<String>;
    async fn chat(&self, messages: Vec<Message>) -> Result<String>;
    fn model_name(&self) -> &str;
}

pub struct ClaudeClient { /* ... */ }
pub struct OpenAIClient { /* ... */ }
pub struct OllamaClient { /* ... */ }
```

**2. Context Builder**
```rust
// meta-core/src/llm/context.rs
pub struct ContextBuilder {
    governance: GovernanceContext,
    max_tokens: usize,
}

impl ContextBuilder {
    pub fn for_query(&self, query: &str) -> String {
        // Intelligently select relevant governance data
        // Format as structured context for LLM
    }

    pub fn for_goal(&self, goal_id: &str) -> String {
        // Goal + dependencies + blockers + related decisions
    }
}
```

**3. Prompt Logger**
```rust
// meta-core/src/llm/logger.rs
pub struct PromptLogger {
    log_dir: PathBuf,
}

impl PromptLogger {
    pub fn log_interaction(
        &self,
        query: &str,
        context: &str,
        response: &str,
        metadata: Metadata,
    ) -> Result<PathBuf> {
        // Write to /governance/06_PROMPTS/logs/YYYY-MM-DD-HHmmss.md
    }
}
```

**4. AI Service**
```rust
// meta-core/src/llm/service.rs
pub struct AIService {
    client: Box<dyn LLMClient>,
    context_builder: ContextBuilder,
    logger: PromptLogger,
}

impl AIService {
    pub async fn ask(&self, query: &str) -> Result<AIResponse> {
        let context = self.context_builder.for_query(query);
        let prompt = format!("Context:\n{}\n\nQuery: {}", context, query);
        let response = self.client.complete(&prompt).await?;
        self.logger.log_interaction(query, &context, &response, metadata)?;
        Ok(AIResponse { text: response, context })
    }

    pub async fn suggest_status(
        &self,
        goal_id: &str,
    ) -> Result<StatusSuggestion> {
        // Analyze goal and suggest next status
    }

    pub async fn suggest_daily_focus(&self) -> Result<Vec<String>> {
        // Suggest goals to work on today
    }
}
```

### Frontend Components

**1. Assistant Chat**
```svelte
<!-- meta-gui/src/lib/Assistant.svelte -->
<script>
  let messages = []
  let currentMessage = ''
  let loading = false

  async function sendMessage() {
    loading = true
    const response = await invoke('ai_ask', { query: currentMessage })
    messages = [...messages,
      { role: 'user', text: currentMessage },
      { role: 'assistant', text: response.text, context: response.context }
    ]
    loading = false
    currentMessage = ''
  }
</script>

<div class="chat-container">
  {#each messages as msg}
    <ChatMessage message={msg} />
  {/each}

  {#if loading}
    <LoadingIndicator />
  {/if}

  <ChatInput bind:value={currentMessage} on:send={sendMessage} />
</div>
```

**2. Smart Status Suggestion**
```svelte
<!-- In GoalExplorer.svelte -->
<script>
  async function getStatusSuggestion(goalId) {
    const suggestion = await invoke('ai_suggest_status', { goalId })
    return suggestion
  }
</script>

{#if aiSuggestion}
  <div class="ai-suggestion">
    <span class="badge badge-ai">AI Suggestion</span>
    <p>Change status to <strong>{aiSuggestion.targetStatus}</strong></p>
    <p class="text-sm text-gray-600">{aiSuggestion.reasoning}</p>
    <div class="flex gap-2">
      <button on:click={() => acceptSuggestion(aiSuggestion)}>Accept</button>
      <button on:click={() => aiSuggestion = null}>Ignore</button>
    </div>
  </div>
{/if}
```

### Configuration

**File:** `meta-gui/src-tauri/config/llm.toml`
```toml
[llm]
provider = "claude"  # claude, openai, ollama
model = "claude-3-5-sonnet-20241022"

[llm.claude]
api_key_env = "ANTHROPIC_API_KEY"
max_tokens = 4096

[llm.openai]
api_key_env = "OPENAI_API_KEY"
model = "gpt-4"

[llm.ollama]
base_url = "http://localhost:11434"
model = "llama3.1:8b"

[context]
max_goals = 20
max_decisions = 10
include_recent_daily_notes = 3
include_canon = true
```

## Guardrails & Safety

### 1. Read-Only AI
- AI **never** writes files directly
- All suggestions require explicit user approval
- User clicks "Accept" to apply suggested changes

### 2. Context Limits
- Maximum 50k tokens per query
- Automatically prune less relevant context
- Warn user if query is too broad

### 3. Prompt Injection Protection
- Sanitize user queries
- System prompts are hardcoded
- Never allow user to override system context

### 4. Privacy Controls
- Option to use local LLM (Ollama) for sensitive data
- API key stored in environment variable (not in files)
- Option to disable logging (for privacy)

### 5. Rate Limiting
- Max 10 AI queries per minute
- Prevent accidental API cost spikes
- Cache common queries

## System Prompts

### Base System Prompt
```
You are an AI assistant for the Aequitas governance system.
You help architects manage goals, decisions, and phases.

Your responses should:
- Be concise and actionable
- Reference specific goal IDs and decision IDs
- Explain your reasoning clearly
- Never suggest modifying Canon documents
- Respect phase boundaries and dependencies

Current governance context:
{CONTEXT}

Remember: You suggest, the human decides. Never be prescriptive.
```

### Status Suggestion Prompt
```
Analyze this goal and suggest the most appropriate next status.

Goal: {GOAL_ID}
Current Status: {CURRENT_STATUS}
Dependencies: {DEPENDENCIES}
Blockers: {BLOCKERS}
Phase: {PHASE}

Available status transitions:
{ALLOWED_TRANSITIONS}

Provide:
1. Recommended next status
2. Brief reasoning (2-3 sentences)
3. Any warnings or considerations
```

## Implementation Phases

### Phase 4A: Foundation (Week 1-2)
- [ ] LLM client abstraction (Claude, OpenAI, Ollama)
- [ ] Context builder (governance data → prompt context)
- [ ] Prompt logger (write logs to /06_PROMPTS/)
- [ ] Basic Tauri command: `ai_ask(query) -> response`
- [ ] Assistant tab in GUI (basic chat interface)

### Phase 4B: Smart Suggestions (Week 3-4)
- [ ] Status suggestion algorithm
- [ ] Daily focus suggestions
- [ ] Goal dependency analyzer
- [ ] Integration in existing tabs (Goal Explorer, Dashboard)

### Phase 4C: Advanced Features (Week 5-6)
- [ ] Decision analyzer
- [ ] Dependency graph visualization
- [ ] Conversation memory (multi-turn chat)
- [ ] Prompt templates for common queries

### Phase 4D: Polish & Optimization (Week 7)
- [ ] Response caching
- [ ] Rate limiting
- [ ] Error handling & retries
- [ ] Documentation
- [ ] User testing

## Success Criteria

- [ ] Can ask natural language questions about governance state
- [ ] Status suggestions are >80% accurate (based on user acceptance)
- [ ] All AI interactions logged with full context
- [ ] Works with local LLM (Ollama) for privacy
- [ ] <2 second response time for simple queries
- [ ] Zero direct file modifications by AI
- [ ] Clear reasoning for all suggestions

## Risks & Mitigations

**Risk:** AI suggests invalid status transitions
**Mitigation:** Server-side validation (same as manual updates)

**Risk:** API costs spiral out of control
**Mitigation:** Rate limiting, caching, token budgets

**Risk:** Sensitive data sent to external API
**Mitigation:** Local LLM option (Ollama), privacy warnings

**Risk:** AI hallucinates non-existent goals
**Mitigation:** Always validate goal IDs against actual files

**Risk:** User over-relies on AI suggestions
**Mitigation:** Clear UI that AI is advisory only, not authoritative

## Future Enhancements (Phase 5+)

- Natural language goal creation ("Create a goal for user authentication")
- Auto-generate decision summaries
- Predict phase completion dates based on velocity
- Identify potential governance debt
- Suggest refactoring opportunities
- Multi-agent collaboration (different AI agents for different domains)

## Conclusion

Phase 4 transforms the Meta Engine from a governance viewer/editor into an intelligent assistant that helps architects navigate complex project states. By maintaining strict guardrails (read-only AI, human approval, full logging), we get the benefits of AI assistance without the risks of autonomous modification.

The system respects the fundamental principle: **AI suggests, humans decide and execute.**
