# AI Assistant Setup Guide

## Overview

The Meta Engine includes an AI Assistant powered by Claude API. This guide shows you how to set it up.

## Option 1: Use Web Chatbot (No Setup Required)

If you don't want to configure an API key:

1. Launch Meta Engine: `cargo tauri dev`
2. Click the **Assistant** tab (🤖)
3. Click the **"Web Chatbot"** button at the top
4. You'll see Claude's web interface
5. Ask questions directly (but without governance context)

**Limitations:**
- No access to your governance data
- Must manually provide context
- Requires internet connection

## Option 2: Full AI Integration (Recommended)

For context-aware AI assistance with your governance data:

### Step 1: Get an Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **"Create Key"**
5. Copy your API key (starts with `sk-ant-...`)

### Step 2: Set Environment Variable

**Linux / macOS (Bash/Zsh):**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Make it permanent (add to ~/.bashrc or ~/.zshrc):**
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**macOS (if using fish shell):**
```fish
set -gx ANTHROPIC_API_KEY "sk-ant-your-key-here"
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Windows (CMD):**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Make it permanent on Windows:**
1. Search for "Environment Variables" in Start Menu
2. Click "Edit the system environment variables"
3. Click "Environment Variables" button
4. Under "User variables", click "New"
5. Variable name: `ANTHROPIC_API_KEY`
6. Variable value: `sk-ant-your-key-here`
7. Click OK on all dialogs

### Step 3: Restart Meta Engine

```bash
cd /home/actpm/Documents/workfolder/aequitas/meta-engine/meta-gui
cargo tauri dev
```

### Step 4: Verify Setup

1. Go to **Assistant** tab (🤖)
2. You should see example prompts
3. Click an example or type your own question
4. AI should respond with governance-aware answers

**If you see "No API Key Configured":**
- Double-check you set the environment variable correctly
- Make sure you restarted the app after setting the variable
- Try running: `echo $ANTHROPIC_API_KEY` (should show your key)

## Using the AI Assistant

### Example Prompts

The Assistant shows context-aware examples like:
- "What should I work on next?"
- "Summarize my 5 active goals"
- "Why do I have 2 blocked goals?"
- "What's the status of Phase P7?"
- "What are the dependencies for goal-onboarding-flow?"
- "Are there any goals with no dependencies?"

### Chat Interface

- **Type your question** in the textarea at the bottom
- **Press Enter** to send (Shift+Enter for new line)
- **Click Send** button as alternative
- **View AI response** with full context
- **Clear Chat** button to start fresh

### What the AI Knows

When you ask a question, the AI receives:
- Current phase
- All goals (active, blocked, done, etc.)
- Goal dependencies
- Statistics (goal counts by status)
- Recent context

### Audit Trail

All AI interactions are logged to:
```
/governance/06_PROMPTS/logs/YYYY-MM-DD-HHmmss.md
```

Each log includes:
- Your question
- Context sent to AI
- AI's response
- Timestamp and model used
- Duration

## API Costs

Claude API charges per token. Approximate costs:

| Model | Input | Output |
|-------|--------|---------|
| Claude 3.5 Sonnet | $3 / 1M tokens | $15 / 1M tokens |

**Typical query cost:** $0.01 - $0.05 per question

**Estimate your usage:**
- Governance context: ~2,000 tokens
- Your question: ~50 tokens
- AI response: ~500 tokens
- **Total per query:** ~2,550 tokens ≈ $0.01

## Privacy & Security

### What's Sent to Anthropic:
- ✅ Governance structure (goals, phases, dependencies)
- ✅ Goal IDs, titles, statuses
- ✅ Your question

### What's NOT Sent:
- ❌ API key (kept locally)
- ❌ Sensitive file contents
- ❌ Personal data
- ❌ Code or implementation details

### Local Alternative (Future)

Phase 4C will add Ollama support for fully local AI:
- No API costs
- Complete privacy
- Works offline
- Slower responses

## Troubleshooting

### "No API Key Configured"

**Problem:** Environment variable not set or not detected.

**Solution:**
```bash
# Check if variable is set
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Restart app
cargo tauri dev
```

### "Network Error"

**Problem:** Can't reach Anthropic API.

**Possible causes:**
- No internet connection
- Firewall blocking requests
- API service down

**Solution:**
- Check internet connection
- Try web chatbot mode as fallback
- Check https://status.anthropic.com/

### "Invalid API Key"

**Problem:** API key is incorrect or expired.

**Solution:**
- Verify key in console: https://console.anthropic.com/
- Generate new key if needed
- Update environment variable
- Restart app

### Responses Too Slow

**Problem:** AI takes >10 seconds to respond.

**Possible causes:**
- Large governance context
- API rate limiting
- Network latency

**Solution:**
- Governance automatically limits context size
- Wait for response (it will arrive)
- Consider local LLM option when available

## Best Practices

### Effective Questions

**Good:**
- "What active goals are blocking Phase 7 completion?"
- "Which goals have no dependencies and can be started now?"
- "Summarize the status of all authentication-related goals"

**Less Effective:**
- "What should I do?" (too vague)
- "Fix my bugs" (AI can't modify files)
- "Write code for me" (AI is advisory only)

### Remember

- ✅ AI **suggests**, you **decide**
- ✅ AI is **read-only** (can't modify files)
- ✅ AI provides **guidance**, not **commands**
- ✅ Always **verify** AI suggestions
- ✅ Use judgment - AI isn't perfect

## FAQ

**Q: Can the AI modify my governance files?**
A: No. The AI is strictly read-only. All suggestions require your manual approval and action.

**Q: Does the AI remember previous questions?**
A: Not yet. Each question is independent. Conversation memory is planned for Phase 4C.

**Q: Can I use a different AI model?**
A: Currently only Claude is supported. OpenAI and Ollama support planned for Phase 4C.

**Q: How much does it cost?**
A: Approximately $0.01-$0.05 per question with Claude 3.5 Sonnet.

**Q: Is my data private?**
A: Governance structure is sent to Anthropic's API. For complete privacy, wait for Ollama (local LLM) support in Phase 4C.

**Q: Can I disable AI features?**
A: Yes. Simply don't set the API key. The app works perfectly without AI assistance.

## Next Steps

Once you're comfortable with the AI Assistant:

1. **Review Logs:** Check `/governance/06_PROMPTS/logs/` to see what context is sent
2. **Experiment:** Try different types of questions
3. **Provide Feedback:** Note what works well and what doesn't
4. **Phase 4C:** Look forward to status suggestions, local LLM, and more!

---

**Need Help?**
- Check logs in `/governance/06_PROMPTS/logs/`
- Review `PHASE_4B_COMPLETE.md` for technical details
- Try Web Chatbot mode as fallback
