# rai-tui - Terminal UI Guide

**Beautiful dashboard interface for rai with live GPU monitoring**

Inspired by Charm's Bubble Tea aesthetic, built with Rich.

---

## What is it?

**rai-tui** is a dashboard-style terminal interface for rai featuring:
- 🎮 **Live GPU stats** - Auto-updating VRAM, temperature
- 📊 **Visual progress bars** - See VRAM usage at a glance
- 📜 **Query history** - Recent queries displayed
- 💬 **Interactive prompts** - Beautiful input with Rich formatting
- 🎨 **Color-coded status** - Green/yellow/red for temps and VRAM

---

## Quick Start

### Launch the TUI

```bash
rai-tui
```

You'll see a beautiful dashboard:

```
╭─────────────────────────────────────────────────────────╮
│          🚀 rai - ROCm AI CLI                           │
╰─────────────────────────────────────────────────────────╯

╭─ 🎮 GPU Stats ──────────────────────────────────────────╮
│       GPU: AMD Radeon AI PRO R9700                      │
│      VRAM: ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│            9.2 / 32.0 GB (29%)                          │
│ Temperature: 52°C                                       │
│   Updated: 14:23:45                                     │
╰─────────────────────────────────────────────────────────╯

╭─ 📜 Recent Queries ─────────────────────────────────────╮
│  • vram                                                 │
│  • gpu temp                                             │
│  • check memory                                         │
│  • ostree status                                        │
╰─────────────────────────────────────────────────────────╯

rai> _
```

### Query Examples

```bash
rai> vram
╭─ 📊 Result ─────────────────────────────────────────────╮
│                                                         │
│ 💾 VRAM Usage:                                          │
│ ======================================                  │
│ Total    32.0 GB                                        │
│ Used      9.2 GB                                        │
│ Free     22.8 GB                                        │
│ Usage       29%                                         │
│                                                         │
╰─────────────────────────────────────────────────────────╯

Press Enter to continue...

rai> gpu temp
╭─ 📊 Result ─────────────────────────────────────────────╮
│                                                         │
│ 🌡️ GPU Temperature: 52°C (125°F) - NORMAL              │
│                                                         │
╰─────────────────────────────────────────────────────────╯

Press Enter to continue...

rai> check memory
╭─ 📊 Result ─────────────────────────────────────────────╮
│                                                         │
│ 💾 Memory Information:                                  │
│ ======================================                  │
│ Total: 31.2 GB                                          │
│ Used: 18.5 GB (59%)                                     │
│ Free: 12.7 GB                                           │
│ Buffers/Cache: 8.3 GB                                   │
│                                                         │
╰─────────────────────────────────────────────────────────╯

Press Enter to continue...
```

---

## Features

### 1. Live GPU Stats Panel

**Auto-updates every 5 seconds:**
- GPU name and architecture
- VRAM usage with visual bar
- Temperature with color coding:
  - 🟢 Green: < 60°C (cool)
  - 🟡 Yellow: 60-75°C (warm)
  - 🔴 Red: > 75°C (hot)
- Last update timestamp

**VRAM bar colors:**
- 🟢 Green: < 50% usage
- 🟡 Yellow: 50-80% usage
- 🔴 Red: > 80% usage

### 2. Query History

Shows last 5 queries with bullet points.

### 3. Dashboard Refresh

After each query result:
- Dashboard refreshes
- GPU stats update
- History updates
- Press Enter to continue querying

### 4. Color-Coded Results

Results are displayed with:
- Syntax highlighting
- Emoji indicators
- Panel borders
- Status colors

---

## Commands

### Special Commands

```bash
/exit, /quit    # Exit the TUI
/clear          # Clear screen
/help           # Show help
```

### GPU Queries

```bash
vram            # VRAM usage
gpu stats       # Full GPU info
gpu temp        # Temperature
show gpu        # GPU details
```

### System Queries

```bash
check memory    # RAM usage
check disk      # Disk usage
list services   # Systemd services
show logs       # Journal logs
```

### Atomic Desktop

```bash
ostree status         # rpm-ostree deployment
show flatpaks         # Flatpak apps
list toolboxes        # Toolbox containers
check updates         # System updates
```

### File Operations

```bash
read /path/file       # Read file
list /home            # List directory
```

### LLM Reasoning

```bash
what is 15 factorial
explain PyTorch tensors
how do I optimize GPU performance
```

---

## Keyboard Shortcuts

- **Enter** - Continue after result
- **Ctrl+C** - Interrupt query (doesn't exit)
- **Ctrl+D** or `/exit` - Exit TUI

---

## Comparison: rai Interfaces

### rai (one-shot)
```bash
rai "gpu stats"
# Single query, then exits
```

**Best for:**
- Bash scripts
- Quick queries
- Non-interactive automation

### rai-shell (REPL)
```bash
rai-shell

rai> gpu stats
rai> vram
rai> /exit
```

**Best for:**
- Multiple queries in succession
- Command history with arrow keys
- Tab completion
- Fast query loop

### rai-tui (Dashboard)
```bash
rai-tui
# Beautiful dashboard with live GPU stats
```

**Best for:**
- GPU monitoring while querying
- Visual feedback with colors
- Beautiful presentation
- Demo/showcase mode

---

## Architecture

```
┌────────────────────────────────────────┐
│  rai-tui.py (Dashboard UI)             │
│  - Rich Layout system                  │
│  - Live GPU stats updater (5s)         │
│  - Interactive prompt loop             │
│  - Panel-based display                 │
└──────────────┬─────────────────────────┘
               ↓
┌────────────────────────────────────────┐
│  rai.py (ROCmCLIAgent)                 │
│  - Same query processing               │
│  - Same MCP integration                │
│  - Same intent classification          │
└──────────────┬─────────────────────────┘
               ↓
┌────────────────────────────────────────┐
│  4 MCP Servers                         │
│  - ROCm (GPU stats)                    │
│  - linux-mcp-server (system)           │
│  - filesystem (files)                  │
│  - atomic (rpm-ostree, Flatpak)        │
└────────────────────────────────────────┘
```

**Key difference:** rai-tui adds:
- Background stats updater thread
- Rich Layout for split panels
- Visual progress bars
- Color-coded status indicators

---

## Performance

| Feature | rai | rai-shell | rai-tui |
|---------|-----|-----------|---------|
| Startup time | Instant | 1-2s | 1-2s |
| Query speed | Fast | Fast | Fast |
| GPU stats | Manual query | Manual query | **Auto-updates** |
| Visual feedback | Text only | Text only | **Bars + colors** |
| History | None | Arrow keys | **Visual display** |
| Best for | Scripts | Interactive | **Monitoring** |

**rai-tui advantage:** See GPU stats while querying, no manual refresh!

---

## Technical Details

### Live Stats Update

```python
# Background thread updates every 5 seconds
def update_stats_loop():
    while running:
        stats.update_from_agent(agent)
        time.sleep(5)
```

No manual refresh needed - GPU stats auto-update!

### Panel Layout

```
┌─────────────────────┬──────────────────────┐
│ GPU Stats           │ Query Input          │
│ (auto-updating)     │ rai> _               │
├─────────────────────┼──────────────────────┤
│ Recent Queries      │ Result Display       │
│ • vram              │                      │
│ • gpu temp          │ [Query output here]  │
└─────────────────────┴──────────────────────┘
```

### Color Scheme

**ROCm theme:**
- Primary: Cyan
- Secondary: Bright Blue
- Success: Bright Green
- Warning: Yellow
- Error: Red

Matches official ROCm branding!

---

## Use Cases

### 1. GPU Monitoring During Training

```bash
# Launch rai-tui
rai-tui

# Watch GPU stats auto-update while you query
rai> vram
# VRAM: 9.2 GB → 24.8 GB (training started!)

# Dashboard refreshes automatically
# See VRAM increase in real-time
```

### 2. System Debugging

```bash
rai-tui

# Check multiple things quickly
rai> check memory
rai> check disk
rai> list services

# GPU stats visible the whole time
```

### 3. Demo/Showcase Mode

```bash
# Show off rai to colleagues
rai-tui

# Beautiful dashboard with live stats
# Color-coded bars
# Professional look
```

### 4. Atomic Desktop Management

```bash
rai-tui

rai> ostree status
rai> show flatpaks
rai> check updates

# All with live GPU monitoring!
```

---

## Troubleshooting

### TUI not displaying correctly

**Issue:** Panels overlap or layout broken

**Fix:**
```bash
# Resize terminal to at least 80x24
# Or use fullscreen
```

### Stats not updating

**Issue:** GPU stats stuck at "Never"

**Check:**
```bash
# Test ROCm MCP server
python3 ~/projects/rai/mcp_servers/rocm_server.py
```

If server works, stats should update after 5 seconds.

### Colors not showing

**Issue:** Plain text instead of colors

**Check Rich:**
```bash
python3 -c "from rich import print; print('[cyan]Test[/cyan]')"
```

Should show colored "Test".

### Input lag

**Issue:** Slow to respond to input

**Cause:** Stats updater blocking

**Fix:** Stats update runs in background thread, shouldn't block. If it does:
- Increase update interval in code (default: 5 seconds)
- Check if ROCm server is slow

---

## Customization

### Change Update Interval

Edit `rai-tui.py`:

```python
self.stats_update_interval = 5  # Change to 10 for slower updates
```

### Change Color Scheme

Edit color thresholds:

```python
# VRAM colors (line ~130)
if vram_percent < 50:
    vram_color = "green"
elif vram_percent < 80:
    vram_color = "yellow"
else:
    vram_color = "red"

# Temperature colors (line ~140)
if temp_num < 60:
    temp_color = "green"
elif temp_num < 75:
    temp_color = "yellow"
else:
    temp_color = "red"
```

### Change Panel Sizes

Edit layout ratios:

```python
# Left/right split (line ~260)
layout["body"].split_row(
    Layout(name="left", ratio=1),    # Left: 1/3
    Layout(name="right", ratio=2)    # Right: 2/3
)
```

---

## Advanced Features

### History Persistence

Query history saves to `~/.rai-history` (shared with rai-shell).

**View history:**
```bash
tail -20 ~/.rai-history
```

### Background Stats Thread

GPU stats update independently from queries:
- Main thread: Handle user input and queries
- Background thread: Update GPU stats every 5s

**No blocking!** You can query while stats update.

---

## Tips & Tricks

### 1. Keep TUI Open for Monitoring

```bash
# Launch rai-tui in one terminal
rai-tui

# GPU stats auto-update
# Run training in another terminal
# Watch VRAM/temp in rai-tui
```

### 2. Quick Refresh

```bash
rai> /clear    # Clear screen
# Dashboard refreshes automatically
```

### 3. Mix Query Types

```bash
# GPU → System → Atomic → File
rai> vram
rai> check memory
rai> ostree status
rai> read /tmp/file.txt
```

All work seamlessly!

---

## Comparison with Charm Tools

### Inspired by Charm

**Charm's Bubble Tea** (Go):
- Event-driven TUI framework
- Component-based architecture
- Beautiful terminal UIs

**rai-tui** (Python + Rich):
- Similar aesthetic
- Panel-based layout
- Live updating stats
- Color-coded status

### Why Rich instead of Bubble Tea?

1. **Python-native** - rai is Python, Rich is Python
2. **Already a dependency** - No new dependencies
3. **Simpler integration** - Direct agent access
4. **Cross-platform** - Works everywhere Python does

### Charm Gum Integration (Future)

Could add Gum for:
- Fancy input prompts: `gum input`
- Selection menus: `gum choose`
- Confirmations: `gum confirm`

Example:
```bash
# Instead of text input
result=$(gum input --placeholder "Ask rai...")
```

---

## Quick Reference

**Launch:** `rai-tui`

**Commands:**
- `/exit` - Exit TUI
- `/clear` - Clear screen
- `/help` - Show help

**Queries:**
- GPU: `vram`, `gpu temp`, `gpu stats`
- System: `check memory`, `list services`
- Atomic: `ostree status`, `show flatpaks`
- Any other rai query works!

**Features:**
- ✅ Live GPU stats (auto-update 5s)
- ✅ Color-coded VRAM/temp
- ✅ Visual progress bars
- ✅ Query history display
- ✅ Beautiful Rich formatting
- ✅ Panel-based layout

---

**Enjoy your beautiful rai dashboard! 🎨**
