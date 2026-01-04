# rai Interfaces - Complete Guide

**Three ways to use rai, each optimized for different workflows**

---

## Overview

| Interface | Mode | Best For | Launch |
|-----------|------|----------|--------|
| **rai** | One-shot | Scripts, automation, quick queries | `rai "query"` |
| **rai-shell** | REPL | Interactive sessions, multiple queries | `rai-shell` |
| **rai-tui** | Dashboard | Monitoring, visual feedback, demos | `rai-tui` |

---

## 1. rai - One-Shot CLI

### Description
Traditional CLI tool - run a single query and exit.

### Launch
```bash
rai "your query here"
```

### Example
```bash
$ rai "gpu stats"
🎮 GPU Statistics
======================================================================
GPU              AMD Radeon AI PRO R9700
Architecture     gfx1201
VRAM Used        9.2 GB
VRAM Total       32.0 GB
VRAM Free        22.8 GB
VRAM Usage       29%
Temperature      52°C (normal)
GPU Usage        15% (idle)

$ rai "vram"
💾 VRAM: 9.2 / 32.0 GB (29%)

$ rai "check memory"
💾 Memory Information:
======================================================================
Total: 31.2 GB
Used: 18.5 GB (59%)
Free: 12.7 GB
```

### Features
✅ Fast startup (instant)
✅ Pipe-friendly output
✅ Perfect for bash scripts
✅ No session overhead

### Use Cases
- **Bash scripts:** Monitor VRAM in loops
- **Cron jobs:** Scheduled system checks
- **Quick queries:** One-off information
- **Piping:** `rai "vram" | grep -o '[0-9.]*'`

### Pros & Cons
**Pros:**
- Instant startup
- Script-friendly
- Simple usage
- Predictable output

**Cons:**
- No session persistence
- MCP reconnection per query
- No command history
- No auto-completion

---

## 2. rai-shell - Interactive REPL

### Description
Persistent shell session with command history and tab completion.

### Launch
```bash
rai-shell
```

### Example
```bash
$ rai-shell

Initializing ROCm AI CLI...
✓ rocm-cli initialized [⚡ wild mode]

🚀 ROCm AI CLI - Interactive Shell
======================================================================
Quick commands:
  gpu stats  - Show GPU information
  vram       - Show VRAM usage
  /help      - Show all commands
  /exit      - Exit shell

Type your query and press Enter.

rai> vram
💾 VRAM: 9.2 / 32.0 GB (29%)

rai> gpu temp
🌡️ GPU Temperature: 52°C (125°F) - NORMAL

rai> check memory
💾 Memory Information:
======================================================================
Total: 31.2 GB
Used: 18.5 GB (59%)
Free: 12.7 GB

rai> /tools
🔧 Available MCP Tools:
======================================================================
rocm:       get_vram, get_gpu_temp, get_gpu_stats, ...
linux:      get_memory_information, list_services, ...
filesystem: read_file, list_directory, ...
atomic:     get_rpm_ostree_status, list_flatpaks, ...

rai> /exit
Goodbye! 👋
```

### Features
✅ Persistent session (no reconnection)
✅ Command history (↑/↓ arrows)
✅ Tab completion
✅ History saved to ~/.rai-history
✅ Special commands (/help, /tools, /history)

### Use Cases
- **Development:** Multiple queries during debugging
- **GPU monitoring:** Check VRAM repeatedly
- **System exploration:** Navigate services, logs, processes
- **Atomic desktop:** Manage rpm-ostree, Flatpak, toolbox

### Pros & Cons
**Pros:**
- No MCP reconnection overhead
- Command history with arrow keys
- Tab completion
- Fast query loop
- Special commands

**Cons:**
- Requires manual GPU stats refresh
- Text-only output (no visual bars)
- Readline-based (simple UI)

---

## 3. rai-tui - Dashboard UI

### Description
Beautiful dashboard with live GPU monitoring and visual feedback.

### Launch
```bash
rai-tui
```

### Example
```
╭─────────────────────────────────────────────────────────────────╮
│              🚀 rai - ROCm AI CLI                               │
╰─────────────────────────────────────────────────────────────────╯

╭─ 🎮 GPU Stats ──────────────────────────────────────────────────╮
│                                                                 │
│       GPU: AMD Radeon AI PRO R9700                              │
│                                                                 │
│      VRAM: ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░        │
│            9.2 / 32.0 GB (29%)                                  │
│                                                                 │
│      Temp: 52°C                                                 │
│                                                                 │
│   Updated: 14:35:22                                             │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯

╭─ 📜 Recent Queries ─────────────────────────────────────────────╮
│  • vram                                                         │
│  • gpu temp                                                     │
│  • check memory                                                 │
│  • ostree status                                                │
│  • show flatpaks                                                │
╰─────────────────────────────────────────────────────────────────╯

rai> vram

╭─ 📊 Result ─────────────────────────────────────────────────────╮
│                                                                 │
│ 💾 VRAM Usage:                                                  │
│ ==============================================                  │
│ Total    32.0 GB                                                │
│ Used      9.2 GB                                                │
│ Free     22.8 GB                                                │
│ Usage       29%                                                 │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯

Press Enter to continue...
```

### Features
✅ **Live GPU stats** - Auto-updates every 5 seconds
✅ **Visual progress bars** - See VRAM at a glance
✅ **Color-coded status** - Green/yellow/red temps
✅ **Panel-based layout** - Beautiful organization
✅ **Query history display** - Last 5 queries shown
✅ **Rich formatting** - Panels, colors, emoji

### Use Cases
- **GPU monitoring:** Watch VRAM during training
- **Demos/presentations:** Beautiful visual interface
- **System status:** Dashboard view of everything
- **Development:** See stats while querying

### Pros & Cons
**Pros:**
- Auto-updating GPU stats
- Beautiful visual design
- Color-coded status indicators
- No manual refresh needed
- Professional look

**Cons:**
- Requires larger terminal (80x24+)
- More complex UI (vs simple REPL)
- Press Enter after each query

---

## Feature Comparison Matrix

| Feature | rai | rai-shell | rai-tui |
|---------|-----|-----------|---------|
| **Speed** |
| Startup | Instant | 1-2s | 1-2s |
| Query execution | Fast | Fast | Fast |
| Session persistence | No | Yes | Yes |
| **UI/UX** |
| Command history | No | Yes (↑/↓) | Yes (visual) |
| Tab completion | No | Yes | No |
| Visual bars | No | No | Yes |
| Color coding | Basic | Basic | Advanced |
| Live GPU stats | No | No | Yes (auto) |
| **Output** |
| Format | Text | Text | Panels |
| Pipe-friendly | Yes | No | No |
| Script-friendly | Yes | No | No |
| **Interaction** |
| Query method | Args | Prompt | Prompt |
| Multiple queries | New process | Same session | Same session |
| Special commands | No | Yes (/help) | Yes (/help) |
| **Best For** |
| Automation | ✅✅✅ | ❌ | ❌ |
| Interactive use | ❌ | ✅✅✅ | ✅✅✅ |
| Monitoring | ✅ | ✅✅ | ✅✅✅ |
| Demos | ✅ | ✅✅ | ✅✅✅ |
| Scripts | ✅✅✅ | ❌ | ❌ |

---

## When to Use Each

### Use `rai` (one-shot) when:
- Writing bash scripts
- Need pipe-friendly output
- Cron jobs or automation
- Quick one-off queries
- Don't need session persistence

**Example:**
```bash
#!/bin/bash
# Monitor VRAM in a loop
while true; do
    vram=$(rai "vram" | grep -o '[0-9.]*' | head -1)
    if (( $(echo "$vram > 28" | bc -l) )); then
        echo "VRAM high! $vram GB"
    fi
    sleep 5
done
```

### Use `rai-shell` (REPL) when:
- Doing interactive development
- Need multiple queries in succession
- Want command history with arrows
- Need tab completion
- Prefer simple text interface

**Example:**
```bash
# Debug session
rai-shell

rai> gpu stats          # Check GPU
rai> check memory       # Check RAM
rai> list services      # Check services
rai> show logs          # Check logs
rai> /history           # Review what I did
rai> /exit
```

### Use `rai-tui` (dashboard) when:
- Monitoring GPU during training
- Want visual feedback with colors/bars
- Doing demos or presentations
- Need auto-updating stats
- Prefer beautiful UI

**Example:**
```bash
# Launch TUI, watch GPU while training
rai-tui

# Stats auto-update every 5s
# Query when needed
rai> vram               # See current usage
rai> ostree status      # Check system
rai> show flatpaks      # Check apps

# Dashboard refreshes automatically
# GPU stats always visible
```

---

## Workflow Combinations

### 1. Development Workflow
```bash
# Terminal 1: TUI for monitoring
rai-tui

# Terminal 2: Code and test
python train.py

# Terminal 3: Quick queries
rai "check disk"
rai "list processes"
```

### 2. System Debugging
```bash
# Use shell for exploration
rai-shell

rai> check memory
rai> check disk
rai> list services | grep failed
rai> show logs for systemd
```

### 3. Automation
```bash
# Use one-shot in scripts
if rai "ostree status" | grep -q "updates available"; then
    notify-send "System updates available"
fi
```

### 4. Presentation/Demo
```bash
# Use TUI for visual impact
rai-tui

# Beautiful dashboard
# Live stats
# Professional look
```

---

## Performance Comparison

### Startup Time
```
rai:       < 50ms    (instant)
rai-shell: ~1.5s     (MCP initialization)
rai-tui:   ~2s       (MCP + UI setup)
```

### Query Speed (after startup)
```
rai:       1-2s      (MCP connect + query)
rai-shell: 0.5-1s    (already connected)
rai-tui:   0.5-1s    (already connected)
```

### 10 Queries Total Time
```
rai:       10-20s    (10x reconnection overhead)
rai-shell: 5-10s     (no reconnection)
rai-tui:   5-10s     (no reconnection + auto GPU stats)
```

**Winner:** rai-shell / rai-tui for multiple queries (2x faster)

---

## Memory Usage

```
rai:       ~50 MB    (transient, exits after query)
rai-shell: ~80 MB    (persistent session)
rai-tui:   ~100 MB   (persistent + UI rendering)
```

All negligible on modern systems.

---

## Installation

All three are installed together:

```bash
cd ~/projects/rai

# All executables
ls -lh ~/bin/rai*
lrwxrwxrwx  rai -> /home/hashcat/projects/rai/rai.py
lrwxrwxrwx  rai-shell -> /home/hashcat/projects/rai/rai-shell.py
lrwxrwxrwx  rai-tui -> /home/hashcat/projects/rai/rai-tui.py
```

---

## Quick Start

### Try Each Interface

```bash
# 1. One-shot
rai "gpu stats"
rai "vram"

# 2. REPL
rai-shell
rai> vram
rai> /exit

# 3. TUI
rai-tui
rai> vram
/exit
```

### Pick Your Favorite

Based on your workflow:
- **Scripting?** → `rai`
- **Interactive querying?** → `rai-shell`
- **Monitoring/demos?** → `rai-tui`

**Or use all three for different tasks!**

---

## Summary

**Three interfaces, one powerful backend:**

```
┌─────────────────────────────────────────────────┐
│  rai (CLI) | rai-shell (REPL) | rai-tui (TUI)  │
└────────────────────┬────────────────────────────┘
                     ↓
        ┌────────────────────────┐
        │  ROCmCLIAgent          │
        │  - Intent classifier   │
        │  - MCP integration     │
        │  - LLM reasoning       │
        └────────────────────────┘
                     ↓
        ┌────────────────────────┐
        │  4 MCP Servers         │
        │  - ROCm (GPU)          │
        │  - linux (system)      │
        │  - filesystem          │
        │  - atomic (rpm-ostree) │
        └────────────────────────┘
```

**All share:**
- Same query processing
- Same MCP tools (39 total)
- Same intent patterns
- Same LLM backend

**Differences:**
- Interface style
- Session persistence
- Visual feedback
- Use case optimization

---

**Choose the right tool for the job, or use all three! 🚀**
