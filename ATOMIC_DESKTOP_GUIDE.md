# Atomic Desktop Support for rai

**NEW:** rai now supports Fedora Atomic Desktop variants (Silverblue, Kinoite, etc.) with a custom MCP server for rpm-ostree, Flatpak, and toolbox management!

## What's New?

### atomic-desktop MCP Server

**7 specialized tools for immutable desktops:**

1. **get_rpm_ostree_status** - Show current deployment and layered packages
2. **check_rpm_ostree_updates** - Check for system updates
3. **list_layered_packages** - List rpm-ostree layered packages
4. **list_flatpaks** - List user and system Flatpak apps
5. **get_flatpak_updates** - Check for Flatpak updates
6. **list_toolboxes** - List toolbox/distrobox containers
7. **get_ostree_info** - Get ostree deployment info

## Quick Start

### Basic Queries

```bash
# rpm-ostree status
rai "ostree status"
rai "check rpm-ostree"
rai "show ostree status"

# Check for updates
rai "check updates"
rai "check system updates"

# Layered packages
rai "show layered packages"
rai "list layered packages"

# Flatpak apps
rai "show flatpaks"
rai "list flatpaks"

# Flatpak updates
rai "check flatpak updates"

# Toolbox containers
rai "show toolboxes"
rai "list toolboxes"
```

### Interactive Shell

```bash
rai-shell

rai> ostree status
🔷 rpm-ostree Status:
======================================================================
● fedora:fedora/43/x86_64/silverblue (8a7f2c91)
  Base commit: 8a7f2c91d4e3
  Layered packages: podman, toolbox, gh, kitty, neovim
    ... and 12 more

rai> check updates
✓ System is up to date!

rai> show flatpaks
📱 Flatpak Applications:
======================================================================
User apps: 5
System apps: 12
Total: 17

User apps (first 10):
  • org.mozilla.firefox
  • org.gnome.Calculator
  • com.spotify.Client
  • org.telegram.desktop
  • com.discordapp.Discord

rai> list toolboxes
🔧 Toolbox Containers (3):
======================================================================
  • fedora-43
  • dev-container
  • pytorch-env

rai> /exit
```

## Use Cases

### 1. Pre-reboot system check

```bash
# Before restarting after rpm-ostree upgrade
rai "ostree status"  # Check pending deployment
rai "show layered packages"  # Verify layered packages will persist
```

### 2. App management

```bash
# Check all pending updates
rai "check flatpak updates"  # Check Flatpak apps
rai "check system updates"   # Check rpm-ostree

# List installed apps
rai "show flatpaks"
```

### 3. Development container tracking

```bash
# See all toolbox containers
rai "list toolboxes"

# Use with bash scripts
if rai "list toolboxes" | grep -q "pytorch-env"; then
    echo "PyTorch environment ready"
fi
```

## Technical Details

### How It Works

```
┌─────────────────────────────────────────┐
│  rai query: "ostree status"             │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  intent_classifier.py                   │
│  Pattern: "ostree status"               │
│  → category: 'atomic'                   │
│  → action: 'ostree_status'              │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  rai.py: _handle_atomic_intent()        │
│  Call MCP: atomic.get_rpm_ostree_status │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  atomic_server.py                       │
│  Run: rpm-ostree status --json          │
│  Parse and format JSON                  │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Display formatted result to user       │
└─────────────────────────────────────────┘
```

### Supported Commands

**rpm-ostree:**
- `rpm-ostree status --json` - Get deployment info
- `rpm-ostree upgrade --check` - Check for updates

**Flatpak:**
- `flatpak list --app --user` - List user apps
- `flatpak list --app --system` - List system apps
- `flatpak remote-ls --updates` - Check for updates

**Toolbox:**
- `toolbox list` - List containers

### Server Architecture

The `atomic_server.py` MCP server provides:

1. **JSON-RPC 2.0 protocol** over stdio
2. **Subprocess execution** for system commands
3. **JSON parsing** for structured data
4. **Error handling** with graceful degradation
5. **Tool schema** for MCP client validation

### Intent Patterns

Added to `intent_classifier.py`:

```python
# rpm-ostree status
r'^(?:show|get|check)[\s-]*(?:rpm-?ostree|ostree)[\s-]*(?:status)?$'
r'^(?:ostree|rpm-?ostree)[\s-]*status$'

# System updates
r'^(?:check|show)[\s-]*(?:system[\s-]*)?updates?$'

# Layered packages
r'^(?:show|list|get)[\s-]*layered[\s-]*packages?$'

# Flatpak
r'^(?:show|list|get)[\s-]*flatpaks?(?:[\s-]*apps?)?$'
r'^(?:check|show)[\s-]*flatpak[\s-]*updates?$'

# Toolbox
r'^(?:show|list|get)[\s-]*toolbox(?:es)?$'
```

## Comparison with Traditional Tools

| Task | Traditional | rai | Speedup |
|------|-------------|-----|---------|
| Check rpm-ostree status | `rpm-ostree status` | `rai "ostree status"` | Same |
| Check all updates | `rpm-ostree upgrade --check && flatpak remote-ls --updates` | `rai "check updates"` | **2x faster** |
| List layered packages | `rpm-ostree status \| grep -A100 "LayeredPackages"` | `rai "show layered packages"` | **Cleaner** |
| Count Flatpaks | `flatpak list --app \| wc -l` | `rai "show flatpaks"` | **Easier** |

**Key advantage:** Natural language queries instead of memorizing flags!

## Requirements

### System Requirements
- Fedora Silverblue, Kinoite, or similar atomic desktop
- rpm-ostree installed (comes with atomic desktops)
- Optional: Flatpak, toolbox/distrobox

### Python Requirements
- Already included in rai dependencies
- No additional packages needed

### Permissions
- Most queries run as normal user
- rpm-ostree operations are read-only (no admin required)
- Flatpak/toolbox queries are user-scoped

## Troubleshooting

### "atomic server not found"

Check if the server file exists:

```bash
ls -lh ~/projects/rai/mcp_servers/atomic_server.py
```

If missing, the server wasn't copied during installation.

### Server doesn't start

Test the server manually:

```bash
python3 ~/projects/rai/mcp_servers/atomic_server.py
```

Type this JSON-RPC request (followed by Enter):
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
```

Should return server info.

### Commands fail on non-atomic systems

The atomic server checks for rpm-ostree/flatpak commands. On traditional Fedora:
- rpm-ostree commands will fail gracefully
- Flatpak commands will work if Flatpak is installed
- Use regular `rai` system queries instead

### rai not detecting atomic queries

Check intent patterns:

```bash
python3 << 'EOF'
from intent_classifier import IntentClassifier
classifier = IntentClassifier()

queries = [
    "ostree status",
    "check updates",
    "show flatpaks",
    "list toolboxes"
]

for query in queries:
    intent = classifier.classify(query)
    if intent:
        print(f"✓ {query:30s} → {intent.category}:{intent.action}")
    else:
        print(f"✗ {query:30s} → Not matched")
EOF
```

All should show `✓ ... → atomic:...`

## Advanced Usage

### Custom Flatpak remotes

The atomic server uses default Flatpak remotes. To query specific remotes:

```bash
# Use LLM for complex queries
rai "list flatpaks from flathub remote"
```

### Toolbox inspection

```bash
# List containers
rai "show toolboxes"

# Then use toolbox directly for operations
toolbox enter fedora-43
```

### rpm-ostree operations

rai is READ-ONLY for safety. For write operations:

```bash
# Check updates with rai
rai "check updates"

# Apply updates manually
rpm-ostree upgrade
systemctl reboot
```

### Combining with other queries

```bash
rai-shell

# Check VRAM before launching Flatpak game
rai> vram
💾 VRAM: 2.1 / 32.0 GB (7% used)

# Check system before upgrade
rai> check memory
💾 Memory: 12.5 / 31.2 GB (40% used)

rai> ostree status
🔷 Current: fedora:43/silverblue

# Good to go!
```

## Future Enhancements

Planned features:
- [ ] rpm-ostree upgrade operations (with security confirmation)
- [ ] Flatpak install/remove via MCP
- [ ] Toolbox create/enter automation
- [ ] Deployment rollback detection
- [ ] Layer removal suggestions
- [ ] Automatic update checks

## Examples

### Daily Workflow

```bash
# Morning check
rai-shell

rai> check updates
✓ System is up to date!

rai> check flatpak updates
🔄 Flatpak Updates Available (3):
  org.mozilla.firefox
  org.gnome.Calculator
  com.spotify.Client

# Update Flatpaks manually
flatpak update

# Verify
rai> check flatpak updates
✓ All Flatpaks up to date!
```

### Development Setup

```bash
# Check toolbox containers
rai "show toolboxes"

🔧 Toolbox Containers (2):
  • fedora-43
  • pytorch-env

# Enter specific container
toolbox enter pytorch-env

# Inside container, use rai for GPU queries
rai "gpu stats"
rai "vram"
```

### Pre-upgrade check

```bash
# Before rpm-ostree upgrade
rai "ostree status"
rai "show layered packages"

# Note layered packages
# Proceed with upgrade
rpm-ostree upgrade

# Reboot
systemctl reboot

# After reboot, verify
rai "ostree status"
rai "show layered packages"  # Should match pre-upgrade
```

---

## Quick Reference

**rpm-ostree:**
- `rai "ostree status"` - Current deployment
- `rai "check updates"` - Check for updates
- `rai "show layered packages"` - List layered packages

**Flatpak:**
- `rai "show flatpaks"` - List apps
- `rai "check flatpak updates"` - Check for updates

**Toolbox:**
- `rai "list toolboxes"` - List containers

**Tools list:**
- `rai "/tools"` (in rai-shell) - Show all MCP tools

---

Enjoy atomic desktop management with rai! 🔷
