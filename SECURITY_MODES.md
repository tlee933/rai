# rai Security Modes

**rai** now supports three switchable security postures for privilege escalation:

## Quick Commands

```bash
# Check current mode
rai-security status

# List all modes
rai-security list

# Switch modes
rai-security set mild
rai-security set wild
rai-security set unrestricted

# Setup helpers
rai-security setup-mild    # Generate PolicyKit rules
rai-security setup-wild    # Create SUDO_ASKPASS script
```

## Mode Details

### 🛡️  MILD - PolicyKit with Fine-Grained Permissions

**Best for:** Production environments, shared systems, maximum security

**How it works:**
- Whitelisted commands run without password (rocm-smi, rocminfo, systemctl status)
- Unknown commands require PolicyKit GUI/terminal authentication
- Most restrictive, most secure

**Setup:**
```bash
rai-security set mild
rai-security setup-mild  # Generates PolicyKit rules

# Then install rules:
sudo tee /etc/polkit-1/rules.d/50-rai.rules << 'EOF'
[paste generated rules]
EOF
sudo systemctl restart polkit
```

**Whitelisted commands (no password):**
- `/opt/rocm/bin/rocm-smi`, `rocminfo`, `rocm-bandwidth-test`
- `systemctl status`, `is-active`, `is-enabled`
- `systemctl` operations on `llama-server`, `ollama`

---

### ⚡ WILD - SUDO_ASKPASS with Interactive Prompts

**Best for:** Development workstations, interactive use (RECOMMENDED)

**How it works:**
- Safe commands (read-only) run directly without privileges
- Privileged commands prompt for password via terminal
- Destructive commands require explicit confirmation
- Good balance of security and convenience

**Setup:**
```bash
rai-security set wild
rai-security setup-wild  # Creates askpass script

# Add to ~/.zshrc (auto-added):
export SUDO_ASKPASS="$HOME/.local/bin/rai-askpass"

# Reload shell
source ~/.zshrc
```

**Command classification:**
- **Safe (no prompt):** `rocm-smi`, `rocminfo`, `systemctl status`, `journalctl`, `ps`, `dnf info`
- **Privileged (password):** `systemctl restart`, ROCm power management, writes to /tmp
- **Destructive (confirm):** `rm -rf`, `mkfs`, `dd`, `reboot`, `shutdown`, partition tools

---

### 🚀 UNRESTRICTED - Passwordless Sudo

**Best for:** Personal systems, AI agent autonomy, maximum automation

**How it works:**
- All commands run with `sudo` automatically
- Zero friction, no password prompts
- Destructive commands still require confirmation
- Current default for personal development

**Setup:**
```bash
rai-security set unrestricted

# Requires /etc/sudoers.d/hashcat-nopasswd:
hashcat ALL=(ALL) NOPASSWD:ALL

# Already configured on this system ✓
```

---

## Security Features (All Modes)

### Destructive Command Protection

All modes detect and warn about dangerous operations:

```bash
rai "remove everything in root"
# ⚠️  DESTRUCTIVE COMMAND DETECTED
#    Command: rm -rf /
#    Reason: Matches pattern: rm\s+-rf\s+/
#    Continue? [y/N]:
```

**Patterns detected:**
- `rm -rf /`, `rm -rf ~`, `rm -rf $HOME`
- `mkfs.*`, `dd of=/dev/*`, `fdisk`, `parted`, `gdisk`
- `systemctl stop sshd|network|NetworkManager`
- `reboot`, `shutdown`, `poweroff`
- `wipefs`, `shred`
- `chmod -R 777 /`, `chown -R root /`

### Command Whitelisting

Safe commands run without privilege escalation (varies by mode):

**Read-only operations:**
- `rocm-smi`, `rocminfo`, `rocm-bandwidth-test`
- `systemctl status`, `journalctl`
- `dnf list/info/search`, `rpm -q`
- `ps`, `top`, `ss`, `netstat`
- `lsusb`, `lspci`, `sensors`

**Whitelisted privileged operations:**
- `systemctl restart llama-server`
- `systemctl start/stop/restart ollama`
- `rocm-smi --setpoweroverdrive`, `--setprofile`
- File writes to `/tmp/`

---

## Configuration

### Config file location:
```
~/.config/rai/security.conf
```

### Environment variable override:
```bash
export RAI_SECURITY_MODE=wild
```

### Mode indicator in rai output:
```bash
rai "gpu stats"
# ✓ rocm-cli initialized [⚡ wild mode]
```

---

## Examples

### Check GPU stats (safe command):
```bash
rai "gpu stats"
# No password required in any mode
```

### Restart llama-server (privileged):
```bash
# WILD mode:
rai "restart llama-server"
# 🔐 rai requires elevated privileges
# Password for hashcat: [enter password]

# UNRESTRICTED mode:
rai "restart llama-server"
# Runs immediately with sudo

# MILD mode:
rai "restart llama-server"
# PolicyKit GUI/terminal prompt
```

### Dangerous operation (destructive):
```bash
rai "delete everything"
# ⚠️  DESTRUCTIVE COMMAND DETECTED
#    Command: rm -rf /
#    Reason: Matches pattern: rm\s+-rf\s+/
#    Continue? [y/N]: n
# Command cancelled by user
```

---

## Recommendations

**For personal development systems:**
- Start with **WILD** mode (best balance)
- Upgrade to UNRESTRICTED if password prompts become annoying
- Downgrade to MILD if sharing system with others

**For production/shared systems:**
- Use **MILD** mode exclusively
- Set up PolicyKit rules for common operations
- Audit all command executions

**For AI agent automation:**
- Use **UNRESTRICTED** mode
- Rely on destructive command detection for safety
- Monitor command execution logs

---

## Implementation Details

### Files created:
- `security_config.py` - Core security logic (418 lines)
- `rai-security` - Mode management CLI
- `~/.local/bin/rai-askpass` - SUDO_ASKPASS script (Wild mode)
- `~/.config/rai/security.conf` - Mode configuration

### Integration:
- SecurityManager integrated into rai.py
- Command classification before execution
- Mode-specific privilege escalation
- Visual mode indicator in initialization

### Architecture:
```
User Query → Intent Classifier → SecurityManager
                                       ↓
                         [Classify: safe/privileged/destructive]
                                       ↓
                         Execute based on security mode:
                         - MILD: pkexec
                         - WILD: sudo -A (askpass)
                         - UNRESTRICTED: sudo
```

---

## Current Status

✓ All three modes implemented and tested
✓ Wild mode active (recommended)
✓ SUDO_ASKPASS configured
✓ Destructive command detection active
✓ Command whitelisting functional

**Current mode:** ⚡ WILD

Switch anytime with:
```bash
rai-security set <mild|wild|unrestricted>
```
