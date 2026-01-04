# Hybrid AI Assistant Setup

**rai** now uses a hybrid approach combining instant bash commands, MCP servers, and LLM queries for optimal performance.

## Architecture

```
User Query
   ↓
┌──────────────────────────────────────────────────────────┐
│ FAST PATH (instant bash)                                 │
│  ai-top, ai-mem, ai-disk, ai-stats                      │
│  → Direct PS/free/df commands (< 100ms)                 │
└──────────────────────────────────────────────────────────┘
   ↓ (complex queries)
┌──────────────────────────────────────────────────────────┐
│ MEDIUM PATH (rai + MCP servers)                          │
│  Intent Classifier → MCP Tool Call → Formatted Output    │
│                                                           │
│  ROCm MCP Server:                                        │
│   - GPU stats, VRAM, temperature                         │
│                                                           │
│  linux-mcp-server (RHEL Lightspeed):                     │
│   - Memory, disk, systemd, processes, logs               │
│  → MCP JSON-RPC calls (~1-2s)                            │
└──────────────────────────────────────────────────────────┘
   ↓ (no pattern match)
┌──────────────────────────────────────────────────────────┐
│ SLOW PATH (LLM reasoning)                                │
│  Qwen3-4B-Thinking Model                                 │
│  → Full AI reasoning (~5-10s)                            │
└──────────────────────────────────────────────────────────┘
```

---

## Quick Commands

### Instant Bash Aliases (< 100ms)

```bash
ai-top        # Top 10 CPU processes
ai-mem        # Memory usage + top RAM consumers
ai-disk       # Disk usage by filesystem
ai-stats      # System overview (CPU/RAM/disk/uptime)
ai-services   # Running systemd services
```

### rai with MCP (1-3s)

**GPU queries (ROCm MCP):**
```bash
rai "gpu stats"    # Full GPU statistics
rai "vram"         # VRAM usage
rai "gpu temp"     # GPU temperature
```

**System queries (linux-mcp-server):**
```bash
rai "check memory"           # Memory usage
rai "check disk"             # Disk usage
rai "list services"          # Systemd services
rai "show logs"              # System journal logs
rai "is llama-server running"  # Service status
```

### Code Generation (oi-batch)

```bash
ai-code "analyze this Python file for bugs"
ai-doc "generate docstrings for these functions"
ai-test "create unit tests for this module"
```

---

## Performance Comparison

| Query Type | Old (oi-batch) | New (Hybrid) | Speedup |
|------------|----------------|--------------|---------|
| **Top processes** | 10-15s | < 0.1s | **150x faster** |
| **Memory usage** | 10-15s | 1-2s | **7x faster** |
| **GPU stats** | 10-15s | 1-2s | **7x faster** |
| **Code generation** | 10-15s | 10-15s | Same (still uses LLM) |

---

## MCP Servers

### 1. ROCm MCP Server (custom)

**Location:** `/home/hashcat/TheRock/tools/rocm-cli/mcp_servers/rocm_server.py`

**Tools:**
- `get_vram` - VRAM usage
- `get_gpu_temp` - GPU temperature
- `get_gpu_stats` - Comprehensive GPU info
- `get_gpu_utilization` - Compute utilization
- `get_rocm_version` - ROCm version info
- `get_hip_version` - HIP runtime version
- `rocminfo` - Detailed GPU capabilities

**Command:** `rocm-smi` wrapper

---

### 2. linux-mcp-server (RHEL Lightspeed)

**Location:** `~/.local/bin/linux-mcp-server`
**Version:** 0.1.0a4
**Author:** RHEL Lightspeed (Red Hat)

**Tools (20 total):**

**System Information:**
- `get_system_information` - OS, kernel, distribution
- `get_cpu_information` - CPU details
- `get_memory_information` - RAM and swap
- `get_disk_usage` - Filesystem usage
- `get_hardware_information` - PCI devices, USB, etc.

**Processes:**
- `list_processes` - Running processes
- `get_process_info` - Process details by PID

**Systemd:**
- `list_services` - All systemd services
- `get_service_status` - Service status by name
- `get_service_logs` - Service logs

**Logging:**
- `get_journal_logs` - Systemd journal
- `get_audit_logs` - Audit logs (requires root)
- `read_log_file` - Read specific log files

**Network:**
- `get_network_interfaces` - Network interface details
- `get_network_connections` - Active connections
- `get_listening_ports` - Listening ports

**Filesystem:**
- `list_block_devices` - Block devices
- `list_directories` - Directory listing
- `list_files` - File listing
- `read_file` - Read file contents

**Configuration:**
- Log paths: `/var/log/messages`, `/var/log/journal`, `/home/hashcat/TheRock`
- Log level: ERROR
- User: hashcat

---

### 3. filesystem MCP Server (Anthropic)

**Command:** `npx @modelcontextprotocol/server-filesystem`

**Paths:** `/tmp`, `/home/hashcat`, `/opt/rocm`

**Tools:**
- File reading
- Directory listing
- File searching

---

## Intent Classification

**rai** uses regex pattern matching for fast query classification:

### GPU Patterns (ROCm MCP)
```
"gpu stats"     → get_gpu_stats
"vram"          → get_vram
"gpu temp"      → get_gpu_temp
"show gpu"      → get_gpu_stats
```

### System Patterns (linux-mcp-server)
```
"check memory"  → get_memory_information
"check disk"    → get_disk_usage
"show logs"     → get_journal_logs
"list services" → list_services
"is X running"  → get_service_status
```

### File Patterns (filesystem)
```
"read /path"    → read_file
"list /dir"     → list_directory
```

**No match?** → Falls back to LLM with full context

---

## Examples

### Instant Results (bash)

```bash
$ ai-top
🔥 Top 10 Processes by CPU:
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
hashcat   600728  9.7  7.0 15322848 2314560 ?    Ssl  18:22   3:36 llama-server
hashcat     5416  6.8  1.2 76363288 401568 pts/1 Sl+  09:20  39:48 claude
...

$ ai-mem
💾 Memory Usage:
               total        used        free      shared  buff/cache   available
Mem:            31Gi       7.2Gi       818Mi       266Mi        23Gi        23Gi
Swap:          104Gi       1.7Gi       102Gi

Top 5 by RAM:
hashcat   600728  9.7  7.0 15322848 2314560 ...  llama-server
hashcat     5416  6.8  1.2 76363288 401568  ...  claude
...
```

### MCP Queries (rai)

```bash
$ rai "vram"
✓ rocm-cli initialized [⚡ wild mode]
      💾 VRAM Usage
┏━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Metric      ┃ Value    ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Total       │ 31.86 GB │
│ Used        │ 9.69 GB  │
│ Free        │ 22.17 GB │
│ Utilization │ 30.4%    │
└─────────────┴──────────┘

$ rai "check memory"
✓ rocm-cli initialized [⚡ wild mode]

💾 Memory Information:
======================================================================
=== RAM Information ===
Total: 31.2GB
Available: 23.0GB
Used: 7.4GB (26.5%)
Free: 834.9MB
Buffers: 94.5MB
Cached: 22.9GB

=== Swap Information ===
Total: 104.0GB
Used: 1.8GB (1.8%)
Free: 102.2GB

$ rai "check disk"
✓ rocm-cli initialized [⚡ wild mode]

💿 Disk Usage:
======================================================================
=== Filesystem Usage ===

Filesystem                     Size       Used       Avail      Use%   Mounted on
------------------------------------------------------------------------------------------
/dev/nvme0n1p3                 464.2GB    404.8GB    48.7GB     89.3   /
/dev/nvme0n1p2                 973.4MB    482.4MB    423.8MB    53.2   /boot
/dev/nvme1n1p1                 937.8GB    119.0GB    771.1GB    13.4   /mnt/therock-build
...
```

---

## Benefits

### Speed
- **150x faster** for simple queries (bash vs oi-batch)
- **7x faster** for MCP queries vs full LLM pipeline
- **Zero LLM overhead** for common operations

### Reliability
- No MCP timeouts on simple queries
- Bash commands always work
- Graceful fallback to LLM if needed

### Resource Efficiency
- VRAM: Only ~10GB used (Qwen3-4B) vs ~30GB (Qwen2.5-Coder-32B)
- CPU: Minimal for bash/MCP, heavy only when LLM needed
- Latency: Sub-second for 90% of queries

### Flexibility
- Add new bash aliases easily
- Extend MCP servers with new tools
- LLM always available for complex queries

---

## Security

All commands run under **⚡ Wild mode** security:
- Safe commands (rocm-smi, free, ps) run directly
- Privileged commands require SUDO_ASKPASS password
- Destructive commands (rm -rf) require confirmation

See `SECURITY_MODES.md` for details.

---

## Troubleshooting

### Bash aliases not working

```bash
# Reload shell config
source ~/.zshrc   # for zsh
source ~/.bashrc  # for bash

# Or open new terminal
```

### MCP server timeout

```bash
# Check if linux-mcp-server is installed
which linux-mcp-server

# Test manually
python3 -c "import asyncio; from mcp_bridge import MCPBridge; asyncio.run(MCPBridge().list_tools())"

# Check logs
journalctl -u linux-mcp-server -n 50
```

### rai not finding MCP servers

```bash
# Check server paths
ls -lh ~/.local/bin/linux-mcp-server
ls -lh /home/hashcat/TheRock/tools/rocm-cli/mcp_servers/rocm_server.py

# Test rai with verbose output
rai "gpu stats" 2>&1 | grep -i "error\|mcp"
```

---

## Future Enhancements

- [ ] Add more intent patterns for common queries
- [ ] Create systemd MCP server for service management
- [ ] Add git MCP server for repository operations
- [ ] Implement caching for frequent MCP queries
- [ ] Add streaming output for long-running queries

---

## See Also

- `SECURITY_MODES.md` - Security configuration
- `LLM_SWITCHER.md` - Model switching guide
- `~/TheRock/tools/rocm-cli/` - rai source code
- [RHEL Lightspeed](https://github.com/rhel-lightspeed/linux-mcp-server) - linux-mcp-server docs
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
