---
name: supply-chain-audit-plugin
description: >
  Scan a Java project's SBOM for supply-chain risks on every PR — typosquatting, untrusted
  artifact sources, and license violations — and block the PR with exit code 1 when violations
  are found. Use this skill whenever the user wants to audit dependencies on pull requests,
  enforce supply-chain policies, detect typosquatted or suspicious Maven artifacts, block
  non-Maven-Central dependencies, enforce license allowlists, generate an SBOM, run Grype or
  Syft scans, or set up CI-agnostic dependency gating. Trigger even for casual requests like
  "block bad deps on PRs", "check for license violations", "flag suspicious packages",
  "is this artifact safe?", or "enforce supply chain policy".
---

# Supply-Chain Audit Plugin — Stage 3

Scan a Java project's SBOM (generated via Syft) and audit every dependency for typosquatting,
untrusted sources, and license violations. Blocks PRs via exit code 1 + a structured report.
CI-agnostic — works with GitHub Actions, GitLab CI, Jenkins, or any shell-based pipeline.

---

## What This Plugin Checks

| Check | Tool / Method | Blocks PR? |
|-------|--------------|------------|
| Typosquatting | Name-similarity heuristics against known-good artifact list | ✅ Yes |
| Untrusted source | Artifact not resolvable from Maven Central | ✅ Yes |
| License violation | License not in project allowlist | ✅ Yes |

---

## Workflow

### Step 1 — Understand the Context

Ask (or infer):
1. **Project path** — where is the `pom.xml`?
2. **License allowlist** — which licenses are permitted? (defaults in `references/license-policy.md`)
3. **Custom artifact allowlist** — any known-safe non-Central artifacts to whitelist?

Read `references/license-policy.md` for default allowlist and violation examples.

---

### Step 2 — Install Tools (if needed)

Check for Syft (SBOM generator) and Grype (vulnerability scanner):

```bash
syft version 2>/dev/null || echo "SYFT_NOT_INSTALLED"
grype version 2>/dev/null || echo "GRYPE_NOT_INSTALLED"
```

If missing, read `references/install.md` for installation instructions.

---

### Step 3 — Generate the SBOM

Use Syft to generate a CycloneDX JSON SBOM from the Maven project:

```bash
syft dir:<PROJECT_PATH> \
  --output cyclonedx-json=./sbom.cdx.json \
  --config .syft.yaml 2>/dev/null || \
syft dir:<PROJECT_PATH> \
  --output cyclonedx-json=./sbom.cdx.json
```

Verify output:
```bash
[ -f ./sbom.cdx.json ] && echo "SBOM generated: $(wc -c < sbom.cdx.json) bytes" || echo "SBOM FAILED"
```

The SBOM lists every component (direct + transitive) with name, version, purl, and license.
See `references/sbom-schema.md` for the CycloneDX JSON field reference.

---

### Step 4 — Run Audit Checks

Run all three checks in sequence. Collect all violations before reporting — do **not** stop
at the first violation. Full details for each check in `references/check-details.md`.

#### Check A: Typosquatting Detection

For each component in the SBOM, compute name-similarity against a known-safe artifact
corpus. Flag components whose `groupId` or `artifactId` closely resembles a popular
artifact but differs by 1–2 characters (Levenshtein distance ≤ 2).

Key signals to check:
- Character substitution: `springg-core`, `jakson-databind`
- Hyphen/dot confusion: `spring.core` vs `spring-core`
- Prefix/suffix additions: `spring-core-utils`, `log4j-core2`
- Homoglyph substitution: `1og4j` (numeral 1 vs letter l)

Reference corpus: `references/known-safe-artifacts.txt` (top 500 Maven Central artifacts).

```bash
# Example: flag artifacts with edit distance ≤ 2 from known-safe list
python3 references/typosquat_check.py --sbom ./sbom.cdx.json \
  --corpus references/known-safe-artifacts.txt \
  --threshold 2 \
  --output ./violations-typosquat.json
```

#### Check B: Untrusted Source Detection

Verify every artifact is resolvable from Maven Central. An artifact is trusted if:
- Its purl is `pkg:maven/...` AND
- It exists in Maven Central (`https://search.maven.org/solrsearch/select?q=...`)

```bash
python3 references/source_check.py --sbom ./sbom.cdx.json \
  --allowlist references/source-allowlist.txt \
  --output ./violations-sources.json
```

Artifacts in `references/source-allowlist.txt` are always trusted (for private/internal repos).

#### Check C: License Violation Detection

Compare each component's declared license against the project allowlist in
`references/license-policy.md`.

```bash
python3 references/license_check.py --sbom ./sbom.cdx.json \
  --policy references/license-policy.md \
  --output ./violations-licenses.json
```

Components with no declared license are flagged as `LICENSE_UNKNOWN` — treated as a
warning by default, configurable to block in `references/license-policy.md`.

---

### Step 5 — Aggregate Violations & Generate Report

Merge all violation files into a single `audit-report.json` and Markdown summary.

#### `audit-report.json` structure:

```json
{
  "audit_date": "<ISO-DATE>",
  "project": "<PROJECT_NAME>",
  "sbom_file": "sbom.cdx.json",
  "total_components": 142,
  "result": "BLOCKED",
  "violation_summary": {
    "typosquatting": 1,
    "untrusted_source": 2,
    "license_violation": 3
  },
  "violations": [
    {
      "component": "org.springg:springg-core:5.3.20",
      "check": "typosquatting",
      "severity": "HIGH",
      "detail": "Closely resembles 'org.springframework:spring-core' (edit distance 1)",
      "action": "BLOCK"
    },
    {
      "component": "com.internal:proprietary-lib:1.0.0",
      "check": "untrusted_source",
      "severity": "MEDIUM",
      "detail": "Not found in Maven Central; not in source allowlist",
      "action": "BLOCK"
    },
    {
      "component": "org.gnu:gpl-library:3.1.0",
      "check": "license_violation",
      "severity": "HIGH",
      "detail": "License 'GPL-3.0' not in project allowlist",
      "action": "BLOCK"
    }
  ],
  "warnings": [
    {
      "component": "com.example:unknown-lib:0.0.1",
      "check": "license_violation",
      "severity": "LOW",
      "detail": "No license declared in SBOM",
      "action": "WARN"
    }
  ]
}
```

#### Markdown Summary (always print to stdout):

```markdown
## 🔒 Supply-Chain Audit Report — <PROJECT_NAME>
**Date:** <DATE> | **Components scanned:** <N> | **Result:** 🔴 BLOCKED / 🟢 PASSED

### Violation Summary
| Check | Violations | Warnings |
|-------|-----------|---------|
| 🎭 Typosquatting | X | – |
| 🌐 Untrusted Source | X | – |
| ⚖️ License Violation | X | X |

### 🚨 Blocking Violations

**[TYPOSQUAT]** `org.springg:springg-core:5.3.20`
- Closely resembles `org.springframework:spring-core` (edit distance 1)
- Action: Remove or replace with the legitimate artifact

**[UNTRUSTED]** `com.internal:proprietary-lib:1.0.0`
- Not found in Maven Central; not in source allowlist
- Action: Add to `source-allowlist.txt` if intentional, or remove

**[LICENSE]** `org.gnu:gpl-library:3.1.0`
- License `GPL-3.0` not permitted under project policy
- Action: Replace with a compatible alternative

### ⚠️ Warnings (non-blocking)
...

### ✅ Next Steps
1. Remove or replace all blocking violations listed above
2. Re-run this plugin to confirm clean scan
3. Add legitimate internal artifacts to `source-allowlist.txt`
```

---

### Step 6 — Enforce: Exit Code

After generating the report, enforce the result:

```bash
# Exit 1 if any blocking violations found — fails any CI pipeline step
VIOLATIONS=$(python3 -c "
import json
r = json.load(open('./audit-report.json'))
print(len([v for v in r['violations'] if v['action'] == 'BLOCK']))
")

if [ "$VIOLATIONS" -gt 0 ]; then
  echo "❌ PR BLOCKED — $VIOLATIONS supply-chain violation(s) found. See audit-report.json."
  exit 1
else
  echo "✅ PR PASSED — No supply-chain violations detected."
  exit 0
fi
```

**Exit codes:**
| Code | Meaning |
|------|---------|
| `0` | Clean — no blocking violations |
| `1` | Blocked — one or more violations found |

Warnings never cause a block — they are informational only.

---

### Step 7 — Human Approval Gate ⛔ STOP

After presenting the Markdown summary, **always stop and wait for explicit human approval**
before marking the audit complete or passing results to Stage 4/5.

```
---
⛔ Audit complete — approval required

Output files generated:
  • sbom.cdx.json        (<SIZE>)
  • audit-report.json    (<SIZE>)
Result: BLOCKED / PASSED

Reply with one of:
  • "approve"                        — accept results, pass to next stage
  • "whitelist [artifact]"           — add to source allowlist and re-audit
  • "allow license [SPDX-ID]"        — add license to policy and re-audit
  • "stop here"                      — end session, keep output files only
---
```

If user requests a whitelist or license change, update the relevant reference file,
re-run the affected check only, regenerate the report, and re-present this gate.

---

## Output Files

| File | Format | Consumer |
|------|--------|----------|
| `sbom.cdx.json` | CycloneDX JSON | Grype, Stage 4, Stage 5 |
| `audit-report.json` | JSON | Stage 5 PR Validation Agent |
| Markdown summary | stdout | Human / CI log |
| Exit code | Shell | Any CI pipeline |

---

## CI Integration Snippet (CI-agnostic)

```yaml
# Add to any CI pipeline step
- name: Supply-Chain Audit
  run: |
    claude -p "Run the supply-chain-audit-plugin on this project" \
      --project-path ${{ github.workspace }}
    # Exit code 1 automatically fails the step
```

See `references/ci-snippets.md` for ready-to-paste GitHub Actions, GitLab CI, and Jenkins examples.

---

## Reference Files

- `references/install.md` — Syft + Grype installation (Linux, macOS, Windows, Docker)
- `references/sbom-schema.md` — CycloneDX JSON field reference
- `references/check-details.md` — Deep-dive on typosquat, source, and license check logic
- `references/license-policy.md` — Default license allowlist + configuration
- `references/known-safe-artifacts.txt` — Top 500 Maven Central artifact corpus
- `references/source-allowlist.txt` — Trusted non-Central artifact overrides
- `references/ci-snippets.md` — CI pipeline integration examples