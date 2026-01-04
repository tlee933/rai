# rai - ROCm AI CLI

**Terminal-native AI agent for Fedora/ROCm development with hybrid performance architecture**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**rai** (ROCm AI) is a command-line AI assistant that combines instant bash commands, MCP (Model Context Protocol) servers, and local LLM reasoning for optimal performance. Built specifically for Fedora/RHEL systems with AMD ROCm GPUs.

## Features

🚀 **Hybrid Performance Architecture**
- **Instant queries** (< 100ms): Direct bash for common operations
- **Fast MCP queries** (1-3s): Structured tool calls for system/GPU diagnostics
- **LLM reasoning** (5-10s): Local Qwen3-4B model for complex queries

⚡ **150x Faster Than Traditional AI Assistants**
- No waiting for LLM on simple queries
- Intent classification routes to optimal path
- Graceful fallback to AI reasoning when needed

🛡️ **Switchable Security Modes**
- **MILD**: PolicyKit with fine-grained permissions
- **WILD**: SUDO_ASKPASS with interactive prompts (recommended)
- **UNRESTRICTED**: Passwordless sudo for maximum automation

🎮 **AMD ROCm Integration**
- Native support for AMD Radeon GPUs
- Custom MCP server for rocm-smi
- VRAM monitoring, temperature tracking, performance stats

🔧 **RHEL Lightspeed Compatible**
- Integrates linux-mcp-server (Red Hat's system diagnostics MCP)
- 20+ tools for systemd, journalctl, processes, network
- Works on Fedora without RHEL subscription

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/tlee933/rai.git
cd rai

# Install dependencies
pip install -r requirements.txt

# Create symlinks
ln -s $(pwd)/rai.py ~/bin/rai
ln -s ~/bin/rai ~/bin/rocm-cli
ln -s $(pwd)/rai-security ~/bin/rai-security
chmod +x ~/bin/rai ~/bin/rai-security

# Install MCP servers (optional but recommended)
pip install linux-mcp-server  # RHEL Lightspeed system diagnostics
npm install -g @modelcontextprotocol/server-filesystem  # File operations
```

### Basic Usage

```bash
# GPU queries (via ROCm MCP server)
rai "gpu stats"
rai "vram"
rai "gpu temp"

# System queries (via linux-mcp-server)
rai "check memory"
rai "check disk"
rai "list services"
rai "show logs"

# File operations
rai "read /tmp/test.txt"
rai "list /home"

# Complex reasoning (LLM)
rai "explain how PyTorch tensors work with ROCm"
rai "what is 15 factorial"
```

---

## Architecture

```
User Query
   ↓
┌──────────────────────────────────────────────┐
│ Intent Classifier (regex patterns)          │
│  - GPU queries → ROCm MCP Server            │
│  - System queries → linux-mcp-server        │
│  - File ops → filesystem MCP                │
│  - No match → LLM reasoning                 │
└──────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────┐
│ MCP Servers (parallel execution)            │
│                                              │
│  ROCm MCP:      GPU stats, VRAM, temp       │
│  linux-mcp:     systemd, logs, processes    │
│  filesystem:    file/directory operations   │
└──────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────┐
│ LLM Backend (local Qwen3-4B-Thinking)       │
│  - llama-server on localhost:8080           │
│  - 4B parameters, Q4_K_M quantization       │
│  - ~9GB VRAM, 32K context window            │
└──────────────────────────────────────────────┘
```

---

## Performance

| Query Type | Traditional AI | rai (Hybrid) | Speedup |
|------------|---------------|--------------|---------|
| GPU stats | 10-15s | **1-2s** | **7x faster** |
| System info | 10-15s | **1-2s** | **7x faster** |
| Top processes | 10-15s | **< 0.1s** | **150x faster** (bash aliases) |
| Code generation | 10-15s | 10-15s | Same (still uses LLM) |

**No more timeouts or hangs** - simple queries never touch the LLM!

---

## Security

Three security modes for different use cases:

### 🛡️ MILD - PolicyKit Fine-Grained
```bash
rai-security set mild
```
- Whitelisted commands run without password
- Unknown commands require PolicyKit authentication
- Best for production/shared systems

### ⚡ WILD - Interactive Prompts (Recommended)
```bash
rai-security set wild
```
- Safe commands run directly
- Privileged commands prompt for password via SUDO_ASKPASS
- Destructive commands require confirmation
- Best for development workstations

### 🚀 UNRESTRICTED - Maximum Automation
```bash
rai-security set unrestricted
```
- All commands run with sudo automatically
- Destructive commands still require confirmation
- Best for personal systems, AI agent autonomy

See [SECURITY_MODES.md](SECURITY_MODES.md) for detailed configuration.

---

## MCP Servers

### ROCm MCP Server (Custom)

**Tools:**
- `get_vram` - VRAM usage statistics
- `get_gpu_temp` - GPU temperature monitoring
- `get_gpu_stats` - Comprehensive GPU information
- `get_gpu_utilization` - Compute utilization percentage
- `get_rocm_version` - ROCm version information
- `get_hip_version` - HIP runtime version
- `rocminfo` - Detailed GPU capabilities

**Location:** `mcp_servers/rocm_server.py`

### linux-mcp-server (RHEL Lightspeed)

**20 tools for system diagnostics:**

**System:** OS info, CPU, memory, disk, hardware
**Processes:** List processes, process info
**Systemd:** Services, service status, service logs
**Logging:** Journal logs, audit logs, log files
**Network:** Interfaces, connections, listening ports
**Filesystem:** Block devices, directories, files

**Author:** RHEL Lightspeed (Red Hat)
**Version:** 0.1.0a4
**Installation:** `pip install linux-mcp-server`

### filesystem MCP (Anthropic)

**Standard MCP server for file operations**

**Installation:** `npm install -g @modelcontextprotocol/server-filesystem`

---

## Configuration

### Default Paths

```bash
~/.config/rai/security.conf         # Security mode
~/.local/bin/rai-askpass            # SUDO_ASKPASS script (wild mode)
/etc/polkit-1/rules.d/50-rai.rules # PolicyKit rules (mild mode)
```

### Environment Variables

```bash
RAI_SECURITY_MODE=wild              # Override security mode
SUDO_ASKPASS=$HOME/.local/bin/rai-askpass  # Password prompt script
```

### LLM Backend

**Default:** llama-server on `http://127.0.0.1:8080/v1`

**Recommended models:**
- Qwen3-4B-Thinking (2.4GB) - Fast, gaming-friendly
- Qwen2.5-Coder-32B (19GB) - Best for complex code

Switch models with bash aliases:
```bash
llm-gaming  # Switch to 4B model (fast)
llm-coder   # Switch to 32B model (powerful)
llm-status  # Check current model
```

See [LLM_SWITCHER.md](LLM_SWITCHER.md) for model management.

---

## Advanced Usage

### Bash Aliases (Instant Results)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Process & Resource Monitoring
alias ai-top='echo "🔥 Top 10 Processes:" && ps aux --sort=-%cpu | head -11'
alias ai-mem='echo "💾 Memory:" && free -h && ps aux --sort=-%mem | head -6'
alias ai-disk='echo "💿 Disk:" && df -h | grep -E "^/dev|Filesystem"'

# ROCm/GPU (via rai)
alias ai-gpu='rai "gpu stats"'
alias ai-vram='rai "vram"'
alias ai-temp='rai "gpu temp"'

# Code Generation (via oi-batch)
alias ai-code='oi-batch'
alias ai-doc='oi-batch'
alias ai-test='oi-batch'
```

### Intent Classification Patterns

Add custom patterns to `intent_classifier.py`:

```python
# GPU queries
(r'^(?:show|get|check)[\s-]*(?:gpu[\s-]*)?vram',
 'gpu', 'vram', lambda m: {}),

# System queries
(r'^(?:show|get|check)[\s-]*(?:mem|memory|ram)',
 'system', 'memory', lambda m: {}),

# Service status
(r'^(?:check|is)[\s-]+(.+?)[\s-]+(?:running|active)',
 'system', 'service_status', lambda m: {'service': m.group(1).strip()}),
```

### Custom MCP Servers

Create your own MCP server:

```python
#!/usr/bin/env python3
from mcp import MCPServer

server = MCPServer("my-custom-server")

@server.tool()
def my_custom_tool(arg: str) -> str:
    """Custom tool description"""
    return f"Result: {arg}"

if __name__ == "__main__":
    server.run()
```

Register in `rai.py`:

```python
await self.mcp_client.add_server(MCPServerConfig(
    name="custom",
    command="python3",
    args=["path/to/custom_server.py"]
))
```

---

## Requirements

### System
- Fedora 43+ or RHEL 9.6+ (may work on other Linux distros)
- AMD GPU with ROCm support (optional, for GPU features)
- Python 3.10+
- Node.js 18+ (for filesystem MCP server)

### Python Packages
- `mcp` - Model Context Protocol SDK
- `rich` - Terminal formatting (optional but recommended)
- `linux-mcp-server` - RHEL Lightspeed system diagnostics (optional)

### Optional
- `llama-server` - Local LLM backend
- Open Interpreter - For code generation (`ai-code`, `ai-doc`, `ai-test`)

---

## Troubleshooting

### MCP server timeout

```bash
# Test MCP servers manually
python3 mcp_servers/rocm_server.py
~/.local/bin/linux-mcp-server

# Check MCP connectivity
python3 << EOF
import asyncio
from mcp_bridge import MCPBridge
asyncio.run(MCPBridge().list_tools())
EOF
```

### Security mode not changing

```bash
# Check current mode
rai-security status

# Set mode
rai-security set wild

# Verify config file
cat ~/.config/rai/security.conf
```

### rai not finding tools

```bash
# Check if MCP servers are installed
which linux-mcp-server
ls -lh ~/projects/rai/mcp_servers/rocm_server.py

# Test with verbose output
rai "gpu stats" 2>&1 | grep -i "error"
```

---

## Documentation

- [HYBRID_SETUP.md](HYBRID_SETUP.md) - Hybrid architecture details
- [SECURITY_MODES.md](SECURITY_MODES.md) - Security configuration guide
- [LLM_SWITCHER.md](LLM_SWITCHER.md) - Model switching and management

---

## Roadmap

- [ ] Add git MCP server for repository operations
- [ ] Implement query caching for frequent MCP calls
- [ ] Add streaming output for long-running queries
- [ ] Create systemd service for persistent MCP servers
- [ ] Build web UI for remote access
- [ ] Add support for multiple GPU architectures (NVIDIA, Intel)
- [ ] Integrate with more RHEL Lightspeed features

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Credits

**Built with:**
- [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- [linux-mcp-server](https://github.com/rhel-lightspeed/linux-mcp-server) by RHEL Lightspeed
- [ROCm](https://rocm.docs.amd.com/) by AMD
- [Qwen3](https://qwen.readthedocs.io/) by Alibaba Cloud

**Inspired by:**
- RHEL Lightspeed AI assistant
- Open Interpreter
- GitHub Copilot CLI

---

## Author

Created by [@tlee933](https://github.com/tlee933)

**Hardware:** AMD Radeon AI PRO R9700 (gfx1201, 32GB VRAM)
**OS:** Fedora 43
**ROCm:** Custom 7.11 build with gfx103X support

---

## Support

- Issues: [GitHub Issues](https://github.com/tlee933/rai/issues)
- Discussions: [GitHub Discussions](https://github.com/tlee933/rai/discussions)

---

**rai** - Your terminal-native AI companion for Fedora/ROCm development 🚀
