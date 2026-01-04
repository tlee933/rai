#!/usr/bin/env python3
"""
F3D0R4 MCP Client
Manages connections to MCP servers and executes tool calls
"""

import json
import subprocess
import asyncio
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


class MCPServer:
    """Represents a connection to a single MCP server"""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.tools: List[Dict[str, Any]] = []
        self.resources: List[Dict[str, Any]] = []
        self._request_id = 0

    async def start(self):
        """Start the MCP server process"""
        logger.info(f"Starting MCP server: {self.config.name}")

        env = self.config.env.copy() if self.config.env else {}

        self.process = subprocess.Popen(
            [self.config.command] + self.config.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env={**subprocess.os.environ, **env}
        )

        # Initialize connection
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "f3d0r4-ai",
                "version": "0.1.0"
            }
        })

        # Send initialized notification
        await self._send_notification("initialized", {})

        # List available tools
        tools_response = await self._send_request("tools/list", {})
        self.tools = tools_response.get("tools", [])

        logger.info(f"Server {self.config.name} initialized with {len(self.tools)} tools")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool call on this server"""
        logger.debug(f"Calling tool {tool_name} on {self.config.name}")

        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        return response.get("content", [])

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server"""
        if not self.process or not self.process.stdin:
            raise RuntimeError(f"Server {self.config.name} not started")

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }

        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError(f"Server {self.config.name} closed connection")

        response = json.loads(response_line)

        if "error" in response:
            raise Exception(f"MCP error: {response['error']}")

        return response.get("result", {})

    async def _send_notification(self, method: str, params: Dict[str, Any]):
        """Send a JSON-RPC notification (no response expected)"""
        if not self.process or not self.process.stdin:
            raise RuntimeError(f"Server {self.config.name} not started")

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        # Send notification
        notification_json = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_json)
        self.process.stdin.flush()

    def stop(self):
        """Stop the MCP server process"""
        if self.process:
            logger.info(f"Stopping MCP server: {self.config.name}")
            self.process.terminate()
            self.process.wait(timeout=5)


class MCPClient:
    """Manages multiple MCP server connections"""

    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}

    async def add_server(self, config: MCPServerConfig):
        """Add and start a new MCP server"""
        server = MCPServer(config)
        await server.start()
        self.servers[config.name] = server

    def get_all_tools(self) -> Dict[str, List[str]]:
        """Get all available tools from all servers"""
        all_tools = {}
        for name, server in self.servers.items():
            all_tools[name] = [tool["name"] for tool in server.tools]
        return all_tools

    def get_tool_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about all available tools"""
        tool_info = []
        for server_name, server in self.servers.items():
            for tool in server.tools:
                tool_info.append({
                    "server": server_name,
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "schema": tool.get("inputSchema", {})
                })
        return tool_info

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool on a specific server"""
        if server_name not in self.servers:
            raise ValueError(f"Unknown server: {server_name}")

        return await self.servers[server_name].call_tool(tool_name, arguments)

    def find_tool(self, tool_name: str) -> Optional[tuple[str, str]]:
        """Find which server provides a given tool"""
        for server_name, server in self.servers.items():
            for tool in server.tools:
                if tool["name"] == tool_name:
                    return (server_name, tool_name)
        return None

    def stop_all(self):
        """Stop all MCP servers"""
        for server in self.servers.values():
            server.stop()


async def main():
    """Test the MCP client"""
    # Create client
    client = MCPClient()

    # Add filesystem server
    await client.add_server(MCPServerConfig(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp", "/home/hashcat"]
    ))

    # List tools
    print("\nAvailable tools:")
    for server_name, tools in client.get_all_tools().items():
        print(f"\n{server_name}:")
        for tool in tools:
            print(f"  - {tool}")

    # Test tool call
    print("\n\nTesting file read:")
    result = await client.call_tool("filesystem", "read_file", {
        "path": "/tmp/test.txt"
    })
    print(result)

    # Cleanup
    client.stop_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
