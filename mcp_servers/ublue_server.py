#!/usr/bin/env python3
"""
Universal Blue MCP Server
Tools for Universal Blue, Bazzite, Aurora, Bluefin management and building

Integrates with:
- rpm-ostree (atomic updates)
- ujust (recipe runner)
- bootc (bootable containers)
- podman (container builds)
- GitHub Actions (CI/CD)
- CoreOS tooling (ISO builds)

Supports:
- Image metadata and status
- Build orchestration
- ISO generation
- Custom recipe management
- Gaming tools (Bazzite)
- Dev tools (Aurora)
"""

import subprocess
import json
import sys
import os
import re
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime


class UBlueServer:
    """MCP server for Universal Blue operations"""

    def __init__(self):
        self.name = "ublue-server"
        self.version = "0.1.0"

    def _run_command(self, cmd: list[str], capture_json=False) -> str:
        """Run a shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout if result.returncode == 0 else result.stderr

            if capture_json:
                try:
                    return json.dumps(json.loads(output), indent=2)
                except:
                    return output

            return output
        except Exception as e:
            return f"ERROR: {e}"

    # ==================== Image Information ====================

    def get_image_info(self) -> str:
        """Get current Universal Blue image information"""
        # Get rpm-ostree status
        status_json = self._run_command(["rpm-ostree", "status", "--json"])

        try:
            data = json.loads(status_json)
            deployments = data.get('deployments', [])

            if not deployments:
                return json.dumps({"error": "No deployments found"})

            current = deployments[0]

            # Extract image info
            origin = current.get('origin', '')
            version = current.get('version', 'unknown')
            checksum = current.get('checksum', '')[:12]
            timestamp = current.get('timestamp', 0)

            # Parse origin for image details
            # Format: ostree-image-signed:docker://ghcr.io/ublue-os/bazzite:stable
            image_url = "unknown"
            if 'docker://' in origin:
                image_url = origin.split('docker://')[-1]

            # Get layered packages
            layered = current.get('requested-packages', [])

            # Format timestamp
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                formatted_time = "unknown"

            result = {
                "image": image_url,
                "version": version,
                "checksum": checksum,
                "deployed": formatted_time,
                "layered_packages": len(layered),
                "packages": layered[:10] if layered else [],
                "origin": origin
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    def check_image_updates(self) -> str:
        """Check for new Universal Blue image builds"""
        # Check for updates
        output = self._run_command(["rpm-ostree", "upgrade", "--check"])

        if "No upgrade available" in output or "No updates available" in output:
            return json.dumps({
                "updates_available": False,
                "message": "Image is up to date",
                "current_image": self._get_current_image()
            })
        else:
            return json.dumps({
                "updates_available": True,
                "details": output,
                "current_image": self._get_current_image()
            })

    def _get_current_image(self) -> str:
        """Helper: Get current image name"""
        try:
            status = self._run_command(["rpm-ostree", "status", "--json"])
            data = json.loads(status)
            origin = data['deployments'][0].get('origin', '')
            if 'docker://' in origin:
                return origin.split('docker://')[-1]
            return "unknown"
        except:
            return "unknown"

    # ==================== ujust Integration ====================

    def list_ujust_recipes(self) -> str:
        """List available ujust recipes"""
        # ujust --list
        output = self._run_command(["ujust", "--list"])

        recipes = []
        for line in output.split('\n'):
            line = line.strip()
            if line and not line.startswith('Available recipes:'):
                # Parse recipe name and description
                parts = line.split('#', 1)
                if parts:
                    recipe = parts[0].strip()
                    desc = parts[1].strip() if len(parts) > 1 else ""
                    recipes.append({"name": recipe, "description": desc})

        return json.dumps({
            "count": len(recipes),
            "recipes": recipes
        }, indent=2)

    def run_ujust_recipe(self, recipe: str) -> str:
        """Run a ujust recipe"""
        # Safety check - only allow certain safe recipes
        safe_recipes = [
            "update", "changelogs", "distrobox-assemble",
            "setup-gaming", "setup-flatpaks", "check-updates",
            "bazzite-rollback-helper"
        ]

        if recipe not in safe_recipes:
            return json.dumps({
                "error": f"Recipe '{recipe}' not in safe list. Use 'list_ujust_recipes' to see available recipes.",
                "safe_recipes": safe_recipes
            })

        output = self._run_command(["ujust", recipe])

        return json.dumps({
            "recipe": recipe,
            "output": output[:2000]  # Limit output
        })

    def get_ujust_info(self) -> str:
        """Get ujust configuration and status"""
        # Check if ujust is installed
        which = self._run_command(["which", "ujust"])

        if "not found" in which:
            return json.dumps({"installed": False})

        # Get justfile location
        justfile_paths = [
            "/usr/share/ublue-os/just",
            "/etc/justfile",
            str(Path.home() / ".justfile")
        ]

        found_justfile = None
        for path in justfile_paths:
            if Path(path).exists():
                found_justfile = path
                break

        return json.dumps({
            "installed": True,
            "ujust_path": which.strip(),
            "justfile": found_justfile,
            "recipes_available": "run list_ujust_recipes"
        })

    # ==================== Build Information ====================

    def get_build_info(self) -> str:
        """Get information about the current build/image"""
        # Get /usr/share/ublue-os metadata if it exists
        metadata_path = Path("/usr/share/ublue-os/image-info.json")

        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    return f.read()
            except:
                pass

        # Fallback: parse from rpm-ostree
        return self.get_image_info()

    def check_build_type(self) -> str:
        """Detect which Universal Blue variant is running"""
        # Check /etc/os-release
        os_release = {}
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os_release[key] = value.strip('"')
        except:
            pass

        variant = "unknown"
        name = os_release.get('NAME', '').lower()
        pretty_name = os_release.get('PRETTY_NAME', '').lower()

        # Detect variant
        if 'bazzite' in name or 'bazzite' in pretty_name:
            variant = "bazzite"
        elif 'aurora' in name or 'aurora' in pretty_name:
            variant = "aurora"
        elif 'bluefin' in name or 'bluefin' in pretty_name:
            variant = "bluefin"
        elif 'silverblue' in name or 'silverblue' in pretty_name:
            variant = "silverblue"
        elif 'kinoite' in name or 'kinoite' in pretty_name:
            variant = "kinoite"

        return json.dumps({
            "variant": variant,
            "name": os_release.get('NAME', 'unknown'),
            "version": os_release.get('VERSION', 'unknown'),
            "version_id": os_release.get('VERSION_ID', 'unknown'),
            "pretty_name": os_release.get('PRETTY_NAME', 'unknown'),
            "image_name": os_release.get('IMAGE_NAME', 'unknown'),
            "image_vendor": os_release.get('IMAGE_VENDOR', 'unknown')
        }, indent=2)

    # ==================== Gaming Tools (Bazzite) ====================

    def get_gaming_status(self) -> str:
        """Get gaming-related status (Bazzite-specific)"""
        status = {}

        # Check Steam
        steam_check = self._run_command(["which", "steam"])
        status['steam_installed'] = "not found" not in steam_check

        # Check Proton versions (if Steam is installed)
        if status['steam_installed']:
            proton_path = Path.home() / ".steam/steam/compatibilitytools.d"
            if proton_path.exists():
                proton_versions = [d.name for d in proton_path.iterdir() if d.is_dir()]
                status['proton_versions'] = proton_versions
            else:
                status['proton_versions'] = []

        # Check GameMode
        gamemode_check = self._run_command(["which", "gamemoderun"])
        status['gamemode_installed'] = "not found" not in gamemode_check

        # Check MangoHud
        mangohud_check = self._run_command(["which", "mangohud"])
        status['mangohud_installed'] = "not found" not in mangohud_check

        # Check Lutris
        lutris_check = self._run_command(["which", "lutris"])
        status['lutris_installed'] = "not found" not in lutris_check

        return json.dumps(status, indent=2)

    # ==================== ISO Building ====================

    def check_build_tools(self) -> str:
        """Check if ISO build tools are available"""
        tools = {}

        # Check bootc
        bootc = self._run_command(["which", "bootc"])
        tools['bootc'] = "not found" not in bootc

        # Check podman
        podman = self._run_command(["which", "podman"])
        tools['podman'] = "not found" not in podman

        # Check buildah
        buildah = self._run_command(["which", "buildah"])
        tools['buildah'] = "not found" not in buildah

        # Check mkosi
        mkosi = self._run_command(["which", "mkosi"])
        tools['mkosi'] = "not found" not in mkosi

        # Check lorax
        lorax = self._run_command(["which", "lorax"])
        tools['lorax'] = "not found" not in lorax

        # Check if we have container build capability
        tools['can_build_containers'] = tools['podman'] or tools['buildah']

        # Check if we have ISO build capability
        tools['can_build_isos'] = tools['bootc'] or tools['mkosi'] or tools['lorax']

        return json.dumps(tools, indent=2)

    def list_container_images(self) -> str:
        """List local container images (for building)"""
        output = self._run_command(["podman", "images", "--format", "json"])

        try:
            images = json.loads(output)

            # Filter for relevant images
            ublue_images = []
            for img in images:
                names = img.get('Names', [])
                for name in names:
                    if any(x in name.lower() for x in ['ublue', 'bazzite', 'aurora', 'bluefin', 'silverblue']):
                        ublue_images.append({
                            'name': name,
                            'id': img.get('Id', '')[:12],
                            'created': img.get('Created', ''),
                            'size': img.get('Size', 0)
                        })

            return json.dumps({
                "total_images": len(images),
                "ublue_images": len(ublue_images),
                "images": ublue_images
            }, indent=2)
        except:
            return output

    def get_containerfile_template(self, variant: str = "base") -> str:
        """Get a Containerfile template for building custom images"""

        templates = {
            "base": """# Universal Blue Custom Image
ARG IMAGE_NAME="${IMAGE_NAME:-silverblue}"
ARG SOURCE_IMAGE="${SOURCE_IMAGE:-silverblue-main}"
ARG SOURCE_SUFFIX="${SOURCE_SUFFIX:-}"
ARG FEDORA_MAJOR_VERSION="${FEDORA_MAJOR_VERSION:-40}"
ARG BASE_IMAGE_URL="${BASE_IMAGE_URL:-ghcr.io/ublue-os}"

FROM ${BASE_IMAGE_URL}/${SOURCE_IMAGE}${SOURCE_SUFFIX}:${FEDORA_MAJOR_VERSION}

# Copy build files
COPY build.sh /tmp/build.sh
COPY custom-packages.txt /tmp/custom-packages.txt

# Run build script
RUN chmod +x /tmp/build.sh && /tmp/build.sh

# Install custom packages
RUN rpm-ostree install $(cat /tmp/custom-packages.txt)

# Cleanup
RUN rm -rf /tmp/* /var/*
RUN ostree container commit
""",
            "bazzite": """# Bazzite Custom Gaming Image
ARG FEDORA_MAJOR_VERSION="${FEDORA_MAJOR_VERSION:-40}"

FROM ghcr.io/ublue-os/bazzite:${FEDORA_MAJOR_VERSION}

# Add custom gaming packages
RUN rpm-ostree install \\
    game-package-1 \\
    game-package-2

# Custom gaming configurations
COPY gaming-configs/ /etc/gaming/

RUN ostree container commit
""",
            "aurora": """# Aurora Custom Developer Image
ARG FEDORA_MAJOR_VERSION="${FEDORA_MAJOR_VERSION:-40}"

FROM ghcr.io/ublue-os/aurora:${FEDORA_MAJOR_VERSION}

# Add dev tools
RUN rpm-ostree install \\
    rust \\
    golang \\
    nodejs

# Install VSCode extensions
COPY vscode-extensions.txt /tmp/
RUN cat /tmp/vscode-extensions.txt | xargs -L1 code --install-extension

RUN ostree container commit
"""
        }

        template = templates.get(variant, templates["base"])

        return json.dumps({
            "variant": variant,
            "template": template,
            "description": f"Containerfile template for {variant} custom image"
        })

    # ==================== GitHub Actions Integration ====================

    def get_github_workflow_template(self) -> str:
        """Get GitHub Actions workflow template for building UBlue images"""

        workflow = """name: Build Custom Image
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  push:
    branches:
      - main
    paths-ignore:
      - '**.md'
  pull_request:
  workflow_dispatch:

env:
  IMAGE_REGISTRY: ghcr.io/${{ github.repository_owner }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build Image
        id: build
        uses: redhat-actions/buildah-build@v2
        with:
          containerfiles: ./Containerfile
          image: custom-image
          tags: |
            latest
            ${{ github.sha }}
          oci: true

      - name: Push to Registry
        uses: redhat-actions/push-to-registry@v2
        with:
          image: ${{ steps.build.outputs.image }}
          tags: ${{ steps.build.outputs.tags }}
          registry: ${{ env.IMAGE_REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Sign Image
        run: |
          cosign sign --yes \\
            ${{ env.IMAGE_REGISTRY }}/${{ steps.build.outputs.image }}@${{ steps.build.outputs.digest }}
"""

        return json.dumps({
            "workflow": workflow,
            "file": ".github/workflows/build.yml",
            "description": "GitHub Actions workflow for automated image builds"
        })

    # ==================== MCP Protocol Methods ====================

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
                # Image Information
                {
                    "name": "get_image_info",
                    "description": "Get current Universal Blue image information (version, source, packages)",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "check_image_updates",
                    "description": "Check for new Universal Blue image builds available",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "check_build_type",
                    "description": "Detect which Universal Blue variant is running (Bazzite/Aurora/Bluefin)",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "get_build_info",
                    "description": "Get detailed build/image metadata",
                    "inputSchema": {"type": "object", "properties": {}}
                },

                # ujust Integration
                {
                    "name": "list_ujust_recipes",
                    "description": "List all available ujust recipes for Universal Blue",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "run_ujust_recipe",
                    "description": "Run a specific ujust recipe (safe recipes only)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "recipe": {
                                "type": "string",
                                "description": "Recipe name (e.g., 'update', 'changelogs')"
                            }
                        },
                        "required": ["recipe"]
                    }
                },
                {
                    "name": "get_ujust_info",
                    "description": "Get ujust installation and configuration status",
                    "inputSchema": {"type": "object", "properties": {}}
                },

                # Gaming (Bazzite)
                {
                    "name": "get_gaming_status",
                    "description": "Get gaming tools status (Steam, Proton, GameMode, MangoHud) - Bazzite",
                    "inputSchema": {"type": "object", "properties": {}}
                },

                # Build Tools
                {
                    "name": "check_build_tools",
                    "description": "Check if ISO/container build tools are available (bootc, podman, mkosi, lorax)",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "list_container_images",
                    "description": "List local container images (for custom builds)",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "get_containerfile_template",
                    "description": "Get Containerfile template for building custom images",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "variant": {
                                "type": "string",
                                "description": "Image variant (base/bazzite/aurora)",
                                "enum": ["base", "bazzite", "aurora"]
                            }
                        }
                    }
                },
                {
                    "name": "get_github_workflow_template",
                    "description": "Get GitHub Actions workflow template for automated builds",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]
        }

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> list:
        """Execute a tool and return result"""

        tool_map = {
            "get_image_info": lambda: self.get_image_info(),
            "check_image_updates": lambda: self.check_image_updates(),
            "check_build_type": lambda: self.check_build_type(),
            "get_build_info": lambda: self.get_build_info(),
            "list_ujust_recipes": lambda: self.list_ujust_recipes(),
            "run_ujust_recipe": lambda: self.run_ujust_recipe(arguments.get('recipe', '')),
            "get_ujust_info": lambda: self.get_ujust_info(),
            "get_gaming_status": lambda: self.get_gaming_status(),
            "check_build_tools": lambda: self.check_build_tools(),
            "list_container_images": lambda: self.list_container_images(),
            "get_containerfile_template": lambda: self.get_containerfile_template(arguments.get('variant', 'base')),
            "get_github_workflow_template": lambda: self.get_github_workflow_template(),
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
    server = UBlueServer()
    server.run()
