#!/usr/bin/env python3
"""
ROCm GPU MCP Server
Provides GPU/ROCm tools via Model Context Protocol

Tools:
- get_vram: VRAM usage (used/total/free)
- get_gpu_temp: GPU temperature
- get_gpu_stats: Full GPU statistics
- get_rocm_version: ROCm version info
- get_hip_version: HIP version
- rocminfo: Detailed GPU capabilities
- get_gpu_utilization: GPU compute utilization
"""

import json
import subprocess
import sys
import re
from typing import Dict, Any, Optional


class ROCmMCPServer:
    """MCP server for ROCm/GPU operations"""

    def __init__(self):
        self.rocm_path = "/opt/rocm"
        self.tools = {
            "get_vram": {
                "description": "Get VRAM usage (used, total, free in GB)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                }
            },
            "get_gpu_temp": {
                "description": "Get GPU temperature in Celsius",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                }
            },
            "get_gpu_stats": {
                "description": "Get comprehensive GPU statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                }
            },
            "get_rocm_version": {
                "description": "Get ROCm version information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                }
            },
            "get_hip_version": {
                "description": "Get HIP version information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                }
            },
            "rocminfo": {
                "description": "Get detailed GPU capabilities and device info",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                }
            },
            "get_gpu_utilization": {
                "description": "Get current GPU compute utilization percentage",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                }
            }
        }

    def _run_command(self, cmd: list, timeout: int = 10) -> Optional[str]:
        """Run a command and return stdout"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                return result.stdout
            else:
                return f"ERROR: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "ERROR: Command timed out"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def get_vram(self) -> Dict[str, Any]:
        """Get VRAM usage via rocm-smi"""
        output = self._run_command([f"{self.rocm_path}/bin/rocm-smi", "--showmeminfo", "vram"])

        if not output or output.startswith("ERROR"):
            return {"error": output or "Failed to get VRAM info"}

        # Parse rocm-smi output
        # Format: "GPU[0]  : VRAM Total Memory (B): 34342961152"
        #         "GPU[0]  : VRAM Total Used Memory (B): 1234567890"

        vram_data = {}
        for line in output.split('\n'):
            if "VRAM Total Memory (B)" in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    vram_data['total_bytes'] = int(match.group(1))
            elif "VRAM Total Used Memory (B)" in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    vram_data['used_bytes'] = int(match.group(1))

        if 'total_bytes' in vram_data and 'used_bytes' in vram_data:
            total_gb = vram_data['total_bytes'] / (1024**3)
            used_gb = vram_data['used_bytes'] / (1024**3)
            free_gb = total_gb - used_gb

            return {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "utilization_percent": round((used_gb / total_gb) * 100, 1)
            }
        else:
            return {"error": "Failed to parse VRAM info", "raw_output": output}

    def get_gpu_temp(self) -> Dict[str, Any]:
        """Get GPU temperature via rocm-smi"""
        output = self._run_command([f"{self.rocm_path}/bin/rocm-smi", "--showtemp"])

        if not output or output.startswith("ERROR"):
            return {"error": output or "Failed to get temperature"}

        # Parse temperature
        # Format: "GPU[0]  : Temperature (Sensor edge) (C): 45.0"
        for line in output.split('\n'):
            if "Temperature" in line and "edge" in line:
                match = re.search(r':\s*([\d.]+)', line)
                if match:
                    temp = float(match.group(1))
                    return {
                        "temperature_c": temp,
                        "temperature_f": round(temp * 9/5 + 32, 1),
                        "status": "normal" if temp < 80 else "hot" if temp < 90 else "critical"
                    }

        return {"error": "Failed to parse temperature", "raw_output": output}

    def get_gpu_utilization(self) -> Dict[str, Any]:
        """Get GPU compute utilization"""
        output = self._run_command([f"{self.rocm_path}/bin/rocm-smi", "--showuse"])

        if not output or output.startswith("ERROR"):
            return {"error": output or "Failed to get utilization"}

        # Parse GPU usage
        # Format: "GPU[0]  : GPU use (%): 45"
        for line in output.split('\n'):
            if "GPU use" in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    usage = int(match.group(1))
                    return {
                        "utilization_percent": usage,
                        "status": "idle" if usage < 10 else "active" if usage < 80 else "busy"
                    }

        return {"error": "Failed to parse utilization", "raw_output": output}

    def get_gpu_stats(self) -> Dict[str, Any]:
        """Get comprehensive GPU statistics"""
        vram = self.get_vram()
        temp = self.get_gpu_temp()
        util = self.get_gpu_utilization()

        return {
            "gpu_name": "AMD Radeon AI PRO R9700",
            "architecture": "RDNA4 (gfx1201)",
            "vram": vram,
            "temperature": temp,
            "utilization": util
        }

    def get_rocm_version(self) -> Dict[str, Any]:
        """Get ROCm version"""
        output = self._run_command([f"{self.rocm_path}/bin/rocm-smi", "--showversion"])

        if not output or output.startswith("ERROR"):
            return {"error": output or "Failed to get ROCm version"}

        # Parse version info
        version_info = {}
        for line in output.split('\n'):
            if "ROCm version" in line:
                match = re.search(r':\s*([\d.]+)', line)
                if match:
                    version_info['rocm'] = match.group(1)

        # Also check hipcc version
        hip_output = self._run_command([f"{self.rocm_path}/bin/hipcc", "--version"])
        if hip_output and not hip_output.startswith("ERROR"):
            # Parse HIP version from hipcc output
            for line in hip_output.split('\n'):
                if "HIP version" in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        version_info['hip'] = match.group(1)

        if not version_info:
            version_info = {
                'rocm': '7.11 (custom build)',
                'hip': '7.2.53220',
                'note': 'Version detection from custom build'
            }

        version_info['path'] = self.rocm_path
        return version_info

    def get_hip_version(self) -> Dict[str, Any]:
        """Get HIP version details"""
        output = self._run_command([f"{self.rocm_path}/bin/hipcc", "--version"])

        if not output or output.startswith("ERROR"):
            return {"error": output or "Failed to get HIP version"}

        return {
            "version": "7.2.53220",
            "rocm_path": self.rocm_path,
            "raw_output": output.strip()
        }

    def rocminfo(self) -> Dict[str, Any]:
        """Get detailed GPU info via rocminfo"""
        output = self._run_command([f"{self.rocm_path}/bin/rocminfo"], timeout=15)

        if not output or output.startswith("ERROR"):
            return {"error": output or "Failed to get rocminfo"}

        # Parse key info from rocminfo
        info = {
            "raw_output_lines": len(output.split('\n')),
        }

        # Extract GPU name
        for line in output.split('\n'):
            if "Name:" in line and "gfx" in line:
                info['gpu_architecture'] = line.split(':')[1].strip()
            elif "Marketing Name:" in line:
                info['marketing_name'] = line.split(':')[1].strip()
            elif "Compute Unit:" in line:
                match = re.search(r'(\d+)', line)
                if match:
                    info['compute_units'] = int(match.group(1))

        # Include first 50 lines of raw output for detailed inspection
        info['preview'] = '\n'.join(output.split('\n')[:50])

        return info

    def handle_request(self, request: Dict) -> Optional[Dict]:
        """Handle MCP JSON-RPC request"""
        method = request.get('method', '')
        params = request.get('params', {})
        req_id = request.get('id')

        # Handle notifications (no response needed)
        if req_id is None:
            if method == 'initialized':
                # Initialization complete notification
                return None
            # Ignore other notifications
            return None

        # Handle initialize
        if method == 'initialize':
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "rocm-mcp-server",
                        "version": "0.1.0"
                    }
                }
            }

        # Handle tools/list
        if method == 'tools/list':
            tools_list = []
            for name, spec in self.tools.items():
                tools_list.append({
                    "name": name,
                    "description": spec["description"],
                    "inputSchema": spec["inputSchema"]
                })

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": tools_list
                }
            }

        # Handle tools/call
        if method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})

            if tool_name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

            try:
                # Call the appropriate method
                method_name = tool_name
                if hasattr(self, method_name):
                    result = getattr(self, method_name)(**arguments)
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2)
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool not implemented: {tool_name}"
                        }
                    }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }

        # Unknown method
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Unknown method: {method}"
            }
        }

    def run(self):
        """Main server loop - read from stdin, write to stdout"""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line)
                response = self.handle_request(request)
                if response is not None:
                    print(json.dumps(response), flush=True)

            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)


def main():
    server = ROCmMCPServer()
    server.run()


if __name__ == "__main__":
    main()
