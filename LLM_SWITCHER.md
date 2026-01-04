# LLM Model Switcher

Quick aliases for switching between llama-server models in **rai**.

## Usage

Open a new terminal (or run `source ~/.zshrc` / `source ~/.bashrc`) to load the aliases.

### Commands

```bash
# Show available models
llm-models

# Switch to heavy coder model (19GB VRAM)
llm-coder

# Switch to light gaming model (2.4GB VRAM)
llm-gaming

# Check current model and VRAM
llm-status
```

## Model Profiles

### 🚀 llm-coder - Qwen2.5-Coder-32B
**Size:** 19 GB GGUF (Q4_K_M)
**VRAM:** ~30 GB when loaded
**Best for:**
- Complex code generation
- Large refactoring tasks
- Multi-file analysis
- Production coding sessions

**Service file:** `/tmp/llama-server-qwen-coder-32b.service`

---

### 🎮 llm-gaming - Qwen3-4B-Thinking
**Size:** 2.4 GB GGUF (Q4_K_M)
**VRAM:** ~9 GB when loaded
**Free VRAM:** ~22 GB (perfect for gaming!)
**Best for:**
- Gaming sessions (CS2, etc.)
- Quick system queries
- Terminal workflows
- Daily development
- Reasoning/thinking tasks

**Service file:** `/tmp/llama-server-qwen3-thinking.service`

---

## Examples

### Switch before gaming:
```bash
llm-gaming
# 🎮 Switched to Qwen3-4B-Thinking (2.4GB VRAM)
# [Shows VRAM stats - ~22GB free]

# Launch Counter-Strike 2 or other games
steam
```

### Switch back for heavy coding:
```bash
llm-coder
# 🚀 Switched to Qwen2.5-Coder-32B (19GB VRAM)
# [Shows GPU stats - better for complex code]

# Use with rai or oi
rai "write a complex async Python function"
```

### Check what's running:
```bash
llm-status
# ● llama-server.service - llama-server (Qwen3-4B-Thinking...)
#      Active: active (running)
#
# 💾 VRAM Usage: 9.62 GB / 31.86 GB (30.2%)
```

---

## Technical Details

### How it works:
1. Copies service file from `/tmp/` to `/etc/systemd/system/llama-server.service`
2. Reloads systemd daemon
3. Restarts llama-server service
4. Shows VRAM stats to confirm switch

### Service files location:
```bash
ls -lh /tmp/llama-server*.service

# -rw-r--r-- 1 hashcat hashcat 734 Jan  3 18:21 llama-server-qwen3-thinking.service
# -rw-r--r-- 1 hashcat hashcat 768 Jan  3 18:28 llama-server-qwen-coder-32b.service
```

### Model locations:
```bash
# 32B Coder:
~/.lmstudio/models/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF/qwen2.5-coder-32b-instruct-q4_k_m.gguf

# 4B Thinking:
~/.lmstudio/models/lmstudio-community/Qwen3-4B-Thinking-2507-GGUF/Qwen3-4B-Thinking-2507-Q4_K_M.gguf
```

---

## Integration with rai

Both models work seamlessly with **rai** (rocm-cli):

```bash
# After switching with llm-gaming or llm-coder:
rai "gpu stats"
rai "vram"
rai "explain PyTorch tensors"

# rai automatically detects and uses the active model
```

**Security mode:** Wild (⚡) - interactive prompts for privileged commands

---

## Troubleshooting

### Alias not found:
```bash
# Reload shell config
source ~/.zshrc    # for zsh
source ~/.bashrc   # for bash

# Or open new terminal
```

### Service fails to start:
```bash
# Check service status
systemctl status llama-server --no-pager

# Check journal
journalctl -u llama-server -n 50

# Verify model file exists
ls -lh ~/.lmstudio/models/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF/
```

### VRAM still high after switching:
```bash
# Wait for model to fully load/unload
sleep 10 && rai "vram"

# Force restart
sudo systemctl restart llama-server
```

---

## Performance Notes

**Switching time:** ~10-15 seconds
**32B → 4B:** VRAM drops from ~30GB to ~9GB
**4B → 32B:** VRAM increases from ~9GB to ~30GB

**Gaming headroom with 4B model:**
- Counter-Strike 2: Needs ~8GB VRAM ✅ (22GB free)
- Cyberpunk 2077: Needs ~12GB VRAM ✅ (22GB free)
- Most games: ✅ Plenty of room

---

## See Also

- `rai-security status` - Check rai security mode
- `SECURITY_MODES.md` - Security configuration guide
- `~/TheRock/tools/rocm-cli/` - rai installation directory
