# Phase 4B: AI Assistant - User Guide

## What You'll See

### Assistant Tab (🤖)

When you click the Assistant tab, you'll see one of two modes:

#### Mode 1: AI Chat (With API Key)

```
┌─────────────────────────────────────────────────────┐
│ AI Assistant                    [AI Chat|Webview]   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  💡 Try asking:                                     │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ "What should I work on next?"                 │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ "Summarize my 5 active goals"                 │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ "Why do I have 2 blocked goals?"              │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ "What's the status of Phase P7?"              │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Ask me anything about your governance...            │
│ ┌─────────────────────────────────────────────────┐│
│ │                                                 ││
│ │ Type your question here...                      ││
│ │                                                 ││
│ └─────────────────────────────────────────────────┘│
│                                         [Send] [X]  │
└─────────────────────────────────────────────────────┘
```

**When you click an example or type a question:**

```
┌─────────────────────────────────────────────────────┐
│ AI Assistant                    [AI Chat|Webview]   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────┐ You  │
│  │ What should I work on next?              │      │
│  └──────────────────────────────────────────┘      │
│                                                     │
│ AI  ┌────────────────────────────────────────────┐ │
│     │ Based on your current Phase P7 and active │ │
│     │ goals, I recommend focusing on:           │ │
│     │                                           │ │
│     │ 1. goal-onboarding-flow (active)         │ │
│     │    - All dependencies met                │ │
│     │    - Critical for Phase 7 completion     │ │
│     │                                           │ │
│     │ 2. goal-dashboard-metrics (active)       │ │
│     │    - Blocked by 1 dependency             │ │
│     │    - Can start partial work              │ │
│     │                                           │ │
│     │ Would you like more details on either?   │ │
│     │                                           │ │
│     │ [claude-3-5-sonnet] [Context: P7, 5 goals]│
│     └────────────────────────────────────────────┘ │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Ask me anything about your governance...            │
│ ┌─────────────────────────────────────────────────┐│
│ │                                                 ││
│ └─────────────────────────────────────────────────┘│
│                               [Clear Chat] [Send]  │
└─────────────────────────────────────────────────────┘
```

#### Mode 2: Web Chatbot (Fallback)

```
┌─────────────────────────────────────────────────────┐
│ AI Assistant                    [AI Chat|Webview]   │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌───────────────────────────────────────────────┐  │
│ │                                               │  │
│ │     [Claude.ai Web Interface Loaded Here]    │  │
│ │                                               │  │
│ │     Full chat interface with Claude          │  │
│ │                                               │  │
│ │     Note: No governance context available    │  │
│ │     You'll need to provide context manually  │  │
│ │                                               │  │
│ └───────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Option 1: Test Immediately (No Setup)

```bash
# App is already running!
# Go to: http://localhost:5174
# Click: Assistant tab (🤖)
# Click: "Web Chatbot" button
```

You'll have full Claude web interface, but without governance context.

### Option 2: Full AI Integration (5 Minutes)

1. **Get API Key**
   - Visit: https://console.anthropic.com/
   - Sign up/Login → API Keys → Create Key
   - Copy your key (starts with `sk-ant-`)

2. **Set Environment Variable**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```

3. **Restart Meta Engine**
   ```bash
   cd /home/actpm/Documents/workfolder/aequitas/meta-engine/meta-gui
   cargo tauri dev
   ```

4. **Test**
   - Go to: http://localhost:5174
   - Click: Assistant tab (🤖)
   - AI Chat should be active
   - Click an example prompt
   - Watch AI respond with governance context!

## What the AI Knows

When you ask a question in **AI Chat mode**, the AI receives:

```markdown
## Current Phase
P7

## Active Goals
- goal-onboarding-flow (active): User onboarding flow implementation
- goal-dashboard-metrics (active): Dashboard metrics and analytics
- goal-api-integration (active): Backend API integration
- goal-auth-system (blocked): Authentication system (blocked by 1 dep)
- goal-data-validation (blocked): Data validation layer (blocked by 2 deps)

## Completed Goals
- goal-initial-setup (done): Initial project setup
- goal-core-models (done): Core domain models
...

## Dependencies
- goal-onboarding-flow depends on: [goal-core-models, goal-initial-setup]
- goal-auth-system depends on: [goal-onboarding-flow]
...

## Statistics
- Total Goals: 15
- Active: 5
- Blocked: 2
- Done: 8
```

**The AI uses this context to give you relevant, actionable advice!**

## Example Conversations

### Example 1: Getting Recommendations

**You:** "What should I work on next?"

**AI:**
> Based on your current Phase P7 status, I recommend focusing on **goal-onboarding-flow**. All its dependencies are complete, and it's critical for Phase 7 completion. Once you finish this, you'll unblock goal-auth-system which depends on it.

### Example 2: Understanding Blockers

**You:** "Why do I have 2 blocked goals?"

**AI:**
> You have 2 blocked goals due to pending dependencies:
>
> 1. **goal-auth-system** - Blocked by goal-onboarding-flow (active)
> 2. **goal-data-validation** - Blocked by goal-api-integration and goal-auth-system
>
> Completing goal-onboarding-flow will unblock goal-auth-system, which will then help unblock goal-data-validation.

### Example 3: Phase Status

**You:** "What's the status of Phase P7?"

**AI:**
> Phase P7 is currently active with:
> - 5 active goals in progress
> - 2 goals blocked by dependencies
> - 8 goals already completed
>
> You're 53% through Phase P7 goals (8/15 complete). Focus on active goals with no blockers for fastest progress.

## Where Logs Are Stored

Every AI interaction is logged to:

```
/home/actpm/Documents/workfolder/aequitas/governance/06_PROMPTS/logs/
```

**Example log file:** `2025-12-29-160530.md`

```markdown
---
timestamp: 2025-12-29T16:05:30Z
user_query: "What should I work on next?"
model: claude-3-5-sonnet-20241022
duration_ms: 1850
---

# AI Interaction Log

## User Query
What should I work on next?

## Context Provided
## Current Phase
P7

## Active Goals
- goal-onboarding-flow (active): User onboarding flow implementation
...

## AI Response
Based on your current Phase P7 status, I recommend...

## Actions Taken
- Viewed response
- No automated actions taken
```

**This gives you complete transparency about what the AI knows and how it responds.**

## Features

### ✅ Implemented in Phase 4B

- [x] AI Chat mode with Claude API
- [x] Web Chatbot fallback mode
- [x] Context-aware responses
- [x] Dynamic example prompts
- [x] Chat history during session
- [x] Full audit logging
- [x] Auto API key detection
- [x] Error handling
- [x] Toast notifications
- [x] Mode switching

### ⏳ Coming in Phase 4C

- [ ] Conversation memory (multi-turn chat)
- [ ] Status suggestion badges on goals
- [ ] Daily focus assistant
- [ ] Dependency analyzer
- [ ] Local LLM (Ollama) integration
- [ ] Cost tracking
- [ ] Response streaming

## Costs

| Mode | Cost | Privacy | Context |
|------|------|---------|---------|
| **AI Chat** | ~$0.01-$0.05 per query | Data sent to Anthropic | Full governance context |
| **Web Chatbot** | Free (uses your claude.ai account) | Same as claude.ai | Manual context only |
| **Ollama** (Phase 4C) | Free (electricity only) | 100% local | Full governance context |

## Privacy

### What's Sent to Anthropic (AI Chat Mode)

✅ **Sent:**
- Current phase ID
- Goal IDs, titles, and statuses
- Goal dependencies
- Statistics (goal counts)
- Your question

❌ **NOT Sent:**
- API key (stored locally only)
- File contents beyond governance structure
- Personal data
- Implementation code
- Sensitive project details

### What's Logged Locally

**Everything.** All interactions are logged to `/governance/06_PROMPTS/logs/` so you can audit exactly what was sent and received.

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| "No API Key Configured" | ANTHROPIC_API_KEY not set | `export ANTHROPIC_API_KEY="sk-ant-..."` and restart |
| API key set but still shows error | App not restarted | Run `cargo tauri dev` again |
| Network error | No internet or API down | Check connection, try Web Chatbot mode |
| Web Chatbot doesn't load | Firewall or no internet | Check connection |
| Slow responses | Large context or API latency | Normal, wait ~2-5 seconds |

## App Controls

### Navigation

- **Dashboard** 📊 - Phase and goal overview
- **Daily** 📅 - Daily notes editor
- **Goals** 🎯 - Goal management
- **Assistant** 🤖 - AI Assistant (YOU ARE HERE)
- **Audit** ✓ - Audit trail

### Assistant Controls

- **Mode Switcher** - Toggle between AI Chat and Web Chatbot
- **Example Prompts** - Click to use suggested questions
- **Send Button** - Submit your question
- **Clear Chat** - Start fresh conversation
- **Input Field** - Type your question (Enter to send, Shift+Enter for new line)

## Current Status

✅ **App Running:** http://localhost:5174
✅ **Phase 4B:** Complete
✅ **Backend:** All commands registered
✅ **Frontend:** Assistant tab functional
✅ **Tests:** Ready to execute

## Next Steps

1. **Test Web Chatbot** (no setup required)
   - Click Assistant tab → Web Chatbot button

2. **Set up API Key** (5 minutes)
   - Get key from console.anthropic.com
   - Set environment variable
   - Restart app

3. **Test AI Chat** (with API key)
   - Click example prompts
   - Ask your own questions
   - Check logs in `/governance/06_PROMPTS/logs/`

4. **Provide Feedback**
   - What works well?
   - What could be improved?
   - What features would you like in Phase 4C?

## Documentation

| Document | Purpose |
|----------|---------|
| **README_PHASE_4B.md** | This guide (overview and visuals) |
| [QUICK_START_ASSISTANT.md](QUICK_START_ASSISTANT.md) | 3-minute quick start |
| [AI_SETUP_GUIDE.md](AI_SETUP_GUIDE.md) | Detailed setup instructions |
| [PHASE_4B_VERIFICATION.md](PHASE_4B_VERIFICATION.md) | Testing checklist |
| [PHASE_4B_COMPLETE.md](PHASE_4B_COMPLETE.md) | Technical documentation |
| [PHASE_4B_SUMMARY.md](PHASE_4B_SUMMARY.md) | Implementation summary |
| [OLLAMA_SETUP.md](OLLAMA_SETUP.md) | Local LLM setup (Phase 4C) |

---

**Phase 4B Status:** ✅ **COMPLETE AND READY**

**Your Action:** Click the Assistant tab and start asking questions! 🤖
