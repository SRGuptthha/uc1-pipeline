---
name: auto-remediation-skill
description: >
  Safe Maven version upgrades with auto-generated GitHub PRs, changelog summaries, and CVE
  fix details. Use this skill whenever the user wants to fix vulnerable dependencies, upgrade
  Maven artifacts, auto-generate remediation PRs, get changelog summaries for dependency
  upgrades, or automate CVE fixes in pom.xml. Triggers after Stage 1 OWASP scan and/or Stage 2
  risk scoring, or whenever the user says things like "fix my vulnerabilities", "upgrade my
  deps", "create a PR to fix CVEs", "auto-remediate", "patch my pom.xml", or "what version
  should I upgrade to?". Covers patch, minor, and major upgrades with breaking-change warnings.
---

# Auto-Remediation Skill — Stage 4

Merge inputs from Stage 1 (OWASP CVE scan) and Stage 2 (risk scores), resolve the safest
available upgrade for each vulnerable dependency, patch `pom.xml`, generate a changelog
summary with CVE fix details, and open a GitHub Pull Request — one PR per dependency or
one consolidated PR, per user preference.

---

## Workflow

### Step 1 — Load & Merge Inputs

Load both upstream outputs:

```
Stage 1: ./dependency-check-report/dependency-check-report.json   (CVE details)
Stage 2: ./risk-scores.json                                        (composite risk scores)
```

Merge on artifact GAV (`groupId:artifactId:version`). For each dependency build a unified
record:

```json
{
  "artifact": "org.apache.struts:struts2-core:2.5.28",
  "composite_risk_score": 91.4,
  "risk_tier": "CRITICAL",
  "cves": [
    { "id": "CVE-2023-50164", "cvss": 9.8, "severity": "CRITICAL" }
  ],
  "current_version": "2.5.28"
}
```

If Stage 2 output is missing, fall back to CVSS score from Stage 1 as the sort key.
Sort merged list by `composite_risk_score` descending — highest risk fixed first.

See `references/input-schema.md` for full field mapping.

---

### Step 2 — Resolve Safe Upgrade Versions

For each vulnerable dependency, query Maven Central to find the latest available version:

```bash
GROUP=$(echo "$GAV" | cut -d: -f1 | tr '.' '/')
ARTIFACT=$(echo "$GAV" | cut -d: -f2)

# Latest version
curl -s "https://search.maven.org/solrsearch/select?\
q=g:${GROUP}+AND+a:${ARTIFACT}&rows=1&core=gav&sort=score+desc&wt=json" \
| python3 -c "
import sys, json
d = json.load(sys.stdin)['response']['docs']
print(d[0]['v'] if d else 'NOT_FOUND')
"
```

Then verify the target version actually fixes the CVEs — cross-check against NVD:

```bash
curl -s "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=<CVE_ID>" \
| python3 -c "
import sys, json
d = json.load(sys.stdin)
# Check vulnerableSoftware for fixed version range
for cfg in d['vulnerabilities'][0]['cve']['configurations']:
    for node in cfg['nodes']:
        for match in node['cpeMatch']:
            if match.get('versionEndExcluding'):
                print('Fixed in:', match['versionEndExcluding'])
"
```

For **major version bumps**, flag explicitly — include changelog link and breaking change warning.
See `references/version-resolution.md` for full resolution logic and edge cases.

---

### Step 3 — Human Approval Gate ⛔ STOP BEFORE PATCHING

Present the full upgrade plan and wait for explicit approval before touching any files.

```
---
⛔ Upgrade plan ready — approval required before patching pom.xml

| # | Artifact | Current | → Safe Version | Risk Score | Bump Type | CVEs Fixed |
|---|----------|---------|----------------|------------|-----------|------------|
| 1 | struts2-core | 2.5.28 | 6.3.0.2 | 91.4 🔴 | MAJOR ⚠️ | CVE-2023-50164 |
| 2 | jackson-databind | 2.13.0 | 2.15.4 | 74.2 🟠 | MINOR | CVE-2022-42003 |
| 3 | log4j-core | 2.14.1 | 2.23.1 | 68.1 🟠 | MINOR | CVE-2021-44228 |

⚠️ MAJOR bumps may introduce breaking changes. Review changelogs before approving.
  • struts2-core changelog: https://struts.apache.org/announce/

PR strategy:
  • "one PR per dep"  — separate branch + PR for each dependency (safer, easier to revert)
  • "one PR all"      — single consolidated branch + PR for all upgrades

Reply with one of:
  • "approve all — one PR per dep"
  • "approve all — one PR all"
  • "approve [artifact]"          — approve a specific artifact only
  • "skip [artifact]"             — exclude from this run
  • "show changelog [artifact]"   — fetch and summarise the changelog first
---
```

Wait for user reply before continuing. Handle partial approvals — track skipped items.

---

### Step 4 — Patch pom.xml

For each approved upgrade, update the version in `pom.xml`.

#### Direct dependency update:
```python
import re

def patch_pom(pom_path, artifact_id, old_version, new_version):
    with open(pom_path) as f:
        content = f.read()
    # Match <version> tag scoped within <dependency> block for this artifactId
    pattern = rf'(<artifactId>{re.escape(artifact_id)}</artifactId>\s*<version>){re.escape(old_version)}(</version>)'
    updated = re.sub(pattern, rf'\g<1>{new_version}\g<2>', content)
    with open(pom_path, "w") as f:
        f.write(updated)
    return updated != content  # True if a change was made
```

#### Property-based version (e.g. `${spring.version}`):
If the version is a property reference, update the `<properties>` block instead:
```python
pattern = rf'(<{prop_name}>){re.escape(old_version)}(</{prop_name}>)'
```

See `references/pom-patching.md` for multi-module POM handling and BOM (Bill of Materials) cases.

After patching, verify the build still resolves:
```bash
mvn dependency:resolve -q && echo "RESOLVE_OK" || echo "RESOLVE_FAILED"
```

If resolve fails, revert the patch and report to the user before continuing.

---

### Step 5 — Fetch Changelog & CVE Fix Summary

For each patched dependency, generate a PR description containing:

1. **CVE Fix Details** — from NVD:
   - CVE ID, CVSS score, severity
   - Plain-English description of the vulnerability
   - Confirmation that the new version is outside the vulnerable range

2. **Changelog Summary** — fetched from the project's GitHub releases or changelog URL:
   ```bash
   # Try GitHub releases API first
   curl -s "https://api.github.com/repos/<OWNER>/<REPO>/releases?per_page=20" \
   | python3 -c "
   import sys, json
   releases = json.load(sys.stdin)
   for r in releases:
       print(r['tag_name'], ':', r['body'][:300])
   "
   ```
   If no GitHub releases, fall back to the artifact's Maven Central `url` field.
   Summarise release notes between `current_version` and `new_version` — 3–5 bullet points.

3. **Breaking Change Warning** (major bumps only):
   - List removed/renamed APIs from the changelog
   - Link to migration guide if available

See `references/changelog-fetcher.md` for source lookup logic per artifact family.

---

### Step 6 — Create GitHub Pull Request

For each approved upgrade (or one consolidated PR), create a branch and open a PR via
the GitHub API. Read `references/github-pr.md` for full API details and auth setup.

#### Branch naming:
```
fix/cve-<ARTIFACT_ID>-<NEW_VERSION>          # single dep
fix/supply-chain-remediation-<DATE>          # consolidated
```

#### Git operations:
```bash
git checkout -b fix/cve-<ARTIFACT_ID>-<NEW_VERSION>
git add pom.xml
git commit -m "fix(deps): upgrade <ARTIFACT_ID> <OLD> → <NEW> (fixes <CVE_IDS>)"
git push origin fix/cve-<ARTIFACT_ID>-<NEW_VERSION>
```

#### PR via GitHub API:
```bash
curl -s -X POST "https://api.github.com/repos/<OWNER>/<REPO>/pulls" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "fix(deps): upgrade <ARTIFACT> <OLD> → <NEW> [<CVE_IDS>]",
    "head":  "fix/cve-<ARTIFACT_ID>-<NEW_VERSION>",
    "base":  "main",
    "body":  "<PR_BODY>",
    "draft": false
  }'
```

#### PR body template:
```markdown
## 🔐 Dependency Security Upgrade

**Artifact:** `<groupId>:<artifactId>` `<old>` → `<new>` (<bump_type>)
**Risk Score:** <score> (<tier>)

---

### 🚨 CVEs Fixed

| CVE | CVSS | Severity | Description |
|-----|------|----------|-------------|
| CVE-XXXX-XXXXX | 9.8 | Critical | <one-line description> |

---

### 📋 Changelog Summary (<old> → <new>)

- <bullet 1 from release notes>
- <bullet 2 from release notes>
- <bullet 3 from release notes>

Full changelog: <URL>

---

### ⚠️ Breaking Changes
<Only present for major bumps — list removed APIs and migration guide link>

---

### ✅ Checklist
- [x] pom.xml updated
- [x] `mvn dependency:resolve` passes
- [ ] CI pipeline passes
- [ ] Manual smoke test (if major bump)

---
*Auto-generated by Auto-Remediation Skill (Stage 4) — <DATE>*
```

---

### Step 7 — Post-PR Summary

After all PRs are created, present a final summary:

```markdown
## ✅ Remediation PRs Created

| Artifact | Old → New | CVEs Fixed | PR |
|----------|-----------|------------|----|
| struts2-core | 2.5.28 → 6.3.0.2 | CVE-2023-50164 | #42 |
| jackson-databind | 2.13.0 → 2.15.4 | CVE-2022-42003 | #43 |

⏸️ Skipped (deferred by user):
- log4j-core 2.14.1 — skipped, pending manual review

Next step: Stage 5 PR Validation Agent will run mvn test + OWASP scan + Grype on each PR.
```

Output `remediation-manifest.json` for Stage 5 to consume — see `references/input-schema.md`.

---

## Output Files

| File | Format | Consumer |
|------|--------|----------|
| `remediation-manifest.json` | JSON | Stage 5 PR Validation Agent |
| Patched `pom.xml` | XML | Git commit |
| GitHub PRs | GitHub API | Human review + Stage 5 |
| Markdown summary | Chat | Human |

---

## Reference Files

- `references/input-schema.md` — Stage 1 + Stage 2 merge logic and remediation-manifest.json schema
- `references/version-resolution.md` — Maven Central lookup, NVD CVE fix verification, edge cases
- `references/pom-patching.md` — Direct deps, property refs, multi-module POMs, BOM handling
- `references/changelog-fetcher.md` — Changelog source lookup per artifact family
- `references/github-pr.md` — GitHub API auth, branch creation, PR creation, error handling