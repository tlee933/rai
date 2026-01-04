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
