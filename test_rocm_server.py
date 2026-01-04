#!/usr/bin/env python3
"""
Test ROCm MCP Server
Standalone test to verify ROCm server works correctly
"""

import json
import subprocess
import sys


def test_rocm_server():
    """Test the ROCm MCP server"""

    print("=" * 70)
    print("ROCm MCP Server Test")
    print("=" * 70)

    # Start the server
    print("\n1. Starting ROCm MCP server...")
    server = subprocess.Popen(
        ["python3", "/home/hashcat/TheRock/tools/rocm-cli/mcp_servers/rocm_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    def send_request(method, params=None):
        """Send JSON-RPC request to server"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }

        server.stdin.write(json.dumps(request) + "\n")
        server.stdin.flush()

        response_line = server.stdout.readline()
        return json.loads(response_line)

    try:
        # Test 1: Initialize
        print("\n2. Initializing server...")
        response = send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "0.1.0"}
        })
        print(f"   ✓ Server initialized: {response['result']['serverInfo']['name']}")

        # Test 2: List tools
        print("\n3. Listing available tools...")
        response = send_request("tools/list")
        tools = response['result']['tools']
        print(f"   ✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"     - {tool['name']}: {tool['description']}")

        # Test 3: Get VRAM
        print("\n4. Testing get_vram...")
        response = send_request("tools/call", {
            "name": "get_vram",
            "arguments": {}
        })
        vram_data = json.loads(response['result']['content'][0]['text'])
        print(f"   ✓ VRAM: {vram_data.get('used_gb', 'N/A')} GB used / {vram_data.get('total_gb', 'N/A')} GB total")
        print(f"     Free: {vram_data.get('free_gb', 'N/A')} GB ({vram_data.get('utilization_percent', 'N/A')}% used)")

        # Test 4: Get temperature
        print("\n5. Testing get_gpu_temp...")
        response = send_request("tools/call", {
            "name": "get_gpu_temp",
            "arguments": {}
        })
        temp_data = json.loads(response['result']['content'][0]['text'])
        print(f"   ✓ GPU Temperature: {temp_data.get('temperature_c', 'N/A')}°C ({temp_data.get('temperature_f', 'N/A')}°F)")
        print(f"     Status: {temp_data.get('status', 'unknown')}")

        # Test 5: Get GPU stats
        print("\n6. Testing get_gpu_stats...")
        response = send_request("tools/call", {
            "name": "get_gpu_stats",
            "arguments": {}
        })
        stats_data = json.loads(response['result']['content'][0]['text'])
        print(f"   ✓ GPU: {stats_data.get('gpu_name', 'N/A')}")
        print(f"     Architecture: {stats_data.get('architecture', 'N/A')}")
        if 'utilization' in stats_data:
            util = stats_data['utilization']
            print(f"     Utilization: {util.get('utilization_percent', 'N/A')}% ({util.get('status', 'unknown')})")

        # Test 6: Get ROCm version
        print("\n7. Testing get_rocm_version...")
        response = send_request("tools/call", {
            "name": "get_rocm_version",
            "arguments": {}
        })
        version_data = json.loads(response['result']['content'][0]['text'])
        print(f"   ✓ ROCm: {version_data.get('rocm', 'N/A')}")
        print(f"     HIP: {version_data.get('hip', 'N/A')}")
        print(f"     Path: {version_data.get('path', 'N/A')}")

        print("\n" + "=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        server.terminate()
        server.wait()


if __name__ == "__main__":
    test_rocm_server()
