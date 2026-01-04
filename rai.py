#!/usr/bin/env python3
"""
rocm-cli (rai) - Terminal-native AI Agent
Natural language interface for Fedora/ROCm development workflows
ROCm AI - Your GPU assistant
"""

import sys
import asyncio
import json
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any

from intent_classifier import IntentClassifier, Intent
from mcp_client import MCPClient, MCPServerConfig
from security_config import SecurityManager, load_config, get_mode_info

# Rich library for beautiful terminal output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for beautiful terminal output: pip install rich")


# ROCm CLI Color scheme
COLORS = {
    'primary': 'cyan',           # ROCm cyan
    'secondary': 'bright_blue',
    'success': 'bright_green',
    'warning': 'yellow',
    'error': 'red',
    'code': 'blue',
}


class ROCmCLIAgent:
    """Main AI agent coordinating all operations"""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.classifier = IntentClassifier()
        self.mcp_client: Optional[MCPClient] = None
        self.llama_server_url = "http://127.0.0.1:8080/v1/chat/completions"

        # Security configuration
        self.security_config = load_config()
        self.security_manager = SecurityManager(self.security_config)

    async def initialize(self):
        """Initialize MCP servers and connections"""
        self.mcp_client = MCPClient()

        # Add filesystem server
        await self.mcp_client.add_server(MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp", "/home/hashcat", "/opt/rocm"]
        ))

        # Add ROCm GPU server
        # Resolve symlink to get real file path
        real_file = Path(__file__).resolve()
        rocm_server_path = real_file.parent / "mcp_servers" / "rocm_server.py"
        await self.mcp_client.add_server(MCPServerConfig(
            name="rocm",
            command="python3",
            args=[str(rocm_server_path)]
        ))

        # Add Linux system server (RHEL Lightspeed)
        linux_mcp_path = Path.home() / ".local" / "bin" / "linux-mcp-server"
        if linux_mcp_path.exists():
            await self.mcp_client.add_server(MCPServerConfig(
                name="linux",
                command=str(linux_mcp_path),
                args=[],
                env={
                    "LINUX_MCP_ALLOWED_LOG_PATHS": "/var/log/messages,/var/log/journal,/home/hashcat/TheRock,/var/log",
                    "LINUX_MCP_LOG_LEVEL": "ERROR",
                    "LINUX_MCP_USER": "hashcat",
                }
            ))

        # Add Atomic Desktop server (rpm-ostree, Flatpak, toolbox)
        atomic_server_path = real_file.parent / "mcp_servers" / "atomic_server.py"
        if atomic_server_path.exists():
            await self.mcp_client.add_server(MCPServerConfig(
                name="atomic",
                command="python3",
                args=[str(atomic_server_path)]
            ))

        # Add Universal Blue server (UBlue, Bazzite, Aurora, image building)
        ublue_server_path = real_file.parent / "mcp_servers" / "ublue_server.py"
        if ublue_server_path.exists():
            await self.mcp_client.add_server(MCPServerConfig(
                name="ublue",
                command="python3",
                args=[str(ublue_server_path)]
            ))

        # Show security mode
        mode_icon = {
            "mild": "🛡️ ",
            "wild": "⚡",
            "unrestricted": "🚀"
        }.get(self.security_config.mode.value, "")

        self._print_success(f"rocm-cli initialized [{mode_icon} {self.security_config.mode.value} mode]")

    async def process_query(self, query: str) -> str:
        """Main query processing pipeline"""

        # 1. Try fast intent classification
        intent = self.classifier.classify(query)

        if intent:
            # Fast path: Execute directly via MCP
            return await self._execute_intent(intent)
        else:
            # Slow path: Use LLM for complex queries
            return await self._query_llm(query)

    async def _execute_intent(self, intent: Intent) -> str:
        """Execute a classified intent via MCP tools"""

        # Map intents to MCP tool calls
        if intent.category == 'file':
            return await self._handle_file_intent(intent)
        elif intent.category == 'gpu':
            return await self._handle_gpu_intent(intent)
        elif intent.category == 'git':
            return await self._handle_git_intent(intent)
        elif intent.category == 'system':
            return await self._handle_system_intent(intent)
        elif intent.category == 'atomic':
            return await self._handle_atomic_intent(intent)
        elif intent.category == 'ublue':
            return await self._handle_ublue_intent(intent)
        else:
            # Fallback to LLM
            return await self._query_llm(f"Execute: {intent.category} {intent.action}")

    async def _handle_file_intent(self, intent: Intent) -> str:
        """Handle file operations via filesystem MCP server"""

        if intent.action == 'read':
            path = intent.params['path']
            result = await self.mcp_client.call_tool("filesystem", "read_file", {"path": path})
            return self._format_file_content(path, result)

        elif intent.action == 'list':
            path = intent.params['path']
            result = await self.mcp_client.call_tool("filesystem", "list_directory", {"path": path})
            return self._format_directory_list(path, result)

        elif intent.action == 'search':
            pattern = intent.params['pattern']
            path = intent.params.get('path', '.')
            result = await self.mcp_client.call_tool("filesystem", "search_files", {
                "path": path,
                "pattern": pattern
            })
            return self._format_search_results(pattern, result)

        return "File operation not implemented yet"

    async def _handle_gpu_intent(self, intent: Intent) -> str:
        """Handle GPU/ROCm queries via ROCm MCP server"""

        # Map action to ROCm server tool
        if intent.action == 'stats':
            result = await self.mcp_client.call_tool("rocm", "get_gpu_stats", {})
            return self._format_gpu_stats(result)
        elif intent.action == 'vram':
            result = await self.mcp_client.call_tool("rocm", "get_vram", {})
            return self._format_vram_info(result)
        elif intent.action == 'temp':
            result = await self.mcp_client.call_tool("rocm", "get_gpu_temp", {})
            return self._format_temp_info(result)
        else:
            # Default: show full stats
            result = await self.mcp_client.call_tool("rocm", "get_gpu_stats", {})
            return self._format_gpu_stats(result)

    async def _handle_git_intent(self, intent: Intent) -> str:
        """Handle git operations"""
        # This would use git MCP server
        # For now, delegate to LLM
        query = f"Run git {intent.action}"
        return await self._query_llm(query)

    async def _handle_system_intent(self, intent: Intent) -> str:
        """Handle system queries via linux-mcp-server"""

        if intent.action == 'memory':
            result = await self.mcp_client.call_tool("linux", "get_memory_information", {})
            return self._format_memory_info(result)

        elif intent.action == 'disk':
            result = await self.mcp_client.call_tool("linux", "get_disk_usage", {})
            return self._format_disk_info(result)

        elif intent.action == 'service_status':
            service = intent.params.get('service', '')
            result = await self.mcp_client.call_tool("linux", "get_service_status", {"service_name": service})
            return f"\\n🔧 Service: {service}\\n{'='*70}\\n{result}\\n"

        elif intent.action == 'list_services':
            result = await self.mcp_client.call_tool("linux", "list_services", {})
            return f"\\n🔧 Systemd Services:\\n{'='*70}\\n{result}\\n"

        elif intent.action == 'processes':
            result = await self.mcp_client.call_tool("linux", "list_processes", {})
            return f"\\n📊 Running Processes:\\n{'='*70}\\n{result[:2000]}\\n"

        elif intent.action == 'logs':
            filter_str = intent.params.get('filter')
            args = {"lines": 50}
            if filter_str:
                args["filter"] = filter_str
            result = await self.mcp_client.call_tool("linux", "get_journal_logs", args)
            return f"\\n📋 System Logs:\\n{'='*70}\\n{result[:2000]}\\n"

        # Fallback to LLM for unhandled system queries
        query = f"Get {intent.action} information"
        return await self._query_llm(query)

    async def _handle_atomic_intent(self, intent: Intent) -> str:
        """Handle atomic desktop queries via atomic MCP server"""

        if intent.action == 'ostree_status':
            result = await self.mcp_client.call_tool("atomic", "get_rpm_ostree_status", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)
            return f"\n🔷 rpm-ostree Status:\n{'='*70}\n{data.get('details', 'N/A')}\n"

        elif intent.action == 'check_updates':
            result = await self.mcp_client.call_tool("atomic", "check_rpm_ostree_updates", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            if data.get('updates_available'):
                return f"\n🔄 Updates Available!\n{'='*70}\n{data.get('details', 'Check failed')}\n"
            else:
                return f"\n✓ System is up to date!\n"

        elif intent.action == 'layered_packages':
            result = await self.mcp_client.call_tool("atomic", "list_layered_packages", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)
            packages = data.get('packages', [])

            if packages:
                return f"\n📦 Layered Packages ({len(packages)}):\n{'='*70}\n" + "\n".join(f"  • {pkg}" for pkg in packages) + "\n"
            else:
                return "\n📦 No layered packages\n"

        elif intent.action == 'flatpaks':
            result = await self.mcp_client.call_tool("atomic", "list_flatpaks", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            output = f"\n📱 Flatpak Applications:\n{'='*70}\n"
            output += f"User apps: {data.get('user_flatpaks', 0)}\n"
            output += f"System apps: {data.get('system_flatpaks', 0)}\n"
            output += f"Total: {data.get('total', 0)}\n"

            if data.get('user_apps'):
                output += "\nUser apps (first 10):\n"
                output += "\n".join(f"  • {app}" for app in data['user_apps'])

            return output + "\n"

        elif intent.action == 'flatpak_updates':
            result = await self.mcp_client.call_tool("atomic", "get_flatpak_updates", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            if data.get('updates_available'):
                return f"\n🔄 Flatpak Updates Available ({data.get('count', 0)}):\n{'='*70}\n" + "\n".join(data.get('updates', [])) + "\n"
            else:
                return "\n✓ All Flatpaks up to date!\n"

        elif intent.action == 'toolboxes':
            result = await self.mcp_client.call_tool("atomic", "list_toolboxes", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)
            containers = data.get('containers', [])

            if containers:
                output = f"\n🔧 Toolbox Containers ({len(containers)}):\n{'='*70}\n"
                output += "\n".join(f"  • {c['name']}" for c in containers)
                return output + "\n"
            else:
                return "\n🔧 No toolbox containers\n"

        # Fallback to LLM
        query = f"Get atomic desktop {intent.action} information"
        return await self._query_llm(query)

    async def _handle_ublue_intent(self, intent: Intent) -> str:
        """Handle Universal Blue queries via ublue MCP server"""

        if intent.action == 'image_info':
            result = await self.mcp_client.call_tool("ublue", "get_image_info", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            output = "\n🔵 Universal Blue Image:\n" + "="*70 + "\n"
            output += f"Image:    {data.get('image', 'unknown')}\n"
            output += f"Version:  {data.get('version', 'unknown')}\n"
            output += f"Deployed: {data.get('deployed', 'unknown')}\n"
            output += f"Layered:  {data.get('layered_packages', 0)} packages\n"

            if data.get('packages'):
                output += "\nLayered packages:\n"
                output += "\n".join(f"  • {pkg}" for pkg in data['packages'][:10])
                if data.get('layered_packages', 0) > 10:
                    output += f"\n  ... and {data['layered_packages'] - 10} more"

            return output + "\n"

        elif intent.action == 'image_updates':
            result = await self.mcp_client.call_tool("ublue", "check_image_updates", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            if data.get('updates_available'):
                return f"\n🔄 Updates Available!\n{'='*70}\n{data.get('details', 'Unknown')}\n"
            else:
                return f"\n✓ Image is up to date: {data.get('current_image', 'unknown')}\n"

        elif intent.action == 'build_type':
            result = await self.mcp_client.call_tool("ublue", "check_build_type", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            output = "\n🔵 System Variant:\n" + "="*70 + "\n"
            output += f"Variant:      {data.get('variant', 'unknown')}\n"
            output += f"Name:         {data.get('name', 'unknown')}\n"
            output += f"Version:      {data.get('version', 'unknown')}\n"
            output += f"Pretty Name:  {data.get('pretty_name', 'unknown')}\n"

            return output + "\n"

        elif intent.action == 'list_recipes':
            result = await self.mcp_client.call_tool("ublue", "list_ujust_recipes", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            recipes = data.get('recipes', [])
            if not recipes:
                return "\n📜 No ujust recipes available (ujust not installed)\n"

            output = f"\n📜 ujust Recipes ({len(recipes)}):\n" + "="*70 + "\n"
            for recipe in recipes:
                name = recipe.get('name', '')
                desc = recipe.get('description', '')
                if desc:
                    output += f"  • {name:30s} - {desc}\n"
                else:
                    output += f"  • {name}\n"

            return output + "\n"

        elif intent.action == 'run_recipe':
            recipe = intent.params.get('recipe', '')
            result = await self.mcp_client.call_tool("ublue", "run_ujust_recipe", {'recipe': recipe})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            if 'error' in data:
                return f"\n❌ Recipe Error:\n{'='*70}\n{data['error']}\n"

            return f"\n✓ Recipe '{recipe}' executed:\n{'='*70}\n{data.get('output', 'No output')}\n"

        elif intent.action == 'gaming_status':
            result = await self.mcp_client.call_tool("ublue", "get_gaming_status", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            output = "\n🎮 Gaming Status:\n" + "="*70 + "\n"
            output += f"Steam:     {'✓ Installed' if data.get('steam_installed') else '✗ Not installed'}\n"
            output += f"GameMode:  {'✓ Installed' if data.get('gamemode_installed') else '✗ Not installed'}\n"
            output += f"MangoHud:  {'✓ Installed' if data.get('mangohud_installed') else '✗ Not installed'}\n"
            output += f"Lutris:    {'✓ Installed' if data.get('lutris_installed') else '✗ Not installed'}\n"

            proton = data.get('proton_versions', [])
            if proton:
                output += f"\nProton versions ({len(proton)}):\n"
                output += "\n".join(f"  • {v}" for v in proton[:5])
                if len(proton) > 5:
                    output += f"\n  ... and {len(proton) - 5} more"

            return output + "\n"

        elif intent.action == 'build_tools':
            result = await self.mcp_client.call_tool("ublue", "check_build_tools", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            output = "\n🔨 Build Tools:\n" + "="*70 + "\n"
            output += f"bootc:    {'✓ Available' if data.get('bootc') else '✗ Not available'}\n"
            output += f"podman:   {'✓ Available' if data.get('podman') else '✗ Not available'}\n"
            output += f"buildah:  {'✓ Available' if data.get('buildah') else '✗ Not available'}\n"
            output += f"mkosi:    {'✓ Available' if data.get('mkosi') else '✗ Not available'}\n"
            output += f"lorax:    {'✓ Available' if data.get('lorax') else '✗ Not available'}\n"
            output += f"\nCan build containers: {'Yes' if data.get('can_build_containers') else 'No'}\n"
            output += f"Can build ISOs:       {'Yes' if data.get('can_build_isos') else 'No'}\n"

            return output + "\n"

        elif intent.action == 'list_images':
            result = await self.mcp_client.call_tool("ublue", "list_container_images", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            images = data.get('ublue_images', [])
            if not images:
                return "\n📦 No UBlue container images found locally\n"

            output = f"\n📦 UBlue Container Images ({len(images)}):\n" + "="*70 + "\n"
            for img in images:
                output += f"  • {img.get('name', 'unknown')}\n"
                output += f"    ID: {img.get('id', 'unknown')}, Size: {img.get('size', 0)} bytes\n"

            return output + "\n"

        elif intent.action == 'containerfile_template':
            variant = intent.params.get('variant', 'base')
            result = await self.mcp_client.call_tool("ublue", "get_containerfile_template", {'variant': variant})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            return f"\n📝 Containerfile Template ({variant}):\n{'='*70}\n{data.get('template', 'No template')}\n"

        elif intent.action == 'github_workflow':
            result = await self.mcp_client.call_tool("ublue", "get_github_workflow_template", {})
            data = json.loads(result[0]['text']) if isinstance(result, list) else json.loads(result)

            return f"\n⚙️ GitHub Actions Workflow:\n{'='*70}\n{data.get('workflow', 'No workflow')}\n"

        # Fallback to LLM
        return await self._query_llm(f"Get Universal Blue {intent.action} information")

    async def _query_llm(self, query: str) -> str:
        """Query the LLM for complex questions"""

        # Get available MCP tools for context
        tools_info = ""
        if self.mcp_client:
            all_tools = self.mcp_client.get_all_tools()
            tools_info = "\n\nAvailable tools:\n"
            for server, tools in all_tools.items():
                tools_info += f"{server}: {', '.join(tools)}\n"

        system_prompt = f"""You are rocm-cli (rai), a terminal-native AI assistant for Fedora/ROCm development.

System Info:
- OS: Fedora 43
- GPU: AMD Radeon AI PRO R9700 (gfx1201, 32GB VRAM)
- ROCm: 7.11 (custom build in /opt/rocm)
- PyTorch: 2.11.0a0 with ROCm backend
{tools_info}

Security Mode: {self.security_config.mode.value}
{get_mode_info(self.security_config.mode)}

Safe commands (no privileges needed):
{', '.join(self.security_config.safe_commands[:10])}...

Privileged commands (require authentication):
{', '.join(self.security_config.privileged_commands[:5])}...

Style:
- Concise, technical responses
- Use terminal-friendly formatting
- Prefer showing code/commands over explanations
- Always warn before destructive operations
"""

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "max_tokens": 2048,
            "temperature": 0.1,
            "stream": False
        }

        try:
            req = urllib.request.Request(
                self.llama_server_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data['choices'][0]['message']['content']

        except Exception as e:
            return f"ERROR: LLM query failed: {e}"

    def _format_file_content(self, path: str, content: Any) -> str:
        """Format file content for display"""
        # Parse MCP response: [{'type': 'text', 'text': 'content'}]
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get('text', str(content))
        else:
            text = str(content)

        if RICH_AVAILABLE:
            # Try to detect file type for syntax highlighting
            suffix = Path(path).suffix.lstrip('.')
            if suffix in ['py', 'sh', 'yaml', 'yml', 'json', 'toml', 'md', 'txt']:
                syntax = Syntax(text, suffix, theme="monokai", line_numbers=True)
                self.console.print(Panel(syntax, title=f"📄 {path}", border_style=COLORS['primary']))
                return ""
            else:
                return f"\n📄 {path}\n{'='*70}\n{text}\n"
        else:
            return f"\n📄 {path}\n{'='*70}\n{text}\n"

    def _format_directory_list(self, path: str, items: Any) -> str:
        """Format directory listing"""
        if RICH_AVAILABLE:
            table = Table(title=f"📁 {path}", border_style=COLORS['secondary'])
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Size", style="green")

            for item in items:
                table.add_row(
                    item.get('name', ''),
                    item.get('type', ''),
                    item.get('size', '')
                )

            self.console.print(table)
            return ""
        else:
            return f"\n📁 {path}\n{'='*70}\n{items}\n"

    def _format_search_results(self, pattern: str, results: Any) -> str:
        """Format search results"""
        return f"\n🔍 Search results for '{pattern}':\n{results}\n"

    def _format_gpu_stats(self, result: Any) -> str:
        """Format comprehensive GPU statistics"""
        # Parse JSON from MCP result
        if isinstance(result, list) and len(result) > 0:
            data = json.loads(result[0]['text'])
        else:
            data = result

        if RICH_AVAILABLE:
            table = Table(title="🎮 GPU Statistics", border_style=COLORS['primary'])
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="bright_magenta")

            table.add_row("GPU", data.get('gpu_name', 'N/A'))
            table.add_row("Architecture", data.get('architecture', 'N/A'))

            if 'vram' in data:
                vram = data['vram']
                table.add_row("VRAM Used", f"{vram.get('used_gb', 'N/A')} GB")
                table.add_row("VRAM Total", f"{vram.get('total_gb', 'N/A')} GB")
                table.add_row("VRAM Free", f"{vram.get('free_gb', 'N/A')} GB")
                table.add_row("VRAM Usage", f"{vram.get('utilization_percent', 'N/A')}%")

            if 'temperature' in data:
                temp = data['temperature']
                temp_c = temp.get('temperature_c', 'N/A')
                status = temp.get('status', 'unknown')
                table.add_row("Temperature", f"{temp_c}°C ({status})")

            if 'utilization' in data:
                util = data['utilization']
                util_pct = util.get('utilization_percent', 'N/A')
                util_status = util.get('status', 'unknown')
                table.add_row("GPU Usage", f"{util_pct}% ({util_status})")

            self.console.print(table)
            return ""
        else:
            output = "\n🎮 GPU Statistics\n" + "="*70 + "\n"
            output += f"GPU: {data.get('gpu_name', 'N/A')}\n"
            output += f"Architecture: {data.get('architecture', 'N/A')}\n"
            if 'vram' in data:
                vram = data['vram']
                output += f"VRAM: {vram.get('used_gb', 'N/A')} / {vram.get('total_gb', 'N/A')} GB ({vram.get('utilization_percent', 'N/A')}%)\n"
            if 'temperature' in data:
                temp = data['temperature']
                output += f"Temperature: {temp.get('temperature_c', 'N/A')}°C\n"
            if 'utilization' in data:
                util = data['utilization']
                output += f"Utilization: {util.get('utilization_percent', 'N/A')}%\n"
            return output

    def _format_vram_info(self, result: Any) -> str:
        """Format VRAM usage information"""
        if isinstance(result, list) and len(result) > 0:
            data = json.loads(result[0]['text'])
        else:
            data = result

        if RICH_AVAILABLE:
            table = Table(title="💾 VRAM Usage", border_style=COLORS['secondary'])
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="bright_green")

            table.add_row("Total", f"{data.get('total_gb', 'N/A')} GB")
            table.add_row("Used", f"{data.get('used_gb', 'N/A')} GB")
            table.add_row("Free", f"{data.get('free_gb', 'N/A')} GB")
            table.add_row("Utilization", f"{data.get('utilization_percent', 'N/A')}%")

            self.console.print(table)
            return ""
        else:
            return f"\n💾 VRAM: {data.get('used_gb', 'N/A')} / {data.get('total_gb', 'N/A')} GB ({data.get('utilization_percent', 'N/A')}%)\n"

    def _format_temp_info(self, result: Any) -> str:
        """Format GPU temperature information"""
        if isinstance(result, list) and len(result) > 0:
            data = json.loads(result[0]['text'])
        else:
            data = result

        temp_c = data.get('temperature_c', 'N/A')
        temp_f = data.get('temperature_f', 'N/A')
        status = data.get('status', 'unknown')

        if RICH_AVAILABLE:
            color = COLORS['success'] if status == 'normal' else COLORS['warning'] if status == 'hot' else COLORS['error']
            self.console.print(f"\n🌡️  GPU Temperature: [{color}]{temp_c}°C ({temp_f}°F) - {status.upper()}[/{color}]\n")
            return ""
        else:
            return f"\n🌡️  GPU Temperature: {temp_c}°C ({temp_f}°F) - {status}\n"

    def _print_success(self, message: str):
        """Print success message"""
        if RICH_AVAILABLE:
            self.console.print(f"[{COLORS['success']}]✓ {message}[/{COLORS['success']}]")
        else:
            print(f"✓ {message}")

    def _print_error(self, message: str):
        """Print error message"""
        if RICH_AVAILABLE:
            self.console.print(f"[{COLORS['error']}]✗ {message}[/{COLORS['error']}]")
        else:
            print(f"✗ {message}")

    def _format_memory_info(self, result: Any) -> str:
        """Format memory information"""
        # MCP returns JSON string in result
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get('text', str(result))
        else:
            text = str(result)

        return f"\n💾 Memory Information:\n{'='*70}\n{text}\n"

    def _format_disk_info(self, result: Any) -> str:
        """Format disk usage information"""
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get('text', str(result))
        else:
            text = str(result)

        return f"\n💿 Disk Usage:\n{'='*70}\n{text}\n"

    async def shutdown(self):
        """Cleanup and shutdown"""
        if self.mcp_client:
            self.mcp_client.stop_all()


async def main():
    """Main entry point"""

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: rai 'your query here'")
        print("   or: rocm-cli 'your query here'")
        print("   or: echo 'your query' | rai")
        print("\nExamples:")
        print("  rai 'gpu stats'")
        print("  rai 'show vram'")
        print("  rai 'gpu temp'")
        print("  rai 'read /tmp/test.txt'")
        sys.exit(1)

    # Get query from args or stdin
    if sys.argv[1] == '-':
        query = sys.stdin.read().strip()
    else:
        query = ' '.join(sys.argv[1:])

    if not query:
        print("ERROR: No query provided")
        sys.exit(1)

    # Initialize agent
    agent = ROCmCLIAgent()

    try:
        await agent.initialize()

        # Process query
        result = await agent.process_query(query)

        # Print result
        if result:
            print(result)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
