#!/usr/bin/env python3
"""
UC1 Supply Chain Security Pipeline — Preflight Installation
Run once before using the pipeline to install optional security tools.

Usage:
    python pipeline-output/preflight.py

Installs grype and syft by downloading release binaries directly from GitHub
using only Python stdlib — no curl, no winget, no package manager required.
"""
import json
import os
import platform
import shutil
import ssl
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

# ── Minimum Python version ────────────────────────────────────────────────────
if sys.version_info < (3, 9):
    print(f"ERROR: Python 3.9+ required. You have {sys.version}")
    sys.exit(1)

HERE     = Path(__file__).parent          # pipeline-output/
WIN_BIN  = HERE / "bin"                   # Windows local install dir
UNIX_BIN = Path.home() / ".local" / "bin" # Linux/Mac user bin (no sudo)
IS_WIN   = sys.platform == "win32"
INSTALL_DIR = WIN_BIN if IS_WIN else UNIX_BIN

print("=" * 62)
print("  UC1 Supply Chain Security Pipeline — Preflight")
print("=" * 62)

# ── SSL context (same pattern as run_pipeline.py) ─────────────────────────────
_ctx = ssl.create_default_context()
try:
    import certifi
    _ctx = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    pass


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "UC1-preflight/1.0"})
    with urllib.request.urlopen(req, context=_ctx, timeout=timeout) as r:
        return r.read()


def _get_json(url, timeout=15):
    return json.loads(_get(url, timeout))


# ─────────────────────────────────────────────────────────────
# 1. Network connectivity check
# ─────────────────────────────────────────────────────────────
print("\n[1] Checking network connectivity...")
_net_ok = False
try:
    urllib.request.urlopen("https://api.osv.dev", context=_ctx, timeout=8)
    _net_ok = True
    print("  api.osv.dev        : reachable")
except Exception:
    print("  api.osv.dev        : UNREACHABLE — CVE scan will fail")

try:
    urllib.request.urlopen("https://api.github.com", context=_ctx, timeout=8)
    print("  api.github.com     : reachable")
except Exception:
    print("  api.github.com     : UNREACHABLE — binary download will fail")


# ─────────────────────────────────────────────────────────────
# 2. Check existing tools
# ─────────────────────────────────────────────────────────────
print("\n[2] Checking installed tools...")

def _check(name):
    path = shutil.which(name)
    # Also check the local bin dir we install to
    if not path:
        local = INSTALL_DIR / (name + (".exe" if IS_WIN else ""))
        if local.exists():
            path = str(local)
    return path

_status = {
    "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "git":    _check("git"),
    "mvn":    _check("mvn"),
    "grype":  _check("grype"),
    "syft":   _check("syft"),
}
for tool, val in _status.items():
    tag = "OK" if val else "NOT FOUND"
    print(f"  {tool:<10} {tag:<12} {val or ''}")


# ─────────────────────────────────────────────────────────────
# 3. Detect platform / arch for binary download
# ─────────────────────────────────────────────────────────────
def _detect_arch():
    m = platform.machine().lower()
    if m in ("x86_64", "amd64"):
        return "amd64"
    if m in ("aarch64", "arm64"):
        return "arm64"
    return "amd64"  # fallback

def _asset_pattern(tool, version, os_name, arch, ext):
    return f"{tool}_{version}_{os_name}_{arch}.{ext}"

def _os_name():
    if IS_WIN:
        return "windows"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"

OS_NAME = _os_name()
ARCH    = _detect_arch()
EXT     = "zip" if IS_WIN else "tar.gz"
BIN_EXT = ".exe" if IS_WIN else ""

print(f"\n  Platform : {OS_NAME}  arch: {ARCH}")


# ─────────────────────────────────────────────────────────────
# 4. Install helper — download + extract binary
# ─────────────────────────────────────────────────────────────
def _install_tool(tool, repo):
    """Download latest binary release of `tool` from anchore/{repo}."""
    if _check(tool):
        print(f"  {tool:<6} : already installed — skipping")
        return True

    print(f"  {tool:<6} : fetching latest release info...")
    try:
        release = _get_json(
            f"https://api.github.com/repos/anchore/{repo}/releases/latest",
            timeout=20
        )
    except Exception as exc:
        print(f"  {tool:<6} : could not fetch release info — {exc}")
        return False

    version = release["tag_name"].lstrip("v")
    assets  = release.get("assets", [])

    # Find the right asset
    target = _asset_pattern(tool, version, OS_NAME, ARCH, EXT)
    asset  = next((a for a in assets if a["name"] == target), None)
    if not asset:
        # Try without version prefix pattern (some releases use different naming)
        asset = next((a for a in assets
                      if OS_NAME in a["name"] and ARCH in a["name"]
                      and a["name"].endswith(EXT)), None)
    if not asset:
        print(f"  {tool:<6} : no asset found for {OS_NAME}/{ARCH} in release {version}")
        print(f"         Available: {[a['name'] for a in assets[:6]]}")
        return False

    print(f"  {tool:<6} : downloading {asset['name']} ({asset['size']//1024} KB)...")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        archive = os.path.join(tmp, asset["name"])
        try:
            urllib.request.urlretrieve(asset["browser_download_url"], archive)
        except Exception as exc:
            print(f"  {tool:<6} : download failed — {exc}")
            return False

        # Extract the binary
        bin_name = tool + BIN_EXT
        dest     = INSTALL_DIR / bin_name
        try:
            if EXT == "tar.gz":
                with tarfile.open(archive, "r:gz") as tf:
                    member = next(
                        m for m in tf.getmembers()
                        if m.name == bin_name or m.name.endswith(f"/{bin_name}")
                    )
                    member.name = bin_name
                    tf.extract(member, path=str(INSTALL_DIR))
            else:
                with zipfile.ZipFile(archive) as zf:
                    member = next(
                        n for n in zf.namelist()
                        if n == bin_name or n.endswith(f"/{bin_name}")
                    )
                    with zf.open(member) as src, open(dest, "wb") as dst:
                        dst.write(src.read())
        except Exception as exc:
            print(f"  {tool:<6} : extraction failed — {exc}")
            return False

        # Make executable on Unix
        if not IS_WIN:
            dest.chmod(0o755)

    print(f"  {tool:<6} : installed to {dest}")
    _status[tool] = str(dest)
    return True


# ─────────────────────────────────────────────────────────────
# 5. Install grype and syft
# ─────────────────────────────────────────────────────────────
print("\n[3] Installing grype and syft...")
_grype_ok = _install_tool("grype", "grype")
_syft_ok  = _install_tool("syft",  "syft")


# ─────────────────────────────────────────────────────────────
# 6. git / mvn hints (not auto-installed)
# ─────────────────────────────────────────────────────────────
print("\n[4] Checking git and mvn (not auto-installed)...")
if not _status["git"]:
    print("  git : NOT FOUND")
    print("        Install: https://git-scm.com/downloads")
    print("        Stage 5 PR cloning gates will be SKIPPED without git")
else:
    print(f"  git : {_status['git']}")

if not _status["mvn"]:
    print("  mvn : NOT FOUND")
    print("        Install: https://maven.apache.org/download.cgi")
    print("        Stage 5 unit test + JaCoCo gates will be SKIPPED without mvn")
else:
    print(f"  mvn : {_status['mvn']}")


# ─────────────────────────────────────────────────────────────
# 7. MCP server dep hint
# ─────────────────────────────────────────────────────────────
print("\n[5] Checking MCP server dependency...")
try:
    import mcp  # noqa: F401
    print("  mcp : installed")
except ImportError:
    print("  mcp : NOT installed (optional — only needed for Claude Code / MCP integration)")
    print("        Install: pip install -r pipeline-output/mcp-requirements.txt")


# ─────────────────────────────────────────────────────────────
# 8. Windows PATH reminder
# ─────────────────────────────────────────────────────────────
if IS_WIN and ((_grype_ok and not shutil.which("grype"))
               or (_syft_ok and not shutil.which("syft"))):
    print(f"\n  NOTE (Windows): tools installed to {WIN_BIN}")
    print(f"  Add this folder to your PATH to use them from any directory:")
    print(f"    $env:PATH += \";{WIN_BIN}\"   (current session)")
    print(f"  Or add permanently via System Properties → Environment Variables.")

if not IS_WIN and str(UNIX_BIN) not in os.environ.get("PATH", ""):
    print(f"\n  NOTE: tools installed to {UNIX_BIN}")
    print(f"  Add to your shell profile if not already present:")
    print(f"    export PATH=\"$HOME/.local/bin:$PATH\"")


# ─────────────────────────────────────────────────────────────
# 9. Final summary
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 62)
print("  PREFLIGHT SUMMARY")
print("=" * 62)

rows = [
    ("python", _status["python"],       "All pipeline stages"),
    ("git",    _status.get("git"),       "Stage 5 PR cloning"),
    ("mvn",    _status.get("mvn"),       "Stage 5 Gates 1 + 4 (unit tests, JaCoCo)"),
    ("grype",  _status.get("grype"),     "Stage 1.6 + Stage 5 Gate 3 (SBOM audit)"),
    ("syft",   _status.get("syft"),      "Stage 1.6 Syft SBOM generation"),
]
for tool, val, gates in rows:
    if val:
        tag = "OK" if tool == "python" else "READY"
    else:
        tag = "SKIPPED"
    print(f"  {tool:<8} {tag:<10} {gates}")

print()
if not (_grype_ok and _syft_ok):
    print("  Some tools could not be installed — check errors above.")
else:
    print("  All security tools installed. Run the pipeline:")
    print(f"    python {HERE}/run_pipeline.py <github-url>")
print()
