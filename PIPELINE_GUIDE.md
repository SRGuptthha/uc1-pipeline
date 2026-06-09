# UC1 Supply Chain Security Pipeline — End-to-End Guide

This document walks through the entire pipeline from start to finish: what each stage
does, what data flows between stages, how to interpret every output, and what actions
to take. All examples use the real WebGoat / uc1-security-demo scans included in
`pipeline-output/`.

---

## Table of Contents

1. [What This Pipeline Solves](#1-what-this-pipeline-solves)
2. [Architecture Overview](#2-architecture-overview)
3. [Prerequisites & Setup](#3-prerequisites--setup)
4. [Stage-by-Stage Walkthrough](#4-stage-by-stage-walkthrough)
   - [Setup — Language Detection & Manifest Parsing](#setup--language-detection--manifest-parsing)
   - [Stage 1 — CVE Scan](#day-1--cve-scan)
   - [Stage 1.5 — SBOM Generation](#day-15--sbom-generation)
   - [Stage 2 — Risk Scoring](#day-2--risk-scoring)
   - [Stage 3 — Supply-Chain Audit & License Checking](#day-3--supply-chain-audit--license-checking)
   - [Stage 3.5 — Secret Detection](#day-35--secret-detection)
   - [Stage 3.7 — Policy Enforcement](#day-37--policy-enforcement)
   - [Stage 3.9 — Dependency Drift Detection](#day-39--dependency-drift-detection)
   - [Stage 4 — Auto-Remediation](#day-4--auto-remediation)
   - [Stage 5 — PR Validation](#day-5--pr-validation)
   - [Stage 6 — E2E Stress Test](#day-6--e2e-stress-test)
   - [Stage 7 — Audit Trail & Health Report](#day-7--audit-trail--health-report)
   - [Stage 7a — Unit Tests](#day-7a--unit-tests)
5. [Data Flow Between Stages](#5-data-flow-between-stages)
6. [Reading the HTML Report](#6-reading-the-html-report)
7. [Acting on the Results](#7-acting-on-the-results)
8. [CI/CD Integration](#8-cicd-integration)
9. [Customisation Reference](#9-customisation-reference)

---

## 1. What This Pipeline Solves

When a project pulls in a third-party library, it implicitly trusts that library to be
safe. In practice, `log4j-core:2.14.1` contained **Log4Shell (CVE-2021-44228)** — a
remote code execution vulnerability with a CVSS score of 9.5. Most teams don't discover
this until a security scanner flags it in production, months after the library was added.

This pipeline answers three questions automatically, every time, across **any supported
ecosystem**:

| Question | Stage | Answer |
| ---------- | ------- | -------- |
| **What's broken?** | Days 1–3 | CVEs found, risk-scored, supply-chain audited, licenses verified |
| **What should we fix?** | Stage 4 | Upgrade plan with GitHub PR, manifest patched for your ecosystem |
| **Is the fix safe?** | Stage 5 | Four validation gates: tests, OWASP, Grype, coverage |

It runs in under 90 seconds for a typical project, requires only Python 3.9+, and
writes all outputs as standard JSON so other tools can consume them.

### Supported Ecosystems

| Language | Manifest file | Package registry | CVE ecosystem |
| ---------- | -------------- | ----------------- | --------------- |
| Java | `pom.xml` | Maven Central | Maven |
| Python | `requirements.txt` / `pyproject.toml` | PyPI | PyPI |
| Node.js | `package.json` | npm | npm |
| .NET | `*.csproj` | NuGet | NuGet |
| Ruby | `Gemfile` | RubyGems | RubyGems |
| Go | `go.mod` | Go Proxy | Go |

---

## 2. Architecture Overview

```
GitHub Repo (any manifest — pom.xml / requirements.txt / package.json / ...)
       │
       ▼  detect_language() — probes for manifest in priority order
┌─────────────────────────────────────────────────────────────────────┐
│                        run_pipeline.py                              │
│                                                                     │
│  Setup ──► Stage 1 ──► Stage 1.5 ──► Stage 2 ──► Stage 3 ──► Stage 3.5      │
│ (detect)  (CVEs)   (SBOM)    (scoring) (audit+  (secrets)          │
│                                         license)                    │
│                                                                     │
│  Stage 3.7 ──► Stage 3.9 ──► Stage 4 ──► Stage 5 ──► Stage 6 ──► Stage 7/7a   │
│  (policy)  (drift)    (PR)     (validate) (E2E)  (report+tests)    │
└─────────────────────────────────────────────────────────────────────┘
       │
       ▼
  15 output files  +  HTML report (with unit test panel)  +  GitHub PR (if --token)
```

**Data sources used (all free, no auth required for core scan):**

| Source | Used for |
| -------- | ---------- |
| [OSV.dev](https://osv.dev) | CVE/vulnerability lookup (all ecosystems) |
| [Maven Central](https://repo1.maven.org) | Java version lookup + license from POM |
| [PyPI](https://pypi.org) | Python version + license lookup |
| [npm Registry](https://registry.npmjs.org) | Node.js version + license lookup |
| [NuGet](https://api.nuget.org) | .NET version + license lookup |
| [RubyGems](https://rubygems.org) | Ruby version + license lookup |
| [Go Proxy](https://proxy.golang.org) | Go module version lookup |
| GitHub API | Manifest fetch, PR creation/commenting/merging (needs `--token` for writes) |

---

## 3. Prerequisites & Setup

### Minimum (dry-run, no GitHub writes)
```
Python 3.9+   ← only requirement; uses stdlib only (no pip install)
Internet      ← OSV.dev, registry APIs, GitHub raw content
```

### For live PR creation
```
GitHub PAT    ← with `repo` scope
              ← create at: github.com → Settings → Developer settings → PATs
```

### For full local gate execution (optional)
```
git           ← clone PR branch
mvn           ← run tests + JaCoCo coverage  (Java repos only)
grype         ← Grype vulnerability scanner (anchore.io/grype)
```
Gates that need these tools show `SKIPPED` (not `FAIL`) when the tool is not found,
so the pipeline always completes. The generated GitHub Actions workflow runs all
4 gates in CI where these tools are pre-installed.

### Running the pipeline
```powershell
# Dry-run (no token — reports only, no GitHub writes):
python pipeline-output/run_pipeline.py https://github.com/WebGoat/WebGoat

# Live mode (creates a real branch and PR):
python pipeline-output/run_pipeline.py https://github.com/MyOrg/MyRepo `
  --token ghp_xxxxxxxxxxxxxxxxxxxx

# Custom output directory:
python pipeline-output/run_pipeline.py https://github.com/MyOrg/MyRepo `
  --token ghp_xxxx `
  --out-dir C:\scans\myrepo-2026-06
```

> See [SETUP.md](SETUP.md) for the complete first-run checklist including GitHub PAT
> creation, proxy configuration, and optional tool installation.

---

## 4. Stage-by-Stage Walkthrough

### Setup — Language Detection & Manifest Parsing

**What it does:**
1. Calls `detect_language()` — probes the GitHub raw content API for manifest files
   in priority order: `pom.xml → requirements.txt → pyproject.toml → package.json →
   *.csproj → Gemfile → go.mod`. First match wins.
2. Falls back to a local copy of the manifest in the output directory (useful for
   testing with synthetic fixtures).
3. Dispatches to the appropriate parser for the detected ecosystem.
4. Extracts all direct dependencies with their declared versions, resolving variable
   references where applicable (e.g. `${log4j.version}` in Maven).
5. For Maven projects: also runs `parse_pom_plugins()` to extract `<build><plugins>`
   entries — Maven plugins are first-class dependencies and can carry CVEs.
6. Filters to compile/runtime scope only (test/provided deps are skipped — they don't
   ship in production artifacts).

**Console output:**
```
Language    : java-maven
Manifest    : pom.xml  (4.2 KB)
Parsed 7 total deps  (7 compile/runtime including 1 plugin, 0 test/provided)
Resolved 2 property variables
```

**Why plugins are included:** Build plugins like `maven-surefire-plugin` or
`spring-boot-maven-plugin` run during the build pipeline. A compromised or
vulnerable plugin can exfiltrate source code or inject malicious bytecode at
compile time — a textbook supply chain attack vector.

**Supported parser functions:**

| Function | Ecosystem | Notes |
| ---------- | ----------- | ------- |
| `parse_pom()` + `parse_pom_plugins()` | Maven | Resolves `${properties}`, includes build plugins |
| `parse_requirements_txt()` | PyPI | Handles `==`, `>=`, `~=` version pins |
| `parse_pyproject_toml()` | PyPI | Reads `[project.dependencies]` table |
| `parse_package_json()` | npm | Reads `dependencies` (not devDependencies) |
| `parse_csproj()` | NuGet | Reads `<PackageReference>` elements |
| `parse_gemfile()` | RubyGems | Reads `gem 'name', 'version'` lines |
| `parse_go_mod()` | Go | Reads `require` block |

---

### Stage 1 — CVE Scan

**Reads:** Manifest (parsed dependencies)  
**Writes:** `dependency-check-report.json`

**What it does:**
1. Converts each dependency to an ecosystem-aware OSV package spec using
   `_osv_package_spec()`:
   - Maven: `{"name": "group:artifact", "ecosystem": "Maven"}`
   - PyPI: `{"name": "artifact", "ecosystem": "PyPI"}`
   - npm: `{"name": "artifact", "ecosystem": "npm"}`
   - (same pattern for NuGet, RubyGems, Go)
2. Sends a single batch query to `https://api.osv.dev/v1/querybatch` — one HTTP call
   for all dependencies.
3. Fetches full CVE detail for each unique vulnerability ID.
4. Extracts CVSS score and severity; maps OSV IDs to CVE IDs via the `aliases` field.
5. Builds an OWASP Dependency-Check-compatible JSON report.

**Real example — uc1-security-demo (Java/Maven):**
```
Dependencies scanned : 7  (including 1 Maven plugin)
CVEs found           : 28
  CRITICAL           : 5
  HIGH               : 12
  MEDIUM             : 11
  LOW                : 0
```

**Top findings:**
| CVE | CVSS | Dep | What it means |
| ----- | ------ | ----- | --------------- |
| CVE-2021-44228 | 10.0 | log4j-core:2.14.1 | Log4Shell — RCE via JNDI lookup |
| CVE-2022-22965 | 9.8 | spring-core:5.3.20 | Spring4Shell — RCE via data binding |
| CVE-2022-42889 | 9.8 | commons-text:1.9 | Text4Shell — JNDI injection in string interpolation |
| CVE-2022-23221 | 9.8 | h2:2.1.210 | H2 console RCE via init string |

**Output structure (`dependency-check-report.json`):**
```json
{
  "reportSchema": "1.1",
  "projectInfo": { "name": "uc1-security-demo", "reportDate": "2026-06-08T10:00:00Z" },
  "dependencies": [
    {
      "fileName": "log4j-core-2.14.1.jar",
      "packages": [{ "id": "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1" }],
      "vulnerabilities": [
        {
          "name": "CVE-2021-44228",
          "severity": "CRITICAL",
          "cvssv3": { "baseScore": 10.0, "baseSeverity": "CRITICAL" },
          "description": "Apache Log4j2 versions 2.0-beta9 through 2.14.1..."
        }
      ]
    }
  ]
}
```

---

### Stage 1.5 — SBOM Generation

**Reads:** Parsed dependencies  
**Writes:** `sbom-cyclonedx.json`

**What it does:**  
Generates a CycloneDX 1.5 Software Bill of Materials — a machine-readable inventory
of all components. The SBOM is used by Stage 3 (supply-chain audit) and Stage 5 (Grype
scan, when available). Each component entry includes the package URL (PURL) in the
`pkg:<ecosystem>/...` format.

**Why SBOM matters:** US Executive Order 14028 and the EU Cyber Resilience Act
increasingly require a SBOM as part of software supply chain compliance. This stage
produces one automatically in the standard format accepted by procurement and security
teams.

---

### Stage 2 — Risk Scoring

**Reads:** `dependency-check-report.json`  
**Writes:** `risk-scores.json`

**What it does:**  
Computes a composite risk score (0–100) for every vulnerable dependency using four
weighted factors:

| Factor | Weight | How it's measured |
| -------- | -------- | ------------------- |
| CVSS score | 40% | Highest CVE score for this dep, normalised to 0–100 |
| Business criticality | 30% | Inferred from artifact name (security/auth/core = higher) |
| Exposure factor | 20% | Direct dep = 1.0, transitive = 0.5 |
| Maintenance risk | 10% | Years since last release (estimated from version date) |

**Risk tiers:**
- **CRITICAL** (≥ 80) — block deployment, fix immediately
- **HIGH** (60–79) — fix within current sprint
- **MEDIUM** (40–59) — schedule in next sprint
- **LOW** (< 40) — monitor, fix at next maintenance window

**Business criticality detection** — artifact name keyword scoring:
- `security`, `oauth`, `jwt`, `auth` → authentication layer (weight 0.9)
- `core`, `spring`, `boot` → core framework (weight 0.8)
- `data`, `jpa`, `jdbc`, `sql` → data storage (weight 0.75)
- Others → default weight (0.5)

---

### Stage 3 — Supply-Chain Audit & License Checking

**Reads:** Manifest (parsed deps), `sbom-cyclonedx.json`  
**Writes:** `audit-report.json`

**What it does:**  
Checks each dependency against three supply-chain threat categories, plus performs
real license verification.

**1. Untrusted sources**  
Compares each group ID (or package name for non-Maven ecosystems) against a
known-trusted prefix list. Any dep not matching a trusted prefix raises an
`untrusted_source` violation. Trusted prefixes can be extended in `policy.json`.

**2. Typosquatting detection**  
Checks for common typosquat patterns — slight misspellings of popular libraries
(e.g. `org.apche` instead of `org.apache`, `djano` instead of `django`).

**3. Real license verification**  
For up to 30 dependencies, calls the package registry to retrieve the actual declared
license (not a heuristic guess):

| Ecosystem | How license is fetched |
| ----------- | ------------------------ |
| Maven | Downloads the `.pom` file from Maven Central, reads `<licenses><license><name>` |
| PyPI | Calls `https://pypi.org/pypi/{name}/json`, reads `info.license` |
| npm | Calls `https://registry.npmjs.org/{name}/latest`, reads `license` field |
| NuGet | Calls registration API, reads `licenseExpression` or `licenseUrl` |
| RubyGems | Calls `https://rubygems.org/api/v1/gems/{name}.json`, reads `licenses[]` |
| Go | License check not available via proxy; falls back to `UNKNOWN` |

If the returned SPDX identifier matches the `blocked_licenses` list in `policy.json`,
a `license_violation` entry is added. This directly triggers policy rule **P003**.

**Real example — uc1-security-demo:**
```
Audit result : PASSED
Violations   : 0   (all deps from trusted Maven groups)
License check: 7 deps checked — 0 blocked licenses found
```

---

### Stage 3.5 — Secret Detection

**Reads:** All text files in the output/working directory  
**Writes:** `secret-scan-report.json`

**What it does:**  
Scans every text file using 10+ built-in regex patterns for leaked credentials. No
external tools required. Patterns include:

| Pattern | Example match |
| --------- | -------------- |
| AWS Access Key | `AKIA[0-9A-Z]{16}` |
| AWS Secret Key | 40-char key adjacent to `aws_secret` keyword |
| GitHub PAT | `ghp_[A-Za-z0-9]{36}` |
| Generic API key | `api_key = "sk-abc123..."` |
| DB password | `db.password=supersecret` |
| JWT secret | `jwt.secret = "my-signing-key"` |
| Slack webhook | `hooks.slack.com/services/T.../B.../...` |
| Bearer token | `Authorization: Bearer eyJ...` |
| PEM private key | `-----BEGIN RSA PRIVATE KEY-----` |

The actual secret value is never stored in the report — only the file path, line
number, pattern name, and a redacted preview (first 8 chars + `****`).

To suppress false positives (e.g. test fixture credentials), add patterns to the
`[allowlist]` section in `pipeline-output/.gitleaks.toml`.

---

### Stage 3.7 — Policy Enforcement

**Reads:** `dependency-check-report.json`, `risk-scores.json`, `secret-scan-report.json`, `audit-report.json`  
**Reads (optional):** `policy.json` (custom thresholds)  
**Writes:** `policy-report.json`

**What it does:**  
Evaluates five default policy rules against the current scan results:

| Rule ID | Default threshold | What it checks |
| --------- | ------------------ | ---------------- |
| P001 | max CVSS < 9.0 | FAIL if any CVE is at or above the threshold |
| P002 | max High CVEs ≤ 10 | WARN if too many High-severity CVEs accumulate |
| P003 | GPL/AGPL/SSPL blocked | FAIL if a real license check returns a blocked SPDX identifier |
| P006 | fail on secrets | FAIL if any secret at HIGH+ severity is detected |
| P007 | no untrusted sources | WARN if a dep comes from a non-standard source |

**P003 is now reliable:** In prior versions, license checking was heuristic (group ID
patterns only) and P003 rarely triggered. It now uses registry-sourced SPDX identifiers
from Stage 3, so P003 fires whenever a dependency genuinely carries a blocked license.

**Custom policy** (`policy.json`):
```json
{
  "max_critical_cves": 0,
  "max_high_cves": 5,
  "blocked_licenses": ["GPL-2.0", "GPL-3.0", "AGPL-3.0", "SSPL-1.0"],
  "allow_untrusted_sources": false,
  "fail_on_secrets": true,
  "allow_snapshot_versions": false,
  "require_jacoco_coverage_pct": 80,
  "auto_merge_bump_types": ["PATCH", "MINOR"],
  "block_major_auto_merge": true
}
```

Full field reference: see `pipeline-output/policy.json`.

---

### Stage 3.9 — Dependency Drift Detection

**Reads:** Manifest (current deps), `dependency-baseline.json` (previous run)  
**Writes:** `drift-report.json`, `dependency-baseline.json` (updated)

**What it does:**  
Compares the current dependency list against the saved baseline from the last run.
Categorises each change:

| Category | Meaning |
| ---------- | --------- |
| `added` | New dep not in previous baseline |
| `removed` | Dep present before, now gone |
| `upgraded` | Version increased (MAJOR/MINOR/PATCH classified) |
| `downgraded` | Version decreased — always flagged as risky |
| `unchanged` | Same dep, same version |

On first run, the baseline is created and all deps are recorded with mode `INITIAL`.
On subsequent runs, drift is detected and the baseline is updated. Drift detection
catches when a developer quietly bumps a dependency version without a security review.

---

### Stage 4 — Auto-Remediation

**Reads:** `risk-scores.json`, manifest file  
**Writes:** `remediation-manifest.json`, patched manifest (on GitHub branch)

**What it does:**

**Step 1 — Resolve latest stable versions**  
For each vulnerable dependency (top 15 by risk score), queries the appropriate package
registry via `lookup_latest_version_ecosystem()`. Filters out pre-release versions
(SNAPSHOT, alpha, beta, RC). Only recommends a version that actually exists.

**Step 2 — Classify bump type**  
Compares old vs new version using semantic versioning:
- **PATCH** (1.2.3 → 1.2.4) — lowest risk, bug fixes only
- **MINOR** (1.2.x → 1.3.x) — new features, backwards compatible
- **MAJOR** (1.x → 2.x) — breaking changes possible, requires human review

**Step 3 — Patch the manifest**  
`patch_manifest()` handles the correct update strategy per ecosystem:

| Ecosystem | Patching strategy |
| ----------- | ------------------ |
| Maven (`pom.xml`) | Direct `<version>` tags patched; `${property}` references patched at the `<properties>` declaration |
| Python (`requirements.txt`) | Version pin after `==` updated |
| Python (`pyproject.toml`) | Version in `[project.dependencies]` updated |
| npm (`package.json`) | Version string in `dependencies` object updated |
| .NET (`*.csproj`) | `Version` attribute on `<PackageReference>` updated |
| Ruby (`Gemfile`) | Version string in `gem` declaration updated |
| Go (`go.mod`) | Version string in `require` block updated |

**Step 4 — Idempotent PR creation**  
Before creating a new PR, `find_existing_pr()` checks GitHub for an open PR from the
fix branch (`fix/security-consolidated-upgrades`). If one already exists, the pipeline
posts a comment with the updated analysis rather than creating a duplicate PR.

**Real example — uc1-security-demo upgrades:**
```
log4j-core        2.14.1   → 2.26.0   MINOR   (fixes 7 CVEs including Log4Shell)
spring-core       5.3.20   → 7.0.7    MAJOR   ⚠ Breaking changes — human review required
jackson-databind  2.13.0   → 2.22.0   MINOR   (fixes 4 CVEs)
h2                2.1.210  → 2.4.240  MINOR   (fixes 1 CVE)
commons-text      1.9      → 1.15.0   MINOR   (fixes 3 CVEs including Text4Shell)
snakeyaml         1.30     → 2.6      MAJOR   ⚠ Breaking changes — human review required
```

In **dry-run mode** (no `--token`): generates the manifest and logs what would happen.  
In **live mode** (`--token` provided): creates the branch, commits the patched manifest,
opens the PR on GitHub.

---

### Stage 5 — PR Validation

**Reads:** `remediation-manifest.json`, `dependency-check-report.json`  
**Writes:** `validation-report.json`  
**GitHub actions:** Posts PR comment, merges PR (if AUTO_MERGE + token)

**What it does:**  
Runs four gates per upgrade to confirm the change is safe to merge.

**Gate 1 — mvn test** *(requires mvn + git; Java repos only)*  
Clones the PR branch, runs `mvn test --batch-mode`, parses Surefire output for
test counts, failures, and errors.

**Gate 2 — OWASP re-scan** *(always runs — no tools required)*  
Re-queries OSV.dev for the **new** version of each upgraded dependency. Diffs against
the Stage 1 baseline to detect net-new CVEs introduced by the upgrade. Gate fails only
if the upgrade *adds* a new Critical or High CVE.

**Gate 3 — Grype scan** *(requires grype + git)*  
Runs Grype against the cloned branch directory. Parses JSON output for Critical and
High findings.

**Gate 4 — JaCoCo coverage** *(requires mvn + git; Java repos only)*  
Runs `mvn test jacoco:report`, parses `target/site/jacoco/jacoco.xml` for aggregate
LINE coverage percentage. Gate fails if below the `require_jacoco_coverage_pct`
threshold in `policy.json` (default 80%).

**Verdict logic:**

| Condition | Verdict |
| ----------- | --------- |
| All gates PASS + PATCH or MINOR bump | `AUTO_MERGE` — merges automatically if `--token` provided |
| All gates PASS + MAJOR bump | `PENDING_HUMAN` — PR left open for review |
| Any gate FAILS or ERRORS | `BLOCKED` — PR left open, failures listed in comment |
| Gate SKIPPED (tool missing) | Does not block auto-merge |

**Real example — uc1-security-demo (dry-run, no mvn/grype installed):**
```
Validated 6 upgrades:
  auto-merged : 4   (4 MINOR bumps — OWASP gate PASS on all)
  pending     : 2   (spring-core MAJOR, snakeyaml MAJOR — human review required)
  blocked     : 0
Gates mode: OWASP-only (mvn/grype not on PATH)
```

**Gate 2 result example — confirming log4j upgrade is safe:**
```
owasp-scan: PASS  →  "0 new Critical/High CVEs. 7 CVE(s) resolved."
```
This is a **live OSV.dev query** confirming `log4j-core:2.26.0` has no new CVEs — the
upgrade is safe to merge.

---

### Stage 6 — E2E Stress Test

**Reads:** All stage outputs from the current run  
**Writes:** `e2e-report.json`

**What it does:**  
Records an end-to-end execution summary using real wall-clock timing measured at each
stage boundary. Optionally runs the full pipeline against additional repos via subprocess
(`--e2e-repos`).

**Multi-repo E2E:**
```powershell
python run_pipeline.py https://github.com/org/primary-app `
  --token ghp_xxxx `
  --e2e-repos https://github.com/org/service-a,https://github.com/org/service-b
```
Each extra repo is scanned in a temporary directory; results are aggregated into
`e2e-report.json`.

---

### Stage 7 — Audit Trail & Health Report

**Reads:** All 13 previous output files  
**Writes:** `audit-trail.json`, `dependency-health-report.html`, `security-scan.yml`

**Health score computation (0–100):**

Starts at 100 and subtracts for problems found:
```
-15 per Critical CVE
- 8 per High CVE
- 2 per Medium CVE
- 8 per untrusted source
- 5 per license violation
-10 per Critical secret
- 5 per High secret
- 5 per policy FAIL
- 2 per CVE-introducing drift event
```

Then adds back for remediation applied:
```
+10 per CVE fixed by upgrade
+ 5 per PR auto-merged
```

Score is clamped to [0, 100] and mapped to a letter grade (A–F).

**HTML report** (`dependency-health-report.html`):  
A self-contained interactive dashboard showing:
- Health score gauge with letter grade
- CVE breakdown by severity (Chart.js pie chart)
- Risk score table (sortable by score/tier)
- Upgrade summary and PR validation results
- Unit test results panel (from Stage 7a)
- Pipeline run timeline

Open it directly in any browser — no server required.

**GitHub Actions workflow** (`security-scan.yml`):  
Copy it to `.github/workflows/` in your target repo:
```powershell
Copy-Item pipeline-output/security-scan.yml /path/to/your/repo/.github/workflows/
```

The workflow triggers on push, pull requests, and a weekly Sunday schedule. It runs
the full pipeline, uploads the HTML report as a downloadable artifact, and posts a
policy gate status check on PRs (blocks merge if policy FAIL).

---

### Stage 7a — Unit Tests

**Reads:** `test_pipeline.py` (test suite)  
**Writes:** `test-results.json`  
**Injects into:** `dependency-health-report.html` (Unit Test Results panel)

**What it does:**  
Runs the pipeline's own unit test suite (`test_pipeline.py`) as a subprocess and
captures the results. This verifies that all pure helper functions are working
correctly in the current environment.

**63 tests across 15 test classes:**

| Test class | Functions covered |
| ------------ | ------------------ |
| `TestCvssSeverity` | `cvss_severity()` — CVSS score → severity label |
| `TestExtractCvss` | `extract_cvss()` — OSV record → (score, severity) |
| `TestBumpType` | `bump_type()` — version pair → PATCH/MINOR/MAJOR |
| `TestHealthGrade` | `health_grade()` — score → letter grade |
| `TestIsLicenseBlocked` | `is_license_blocked()` — SPDX identifier → blocked/not |
| `TestPatchManifest` | `patch_manifest()` — all 6 ecosystem formats |
| `TestParsePom` | `parse_pom()` — Maven XML → deps list |
| `TestParsePomPlugins` | `parse_pom_plugins()` — Maven build plugins extraction |
| `TestParseRequirementsTxt` | `parse_requirements_txt()` — Python deps |
| `TestParsePackageJson` | `parse_package_json()` — npm deps |
| `TestParseCsproj` | `parse_csproj()` — .NET PackageReference deps |
| `TestParseGemfile` | `parse_gemfile()` — Ruby gem deps |
| `TestParseGoMod` | `parse_go_mod()` — Go module deps |
| `TestOsvPackageSpec` | `_osv_package_spec()` — ecosystem-aware OSV spec |
| `TestPatchPomXml` | pom.xml direct version + property reference patching |

**Console output (normal run):**
```
[Stage 7a] Running unit tests...
  Tests: 63  Passed: 63  Failed: 0  (0.005 s)
  All tests passed.
```

**HTML panel:** The "Unit Test Results" tab in `dependency-health-report.html` shows
per-test pass/fail status so results are visible without running the test suite
separately.

**Test isolation:** `test_pipeline.py` sets the `_UC1_IMPORT_ONLY` environment
variable before importing `run_pipeline.py`. This env guard causes the pipeline to
exit cleanly at the import boundary, preventing any network calls during testing.

---

## 5. Data Flow Between Stages

```
GitHub Repo
    │
    ▼  detect_language() → ecosystem + manifest_content
    │
    ▼  parse_*(manifest_content)
    │
    │  all_deps  ──────────────────────────────────────────────────────┐
    │      │                                                            │
    ▼      ▼                                                            │
Stage 1: _osv_package_spec(dep) + querybatch                             │
    │   └──► dependency-check-report.json                              │
    │             │                                                     │
    ▼             ▼                                                     │
Stage 1.5      Stage 2: risk_score(cves)                                    │
    │             │   └──► risk-scores.json                            │
    ▼             │              │                                      │
sbom-cdx.json     │              ▼                                     │
    │             │         Stage 4: lookup_latest_version_ecosystem()   │
    │             │              + patch_manifest()                    │
    │             │              + find_existing_pr() [idempotency]    │
    │             │              └──► remediation-manifest.json        │
    ▼             │                          │                          │
Stage 3: audit(sbom)│                          ▼                         │
  + lookup_license_for_dep() [real SPDX]    Stage 5: osv_rescan(new_ver) │
    │   └──► audit-report.json              │   └──► validation-report │
    │                                        │                          │
    ▼                                        ▼                          │
Stage 3.5: secret_scan()                      Stage 6: e2e timing          │
    │   └──► secret-scan-report.json         │   └──► e2e-report.json  │
    │                                        │                          │
    ▼                                        ▼                          │
Stage 3.7: policy_eval(all reports)           Stage 7: aggregate all       │
    │   └──► policy-report.json              │   └──► html + yaml      │
    │                                        │                          │
    ▼                                        ▼                          │
Stage 3.9: drift_detect(baseline) ◄───────────────────────────────────── ┘
    └──► drift-report.json + dependency-baseline.json

Stage 7a: test_pipeline.py subprocess → test-results.json → injected into html
```

---

## 6. Reading the HTML Report

Open `pipeline-output/dependency-health-report.html` in any browser.

**Health Score Gauge** (top of page)  
Shows the pipeline health score and letter grade. A red grade before remediation with
a green grade after means the pipeline found and fully fixed the issues — the expected
outcome for a vulnerable repo.

**Executive Summary tab**

- **CVE Breakdown chart** — click any severity segment to filter the dep table to only
  that severity
- **Risk Score Table** — sort by "Risk Score" descending to prioritise fixes; "Action"
  column shows the planned upgrade or "No fix available"
- **Upgrade Summary** — list of all version bumps with old/new/bump-type

**Technical Appendix tab**

- **PR Validation Results** — per-gate status (PASS / FAIL / SKIPPED) with detail message
- **Unit Test Results** — all 63 test results; any failures here indicate a broken helper
  function in the current Python environment
- **Pipeline Timeline** — wall-clock time per stage; Stage 1 OSV.dev scan typically
  dominates for large dependency trees

---

## 7. Acting on the Results

### If policy is FAIL (before running in production)
1. Check `policy-report.json` — which rule ID failed?
2. **P001 (Critical CVEs):** Run with `--token` to create the fix PR, merge it
3. **P003 (License violation):** The blocked license came from a real registry lookup.
   Evaluate whether the dependency can be replaced with a permissively-licensed alternative
4. **P006 (Secrets):** Rotate the leaked credential immediately, remove from code, add
   the pattern to `.gitleaks.toml` allow-list if it was a false positive

### After PRs are created (live mode)
The pipeline creates **one consolidated PR** covering all upgrades (idempotent — re-running
updates the same PR rather than creating duplicates). Your workflow:

1. **AUTO_MERGE PRs** — PATCH/MINOR upgrades that passed all gates were merged automatically
   if `--token` was provided and `auto_merge_bump_types` includes those bump types
2. **PENDING_HUMAN PRs** — MAJOR bumps require human review; check the breaking changes
   section in the PR body, test locally, then approve and merge manually
3. **BLOCKED PRs** — Check which gate failed in `validation-report.json`, fix the
   underlying issue (test failure, new CVE introduced, coverage drop), then re-run

### If health score is still low after remediation
Some CVEs may have no patched version available yet. Check `remediation-manifest.json`
under `"skipped"` — these deps had no newer stable release. Options:
- Replace the library with a maintained alternative
- Add a `<dependencyManagement>` override (Maven) or version pin to force a safe version
- Accept the risk with documented justification in your risk register

### Re-running after fixes
Run the pipeline again after merging the PR. The drift detector captures the version
changes, the CVE scan shows an improved result, and the health score improvement is
tracked against the saved baseline.

---

## 8. CI/CD Integration

### GitHub Actions (live in this repo)

A production-ready workflow is already wired into this repository at
`.github/workflows/security-scan.yml`. It requires no setup beyond adding a secret.

**Trigger manually:**
1. GitHub → **Actions** tab → **UC1 Supply Chain Security Scan** → **Run workflow**
2. Set `target_repo` (default: demo repo)
3. Toggle `create_prs = true` to create real PRs (requires `DEMO_REPO_PAT` secret)

**Auto-triggers already wired:**

| Trigger | Condition | What runs |
| ------- | --------- | --------- |
| Push to `main` | `run_pipeline.py`, `policy.json`, or the workflow file changed | Full scan (dry-run) |
| `workflow_dispatch` | Manual via Actions UI | Full scan, optionally with PR creation |
| Weekly cron | Every Monday 02:00 UTC | Full scan (dry-run) |

**Adding the `DEMO_REPO_PAT` secret** (needed for live PR creation):
1. GitHub → repo Settings → Secrets and variables → Actions → New repository secret
2. Name: `DEMO_REPO_PAT`, Value: your GitHub PAT with `repo` scope

All 4 validation gates (mvn test, OWASP re-scan, Grype, JaCoCo) run in CI where the
Ubuntu runner has Maven and Grype pre-available.

### Generated workflow for other repos

The pipeline also writes a `security-scan.yml` into the output directory at Stage 7.
Copy it to any target repo to give that repo the same CI/CD coverage:

```powershell
Copy-Item pipeline-output/security-scan.yml `
  /path/to/your/repo/.github/workflows/security-scan.yml
```

### Jenkins / GitLab CI / Azure DevOps

The pipeline is a single Python script with no dependencies — runs anywhere Python
3.9+ is available:

```bash
# Run the scan
python pipeline-output/run_pipeline.py $GITHUB_REPO_URL --token $GITHUB_TOKEN

# Check policy gate exit code (0 = pass, 1 = fail)
python -c "
import json, sys
r = json.load(open('policy-report.json'))
sys.exit(0 if r['result'] == 'PASS' else 1)
"
```

For detailed CI/CD snippets, see
`skills/dependency-supply-chain-hygiene/references/cicd.md`.

### MCP Server (Claude Code integration)

An MCP server is bundled at `pipeline-output/mcp_server.py` and pre-configured in
`.mcp.json`. When Claude Code loads this project, the `supply-chain-security` MCP
server starts automatically.

| Tool | What it does |
| ---- | ------------ |
| `scan_repo` | Run the full pipeline against any GitHub URL |
| `get_health_report` | Return the health report from the last scan |
| `get_cve_summary` | Return CVE findings from the last scan |
| `get_policy_status` | Return the policy gate result from the last scan |
| `create_remediation_prs` | Trigger PR creation for the last scan (needs token) |

This lets Claude drive the entire pipeline conversationally — no terminal required.

---

## 9. Customisation Reference

### Policy thresholds (`policy.json`)

Place `policy.json` in the same directory as `run_pipeline.py`. All fields are optional
— omitted fields use the pipeline defaults:

```json
{
  "max_critical_cves": 0,
  "max_high_cves": 5,
  "blocked_licenses": ["GPL-2.0", "GPL-3.0", "AGPL-3.0", "SSPL-1.0"],
  "allow_untrusted_sources": false,
  "fail_on_secrets": true,
  "allow_snapshot_versions": false,
  "max_composite_risk_score": 90,
  "require_jacoco_coverage_pct": 80,
  "auto_merge_bump_types": ["PATCH", "MINOR"],
  "block_major_auto_merge": true,
  "secret_severity_threshold": "HIGH",
  "trusted_group_prefixes": [
    "org.springframework", "com.fasterxml.jackson",
    "org.apache", "com.google", "com.mycompany"
  ]
}
```

Full field descriptions: see `pipeline-output/policy.json`.

### Secret detection suppression (`.gitleaks.toml`)

To suppress false positives (e.g. test fixtures with placeholder credentials):

```toml
[allowlist]
paths = [
  '''src/test/''',           # suppress entire test directory
  '''mock-data/''',          # suppress mock data files
]
regexes = [
  '''^changeit$''',          # common Java keystore placeholder
  '''^YOUR_API_KEY$''',      # obvious placeholder values
]
```

Full example: `pipeline-output/.gitleaks.toml`.

### Multi-repo E2E testing

```powershell
python run_pipeline.py https://github.com/org/primary-app `
  --token ghp_xxxx `
  --e2e-repos https://github.com/org/service-a,https://github.com/org/service-b
```
Results from all repos aggregated into `e2e-report.json`. Each extra repo runs in a
temporary directory and its outputs are cleaned up after the run.

---

## Quick Reference — Output Files at a Glance

| File | Stage | What to look at first |
| ------ | ------- | ----------------------- |
| `dependency-check-report.json` | Stage 1 | `dependencies[*].vulnerabilities` — CVEs per dep |
| `sbom-cyclonedx.json` | Stage 1.5 | `components` — full inventory |
| `risk-scores.json` | Stage 2 | `dependencies[0]` — highest risk score first |
| `audit-report.json` | Stage 3 | `result` — PASS / WARNING / FAIL; `violations` for license issues |
| `secret-scan-report.json` | Stage 3.5 | `result` — CLEAN / FINDINGS; `findings` for details |
| `policy-report.json` | Stage 3.7 | `result` and `violations` — which rules failed |
| `drift-report.json` | Stage 3.9 | `added` and `upgraded` — new CVE-carrying deps |
| `remediation-manifest.json` | Stage 4 | `pull_requests` — upgrade plan; `skipped` — no fix available |
| `validation-report.json` | Stage 5 | `summary` — auto_merged / pending / blocked counts |
| `e2e-report.json` | Stage 6 | `timing_summary` — real stage durations |
| `test-results.json` | Stage 7a | `passed` / `failed` counts; `tests` for per-test detail |
| `audit-trail.json` | Stage 7 | `pipeline_health.score` — before/after health score |
| `dependency-health-report.html` | Stage 7 | Open in browser — interactive dashboard |
| `security-scan.yml` | Stage 7 | Copy to `.github/workflows/` in target repo |
