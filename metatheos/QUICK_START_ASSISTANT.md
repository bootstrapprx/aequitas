# Quick Start: AI Assistant 🤖

## 3-Minute Setup

### Without API Key (Immediate)

```bash
# App is already running!
# Just go to http://localhost:5174
# Click: Assistant tab (🤖)
# Click: "Web Chatbot" button
# ✅ You now have Claude web interface
```

### With API Key (Full Features)

```bash
# 1. Get API key from https://console.anthropic.com/
# 2. Set it:
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# 3. Restart app:
cd /home/actpm/Documents/workfolder/aequitas/meta-engine/meta-gui
cargo tauri dev

# 4. Go to http://localhost:5174
# 5. Click: Assistant tab (🤖)
# 6. Click an example prompt
# ✅ AI responds with governance context!
```

## Quick Test

```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Should show: sk-ant-...
# If empty, set it first
```

## Try These Prompts

Once in AI Chat mode:

1. **"What should I work on next?"**
   - AI suggests goals based on current phase and dependencies

2. **"Summarize my active goals"**
   - AI lists all active goals with context

3. **"Why do I have blocked goals?"**
   - AI analyzes goal dependencies and blockers

4. **"What's the status of Phase P7?"**
   - AI reports on current phase progress

## Check Logs

After asking a question:

```bash
cd /home/actpm/Documents/workfolder/aequitas/governance/06_PROMPTS/logs
ls -lah
# Open the most recent .md file
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No API Key Configured" | Set `ANTHROPIC_API_KEY` and restart |
| Web Chatbot doesn't load | Check internet connection |
| API key set but not detected | Restart app with `cargo tauri dev` |
| Network error | Check https://status.anthropic.com/ |

## Cost

- **Web Chatbot:** Free (uses your claude.ai account)
- **AI Chat:** ~$0.01-$0.05 per query

## App Status

```bash
# Check if running:
ps aux | grep -E "(cargo|tauri|vite)" | grep -v grep

# Should show:
# - cargo-tauri tauri dev
# - node .../vite

# If not running:
cd /home/actpm/Documents/workfolder/aequitas/meta-engine/meta-gui
cargo tauri dev
```

## Full Docs

- **Setup Guide:** [AI_SETUP_GUIDE.md](AI_SETUP_GUIDE.md)
- **Testing:** [PHASE_4B_VERIFICATION.md](PHASE_4B_VERIFICATION.md)
- **Ollama Setup:** [OLLAMA_SETUP.md](OLLAMA_SETUP.md)
- **Technical:** [PHASE_4B_COMPLETE.md](PHASE_4B_COMPLETE.md)

---

**Current Status:** ✅ App running, ready to test!
