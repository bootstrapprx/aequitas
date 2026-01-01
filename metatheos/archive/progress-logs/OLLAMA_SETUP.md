# Ollama Setup for Meta Engine

## Overview

The Meta Engine can use Ollama for local AI inference. Since the main Aequitas app already uses Ollama via Docker, this guide shows how to run a separate Ollama instance for Meta Engine.

## Architecture

```
Main Aequitas App (Docker)
├── Ollama: localhost:11434  ← Main app uses this
└── PostgreSQL, Redis, etc.

Meta Engine (Desktop)
├── Ollama: localhost:11435  ← Meta Engine uses this
└── Governance files
```

## Option 1: Shared Ollama (Recommended)

Use the same Ollama instance for both apps. This saves resources and is simpler.

### Configuration

Set Meta Engine to use the main Ollama:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.1:8b"
```

**Pros:**
- ✅ No additional setup needed
- ✅ Shares downloaded models
- ✅ Lower resource usage

**Cons:**
- ⚠️ Main app and Meta Engine share API limits
- ⚠️ Both must be running

## Option 2: Separate Ollama Instance

Run a dedicated Ollama for Meta Engine on a different port.

### Step 1: Install Second Ollama (if needed)

**Linux:**
```bash
# Ollama is already installed, we just run it on different port
```

**macOS:**
```bash
# Use brew services to run multiple instances
```

**Windows:**
```bash
# Install Ollama normally, configure port
```

### Step 2: Run Ollama on Custom Port

**Linux (systemd):**

Create a custom service:

```bash
sudo nano /etc/systemd/system/ollama-meta.service
```

Add:
```ini
[Unit]
Description=Ollama Service for Meta Engine
After=network.target

[Service]
Type=simple
User=actpm
Environment="OLLAMA_HOST=127.0.0.1:11435"
ExecStart=/usr/local/bin/ollama serve
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ollama-meta
sudo systemctl start ollama-meta
```

**Linux (manual):**
```bash
OLLAMA_HOST=127.0.0.1:11435 ollama serve &
```

**macOS:**
```bash
# Set port in environment
export OLLAMA_HOST=127.0.0.1:11435
ollama serve
```

**Windows:**
```powershell
# Set port
$env:OLLAMA_HOST="127.0.0.1:11435"
ollama serve
```

### Step 3: Pull Model

```bash
# Connect to the custom port
export OLLAMA_HOST=127.0.0.1:11435

# Pull model
ollama pull llama3.1:8b

# Or a smaller model for faster responses
ollama pull llama3.1:7b-q4_K_M
```

### Step 4: Configure Meta Engine

```bash
export OLLAMA_BASE_URL="http://localhost:11435"
export OLLAMA_MODEL="llama3.1:8b"
```

**Make permanent (add to ~/.bashrc):**
```bash
echo 'export OLLAMA_BASE_URL="http://localhost:11435"' >> ~/.bashrc
echo 'export OLLAMA_MODEL="llama3.1:8b"' >> ~/.bashrc
source ~/.bashrc
```

## Option 3: Docker Ollama for Meta Engine

Run Ollama in a separate Docker container.

```bash
docker run -d \
  --name ollama-meta \
  -p 11435:11434 \
  -v ollama-meta:/root/.ollama \
  ollama/ollama
```

Configure Meta Engine:
```bash
export OLLAMA_BASE_URL="http://localhost:11435"
export OLLAMA_MODEL="llama3.1:8b"
```

Pull model:
```bash
docker exec -it ollama-meta ollama pull llama3.1:8b
```

## Recommended Models

### For Performance (Faster, Less Accurate)
```bash
ollama pull llama3.1:7b-q4_K_M    # ~4GB RAM
ollama pull phi3:mini              # ~2GB RAM
```

### For Quality (Slower, More Accurate)
```bash
ollama pull llama3.1:8b            # ~8GB RAM
ollama pull llama3.1:70b           # ~40GB RAM (if you have resources)
```

### For Balance
```bash
ollama pull llama3.1:8b-q5_K_M    # ~6GB RAM, good quality
```

## Testing Setup

### Test Ollama Connection

```bash
# Test if Ollama is running
curl http://localhost:11435/api/tags

# Should return list of models
```

### Test with Meta Engine

1. Set environment variables
2. Launch Meta Engine: `cargo tauri dev`
3. Go to Assistant tab
4. Select "Local LLM" mode (when implemented in Phase 4C)
5. Ask a question

## Port Reference

| Service | Port | Used By |
|---------|------|---------|
| Ollama (Main) | 11434 | Aequitas main app (Docker) |
| Ollama (Meta) | 11435 | Meta Engine (Desktop) |
| Vite Dev Server | 5174 | Meta Engine UI |
| PostgreSQL | 5432 | Aequitas main app |

## Troubleshooting

### Port Already in Use

**Problem:** Port 11435 already taken.

**Solution:**
```bash
# Find what's using the port
lsof -i :11435

# Use a different port
export OLLAMA_HOST=127.0.0.1:11436
export OLLAMA_BASE_URL="http://localhost:11436"
```

### Model Not Found

**Problem:** Ollama says model doesn't exist.

**Solution:**
```bash
# Make sure you're connected to the right instance
export OLLAMA_HOST=127.0.0.1:11435

# List available models
ollama list

# Pull the model
ollama pull llama3.1:8b
```

### Connection Refused

**Problem:** Can't connect to Ollama.

**Solution:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Check the port
netstat -tuln | grep 11435

# Restart Ollama
sudo systemctl restart ollama-meta
```

### Slow Responses

**Problem:** AI takes >30 seconds to respond.

**Possible causes:**
- Large model on limited hardware
- Not enough RAM
- CPU inference (no GPU acceleration)

**Solutions:**
- Use smaller quantized model: `llama3.1:7b-q4_K_M`
- Reduce max tokens in Meta Engine config
- Enable GPU acceleration (if available)

## Performance Comparison

| Model | RAM | Speed | Quality | Use Case |
|-------|-----|-------|---------|----------|
| phi3:mini | 2GB | Fast | Good | Quick queries |
| llama3.1:7b-q4 | 4GB | Medium | Better | Balanced |
| llama3.1:8b | 8GB | Slow | Best | Quality responses |
| llama3.1:70b | 40GB+ | Very Slow | Excellent | Production |

## Cost Comparison

### Claude API (Current)
- **Cost:** ~$0.01-$0.05 per query
- **Speed:** 1-2 seconds
- **Quality:** Excellent
- **Privacy:** Data sent to Anthropic

### Ollama Local (Future - Phase 4C)
- **Cost:** $0 (electricity only)
- **Speed:** 5-30 seconds (depends on hardware)
- **Quality:** Good to Excellent (depends on model)
- **Privacy:** Complete (all local)

## Best Practice Recommendations

### For Development
Use **Option 1** (Shared Ollama):
- Simpler setup
- Lower resource usage
- Main app and Meta Engine both benefit

### For Production Use
Use **Option 2** (Separate Instance):
- Isolated resources
- No conflicts
- Can use different models
- Better reliability

### For Privacy/Offline
Use **Option 2 or 3** with local Ollama:
- No data leaves your machine
- Works offline
- No API costs
- Full control

## Future: Phase 4C Implementation

When Phase 4C adds Ollama support, you'll be able to:

1. **Choose Provider in UI:**
   ```
   Settings > AI Provider
   ○ Claude API (Current)
   ● Ollama Local (New)
   ```

2. **Configure in UI:**
   ```
   Base URL: http://localhost:11435
   Model: llama3.1:8b
   [Test Connection]
   ```

3. **Auto-detection:**
   - Meta Engine will test both Claude and Ollama
   - Show available options
   - Let you choose

## Summary

**Recommended Setup:**
1. Use **shared Ollama** (port 11434) for both apps
2. Configure: `export OLLAMA_BASE_URL="http://localhost:11434"`
3. Use model: `llama3.1:8b` (good balance)
4. Wait for Phase 4C for UI configuration

**For Separate Instance:**
1. Run Ollama on port 11435
2. Pull models to the separate instance
3. Configure Meta Engine to use 11435
4. Both apps can run independently

---

**Current Status:** Phase 4B (Claude API only)
**Next:** Phase 4C will add Ollama UI integration
**ETA:** 1-2 weeks after Phase 4B testing
