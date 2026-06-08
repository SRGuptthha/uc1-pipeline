---
name: dependency-supply-chain-hygiene
description: >
  Run OWASP Dependency-Check scans and interpret the results to identify known security
  vulnerabilities in third-party libraries across Java, Node.js, Python, .NET, and Ruby
  projects. Use this skill whenever the user mentions scanning dependencies, checking for
  CVEs, auditing supply chain security, running OWASP checks, finding vulnerable libraries,
  reviewing pom.xml / package.json / requirements.txt / Gemfile / .csproj for security
  issues, or generating a dependency vulnerability report. Trigger even for casual requests
  like "are my dependencies safe?", "check my project for known vulnerabilities", "audit my
  packages", or "what CVEs do I have?". Covers local developer machines and CI/CD pipelines
  (GitHub Actions, Jenkins, etc.). Outputs HTML reports, JSON/XML for pipelines, and a
  Markdown chat summary with CVSS + OWASP severity prioritization and fix-first
  remediation recommendations.
---

# Dependency & Supply-Chain Hygiene Skill

Identify, explain, and remediate known security vulnerabilities in third-party dependencies
using OWASP Dependency-Check. Covers all major ecosystems and outputs for both humans and
pipelines.

---

## Supported Ecosystems

| Ecosystem    | Manifest Files                              | Lock Files                        |
|--------------|---------------------------------------------|-----------------------------------|
| Java         | `pom.xml`, `build.gradle`, `build.gradle.kts` | N/A                             |
| Node.js      | `package.json`                              | `package-lock.json`, `yarn.lock`  |
| Python       | `requirements.txt`, `setup.py`, `pyproject.toml` | `Pipfile.lock`, `poetry.lock` |
| .NET         | `*.csproj`, `*.vbproj`, `packages.config`   | N/A                               |
| Ruby         | `Gemfile`                                   | `Gemfile.lock`                    |

---

## Workflow

### Step 1 — Understand the Context

Ask (or infer from context):
1. **What is the project path / repo?** (or ask user to upload manifest files)
2. **What ecosystem(s)?** Auto-detect from manifest files if the project is accessible.
3. **Is OWASP Dependency-Check already installed?** If not, offer to install it.
4. **What is the target environment?** Local CLI vs. CI/CD pipeline.
5. **What output formats are needed?** (HTML / JSON / XML / Markdown summary)

If manifest files are uploaded directly, skip to Step 3.

---

### Step 2 — Install OWASP Dependency-Check (if needed)

Read `references/install.md` for platform-specific installation instructions.

Quick-check whether it's already available:
```bash
dependency-check --version 2>/dev/null || echo "NOT INSTALLED"
```

---

### Step 3 — Auto-detect Ecosystem & Build Scan Command

Detect ecosystems from manifest files present in the project root:

```bash
# Detection logic (run from project root)
[ -f pom.xml ] || [ -f build.gradle ] && echo "Java"
[ -f package.json ] && echo "Node.js"
[ -f requirements.txt ] || [ -f pyproject.toml ] && echo "Python"
ls *.csproj 2>/dev/null && echo ".NET"
[ -f Gemfile ] && echo "Ruby"
```

Build the scan command based on detected ecosystems. See `references/scan-commands.md`
for full flag reference and ecosystem-specific options.

**Standard scan template:**
```bash
dependency-check \
  --project "<PROJECT_NAME>" \
  --scan "<PROJECT_PATH>" \
  --format HTML --format JSON \
  --out "./dependency-check-report" \
  --nvdApiKey "<NVD_API_KEY_IF_AVAILABLE>" \
  --failOnCVSS 7
```

> **NVD API Key**: Strongly recommended to avoid rate limiting. Direct users to
> https://nvd.nist.gov/developers/request-an-api-key if they don't have one.

---

### Step 4 — Run the Scan

Run the scan command. Inform the user:
- First run downloads the NVD database (~500MB) and may take 10–20 minutes.
- Subsequent runs are faster (incremental updates).
- For CI/CD, cache the `~/.m2/repository/org/owasp` or equivalent data directory.

Stream output so the user can see progress. If it fails, read `references/troubleshooting.md`.

---

### Step 4b — Output File Approval Gate ⛔ STOP BEFORE PARSING

After the scan completes and report files are written to `./dependency-check-report/`, **always
stop and present the generated files to the user for review before proceeding**.

Present the following prompt:

```
---
⛔ Scan complete — approval required before proceeding

The following output files have been generated:

| File | Format | Size |
|------|--------|------|
| dependency-check-report/dependency-check-report.html | HTML | <SIZE> |
| dependency-check-report/dependency-check-report.json | JSON | <SIZE> |

📎 Please review the files above.

Reply with one of:
  • "approve" or "looks good" — proceed with parsing and summary
  • "stop here"              — end the session; no further analysis
---
```

**Wait for the user's explicit approval before continuing to Step 5.**

---

### Step 5 — Parse & Interpret Results

After the scan, parse the JSON report to extract vulnerabilities. See
`references/report-parsing.md` for the JSON schema and parsing logic.

For each vulnerability found, collect:
- **CVE ID** (e.g., `CVE-2021-44228`)
- **Affected dependency** (name + version)
- **CVSS v3 score** (0.0–10.0)
- **OWASP severity** (Critical / High / Medium / Low)
- **Description** (plain-English explanation of the risk)
- **Fixed version** (from NVD or ecosystem advisory)
- **Confidence** (HIGH / MEDIUM / LOW — how certain is the match)

---

### Step 6 — Generate Markdown Summary

Always produce a Markdown summary in chat regardless of other output formats.

#### Summary Structure

```markdown
## 🔐 Dependency Vulnerability Report — <PROJECT_NAME>
**Scan date:** <DATE>  **Ecosystem(s):** <LIST>  **Total dependencies scanned:** <N>

### 📊 Overview
| Severity | Count |
|----------|-------|
| 🔴 Critical (CVSS 9–10) | X |
| 🟠 High (CVSS 7–8.9)    | X |
| 🟡 Medium (CVSS 4–6.9)  | X |
| 🟢 Low (CVSS < 4)       | X |

### 🚨 Fix First — Critical & High Severity

For each Critical/High CVE:
**[CVE-XXXX-XXXXX]** `library-name:version`
- **Risk:** <one-sentence plain-English explanation>
- **CVSS:** X.X (Critical) | **OWASP:** Critical
- **Fix:** Upgrade to `library-name:safe-version`

### 🟡 Medium & Low Severity
(Grouped summary table — less detail)

### ✅ Remediation Checklist
- [ ] Update X to Y
- [ ] Update A to B
- ...

### ℹ️ False Positive Guidance
(If any LOW confidence findings, explain suppression options)
```

---

### Step 7 — Human Approval Gate ⛔ STOP BEFORE REMEDIATING

After presenting the vulnerability summary (Step 6), **always stop and wait for explicit human
approval before suggesting or applying any fixes**. Do not proceed to remediation automatically.

Present the following approval prompt to the user:

```
---
⛔ Approval required before remediation

Here's a summary of proposed upgrades:

| Library | Current | Safe Version | Severity | Major bump? |
|---------|---------|--------------|----------|-------------|
| ...     | ...     | ...          | ...      | Yes / No    |

⚠️ Upgrading dependencies may introduce breaking changes or compatibility issues
with your project. Please review before proceeding.

Reply with one of:
  • "approve all"        — apply all fixes
  • "approve [library]"  — apply fix for specific library only
  • "skip [library]"     — skip a specific library (will note as deferred)
  • "suppress [CVE-ID]"  — treat as false positive, generate suppression XML
  • "show breaking changes for [library]" — get detailed changelog/migration notes first
---
```

**Wait for the user's reply before continuing.**

Only after receiving approval should you proceed to Step 8 for the approved items.
Track any skipped or deferred items and include them in a "Deferred / Skipped" section
at the end of the remediation output.

---

### Step 8 — Remediation Recommendations

Only run this step for libraries the user has explicitly approved in Step 7.

For every approved vulnerability, provide:

1. **Exact upgrade command** for the ecosystem:
   - Java/Maven: `<dependency>` block change in `pom.xml`
   - Node.js: `npm install library@safe-version` or `yarn upgrade`
   - Python: update `requirements.txt` line; `pip install --upgrade`
   - .NET: `dotnet add package Library --version X.Y.Z`
   - Ruby: update `Gemfile`; `bundle update library`

2. **Breaking change warning** if the safe version is a major version bump — include
   a link to the library's changelog or migration guide where available.

3. **Compatibility check suggestion** — after each upgrade, remind the user to:
   ```bash
   # Run your test suite to catch regressions
   mvn test          # Java/Maven
   npm test          # Node.js
   pytest            # Python
   dotnet test       # .NET
   bundle exec rspec # Ruby
   ```

4. **Suppression guidance** for items the user marked "suppress" — generate the XML:
   ```xml
   <suppress>
     <notes>False positive — library X does not use the vulnerable code path</notes>
     <cve>CVE-XXXX-XXXXX</cve>
   </suppress>
   ```

5. **Deferred items summary** — list any skipped/deferred libraries with their CVEs
   so the user has a record to revisit:
   ```
   ⏸️ Deferred (not yet fixed):
   - struts2-core 2.5.28 → CVE-2023-50164 (Critical) — skipped, major version bump under review
   ```

6. **SBOM note** — recommend generating a Software Bill of Materials alongside the report:
   ```bash
   dependency-check --format SARIF  # for GitHub Advanced Security
   dependency-check --format SPDX   # for SBOM compliance
   ```

---

### Step 9 — CI/CD Integration (if requested)

Read `references/cicd.md` for ready-to-paste pipeline snippets covering:
- GitHub Actions
- Jenkins
- GitLab CI
- Azure DevOps

Key CI/CD considerations to always mention:
- Cache the NVD database between runs (saves 10–15 min per run).
- Use `--failOnCVSS 7` to fail the build on High/Critical findings.
- Store reports as pipeline artifacts.
- Rotate/protect the NVD API key via secrets.

---

## Output Files

| Format   | Flag              | Best For                          |
|----------|-------------------|-----------------------------------|
| HTML     | `--format HTML`   | Human review, sharing with team   |
| JSON     | `--format JSON`   | Parsing, dashboards               |
| XML      | `--format XML`    | Legacy CI tools                   |
| SARIF    | `--format SARIF`  | GitHub Advanced Security          |
| SPDX     | `--format SPDX`   | SBOM / compliance                 |
| CSV      | `--format CSV`    | Spreadsheet reporting             |

Always generate at minimum HTML + JSON unless the user specifies otherwise.

---

## Severity Priority Matrix

| CVSS Score | OWASP Severity | Action                            |
|------------|----------------|-----------------------------------|
| 9.0–10.0   | Critical       | Fix immediately, block deployment |
| 7.0–8.9    | High           | Fix within current sprint         |
| 4.0–6.9    | Medium         | Fix in next release cycle         |
| 0.1–3.9    | Low            | Track, fix when convenient        |
| N/A        | Informational  | Review manually                   |

When both CVSS and OWASP severity disagree, always surface the **higher** of the two.

---

## Reference Files

- `references/install.md` — Installation for Linux, macOS, Windows, Docker, Maven plugin
- `references/scan-commands.md` — Full flag reference and per-ecosystem scan examples
- `references/report-parsing.md` — JSON schema, parsing logic, confidence levels
- `references/cicd.md` — Pipeline integration snippets
- `references/troubleshooting.md` — Common errors and fixes