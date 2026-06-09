# UC1 — Supply Chain Security Pipeline

Automated supply chain security pipeline for Java Maven projects. Scans for CVEs,
scores risk, audits the supply chain, detects secrets, enforces policies, and
auto-generates remediation PRs — all from a single Python script, no external tools
required for the core scan.

---

## Quick Start

```bash
# Dry-run (no GitHub token needed — reads pom.xml, generates full report locally)
python pipeline-output/run_pipeline.py https://github.com/WebGoat/WebGoat

# Live mode (creates a real PR on GitHub)
python pipeline-output/run_pipeline.py https://github.com/MyOrg/MyRepo \
  --token ghp_xxxxxxxxxxxxxxxxxxxx
```

**Requirements:** Python 3.9+ (stdlib only — no pip installs needed for core scan).

---

## What It Does

| Stage | Day | Output |
|-------|-----|--------|
| CVE scan via OSV.dev | Stage 1 | `dependency-check-report.json` |
| SBOM generation (CycloneDX 1.5) | Stage 1.5 | `sbom-cyclonedx.json` |
| Risk scoring (composite model) | Stage 2 | `risk-scores.json` |
| Supply-chain audit + secret detection | Stage 3 | `audit-report.json`, `secret-scan-report.json` |
| Policy enforcement | Stage 3.7 | `policy-report.json` |
| Dependency drift detection | Stage 3.9 | `drift-report.json`, `dependency-baseline.json` |
| Auto-remediation (GitHub PR) | Stage 4 | `remediation-manifest.json` |
| PR validation (OWASP gate + optional mvn/grype/jacoco) | Stage 5 | `validation-report.json` |
| E2E stress test | Stage 6 | `e2e-report.json` |
| Health report + GitHub Actions workflow | Stage 7 | `dependency-health-report.html`, `security-scan.yml` |

---

## CLI Reference

```
python run_pipeline.py <github-url> [options]

Arguments:
  <github-url>          Full GitHub URL, e.g. https://github.com/WebGoat/WebGoat

Options:
  --token TOKEN         GitHub Personal Access Token (repo scope).
                        Required for: creating PRs, posting comments, auto-merge.
                        Without it: dry-run mode (reports generated, no GitHub writes).

  --out-dir PATH        Write all output files to PATH instead of the script directory.
                        Created automatically if it does not exist.

  --e2e-repos URL,...   Comma-separated list of additional GitHub repo URLs to run
                        through the full pipeline as part of the Stage 6 E2E stress test.
                        Each repo is run in a temporary directory and results are
                        aggregated into e2e-report.json.
```

### Examples

```bash
# Scan and write outputs to a custom directory
python run_pipeline.py https://github.com/WebGoat/WebGoat \
  --out-dir /tmp/webgoat-scan

# Full live run with E2E stress test across 3 repos
python run_pipeline.py https://github.com/WebGoat/WebGoat \
  --token ghp_xxxx \
  --e2e-repos https://github.com/spring-projects/spring-petclinic,https://github.com/SasanLabs/VulnerableApp
```

---

## Output Files

All files are written to the script directory (or `--out-dir` if specified).

| File | Description |
|------|-------------|
| `pom.xml` | Copy of the scanned pom.xml |
| `dependency-check-report.json` | OWASP-compatible CVE report (via OSV.dev) |
| `sbom-cyclonedx.json` | CycloneDX 1.5 Software Bill of Materials |
| `risk-scores.json` | Composite risk scores per dependency |
| `audit-report.json` | Supply-chain violations (typosquatting, untrusted sources, license) |
| `secret-scan-report.json` | Leaked credentials detected in source files |
| `policy-report.json` | Policy gate evaluation results |
| `drift-report.json` | Dependency changes vs. saved baseline |
| `dependency-baseline.json` | Snapshot for future drift comparison |
| `remediation-manifest.json` | Upgrade plan + PR details |
| `validation-report.json` | PR gate results (OWASP, mvn test, grype, jacoco) |
| `e2e-report.json` | E2E stress test results with real timing |
| `audit-trail.json` | Complete pipeline audit record |
| `dependency-health-report.html` | Interactive HTML dashboard |
| `security-scan.yml` | GitHub Actions workflow — copy to `.github/workflows/` |

---

## PR Validation Gates (Stage 5)

The pipeline always runs **Gate 2 (OWASP)** — it re-queries OSV.dev for the upgraded
versions and checks for net-new Critical/High CVEs introduced by each upgrade.

Gates 1, 3, and 4 require a local build environment:

| Gate | Tool Required | Behaviour When Missing |
|------|--------------|------------------------|
| Gate 1 — `mvn test` | `mvn` on PATH + `git` (to clone branch) | `SKIPPED` — use CI |
| Gate 2 — OWASP re-scan | None (uses OSV.dev API) | Always runs |
| Gate 3 — Grype scan | `grype` on PATH + `git` | `SKIPPED` — use CI |
| Gate 4 — JaCoCo coverage | `mvn` on PATH + `git` | `SKIPPED` — use CI |

**SKIPPED gates do not block auto-merge.** Use the generated `security-scan.yml`
GitHub Actions workflow to run all 4 gates in CI where Maven and Grype are available.

### Verdict Logic

| Condition | Verdict |
|-----------|---------|
| All gates PASS + PATCH or MINOR bump | `AUTO_MERGE` (merges automatically if `--token` provided) |
| All gates PASS + MAJOR bump | `PENDING_HUMAN` (PR left open for review) |
| Any gate FAILS or ERRORS | `BLOCKED` (PR left open, failures listed in comment) |

---

## Policy Configuration

Create a `policy.json` in the output directory to override default policy thresholds:

```json
{
  "max_critical_cves": 0,
  "max_high_cves": 5,
  "blocked_licenses": ["GPL-2.0", "AGPL-3.0"],
  "allow_untrusted_sources": false,
  "fail_on_secrets": true
}
```

See `pipeline-output/policy.json` for a full example with all supported fields.

---

## Secret Detection

The pipeline scans all text files in the output directory for secrets using built-in
regex patterns (no external tools required). Patterns include:

- AWS Access Keys and Secret Keys
- GitHub Personal Access Tokens
- Generic API keys and Bearer tokens
- Database connection strings with passwords
- JWT secrets
- Slack webhooks

To add custom patterns or suppress false positives, create `.gitleaks.toml` in the
project root. See `pipeline-output/.gitleaks.toml` for an example.

---

## CI/CD Integration

### GitHub Actions (live in this repo)

A production-ready workflow is already wired into this repository at
`.github/workflows/security-scan.yml`. It triggers:

- **On push** to `main` when `run_pipeline.py`, `policy.json`, or the workflow file changes
- **Manually** via `workflow_dispatch` (Actions tab → Run workflow) — choose target repo and whether to create PRs
- **Weekly** every Monday at 02:00 UTC

To create real remediation PRs from the workflow, add a `DEMO_REPO_PAT` secret to the
repo (Settings → Secrets → New repository secret) with a token that has `repo` scope.

### Generated workflow for other repos

The pipeline also emits a `security-scan.yml` into the output directory at Stage 7.
Copy it to any target repo to give that repo the same CI/CD coverage:

```bash
cp pipeline-output/security-scan.yml /path/to/your/repo/.github/workflows/security-scan.yml
```

## MCP Server (Claude Code integration)

An MCP server is bundled at `pipeline-output/mcp_server.py` and pre-configured in
`.mcp.json`. When Claude Code loads this project the `supply-chain-security` MCP
server starts automatically, exposing five tools:

| Tool | Description |
|------|-------------|
| `scan_repo` | Run the full pipeline against any GitHub repo URL |
| `get_health_report` | Return the health report from the most recent scan |
| `get_cve_summary` | Return the CVE findings from the most recent scan |
| `get_policy_status` | Return the policy gate result from the most recent scan |
| `create_remediation_prs` | Trigger PR creation for the most recent scan (needs token) |

These tools let Claude drive the entire supply chain pipeline conversationally — no
terminal commands needed.

---

## Project Structure

```
UC1/
├── README.md                          ← This file
├── SETUP.md                           ← First-run checklist
├── PIPELINE_GUIDE.md                  ← Stage-by-stage documentation
├── .mcp.json                          ← MCP server config (auto-loaded by Claude Code)
├── .github/
│   └── workflows/
│       └── security-scan.yml          ← Live GitHub Actions workflow
├── pipeline-output/
│   ├── run_pipeline.py                ← Main executable (single-file, stdlib only)
│   ├── mcp_server.py                  ← MCP server exposing pipeline as Claude tools
│   ├── policy.json                    ← Example policy configuration
│   ├── .gitleaks.toml                 ← Example secret detection config
│   ├── dependency-health-report.html  ← Sample HTML report (WebGoat scan)
│   └── *.json                         ← Sample output artifacts
├── skills/                            ← Skill documentation (SKILL.md per skill)
│   ├── dependency-supply-chain-hygiene/
│   ├── auto-remediation-skill/
│   ├── e2e-stress-testing/
│   │   └── scenarios/                 ← cve-heavy, zero-cve, complex-tree, malformed-pom, mixed
│   ├── audit-trail-demo/
│   ├── risk-scoring-agent/
│   └── ...
├── agents/
│   └── pr-validation-agent/           ← Stage 5 gate sub-skills and schemas
└── plugins/
    └── supply-chain-audit-plugin/     ← Stage 3 audit plugin
```

---

## Troubleshooting

**`pom.xml not found`** — The pipeline looks for `pom.xml` at the repo root. For
multi-module projects, point to the submodule URL containing the pom.xml.

**`OSV.dev batch query failed`** — Transient network issue. Re-run; OSV.dev is free
and has no auth requirements.

**`Branch creation failed`** — The GitHub token may lack `repo` scope, or the branch
`fix/security-consolidated-upgrades` already exists. Delete it on GitHub and re-run.

**Stage 5 gates all SKIPPED** — Expected when `mvn`/`git` are not on PATH (common on
Windows without Maven installed). Use the generated `security-scan.yml` CI workflow
to run the full gate suite where Maven is available.

**Health score unexpectedly low** — Check `secret-scan-report.json` for false-positive
secrets (common with test data). Add patterns to `.gitleaks.toml` allow-list to
suppress them.

<!-- last verified: 2026-06-08 21:40 -->
