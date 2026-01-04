#!/usr/bin/env python3
"""
rai-tui - Terminal UI for ROCm AI CLI
Beautiful split-panel interface with live GPU monitoring

Inspired by Charm's Bubble Tea, built with Rich
"""

import sys
import asyncio
import threading
import time
from datetime import datetime
from pathlib import Path
from collections import deque

# Import the main agent
from rai import ROCmCLIAgent, RICH_AVAILABLE

if not RICH_AVAILABLE:
    print("ERROR: Rich library required for TUI mode")
    print("Install: pip install rich")
    sys.exit(1)

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich import box
import json


class RAIStats:
    """Live GPU and system statistics"""

    def __init__(self):
        self.vram_used = "0.0"
        self.vram_total = "32.0"
        self.vram_percent = "0"
        self.gpu_temp = "N/A"
        self.gpu_name = "AMD GPU"
        self.last_update = "Never"

    def update_from_agent(self, agent):
        """Update stats from agent"""
        try:
            # Get VRAM
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                agent.mcp_client.call_tool("rocm", "get_vram", {})
            )
            data = json.loads(result[0]['text'])
            self.vram_used = f"{data.get('used_gb', 0.0):.1f}"
            self.vram_total = f"{data.get('total_gb', 32.0):.1f}"
            self.vram_percent = str(data.get('utilization_percent', 0))

            # Get temp
            result = loop.run_until_complete(
                agent.mcp_client.call_tool("rocm", "get_gpu_temp", {})
            )
            data = json.loads(result[0]['text'])
            self.gpu_temp = f"{data.get('temperature_c', 'N/A')}°C"

            # Get GPU name
            result = loop.run_until_complete(
                agent.mcp_client.call_tool("rocm", "get_gpu_stats", {})
            )
            data = json.loads(result[0]['text'])
            self.gpu_name = data.get('gpu_name', 'AMD GPU')

            loop.close()
            self.last_update = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            pass  # Silently fail, keep old values


class RAITUI:
    """Terminal UI for rai"""

    def __init__(self):
        self.console = Console()
        self.agent = ROCmCLIAgent()
        self.stats = RAIStats()
        self.history = deque(maxlen=20)
        self.query_history = deque(maxlen=100)
        self.current_query = ""
        self.current_result = ""
        self.running = True
        self.stats_update_interval = 5  # seconds

        # Load history from file
        self.history_file = Path.home() / ".rai-history"
        self._load_history()

    def _load_history(self):
        """Load command history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-20:]:  # Last 20
                        self.query_history.append(line.strip())
            except Exception:
                pass

    def _save_history(self):
        """Save command history to file"""
        try:
            with open(self.history_file, 'w') as f:
                for query in self.query_history:
                    f.write(query + '\n')
        except Exception:
            pass

    def _make_gpu_panel(self) -> Panel:
        """Create GPU stats panel"""
        # VRAM bar
        vram_used_num = float(self.stats.vram_used)
        vram_total_num = float(self.stats.vram_total)
        vram_percent = int(self.stats.vram_percent)

        bar_width = 30
        filled = int(bar_width * vram_percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        # Color based on usage
        if vram_percent < 50:
            vram_color = "green"
        elif vram_percent < 80:
            vram_color = "yellow"
        else:
            vram_color = "red"

        # Temperature color
        try:
            temp_num = int(self.stats.gpu_temp.replace('°C', ''))
            if temp_num < 60:
                temp_color = "green"
            elif temp_num < 75:
                temp_color = "yellow"
            else:
                temp_color = "red"
        except:
            temp_color = "white"

        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="right")
        table.add_column(style="bright_magenta")

        table.add_row("GPU", self.stats.gpu_name[:40])
        table.add_row("", "")
        table.add_row("VRAM", f"[{vram_color}]{self.stats.vram_used} / {self.stats.vram_total} GB[/{vram_color}]")
        table.add_row("", f"[{vram_color}]{bar}[/{vram_color}] {vram_percent}%")
        table.add_row("", "")
        table.add_row("Temp", f"[{temp_color}]{self.stats.gpu_temp}[/{temp_color}]")
        table.add_row("", "")
        table.add_row("Updated", f"[dim]{self.stats.last_update}[/dim]")

        return Panel(
            table,
            title="🎮 GPU Stats",
            border_style="cyan",
            box=box.ROUNDED
        )

    def _make_history_panel(self) -> Panel:
        """Create command history panel"""
        if not self.query_history:
            content = Text("No history yet", style="dim")
        else:
            lines = []
            for i, query in enumerate(list(self.query_history)[-10:], 1):
                lines.append(f"[dim]{i:2d}.[/dim] {query[:40]}")
            content = "\n".join(lines)

        return Panel(
            content,
            title="📜 Recent Queries",
            border_style="blue",
            box=box.ROUNDED,
            height=14
        )

    def _make_query_panel(self) -> Panel:
        """Create query input panel"""
        if self.current_query:
            content = f"[cyan]rai>[/cyan] {self.current_query}"
        else:
            content = "[cyan]rai>[/cyan] [dim]Type your query...[/dim]"

        return Panel(
            content,
            title="💬 Query",
            border_style="green",
            box=box.ROUNDED
        )

    def _make_result_panel(self) -> Panel:
        """Create result display panel"""
        if self.current_result:
            content = self.current_result
        else:
            content = "[dim]Results will appear here...[/dim]"

        return Panel(
            content,
            title="📊 Result",
            border_style="magenta",
            box=box.ROUNDED,
            height=20
        )

    def _make_help_panel(self) -> Panel:
        """Create help/shortcuts panel"""
        help_text = """[cyan]Shortcuts:[/cyan]
[dim]Ctrl+C[/dim] - Cancel query
[dim]Ctrl+D[/dim] - Exit TUI
[dim]/help[/dim]  - Show all commands
[dim]/exit[/dim]  - Exit TUI

[cyan]Quick Queries:[/cyan]
vram, gpu temp, gpu stats
check memory, list services
ostree status, show flatpaks"""

        return Panel(
            help_text,
            title="❓ Help",
            border_style="yellow",
            box=box.ROUNDED
        )

    def make_layout(self) -> Layout:
        """Create the main layout"""
        layout = Layout()

        # Split into header and body
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )

        # Header
        title = Text("🚀 rai - ROCm AI CLI", style="bold cyan", justify="center")
        layout["header"].update(Panel(title, border_style="cyan"))

        # Split body into left and right
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )

        # Split left into stats and history
        layout["left"].split_column(
            Layout(name="stats"),
            Layout(name="history"),
            Layout(name="help", size=12)
        )

        # Split right into query and result
        layout["right"].split_column(
            Layout(name="query", size=5),
            Layout(name="result")
        )

        # Update panels
        layout["stats"].update(self._make_gpu_panel())
        layout["history"].update(self._make_history_panel())
        layout["help"].update(self._make_help_panel())
        layout["query"].update(self._make_query_panel())
        layout["result"].update(self._make_result_panel())

        return layout

    def update_stats_worker(self):
        """Background thread to update GPU stats"""
        while self.running:
            try:
                self.stats.update_from_agent(self.agent)
            except Exception:
                pass
            time.sleep(self.stats_update_interval)

    async def process_query(self, query: str):
        """Process a user query"""
        self.current_query = query
        self.current_result = "[dim]Processing...[/dim]"

        try:
            # Add to history
            if query and not query.startswith('/'):
                self.query_history.append(query)

            # Handle special commands
            if query.startswith('/'):
                if query.strip().lower() in ['/exit', '/quit']:
                    self.running = False
                    self.current_result = "[yellow]Exiting...[/yellow]"
                    return
                elif query.strip().lower() == '/help':
                    self.current_result = """[cyan]Available Commands:[/cyan]

[yellow]GPU Queries:[/yellow]
  gpu stats, vram, gpu temp

[yellow]System Queries:[/yellow]
  check memory, check disk
  list services, show logs

[yellow]Atomic Desktop:[/yellow]
  ostree status, show flatpaks
  list toolboxes, check updates

[yellow]Special Commands:[/yellow]
  /help - Show this help
  /clear - Clear result
  /exit - Exit TUI"""
                    return
                elif query.strip().lower() == '/clear':
                    self.current_result = ""
                    return

            # Process query
            result = await self.agent.process_query(query)
            self.current_result = result if result else "[dim]No result[/dim]"

        except Exception as e:
            self.current_result = f"[red]Error: {e}[/red]"

    async def run(self):
        """Main TUI loop"""
        try:
            # Initialize agent
            self.console.print("[yellow]Initializing ROCm AI CLI...[/yellow]")
            await self.agent.initialize()

            # Update stats once
            self.stats.update_from_agent(self.agent)

            # Start stats update worker
            stats_thread = threading.Thread(target=self.update_stats_worker, daemon=True)
            stats_thread.start()

            # Main display loop with Live
            with Live(self.make_layout(), console=self.console, screen=True, refresh_per_second=2) as live:
                while self.running:
                    try:
                        # Update layout
                        live.update(self.make_layout())

                        # Get user input (non-blocking)
                        # Note: Live screen mode makes input tricky
                        # We'll use a simpler approach - show a message
                        await asyncio.sleep(0.5)

                    except KeyboardInterrupt:
                        self.running = False
                        break

                # Show exit message
                self.console.print("\n[cyan]Exiting rai TUI...[/cyan]")
                self.console.print("[dim]Use 'rai-shell' for interactive REPL mode[/dim]\n")

        finally:
            # Cleanup
            self._save_history()
            await self.agent.shutdown()


class RAITUIInteractive:
    """Interactive TUI with input handling"""

    def __init__(self):
        self.console = Console()
        self.agent = ROCmCLIAgent()
        self.stats = RAIStats()
        self.query_history = deque(maxlen=100)
        self.display_history = deque(maxlen=10)
        self.running = True

        self.history_file = Path.home() / ".rai-history"
        self._load_history()

    def _load_history(self):
        """Load command history"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    for line in f.readlines()[-100:]:
                        self.query_history.append(line.strip())
            except Exception:
                pass

    def _save_history(self):
        """Save command history"""
        try:
            with open(self.history_file, 'w') as f:
                for query in self.query_history:
                    f.write(query + '\n')
        except Exception:
            pass

    def show_dashboard(self):
        """Show current dashboard state"""
        self.console.clear()

        # Header
        self.console.print(Panel(
            "[bold cyan]🚀 rai - ROCm AI CLI[/bold cyan]",
            border_style="cyan"
        ))

        # GPU Stats
        vram_percent = int(self.stats.vram_percent)
        bar_width = 40
        filled = int(bar_width * vram_percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        vram_color = "green" if vram_percent < 50 else "yellow" if vram_percent < 80 else "red"

        gpu_table = Table.grid(padding=(0, 2))
        gpu_table.add_column(style="cyan", justify="right", width=12)
        gpu_table.add_column()

        gpu_table.add_row("GPU", self.stats.gpu_name)
        gpu_table.add_row("VRAM", f"[{vram_color}]{bar}[/{vram_color}]")
        gpu_table.add_row("", f"[{vram_color}]{self.stats.vram_used} / {self.stats.vram_total} GB ({vram_percent}%)[/{vram_color}]")
        gpu_table.add_row("Temperature", f"{self.stats.gpu_temp}")
        gpu_table.add_row("Updated", f"[dim]{self.stats.last_update}[/dim]")

        self.console.print(Panel(gpu_table, title="🎮 GPU Stats", border_style="cyan"))

        # Recent queries
        if self.display_history:
            history_text = "\n".join([f"  [dim]•[/dim] {q}" for q in list(self.display_history)[-5:]])
            self.console.print(Panel(history_text, title="📜 Recent Queries", border_style="blue"))

        # Prompt
        self.console.print()

    async def run(self):
        """Main interactive loop"""
        try:
            # Initialize
            self.console.print("[yellow]Initializing ROCm AI CLI TUI...[/yellow]")
            await self.agent.initialize()

            # Update stats
            self.stats.update_from_agent(self.agent)

            # Start stats updater in background
            async def update_stats_loop():
                while self.running:
                    await asyncio.sleep(5)
                    self.stats.update_from_agent(self.agent)

            stats_task = asyncio.create_task(update_stats_loop())

            # Main loop
            while self.running:
                try:
                    # Show dashboard
                    self.show_dashboard()

                    # Get input
                    query = input("[cyan]rai>[/cyan] ").strip()

                    if not query:
                        continue

                    # Handle special commands
                    if query.lower() in ['/exit', '/quit']:
                        break

                    if query.lower() == '/clear':
                        continue

                    # Add to history
                    self.query_history.append(query)
                    self.display_history.append(query)

                    # Process query
                    self.console.print("[dim]Processing...[/dim]")
                    result = await self.agent.process_query(query)

                    # Show result
                    if result:
                        self.console.print(Panel(result, title="📊 Result", border_style="magenta"))

                    # Pause before refreshing
                    self.console.print("\n[dim]Press Enter to continue...[/dim]", end='')
                    input()

                except EOFError:
                    break
                except KeyboardInterrupt:
                    self.console.print("\n[dim](Use /exit to quit)[/dim]")

            # Cancel stats task
            stats_task.cancel()

            self.console.print("\n[cyan]Goodbye! 👋[/cyan]\n")

        finally:
            self._save_history()
            await self.agent.shutdown()


async def main():
    """Entry point"""
    # Use interactive version (simpler, works better)
    tui = RAITUIInteractive()
    await tui.run()


if __name__ == "__main__":
    asyncio.run(main())
