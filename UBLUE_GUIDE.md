# Universal Blue Integration Guide

**Complete guide to building custom immutable OS images with rai**

---

## Table of Contents

1. [Introduction](#introduction)
2. [What is Universal Blue?](#what-is-universal-blue)
3. [Getting Started](#getting-started)
4. [Query Reference](#query-reference)
5. [Build Workflow](#build-workflow)
6. [ujust Integration](#ujust-integration)
7. [Gaming Features (Bazzite)](#gaming-features-bazzite)
8. [Developer Features (Aurora)](#developer-features-aurora)
9. [GitHub Actions CI/CD](#github-actions-cicd)
10. [Examples](#examples)
11. [Troubleshooting](#troubleshooting)

---

## Introduction

**rai** provides comprehensive tooling for Universal Blue ecosystem development through its **ublue MCP server** (12 tools). Build custom immutable OS images, generate ISOs, and deploy cloud-native systems with GitOps workflows.

**Key Capabilities:**
- 🔵 Query current UBlue deployment information
- 🔨 Check build tool availability (bootc, podman, mkosi)
- 📝 Generate Containerfile templates (Bazzite, Aurora, base)
- ⚙️ Create GitHub Actions workflows for automated builds
- 📦 List and manage container images
- 🎮 Gaming tools status (Bazzite-specific)
- 📜 ujust recipe management

---

## What is Universal Blue?

**Universal Blue** is a community project building cloud-native, immutable desktop OS images based on Fedora Atomic.

### Core Concepts

**Immutable Infrastructure:**
- Read-only root filesystem
- Atomic updates (all-or-nothing)
- Rollback to previous deployment
- No package manager mutations (use containers instead)

**Container-Based OS:**
- OS is an OCI container image
- Built with standard container tools (podman, buildah)
- Hosted on GitHub Container Registry
- Deployed with rpm-ostree or bootc

**Variants:**
- **Bazzite** - Gaming-focused (Steam, Proton, GameMode)
- **Aurora** - Developer workstation (KDE Plasma 6)
- **Bluefin** - General desktop (GNOME)
- **Silverblue** - Upstream Fedora atomic (GNOME)
- **Kinoite** - Upstream Fedora atomic (KDE)

### Build Pipeline

```
┌─────────────────────────────────────────────────────────┐
│ 1. DEVELOP (Your Development Machine)                  │
│    - Write Containerfile                                │
│    - Define packages, configs, scripts                  │
│    - Test locally with podman                           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. BUILD (GitHub Actions or Local)                     │
│    - podman build → OCI image                           │
│    - Push to ghcr.io/username/custom-image             │
│    - Sign with cosign (optional, recommended)           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. GENERATE ISO (bootc install to-disk)                │
│    - bootc install to-disk --image ghcr.io/...         │
│    - Creates bootable ISO/disk image                    │
│    - Ready for installation                             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. DEPLOY (Target System)                              │
│    - Boot from ISO                                      │
│    - Or: rpm-ostree rebase ghcr.io/...                 │
│    - Immutable rootfs activated                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 5. UPDATE (Pull New Image)                             │
│    - rpm-ostree upgrade (or automatic)                  │
│    - Reboot into new deployment                         │
│    - Previous version available for rollback            │
└─────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

**Development System (Standard Fedora):**
- Fedora 43+ or compatible Linux
- Podman or Docker installed
- Git for version control
- rai with ublue MCP server

**Optional (for ISO building):**
- bootc (`dnf install bootc`)
- mkosi (`dnf install mkosi`)
- lorax (`dnf install lorax`)

### Installation

```bash
# Clone rai (if not already installed)
git clone https://github.com/tlee933/rai.git
cd rai
pip install -r requirements.txt

# ublue_server.py should already be in mcp_servers/
ls mcp_servers/ublue_server.py

# Test rai with ublue integration
rai "check build tools"
```

### Quick Start

```bash
# Check what build tools are available
rai "check build tools"

# Get a Containerfile template for Aurora (KDE Plasma 6)
rai "show containerfile template for aurora"

# Get GitHub Actions workflow template
rai "show github workflow"

# Check if ujust is available (for UBlue systems)
rai "list ujust recipes"
```

---

## Query Reference

### Image Information

**Query current UBlue image (on UBlue system):**
```bash
rai "show ublue image"
rai "show universal blue info"
rai "check ublue status"
```

**Output:**
```
🔵 Universal Blue Image:
======================================================================
Image:    ghcr.io/ublue-os/aurora:40
Version:  40.20250103
Deployed: 2025-01-03 14:23:45
Layered:  3 packages

Layered packages:
  • vim-enhanced
  • tmux
  • htop
```

**Check for image updates:**
```bash
rai "check ublue updates"
rai "check image updates"
```

**Show build type/variant:**
```bash
rai "show build type"
rai "show system type"
rai "show variant type"
```

**Output:**
```
🔵 System Variant:
======================================================================
Variant:      Aurora
Name:         Aurora (Developer Edition)
Version:      40
Pretty Name:  Universal Blue Aurora 40
```

### Build Tools

**Check available build tools:**
```bash
rai "check build tools"
```

**Output:**
```
🔨 Build Tools:
======================================================================
bootc:    ✓ Available
podman:   ✓ Available
buildah:  ✓ Available
mkosi:    ✗ Not available
lorax:    ✗ Not available

Can build containers: Yes
Can build ISOs:       No (install bootc or mkosi)
```

**List local container images:**
```bash
rai "list ublue images"
rai "list container images"
```

### Templates

**Get Containerfile template:**
```bash
rai "show containerfile template"               # Base template
rai "show containerfile template for bazzite"   # Bazzite gaming
rai "show containerfile template for aurora"    # Aurora developer
```

**Get GitHub Actions workflow:**
```bash
rai "show github workflow"
rai "get github workflow template"
```

### ujust Recipes

**List available recipes:**
```bash
rai "list ujust recipes"
```

**Run a recipe (whitelisted only):**
```bash
rai "run ujust update"
rai "execute ujust setup-gaming"
```

**Safe recipes:**
- `update` - System update
- `changelogs` - Show changelogs
- `distrobox-assemble` - Setup distrobox
- `setup-gaming` - Gaming tools setup (Bazzite)
- `setup-flatpaks` - Flatpak setup
- `check-updates` - Check for updates
- `bazzite-rollback-helper` - Rollback helper

### Gaming Status (Bazzite)

**Check gaming tools:**
```bash
rai "check gaming status"
rai "show gaming tools"
```

**Output:**
```
🎮 Gaming Status:
======================================================================
Steam:     ✓ Installed
GameMode:  ✓ Installed
MangoHud:  ✓ Installed
Lutris:    ✓ Installed

Proton versions (5):
  • Proton-9.0
  • Proton-8.0
  • Proton-7.0
  • Proton Experimental
  • GE-Proton
```

---

## Build Workflow

### 1. Development Phase

**On your standard Fedora development machine:**

```bash
# Create project directory
mkdir ~/my-custom-aurora
cd ~/my-custom-aurora

# Get Containerfile template
rai "show containerfile template for aurora" > Containerfile

# Edit Containerfile
vim Containerfile

# Test build locally
podman build -t my-aurora:test .

# Test image in container
podman run --rm -it my-aurora:test bash
```

### 2. GitHub Repository Setup

**Initialize repository:**

```bash
# Initialize git
git init
git add Containerfile
git commit -m "Initial Containerfile for custom Aurora"

# Create GitHub repo
gh repo create my-custom-aurora --public

# Push
git remote add origin https://github.com/username/my-custom-aurora.git
git push -u origin main
```

**Add GitHub Actions workflow:**

```bash
# Get workflow template
rai "show github workflow" > .github/workflows/build.yml

# Commit and push
git add .github/workflows/build.yml
git commit -m "Add GitHub Actions workflow"
git push
```

### 3. Automated Building

**GitHub Actions will automatically:**
1. Build container image on push/schedule
2. Push to ghcr.io/username/my-custom-aurora
3. Sign with cosign (if configured)
4. Create versioned tags

**Monitor build:**
```bash
gh run list
gh run view --log
```

### 4. ISO Generation

**Using bootc:**

```bash
# Pull your custom image
podman pull ghcr.io/username/my-custom-aurora:latest

# Generate bootable ISO
sudo bootc install to-disk \
  --image ghcr.io/username/my-custom-aurora:latest \
  --output my-aurora.iso

# Resulting ISO is ready for installation
```

**Using mkosi:**

```bash
# Create mkosi.conf
cat > mkosi.conf << EOF
[Distribution]
Distribution=fedora
Release=40

[Output]
ImageId=my-aurora
ImageVersion=1.0
Format=disk

[Content]
BaseImage=ghcr.io/username/my-custom-aurora:latest
EOF

# Build ISO
mkosi build
```

### 5. Deployment

**Option A: Install from ISO**
- Boot from ISO
- Follow installation prompts
- System boots into your custom image

**Option B: Rebase existing system**
```bash
# On an existing Fedora Atomic system
rpm-ostree rebase ostree-image-signed:docker://ghcr.io/username/my-custom-aurora:latest

# Reboot
systemctl reboot
```

### 6. Updates

**Automatic updates:**
- rpm-ostree auto-updates enabled by default
- Pulls new image from registry daily
- Applies on reboot

**Manual update:**
```bash
# Check for updates
rai "check ublue updates"

# Update
rpm-ostree upgrade

# Reboot
systemctl reboot
```

**Rollback:**
```bash
# Rollback to previous deployment
rpm-ostree rollback

# Reboot
systemctl reboot
```

---

## ujust Integration

### What is ujust?

**ujust** is a command runner (like `make` or `just`) used by Universal Blue for common operations.

**Location:** `/usr/share/ublue-os/justfile`

### Common Recipes

**System management:**
```bash
rai "run ujust update"              # Full system update
rai "run ujust check-updates"       # Check for updates
```

**Gaming (Bazzite):**
```bash
rai "run ujust setup-gaming"        # Setup gaming tools
```

**Containers:**
```bash
rai "run ujust distrobox-assemble"  # Setup distrobox
```

**Information:**
```bash
rai "run ujust changelogs"          # Show recent changelogs
```

### Safety

**rai only allows whitelisted recipes** to prevent destructive operations.

**Whitelisted recipes:**
- `update`
- `changelogs`
- `distrobox-assemble`
- `setup-gaming`
- `setup-flatpaks`
- `check-updates`
- `bazzite-rollback-helper`

**To run other recipes, use ujust directly:**
```bash
ujust --list                        # List all recipes
ujust recipe-name                   # Run any recipe
```

---

## Gaming Features (Bazzite)

### What is Bazzite?

**Bazzite** is a Universal Blue variant optimized for gaming:
- Steam pre-installed
- Proton configured
- GameMode for performance
- MangoHud for overlays
- Lutris for non-Steam games
- Game launchers (Heroic, Bottles)

### Check Gaming Status

```bash
rai "check gaming status"
```

### Setup Gaming Tools

```bash
# Run ujust gaming setup (Bazzite only)
rai "run ujust setup-gaming"
```

### Custom Bazzite Image

**Containerfile template:**
```dockerfile
ARG FEDORA_MAJOR_VERSION="${FEDORA_MAJOR_VERSION:-40}"
FROM ghcr.io/ublue-os/bazzite:${FEDORA_MAJOR_VERSION}

# Add custom gaming packages
RUN rpm-ostree install \
    steam-devices \
    gamemode \
    mangohud

# Add custom game launchers
RUN rpm-ostree install \
    lutris \
    heroic-games-launcher-bin

# Add ROCm for AMD GPU gaming
RUN rpm-ostree install \
    rocm-hip \
    rocm-opencl

RUN ostree container commit
```

---

## Developer Features (Aurora)

### What is Aurora?

**Aurora** is a Universal Blue variant for developers:
- KDE Plasma 6 desktop
- Developer tools pre-installed
- Distrobox/Toolbox integration
- Modern terminal (Kitty)
- Code editors (VS Code, etc.)

### Custom Aurora Image

**Containerfile template:**
```dockerfile
ARG FEDORA_MAJOR_VERSION="${FEDORA_MAJOR_VERSION:-40}"
FROM ghcr.io/ublue-os/aurora:${FEDORA_MAJOR_VERSION}

# Add dev tools
RUN rpm-ostree install \
    rust \
    golang \
    nodejs \
    python3-pip

# Add ROCm development tools
RUN rpm-ostree install \
    rocm-hip-devel \
    rocm-opencl-devel \
    hipcc

# Add custom utilities
RUN rpm-ostree install \
    vim-enhanced \
    tmux \
    htop \
    neofetch

RUN ostree container commit
```

### Development Workflow

**Use Distrobox for isolated environments:**
```bash
# Create dev container
distrobox create --name dev-fedora --image fedora:40

# Enter container
distrobox enter dev-fedora

# Install packages inside container (no rpm-ostree)
sudo dnf install gcc make cmake
```

---

## GitHub Actions CI/CD

### Workflow Template

```bash
# Get workflow template
rai "show github workflow" > .github/workflows/build.yml
```

**Generated workflow:**
```yaml
name: Build Custom Image
on:
  schedule:
    - cron: '0 0 * * *'  # Daily builds
  push:
    branches: [main]
  workflow_dispatch:

env:
  IMAGE_REGISTRY: ghcr.io/${{ github.repository_owner }}

jobs:
  build:
    name: Build and Push Image
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
          cosign sign --yes \
            ${{ env.IMAGE_REGISTRY }}/${{ steps.build.outputs.image }}@${{ steps.build.outputs.digest }}
```

### UEFI Secure Boot Signing

**Universal Blue provides signing keys:**

If you're granted access to Universal Blue's UEFI signing key:

```yaml
# Add to workflow after build
- name: Sign for Secure Boot
  uses: ublue-os/signing-action@v1
  with:
    image: ${{ steps.build.outputs.image }}
    registry: ghcr.io
```

**Benefits:**
- Boot on secure boot enabled systems
- No manual key enrollment
- Trusted by Universal Blue infrastructure

---

## Examples

### Example 1: Custom Aurora for AI Development

**Containerfile:**
```dockerfile
ARG FEDORA_MAJOR_VERSION="40"
FROM ghcr.io/ublue-os/aurora:${FEDORA_MAJOR_VERSION}

# ROCm for AMD GPU AI workloads
RUN rpm-ostree install \
    rocm-hip \
    rocm-hip-devel \
    rocm-opencl \
    rocm-opencl-devel \
    hipcc \
    rocm-smi

# AI/ML tools
RUN rpm-ostree install \
    python3-pip \
    python3-devel \
    git-lfs

# Development utilities
RUN rpm-ostree install \
    vim-enhanced \
    tmux \
    htop \
    nvtop

RUN ostree container commit

# Metadata
LABEL org.opencontainers.image.title="Aurora AI Dev"
LABEL org.opencontainers.image.description="Aurora with ROCm for AI development"
```

**Build and deploy:**
```bash
# Get template
rai "show containerfile template for aurora" > Containerfile

# Edit as above
vim Containerfile

# Build locally
podman build -t aurora-ai:test .

# Test
podman run --rm -it aurora-ai:test bash

# Push to GitHub, let Actions build
git add Containerfile
git commit -m "Aurora AI dev image"
git push
```

### Example 2: Custom Bazzite for ROCm Gaming

**Containerfile:**
```dockerfile
ARG FEDORA_MAJOR_VERSION="40"
FROM ghcr.io/ublue-os/bazzite:${FEDORA_MAJOR_VERSION}

# ROCm for AMD GPU acceleration
RUN rpm-ostree install \
    rocm-hip \
    rocm-opencl \
    rocm-smi

# Additional gaming tools
RUN rpm-ostree install \
    mangohud \
    gamemode \
    gamescope

# Emulators
RUN rpm-ostree install \
    retroarch \
    pcsx2 \
    dolphin-emu

RUN ostree container commit

LABEL org.opencontainers.image.title="Bazzite ROCm Gaming"
LABEL org.opencontainers.image.description="Bazzite with ROCm optimization"
```

### Example 3: Minimal Base Image

**Containerfile:**
```dockerfile
ARG FEDORA_MAJOR_VERSION="40"
FROM quay.io/fedora/fedora-silverblue:${FEDORA_MAJOR_VERSION}

# Minimal additions
RUN rpm-ostree install \
    vim-enhanced \
    tmux \
    htop

RUN ostree container commit

LABEL org.opencontainers.image.title="Minimal Atomic"
LABEL org.opencontainers.image.description="Minimal immutable Fedora"
```

---

## Troubleshooting

### ublue queries return "not applicable"

**Issue:** Running ublue queries on standard Fedora (not atomic)

**Expected behavior:**
- Image queries won't work (no rpm-ostree)
- Build tool checks work (podman available)
- Templates work (static content)

**Solution:** ublue_server is designed for development AND runtime use. On standard Fedora, use it for development (templates, build tools). On actual UBlue system, all features work.

### "ujust not found"

**Issue:** `rai "list ujust recipes"` returns empty

**Cause:** ujust not installed (only on UBlue systems)

**Solution:**
```bash
# On UBlue system, ujust should be pre-installed
# Check manually:
which ujust
ls /usr/share/ublue-os/justfile
```

### Build tools check shows "not available"

**Issue:** `rai "check build tools"` shows missing tools

**Solution:**
```bash
# Install bootc
sudo dnf install bootc

# Install mkosi
sudo dnf install mkosi

# Install lorax
sudo dnf install lorax

# Install buildah (if podman not enough)
sudo dnf install buildah
```

### Container build fails

**Issue:** `podman build` fails with errors

**Common fixes:**
```bash
# Update podman
sudo dnf upgrade podman

# Clear cache
podman system prune -a

# Check Containerfile syntax
podman build --no-cache -t test .

# Use buildah instead
buildah build-using-dockerfile -t test .
```

### GitHub Actions build fails

**Issue:** Workflow fails to build/push

**Check:**
1. **Permissions:** Ensure workflow has `packages: write`
2. **Secrets:** GitHub token is automatic, no setup needed
3. **Registry:** Check `ghcr.io` is accessible
4. **Containerfile:** Syntax errors in Containerfile

**Debug:**
```bash
# View workflow logs
gh run view --log

# Re-run failed job
gh run rerun <run-id>
```

### Can't rebase to custom image

**Issue:** `rpm-ostree rebase` fails

**Common causes:**
1. Image not signed (use `ostree-unverified-image:docker://...`)
2. Wrong image URL
3. Registry authentication

**Solution:**
```bash
# Use unverified for testing (not recommended for production)
rpm-ostree rebase ostree-unverified-image:docker://ghcr.io/username/image:latest

# Or configure signing
# See Universal Blue signing docs
```

### ISO generation fails with bootc

**Issue:** `bootc install to-disk` fails

**Requirements:**
- Must run with sudo
- Sufficient disk space (10GB+)
- Image must be bootable (contain kernel, bootloader)

**Debug:**
```bash
# Check image contents
podman run --rm -it ghcr.io/username/image:latest bash
ls /boot
ls /usr/lib/modules

# Ensure image has kernel
rpm -qa | grep kernel
```

---

## Advanced Topics

### Multi-Architecture Builds

**Build for multiple architectures (x86_64, aarch64):**

```yaml
# In GitHub Actions workflow
- name: Build Multi-Arch
  uses: redhat-actions/buildah-build@v2
  with:
    containerfiles: ./Containerfile
    platforms: linux/amd64,linux/arm64
    image: custom-image
```

### Image Signing with Cosign

**Setup cosign signing:**

```bash
# Generate key pair
cosign generate-key-pair

# Sign image
cosign sign --key cosign.key ghcr.io/username/image:latest
```

**Add to workflow:**
```yaml
- name: Sign with Cosign
  run: |
    cosign sign --yes --key env://COSIGN_KEY \
      ghcr.io/${{ github.repository }}:latest
  env:
    COSIGN_KEY: ${{ secrets.COSIGN_PRIVATE_KEY }}
```

### Custom ujust Recipes

**Add custom recipes to your image:**

```dockerfile
# In Containerfile
COPY custom.justfile /usr/share/ublue-os/just/custom.justfile
```

**custom.justfile:**
```just
# Custom recipes for my image
setup-dev:
    echo "Setting up development environment"
    distrobox create --name dev --image fedora:40
```

---

## Resources

**Universal Blue:**
- Website: https://universal-blue.org/
- GitHub: https://github.com/ublue-os
- Discord: https://discord.gg/ublue

**Documentation:**
- Universal Blue Docs: https://universal-blue.org/introduction/
- Fedora CoreOS: https://docs.fedoraproject.org/en-US/fedora-coreos/
- rpm-ostree: https://coreos.github.io/rpm-ostree/
- bootc: https://containers.github.io/bootc/

**Image Registries:**
- GitHub Container Registry: https://ghcr.io
- Quay.io: https://quay.io

**Tools:**
- Podman: https://podman.io/
- Buildah: https://buildah.io/
- Cosign: https://github.com/sigstore/cosign

---

## Quick Reference

**Image queries:**
```bash
rai "show ublue image"          # Current deployment
rai "check ublue updates"       # Available updates
rai "show build type"           # Variant detection
```

**Build tools:**
```bash
rai "check build tools"         # Tool availability
rai "list ublue images"         # Local images
```

**Templates:**
```bash
rai "show containerfile template for aurora"  # Aurora template
rai "show github workflow"                     # CI/CD workflow
```

**ujust:**
```bash
rai "list ujust recipes"        # Available recipes
rai "run ujust update"          # Run recipe
```

**Gaming (Bazzite):**
```bash
rai "check gaming status"       # Gaming tools
```

---

**Ready to build your custom immutable OS! 🔵**

For questions, issues, or contributions: https://github.com/tlee933/rai
