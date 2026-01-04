#!/usr/bin/env python3
"""
rai-shell - Interactive REPL for ROCm AI CLI
Persistent session with command history and auto-completion
"""

import sys
import asyncio
import readline
from pathlib import Path

# Import the main agent
from rai import ROCmCLIAgent, RICH_AVAILABLE

if RICH_AVAILABLE:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    console = Console()


class RAIShell:
    """Interactive REPL shell for rai"""

    def __init__(self):
        self.agent = ROCmCLIAgent()
        self.history_file = Path.home() / ".rai-history"
        self.running = True

        # Setup readline
        self._setup_readline()

    def _setup_readline(self):
        """Configure readline for command history and completion"""
        # Load history
        if self.history_file.exists():
            try:
                readline.read_history_file(str(self.history_file))
            except Exception:
                pass

        # Set history length
        readline.set_history_length(1000)

        # Enable tab completion
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self._completer)

    def _completer(self, text, state):
        """Auto-completion for common commands"""
        commands = [
            # Shell commands
            "/help", "/exit", "/quit", "/history", "/clear", "/tools",
            # GPU queries
            "gpu stats", "gpu temp", "vram", "show gpu",
            # System queries
            "check memory", "check disk", "list services", "show logs",
            "list processes", "top processes",
            # File operations
            "read ", "list ", "search ",
            # Common patterns
            "what is", "how do i", "explain", "show me"
        ]

        matches = [cmd for cmd in commands if cmd.startswith(text)]

        if state < len(matches):
            return matches[state]
        return None

    def _save_history(self):
        """Save command history to file"""
        try:
            readline.write_history_file(str(self.history_file))
        except Exception as e:
            print(f"Warning: Could not save history: {e}")

    def _show_welcome(self):
        """Display welcome message"""
        if RICH_AVAILABLE:
            welcome_text = """
# 🚀 ROCm AI CLI - Interactive Shell

**Quick commands:**
- `gpu stats` - Show GPU information
- `vram` - Show VRAM usage
- `gpu temp` - Show temperature
- `check memory` - System memory info
- `list services` - Systemd services
- `read /path/file` - Read a file
- `/help` - Show all commands
- `/exit` - Exit shell

Type your query or command and press Enter.
"""
            console.print(Panel(Markdown(welcome_text), border_style="cyan"))
        else:
            print("\n" + "="*70)
            print("🚀 ROCm AI CLI - Interactive Shell")
            print("="*70)
            print("\nQuick commands:")
            print("  gpu stats     - Show GPU information")
            print("  vram          - Show VRAM usage")
            print("  check memory  - System memory info")
            print("  /help         - Show all commands")
            print("  /exit         - Exit shell")
            print("\nType your query and press Enter.\n")

    def _show_help(self):
        """Display help information"""
        help_text = """
**Shell Commands:**
- `/help` - Show this help
- `/exit`, `/quit` - Exit the shell
- `/history` - Show command history
- `/clear` - Clear screen
- `/tools` - List available MCP tools

**GPU Queries (ROCm MCP):**
- `gpu stats` - Comprehensive GPU info
- `vram` - VRAM usage
- `gpu temp` - GPU temperature
- `show gpu` - GPU details

**System Queries (linux-mcp-server):**
- `check memory` - Memory usage
- `check disk` - Disk usage
- `list services` - Systemd services
- `list processes` - Running processes
- `show logs` - System journal logs
- `is <service> running` - Check service status

**File Operations:**
- `read /path/to/file` - Read file contents
- `list /path/to/dir` - List directory
- `search <pattern> in /path` - Search files

**LLM Reasoning:**
Any query that doesn't match above patterns will use the LLM for reasoning:
- `what is 15 factorial`
- `explain how PyTorch tensors work`
- `how do I optimize ROCm performance`
"""
        if RICH_AVAILABLE:
            console.print(Panel(Markdown(help_text), title="Help", border_style="yellow"))
        else:
            print("\n" + help_text + "\n")

    async def _show_tools(self):
        """List available MCP tools"""
        if not self.agent.mcp_client:
            print("MCP client not initialized")
            return

        all_tools = self.agent.mcp_client.get_all_tools()

        if RICH_AVAILABLE:
            from rich.table import Table

            table = Table(title="🔧 Available MCP Tools", border_style="cyan")
            table.add_column("Server", style="magenta")
            table.add_column("Tools", style="green")

            for server, tools in all_tools.items():
                table.add_row(server, ", ".join(tools))

            console.print(table)
        else:
            print("\n🔧 Available MCP Tools:")
            print("="*70)
            for server, tools in all_tools.items():
                print(f"{server}: {', '.join(tools)}")
            print()

    def _show_history(self):
        """Display command history"""
        history_len = readline.get_current_history_length()

        if history_len == 0:
            print("No command history")
            return

        print("\n📜 Command History:")
        print("="*70)

        # Show last 20 commands
        start = max(1, history_len - 19)
        for i in range(start, history_len + 1):
            item = readline.get_history_item(i)
            if item:
                print(f"{i:3d}  {item}")
        print()

    async def _handle_special_command(self, command: str) -> bool:
        """Handle special shell commands (starting with /)
        Returns True if command was handled, False otherwise
        """
        cmd = command.strip().lower()

        if cmd in ["/exit", "/quit"]:
            self.running = False
            print("\nGoodbye! 👋\n")
            return True

        elif cmd == "/help":
            self._show_help()
            return True

        elif cmd == "/history":
            self._show_history()
            return True

        elif cmd == "/clear":
            print("\033[2J\033[H", end="")  # ANSI clear screen
            return True

        elif cmd == "/tools":
            await self._show_tools()
            return True

        return False

    def _get_prompt(self) -> str:
        """Get the input prompt"""
        if RICH_AVAILABLE:
            # Use Rich color codes
            return "[cyan]rai>[/cyan] "
        else:
            return "rai> "

    async def run(self):
        """Main REPL loop"""
        try:
            # Initialize agent
            if RICH_AVAILABLE:
                console.print("[yellow]Initializing ROCm AI CLI...[/yellow]")
            else:
                print("Initializing ROCm AI CLI...")

            await self.agent.initialize()

            # Show welcome
            self._show_welcome()

            # Main loop
            while self.running:
                try:
                    # Get input
                    if RICH_AVAILABLE:
                        # Rich doesn't support input with markup, so use plain prompt
                        user_input = input("rai> ").strip()
                    else:
                        user_input = input(self._get_prompt()).strip()

                    if not user_input:
                        continue

                    # Handle special commands
                    if user_input.startswith('/'):
                        await self._handle_special_command(user_input)
                        continue

                    # Process query
                    if RICH_AVAILABLE:
                        console.print("[dim]Processing...[/dim]")

                    result = await self.agent.process_query(user_input)

                    # Print result
                    if result:
                        print(result)

                except EOFError:
                    # Ctrl+D pressed
                    self.running = False
                    print("\n\nGoodbye! 👋\n")

                except KeyboardInterrupt:
                    # Ctrl+C pressed
                    print("\n(Use /exit or Ctrl+D to quit)\n")
                    continue

                except Exception as e:
                    if RICH_AVAILABLE:
                        console.print(f"[red]Error: {e}[/red]")
                    else:
                        print(f"Error: {e}")

        finally:
            # Cleanup
            self._save_history()
            await self.agent.shutdown()


async def main():
    """Entry point"""
    shell = RAIShell()
    await shell.run()


if __name__ == "__main__":
    asyncio.run(main())
