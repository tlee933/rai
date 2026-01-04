#!/usr/bin/env python3
"""
Security configuration for rai
Supports three modes: mild, wild, unrestricted
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SecurityMode(Enum):
    """Security posture for rai"""
    MILD = "mild"           # PolicyKit, fine-grained permissions
    WILD = "wild"           # SUDO_ASKPASS, interactive prompts
    UNRESTRICTED = "unrestricted"  # NOPASSWD sudo, full automation


@dataclass
class SecurityConfig:
    """Security configuration"""
    mode: SecurityMode
    askpass_path: str = os.path.expanduser("~/.local/bin/rai-askpass")
    polkit_rules_path: str = "/etc/polkit-1/rules.d/50-rai.rules"

    # Command whitelists for each mode
    safe_commands: List[str] = None
    privileged_commands: List[str] = None
    destructive_patterns: List[str] = None

    def __post_init__(self):
        if self.safe_commands is None:
            self.safe_commands = [
                # Read-only ROCm commands
                'rocm-smi', 'rocminfo', 'rocm-bandwidth-test',
                # Safe system queries
                'systemctl status', 'systemctl is-active', 'systemctl is-enabled',
                'journalctl', 'lsusb', 'lspci', 'sensors',
                # Package queries (no install/remove)
                'dnf list', 'dnf info', 'dnf search', 'rpm -q',
                # Process/network queries
                'ps', 'top', 'ss', 'netstat',
            ]

        if self.privileged_commands is None:
            self.privileged_commands = [
                # Service management (specific services only)
                'systemctl restart llama-server',
                'systemctl start llama-server',
                'systemctl stop llama-server',
                'systemctl restart ollama',
                # ROCm power management
                'rocm-smi --setpoweroverdrive',
                'rocm-smi --setprofile',
                # File operations in /tmp
                'tee /tmp/',
            ]

        if self.destructive_patterns is None:
            self.destructive_patterns = [
                r'rm\s+-rf\s+/',                    # rm -rf /
                r'rm\s+-rf\s+~',                    # rm -rf ~
                r'rm\s+-rf\s+\$HOME',               # rm -rf $HOME
                r'mkfs\.',                           # mkfs.ext4, mkfs.btrfs, etc
                r'dd\s+.*of=/dev/',                  # dd to block device
                r'systemctl\s+stop\s+(sshd|network|NetworkManager)',  # Critical services
                r'systemctl\s+disable\s+(sshd|network|NetworkManager)',
                r'reboot',                           # System reboot
                r'shutdown',                         # System shutdown
                r'poweroff',                         # System poweroff
                r'fdisk|parted|gdisk',              # Partition tools
                r'wipefs',                           # Filesystem wipe
                r'shred',                            # Secure delete
                r'chmod\s+-R\s+777\s+/',            # Dangerous permissions
                r'chown\s+-R\s+.*\s+/',             # Dangerous ownership
            ]


class SecurityManager:
    """Manages command execution based on security mode"""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def classify_command(self, cmd: str) -> Tuple[str, str]:
        """
        Classify command as: safe, privileged, or destructive
        Returns: (classification, reason)
        """
        # Check destructive patterns first
        for pattern in self.config.destructive_patterns:
            if re.search(pattern, cmd, re.IGNORECASE):
                return ("destructive", f"Matches pattern: {pattern}")

        # Check if it's a whitelisted safe command
        for safe_cmd in self.config.safe_commands:
            if cmd.startswith(safe_cmd):
                return ("safe", "Whitelisted safe command")

        # Check if it's a whitelisted privileged command
        for priv_cmd in self.config.privileged_commands:
            if cmd.startswith(priv_cmd):
                return ("privileged", "Whitelisted privileged command")

        # Default: treat unknown commands as privileged
        return ("privileged", "Unknown command, requires privileges")

    async def execute_command(self, cmd: str, confirm_destructive: bool = True) -> Tuple[bool, str]:
        """
        Execute command based on security mode
        Returns: (success, output)
        """
        classification, reason = self.classify_command(cmd)

        # Handle destructive commands
        if classification == "destructive":
            if confirm_destructive:
                print(f"\n⚠️  DESTRUCTIVE COMMAND DETECTED")
                print(f"   Command: {cmd}")
                print(f"   Reason: {reason}")
                response = input("   Continue? [y/N]: ").strip().lower()
                if response != 'y':
                    return (False, "Command cancelled by user")
            else:
                return (False, f"Destructive command blocked: {reason}")

        # Execute based on mode
        if self.config.mode == SecurityMode.MILD:
            return await self._execute_mild(cmd, classification)
        elif self.config.mode == SecurityMode.WILD:
            return await self._execute_wild(cmd, classification)
        else:  # UNRESTRICTED
            return await self._execute_unrestricted(cmd)

    async def _execute_mild(self, cmd: str, classification: str) -> Tuple[bool, str]:
        """Execute with PolicyKit (pkexec)"""
        if classification == "safe":
            # Run directly without privileges
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True
            )
        else:
            # Use pkexec for privileged commands
            result = subprocess.run(
                ["pkexec", "sh", "-c", cmd],
                capture_output=True, text=True
            )

        return (result.returncode == 0, result.stdout or result.stderr)

    async def _execute_wild(self, cmd: str, classification: str) -> Tuple[bool, str]:
        """Execute with SUDO_ASKPASS"""
        if classification == "safe":
            # Run directly without privileges
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True
            )
        else:
            # Use sudo -A with askpass
            env = os.environ.copy()
            env["SUDO_ASKPASS"] = self.config.askpass_path

            result = subprocess.run(
                ["sudo", "-A", "sh", "-c", cmd],
                capture_output=True, text=True, env=env
            )

        return (result.returncode == 0, result.stdout or result.stderr)

    async def _execute_unrestricted(self, cmd: str) -> Tuple[bool, str]:
        """Execute with passwordless sudo"""
        result = subprocess.run(
            ["sudo", "sh", "-c", cmd],
            capture_output=True, text=True
        )
        return (result.returncode == 0, result.stdout or result.stderr)


def load_config() -> SecurityConfig:
    """Load security configuration from file or environment"""
    config_file = Path.home() / ".config" / "rai" / "security.conf"

    # Default mode
    mode = SecurityMode.UNRESTRICTED

    # Try to load from config file
    if config_file.exists():
        try:
            content = config_file.read_text().strip()
            mode = SecurityMode(content)
        except (ValueError, OSError):
            pass

    # Environment variable override
    env_mode = os.getenv("RAI_SECURITY_MODE")
    if env_mode:
        try:
            mode = SecurityMode(env_mode)
        except ValueError:
            pass

    return SecurityConfig(mode=mode)


def save_config(config: SecurityConfig):
    """Save security configuration to file"""
    config_dir = Path.home() / ".config" / "rai"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "security.conf"
    config_file.write_text(config.mode.value + "\n")
    print(f"✓ Security mode saved: {config.mode.value}")


def setup_mild_mode():
    """Setup PolicyKit rules for mild mode"""
    rules_content = """// PolicyKit rules for rai (ROCm CLI)
// Allows hashcat user to run specific ROCm commands without password

polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.policykit.exec" &&
        subject.user == "%USERNAME%") {

        var program = action.lookup("program");
        var command_line = action.lookup("command_line");

        // Whitelist ROCm read-only commands
        if (program == "/opt/rocm/bin/rocm-smi" ||
            program == "/opt/rocm/bin/rocminfo" ||
            program == "/opt/rocm/bin/rocm-bandwidth-test") {
            return polkit.Result.YES;
        }

        // Whitelist systemctl status queries
        if (program == "/usr/bin/systemctl" &&
            (command_line.indexOf("status") >= 0 ||
             command_line.indexOf("is-active") >= 0 ||
             command_line.indexOf("is-enabled") >= 0)) {
            return polkit.Result.YES;
        }

        // Whitelist llama-server management
        if (program == "/usr/bin/systemctl" &&
            (command_line.indexOf("llama-server") >= 0 ||
             command_line.indexOf("ollama") >= 0)) {
            return polkit.Result.YES;
        }
    }

    return polkit.Result.NOT_HANDLED;
});
"""

    # Replace username
    import getpass
    username = getpass.getuser()
    rules_content = rules_content.replace("%USERNAME%", username)

    print("\n📋 PolicyKit Rules for Mild Mode:")
    print("="*70)
    print(rules_content)
    print("="*70)
    print("\nTo install, run:")
    print(f"  sudo tee /etc/polkit-1/rules.d/50-rai.rules << 'EOF'")
    print(rules_content)
    print("EOF")
    print(f"  sudo systemctl restart polkit")


def setup_wild_mode():
    """Setup SUDO_ASKPASS for wild mode"""
    askpass_script = """#!/bin/bash
# rai askpass script - terminal password prompt
echo "🔐 rai requires elevated privileges" >&2
systemd-ask-password "Password for ${USER}:"
"""

    askpass_path = Path.home() / ".local" / "bin" / "rai-askpass"
    askpass_path.parent.mkdir(parents=True, exist_ok=True)
    askpass_path.write_text(askpass_script)
    askpass_path.chmod(0o755)

    print(f"✓ Created askpass script: {askpass_path}")
    print(f"\nAdd to ~/.zshrc:")
    print(f"  export SUDO_ASKPASS=\"{askpass_path}\"")


def get_mode_info(mode: SecurityMode) -> str:
    """Get description of security mode"""
    descriptions = {
        SecurityMode.MILD: """
🛡️  MILD MODE - PolicyKit with Fine-Grained Permissions
   - Whitelisted commands run without password
   - Unknown commands require PolicyKit authentication
   - Best for: Production, shared systems, maximum security
   - Setup required: PolicyKit rules installation
""",
        SecurityMode.WILD: """
⚡ WILD MODE - SUDO_ASKPASS with Interactive Prompts
   - Safe commands run directly
   - Privileged commands prompt for password
   - Destructive commands require confirmation
   - Best for: Development workstations, interactive use
   - Setup required: SUDO_ASKPASS script installation
""",
        SecurityMode.UNRESTRICTED: """
🚀 UNRESTRICTED MODE - Passwordless Sudo
   - All commands run with sudo automatically
   - Zero friction, maximum automation
   - Destructive commands still prompt for confirmation
   - Best for: Personal systems, AI agent autonomy
   - Setup required: /etc/sudoers.d/username-nopasswd
"""
    }
    return descriptions.get(mode, "Unknown mode")
