# UC1 Supply Chain Security Pipeline — Setup Guide

Everything you need to do **before** running the pipeline for the first time.

---

## 1. Verify Python Version

The pipeline requires **Python 3.9 or newer**. It uses the standard library only — no
`pip install` steps are needed for the core scan.

```powershell
python --version
# Must print: Python 3.9.x or higher
```

If you have multiple Python installations, use `python3 --version` or `py --version`
on Windows.

---

## 2. Confirm Internet Access to Required APIs

The pipeline calls several public APIs. All are free and require no API keys except
the GitHub token (covered in Step 3). Make sure these hosts are reachable from your
machine/network:

| Host | Used for |
|------|----------|
| `raw.githubusercontent.com` | Fetch manifest files (pom.xml, requirements.txt, etc.) |
| `api.github.com` | Repo metadata, branch/PR creation (needs token for writes) |
| `api.osv.dev` | CVE/vulnerability lookup |
| `repo1.maven.org` | Maven version + license lookup |
| `pypi.org` | Python package version + license lookup |
| `registry.npmjs.org` | npm package version + license lookup |
| `api.nuget.org` | NuGet version + license lookup |
| `rubygems.org` | Ruby gem version + license lookup |
| `proxy.golang.org` | Go module version lookup |

Quick connectivity check (run any one):

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('https://api.osv.dev').status)"
# Expected: 200 or 405 (both mean reachable)
```

If your environment is behind a corporate proxy, set the standard proxy variables:

```powershell
$env:HTTPS_PROXY = "http://proxy.yourcompany.com:8080"
$env:HTTP_PROXY  = "http://proxy.yourcompany.com:8080"
```

---

## 3. Create a GitHub Personal Access Token (PAT)

A PAT is **required for live mode** (creating fix branches and PRs on GitHub).
Without it the pipeline runs in dry-run mode and still generates all reports locally.

### Steps

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
   - Direct URL: `https://github.com/settings/tokens`
2. Click **Generate new token (classic)**
3. Give it a descriptive name, e.g. `UC1-Pipeline`
4. Set expiry — 30 or 90 days is typical
5. Select the following scopes:

   | Scope | Why needed |
   |-------|------------|
   | `repo` (full) | Read manifest files, create branches, open PRs |
   | `read:org` | Only needed if scanning private org repos |

6. Click **Generate token** and copy it immediately (it won't be shown again)
7. Store it safely — never commit it to source control

Your token will look like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

> **Note:** For public repositories, only `public_repo` (a subset of `repo`) is needed.
> For private repos you need the full `repo` scope.

---

## 4. Identify Your Target Repository

The pipeline scans a GitHub repository and auto-detects its language/manifest. Make
sure the repo meets these requirements:

| Requirement | Details |
|-------------|---------|
| Hosted on GitHub | The pipeline only reads from GitHub (not GitLab, Bitbucket, etc.) |
| Publicly accessible **OR** your token has read access | Private repos need a token with `repo` scope |
| Contains a supported manifest file at the repo root | See table below |

### Supported manifest files (auto-detected in priority order)

| File | Ecosystem |
|------|-----------|
| `pom.xml` | Java / Maven |
| `requirements.txt` | Python / PyPI |
| `pyproject.toml` | Python / PyPI |
| `package.json` | Node.js / npm |
| `*.csproj` | .NET / NuGet |
| `Gemfile` | Ruby / RubyGems |
| `go.mod` | Go |

If no manifest is found at the repo root, the pipeline exits with an error. For
multi-module Maven projects, point the URL at the subdirectory containing `pom.xml`.

### Demo repository (ready to use)

If you do not have a target repo yet, use the pre-seeded demo repo:

```
https://github.com/SRGuptthha/uc1-security-demo
```

This repo contains a `pom.xml` with 7 known-vulnerable dependencies (Log4Shell,
Spring4Shell, Text4Shell, and others) — ideal for a first run that produces real findings.

---

## 5. Review and Customise Policy (Optional)

A default `policy.json` is already included at `pipeline-output/policy.json`. The
pipeline loads it automatically. Review it before your first run and adjust thresholds
to match your organisation's standards:

```json
{
  "max_critical_cves": 0,          // 0 = any Critical CVE blocks the pipeline
  "max_high_cves": 5,              // allow up to 5 High CVEs before blocking
  "blocked_licenses": [
    "GPL-2.0", "GPL-3.0", "AGPL-3.0", "SSPL-1.0"
  ],
  "allow_untrusted_sources": false,
  "fail_on_secrets": true,
  "allow_snapshot_versions": false,
  "max_composite_risk_score": 90,
  "require_jacoco_coverage_pct": 80,
  "auto_merge_bump_types": ["PATCH", "MINOR"],
  "block_major_auto_merge": true
}
```

The file is at: `pipeline-output/policy.json`

Leave it as-is for the first run — the defaults are sensible and will exercise all
policy gates on the demo repo.

---

## 6. Review Secret Detection Config (Optional)

A `.gitleaks.toml` file is included at `pipeline-output/.gitleaks.toml`. It is used
as a reference — the pipeline uses its own built-in regex scanner, not gitleaks itself.
You do not need to install gitleaks.

If the pipeline raises false-positive secret findings on your repo (e.g. test fixture
credentials), add patterns to the `[allowlist] regexes` section of that file.

---

## 7. (Optional) Install Tools for Full PR Validation Gates

The pipeline always runs **Gate 2** (OWASP re-scan via OSV.dev — no tools needed).
Gates 1, 3, and 4 require additional tools. They are **skipped** automatically if the
tools are not present — skipped gates do not block reports.

| Gate | Tool | Install |
|------|------|---------|
| Gate 1 — Unit tests | `mvn` (Maven) + `git` | [maven.apache.org](https://maven.apache.org/download.cgi) / [git-scm.com](https://git-scm.com) |
| Gate 2 — OWASP re-scan | None (OSV.dev API) | Always runs |
| Gate 3 — Grype container scan | `grype` + `git` | `winget install anchore.grype` |
| Gate 4 — JaCoCo coverage | `mvn` + `git` | Same as Gate 1 |

Verify installs:

```powershell
mvn --version
git --version
grype version
```

For a first run, **skipping all optional gates is fine**. The generated
`security-scan.yml` CI workflow runs all 4 gates in GitHub Actions where Maven is
available.

---

## 8. Confirm File Layout

Your working directory should look like this before the first run:

```
d:\ClaudeUC\UC1\
├── SETUP.md                          ← This file
├── README.md
├── PIPELINE_GUIDE.md
├── .mcp.json                         ← MCP server config (auto-loaded by Claude Code)
├── .github\
│   └── workflows\
│       └── security-scan.yml         ← Live GitHub Actions workflow (already wired up)
├── pipeline-output\
│   ├── run_pipeline.py               ← Main script — run this
│   ├── mcp_server.py                 ← MCP server for Claude Code integration
│   ├── test_pipeline.py              ← Unit tests (run by pipeline automatically)
│   ├── policy.json                   ← Policy thresholds (edit to customise)
│   ├── .gitleaks.toml                ← Secret detection allow-list (edit if needed)
│   └── *.json / *.html               ← Sample outputs from a previous run
├── skills\
│   └── audit-trail-demo\templates\
│       └── report.html               ← HTML dashboard template
└── agents\ / plugins\                ← Reference documentation
```

No installation, compilation, or environment setup is required beyond Python.

---

## 9. Run the Pipeline

### Dry-run (no token — reads repo, generates all reports locally, no GitHub writes)

```powershell
cd d:\ClaudeUC\UC1
python pipeline-output/run_pipeline.py https://github.com/SRGuptthha/uc1-security-demo
```

### Live mode (with token — creates a real fix branch and PR on GitHub)

```powershell
python pipeline-output/run_pipeline.py https://github.com/SRGuptthha/uc1-security-demo `
  --token ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Write outputs to a custom directory

```powershell
python pipeline-output/run_pipeline.py https://github.com/SRGuptthha/uc1-security-demo `
  --token ghp_xxxx `
  --out-dir C:\scans\uc1-demo
```

---

## 10. What to Expect on First Run

The pipeline runs through 7 stages and prints progress to the console. A full run on
the demo repo typically completes in **30–90 seconds** depending on network speed.

```
==============================================================
  UC1 Supply Chain Security Pipeline
  Repo : SRGuptthha/uc1-security-demo
  URL  : https://github.com/SRGuptthha/uc1-security-demo
  Mode : LIVE (real PRs)     ← or DRY-RUN if no token
==============================================================
Language    : java-maven
Manifest    : pom.xml  (4.2 KB)

[Stage 1]   CVE scan via OSV.dev...
[Stage 1.5] Generating SBOM (CycloneDX 1.5)...
[Stage 2]   Risk scoring...
[Stage 3]   Supply-chain audit...
[Stage 3.5] Secret detection...
[Stage 3.7] Evaluating policy rules...
[Stage 3.9] Dependency drift detection...
[Stage 4]   Auto-remediation — generating upgrade PR...
[Stage 5]   PR validation gates...
[Stage 6]   E2E stress test...
[Stage 7]   Generating health report...
[Stage 7a]  Unit tests...

Pipeline complete.  Health grade: F   Score: 12/100
Report: pipeline-output/dependency-health-report.html
```

### Output files generated

| File | What it contains |
|------|-----------------|
| `dependency-health-report.html` | **Open this in a browser** — the main interactive dashboard |
| `dependency-check-report.json` | All CVEs found, CVSS scores, affected packages |
| `sbom-cyclonedx.json` | Full Software Bill of Materials (CycloneDX 1.5 format) |
| `risk-scores.json` | Composite risk score per dependency |
| `audit-report.json` | Supply-chain violations (typosquatting, license, untrusted sources) |
| `secret-scan-report.json` | Any secrets detected in scanned files |
| `policy-report.json` | Policy gate PASS/FAIL results |
| `drift-report.json` | Changes vs. previous baseline (empty on first run) |
| `dependency-baseline.json` | Saved snapshot for future drift comparisons |
| `remediation-manifest.json` | Proposed upgrades and PR details |
| `validation-report.json` | PR gate results (PASS / SKIPPED / BLOCKED) |
| `e2e-report.json` | End-to-end timing and stage results |
| `audit-trail.json` | Full pipeline audit record |
| `security-scan.yml` | GitHub Actions workflow — copy to your repo's `.github/workflows/` |
| `test-results.json` | Unit test results (63 tests) |

---

## 11. Troubleshooting First-Run Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid GitHub URL` | URL malformed or missing owner/repo | Use full URL: `https://github.com/owner/repo` |
| `No manifest file detected` | Repo has no supported manifest at root | Check repo structure; for mono-repos point to the submodule URL |
| `OSV.dev batch query failed` | Transient network / timeout | Re-run; OSV.dev has no rate limit |
| `403 on GitHub API` | Token expired or wrong scope | Regenerate token with `repo` scope (Step 3) |
| `Branch already exists` | Previous live run created the fix branch | Delete branch `fix/security-consolidated-upgrades` on GitHub, re-run |
| `All Stage 5 gates SKIPPED` | `mvn` / `git` not on PATH | Expected on Windows without Maven — use generated `security-scan.yml` in CI |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Corporate CA bundle missing | Set `REQUESTS_CA_BUNDLE` or `SSL_CERT_FILE` env var to your CA bundle path |
| `Health score unexpectedly low` | False-positive secrets detected | Check `secret-scan-report.json`; add allow-list entries to `.gitleaks.toml` |

---

## 12. Quick Reference — All CLI Options

```
python run_pipeline.py <github-url> [options]

  <github-url>          Full GitHub URL  (required)
                        e.g. https://github.com/WebGoat/WebGoat

  --token TOKEN         GitHub PAT with repo scope
                        Required for: branch creation, PR creation, auto-merge
                        Omit for: dry-run (reports only, no GitHub writes)

  --out-dir PATH        Write all output files to PATH
                        Defaults to the directory containing run_pipeline.py
                        Created automatically if it does not exist

  --e2e-repos URL,...   Comma-separated extra repos for Stage 6 E2E stress test
                        Each is scanned in a temp directory; results aggregated
                        into e2e-report.json
```

---

## Summary Checklist

- [ ] Python 3.9+ installed and on PATH
- [ ] Internet access to GitHub, OSV.dev, Maven Central, and relevant package registries
- [ ] GitHub PAT created with `repo` scope (for live mode) — or skip for dry-run
- [ ] Target repository identified and accessible
- [ ] `policy.json` reviewed (leave defaults for first run)
- [ ] (Optional) Maven + Git installed for full PR validation gates
- [ ] Run the pipeline: `python pipeline-output/run_pipeline.py <github-url> [--token ...]`
- [ ] Open `dependency-health-report.html` in a browser to view results

---

## GitHub Actions (already set up)

The workflow at `.github/workflows/security-scan.yml` is live. To trigger it manually:

1. Go to the repo on GitHub → **Actions** tab
2. Click **UC1 Supply Chain Security Scan** → **Run workflow**
3. Set `target_repo` (default: demo repo) and toggle `create_prs` if you want real PRs
4. Add a `DEMO_REPO_PAT` secret (Settings → Secrets) for live PR creation

The workflow also runs automatically every Monday at 02:00 UTC and on every push to
`main` that touches `run_pipeline.py` or `policy.json`.

---

## Use as an AI Agent (MCP)

The pipeline is packaged as an **MCP (Model Context Protocol) server** — the universal
standard for AI tool integration. Once running, any MCP-compatible AI (Claude, Cursor,
VS Code Copilot, and others) can scan any repo with a single call:

```
AI: scan_repo("https://github.com/my-org/my-service")
→  Health: B (82/100) | CVEs: 3 critical, 7 high | Policy: WARN
```

### One-time install (MCP server only)

```powershell
pip install -r pipeline-output/mcp-requirements.txt
# installs: mcp[cli]>=1.0
```

### The 8 available tools

| Tool | Required input | What it does |
| ---- | ------------- | ----------- |
| `scan_repo(repo_url)` | GitHub URL | Full dry-run scan — health grade + CVE summary |
| `create_remediation_prs(repo_url, token)` | GitHub URL + PAT | Live scan + opens upgrade PR |
| `get_health_report()` | — | Score/grade from last run |
| `get_cve_summary()` | — | CVE list sorted by CVSS from last run |
| `get_policy_status()` | — | P001–P009 results from last run |
| `get_sbom()` | — | CycloneDX component list from last run |
| `get_drift_report()` | — | Dependency changes vs baseline from last run |
| `update_policy(field, value)` | field + value | Update a policy.json threshold |

### Connect from Claude Code (already wired up)

`.mcp.json` at the repo root pre-configures the server. Open this project in
Claude Code and the server starts automatically. Verify:

```text
scan_repo("https://github.com/SRGuptthha/uc1-security-demo")
```

### Connect from Claude Desktop

Add to `~/AppData/Roaming/Claude/claude_desktop_config.json` (Windows) or
`~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

```json
{
  "mcpServers": {
    "supply-chain-security": {
      "command": "python",
      "args": ["C:/path/to/uc1-pipeline/pipeline-output/mcp_server.py"]
    }
  }
}
```

Replace `C:/path/to/uc1-pipeline` with your actual clone path. Restart Claude Desktop.

### Connect from Cursor

Add to `.cursor/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "supply-chain-security": {
      "command": "python",
      "args": ["C:/path/to/uc1-pipeline/pipeline-output/mcp_server.py"]
    }
  }
}
```

### Connect from any Anthropic SDK agent

```python
import anthropic

client = anthropic.Anthropic()

# The MCP server must be running: python pipeline-output/mcp_server.py
result = client.beta.messages.create(
    model="claude-opus-4-8",
    max_tokens=1024,
    tools=[{"type": "mcp", "server_label": "supply-chain-security"}],
    messages=[{
        "role": "user",
        "content": "Scan https://github.com/my-org/my-service for vulnerabilities"
    }]
)
```

### Verify the server starts correctly

```powershell
python pipeline-output/mcp_server.py
# Should print: Starting MCP server supply-chain-security ...
# Press Ctrl+C to stop
```
