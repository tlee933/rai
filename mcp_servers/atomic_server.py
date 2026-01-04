#!/usr/bin/env python3
"""
Atomic Desktop MCP Server
Tools for Fedora Atomic/Silverblue/Kinoite management

Provides:
- rpm-ostree status and operations
- Flatpak management
- ostree commands
- Toolbox/Distrobox integration
"""

import subprocess
import json
import sys
from typing import Any, Dict


class AtomicServer:
    """MCP server for atomic desktop operations"""

    def __init__(self):
        self.name = "atomic-desktop-server"
        self.version = "0.1.0"

    def _run_command(self, cmd: list[str]) -> str:
        """Run a shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"ERROR: {e}"

    def get_rpm_ostree_status(self) -> str:
        """Get rpm-ostree status (deployments, updates, etc)"""
        output = self._run_command(["rpm-ostree", "status", "--json"])
        try:
            data = json.loads(output)
            deployments = data.get('deployments', [])

            result = []
            for i, dep in enumerate(deployments):
                is_current = "●" if i == 0 else "○"
                version = dep.get('version', 'unknown')
                timestamp = dep.get('timestamp', 0)
                checksum = dep.get('checksum', '')[:7]

                result.append(f"{is_current} {version} ({checksum})")

                if i == 0:  # Current deployment
                    result.append(f"  Base commit: {dep.get('base-checksum', 'N/A')[:12]}")
                    layered = dep.get('requested-packages', [])
                    if layered:
                        result.append(f"  Layered packages: {', '.join(layered[:5])}")
                        if len(layered) > 5:
                            result.append(f"    ... and {len(layered) - 5} more")

            return json.dumps({
                "status": "success",
                "deployments": len(deployments),
                "current_version": deployments[0].get('version', 'unknown') if deployments else 'none',
                "details": "\n".join(result)
            }, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def check_rpm_ostree_updates(self) -> str:
        """Check for available rpm-ostree updates"""
        # rpm-ostree upgrade --check
        output = self._run_command(["rpm-ostree", "upgrade", "--check"])

        if "No upgrade available" in output or "No updates available" in output:
            return json.dumps({
                "updates_available": False,
                "message": "System is up to date"
            })
        else:
            return json.dumps({
                "updates_available": True,
                "details": output
            })

    def list_layered_packages(self) -> str:
        """List rpm-ostree layered packages"""
        output = self._run_command(["rpm-ostree", "status", "--json"])
        try:
            data = json.loads(output)
            deployments = data.get('deployments', [])

            if not deployments:
                return json.dumps({"layered_packages": []})

            current = deployments[0]
            layered = current.get('requested-packages', [])

            return json.dumps({
                "count": len(layered),
                "packages": layered
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def list_flatpaks(self) -> str:
        """List installed Flatpak applications"""
        # Get user flatpaks
        user_output = self._run_command(["flatpak", "list", "--app", "--user"])
        # Get system flatpaks
        system_output = self._run_command(["flatpak", "list", "--app", "--system"])

        user_apps = [line.split('\t')[0] for line in user_output.strip().split('\n') if line]
        system_apps = [line.split('\t')[0] for line in system_output.strip().split('\n') if line]

        return json.dumps({
            "user_flatpaks": len(user_apps),
            "system_flatpaks": len(system_apps),
            "total": len(user_apps) + len(system_apps),
            "user_apps": user_apps[:10],  # First 10
            "system_apps": system_apps[:10]
        }, indent=2)

    def get_flatpak_updates(self) -> str:
        """Check for Flatpak updates"""
        output = self._run_command(["flatpak", "remote-ls", "--updates"])

        updates = [line for line in output.strip().split('\n') if line]

        return json.dumps({
            "updates_available": len(updates) > 0,
            "count": len(updates),
            "updates": updates[:10]  # First 10
        }, indent=2)

    def list_toolboxes(self) -> str:
        """List toolbox containers"""
        output = self._run_command(["toolbox", "list"])

        lines = output.strip().split('\n')
        containers = []

        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    containers.append({
                        "name": parts[1],
                        "image": parts[0] if len(parts) > 0 else "unknown"
                    })

        return json.dumps({
            "count": len(containers),
            "containers": containers
        }, indent=2)

    def get_ostree_info(self) -> str:
        """Get ostree deployment information"""
        output = self._run_command(["ostree", "admin", "status"])

        return json.dumps({
            "status": output
        })

    # MCP Protocol Methods

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }

    def handle_tools_list(self) -> Dict[str, Any]:
        """Return list of available tools"""
        return {
            "tools": [
                {
                    "name": "get_rpm_ostree_status",
                    "description": "Get rpm-ostree deployment status and layered packages",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "check_rpm_ostree_updates",
                    "description": "Check for available rpm-ostree system updates",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "list_layered_packages",
                    "description": "List rpm-ostree layered packages",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "list_flatpaks",
                    "description": "List installed Flatpak applications",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "get_flatpak_updates",
                    "description": "Check for available Flatpak updates",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "list_toolboxes",
                    "description": "List toolbox/distrobox containers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "get_ostree_info",
                    "description": "Get ostree deployment information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> list:
        """Execute a tool and return result"""

        tool_map = {
            "get_rpm_ostree_status": self.get_rpm_ostree_status,
            "check_rpm_ostree_updates": self.check_rpm_ostree_updates,
            "list_layered_packages": self.list_layered_packages,
            "list_flatpaks": self.list_flatpaks,
            "get_flatpak_updates": self.get_flatpak_updates,
            "list_toolboxes": self.list_toolboxes,
            "get_ostree_info": self.get_ostree_info,
        }

        if name in tool_map:
            result = tool_map[name]()
            return [{"type": "text", "text": result}]
        else:
            return [{"type": "text", "text": json.dumps({"error": f"Unknown tool: {name}"})}]

    def run(self):
        """Main MCP server loop"""

        for line in sys.stdin:
            try:
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                req_id = request.get("id")

                response = {"jsonrpc": "2.0", "id": req_id}

                if method == "initialize":
                    response["result"] = self.handle_initialize(params)
                elif method == "initialized":
                    # Notification - no response needed
                    continue
                elif method == "tools/list":
                    response["result"] = self.handle_tools_list()
                elif method == "tools/call":
                    tool_name = params.get("name")
                    tool_args = params.get("arguments", {})
                    response["result"] = {
                        "content": self.handle_tool_call(tool_name, tool_args)
                    }
                else:
                    # Unknown method
                    if req_id is not None:
                        # It's a request (has id), send error response
                        response["error"] = {"code": -32601, "message": f"Method not found: {method}"}
                    else:
                        # It's a notification (no id), ignore silently
                        continue

                # Only print response if it's a request (has id)
                if req_id is not None:
                    print(json.dumps(response), flush=True)

            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {"code": -32603, "message": f"Internal error: {e}"}
                }
                print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    server = AtomicServer()
    server.run()
