---
name: risk-scoring-agent
description: >
  Score Java dependencies by risk using CVE severity, business criticality, exposure type,
  and maintenance status. Use this skill whenever the user wants to prioritize vulnerabilities,
  rank dependencies by risk, score CVEs beyond raw CVSS, assign business impact to scan
  results, or generate a risk-ranked dependency report. Triggers after an OWASP Dependency-Check
  scan (Stage 1) or whenever the user says things like "score my dependencies", "which CVEs
  should I fix first?", "rank by risk", "business criticality scoring", "prioritize my
  vulnerabilities", or "risk report for my Java project".
---

# Risk Scoring Agent — Stage 2

Score every Java dependency from the Stage 1 OWASP scan output by composite risk, combining
CVE severity, business criticality, transitive exposure, and maintenance health. Outputs a
Markdown summary (chat) + `risk-scores.json` (machine-readable) for downstream agents.

---

## Scoring Model

Each dependency receives a **Composite Risk Score (0–100)** built from four weighted factors:

| Factor | Weight | Source |
|--------|--------|--------|
| CVE CVSS Severity | 40% | NVD CVSS v3 score from OWASP JSON report |
| Business Criticality | 30% | User-defined tags (e.g. `payment`, `auth`, `core`) |
| Dependency Exposure | 20% | Direct vs. transitive (from OWASP `isVirtual` + dependency tree) |
| Maintenance Status | 10% | Dependency age + release recency heuristics |

See `references/scoring-formulas.md` for exact calculation logic per factor.

---

## Workflow

### Step 1 — Locate the OWASP Scan Output

Look for the Stage 1 scan report in the default output location:
```
./dependency-check-report/dependency-check-report.json
```

If not found, ask the user to provide the path or upload the file. Do **not** re-run the
OWASP scan — this agent consumes existing output only.

---

### Step 2 — Extract Dependencies & CVEs

Parse the OWASP JSON report. For each dependency entry, extract:
- `fileName` — JAR/artifact name
- `isVirtual` — whether it's a transitive dependency
- `vulnerabilities[]` — list of CVEs with `cvssv3.baseScore` and `severity`
- `packages[].id` — Maven GAV (groupId:artifactId:version)

See `references/owasp-json-schema.md` for the full field reference.

---

### Step 3 — Collect Business Criticality Tags

Present the user with a list of unique dependencies found in the scan and ask them to tag
any that are business-critical:

```
The following dependencies were found. Please tag any that are business-critical
(e.g. payment, auth, core, public-api, data-storage). Leave blank if not critical.

  1. org.springframework:spring-core:5.3.20        → [tag or blank]
  2. com.fasterxml.jackson.core:jackson-databind   → [tag or blank]
  3. org.apache.struts:struts2-core:2.5.28         → [tag or blank]
  ...

You can also provide a criticality-tags.json file — see references/tags-format.md.
```

Accepted tag values and their score multipliers are defined in `references/scoring-formulas.md`.

If the user skips tagging, default all business criticality scores to **0.5 (neutral)**.

---

### Step 4 — Compute Composite Risk Scores

For each dependency, compute the four factor scores and combine them. Read
`references/scoring-formulas.md` for the exact formulas.

High-level logic:
1. **CVSS Factor** — normalize the highest CVE CVSS score (0–10) → (0–1), weight × 0.40
2. **Business Criticality Factor** — map tag to score (0–1), weight × 0.30
3. **Exposure Factor** — direct = 1.0, transitive = 0.5, weight × 0.20
4. **Maintenance Factor** — score based on artifact age + last release recency, weight × 0.10

Final score = sum of weighted factors × 100, rounded to one decimal.

---

### Step 5 — Generate Output Files

#### A) `risk-scores.json`

```json
{
  "scan_date": "<ISO-DATE>",
  "project": "<PROJECT_NAME>",
  "scoring_model_version": "1.0",
  "dependencies": [
    {
      "artifact": "org.apache.struts:struts2-core:2.5.28",
      "composite_risk_score": 91.4,
      "risk_tier": "CRITICAL",
      "factors": {
        "cvss_score": 9.8,
        "cvss_factor": 0.98,
        "business_criticality_tag": "core",
        "business_criticality_factor": 1.0,
        "exposure": "direct",
        "exposure_factor": 1.0,
        "artifact_age_days": 730,
        "maintenance_factor": 0.3
      },
      "cves": ["CVE-2023-50164"],
      "recommended_action": "Fix immediately — block deployment"
    }
  ]
}
```

#### B) Markdown Summary (in chat)

```markdown
## 🎯 Dependency Risk Scores — <PROJECT_NAME>
**Scored:** <N> dependencies | **Scan date:** <DATE>

### Risk Tier Breakdown
| Tier | Score Range | Count |
|------|-------------|-------|
| 🔴 Critical | 80–100 | X |
| 🟠 High     | 60–79  | X |
| 🟡 Medium   | 40–59  | X |
| 🟢 Low      | 0–39   | X |

### 🔴 Critical Risk Dependencies (score ≥ 80)
| Artifact | Score | Top CVE | Exposure | Business Tag |
|----------|-------|---------|----------|--------------|
| struts2-core:2.5.28 | 91.4 | CVE-2023-50164 (9.8) | Direct | core |

### 🟠 High Risk Dependencies (score 60–79)
...

### ✅ Recommended Fix Order
1. `struts2-core:2.5.28` — Score 91.4 — Fix immediately
2. ...
```

---

### Step 6 — Human Approval Gate ⛔ STOP BEFORE HANDING OFF

After presenting the Markdown summary and generating `risk-scores.json`, **always stop and
wait for explicit human approval** before passing results to any downstream agent (Stage 3+).

```
---
⛔ Risk scoring complete — approval required

Output files generated:
  • risk-scores.json  (<SIZE>)

Does the scoring look accurate? Reply with:
  • "approve"                      — pass results to next stage
  • "retag [artifact] as [tag]"    — adjust a business criticality tag and re-score
  • "stop here"                    — end session, keep output files only
---
```

If the user requests a retag, update the tag, recompute that dependency's score, regenerate
both output files, and re-present the approval gate.

---

## Risk Tiers

| Tier | Score | Recommended Action |
|------|-------|--------------------|
| 🔴 Critical | 80–100 | Fix immediately, block deployment |
| 🟠 High | 60–79 | Fix within current sprint |
| 🟡 Medium | 40–59 | Fix in next release cycle |
| 🟢 Low | 0–39 | Track, fix when convenient |

---

## Output Files

| File | Format | Consumer |
|------|--------|----------|
| `risk-scores.json` | JSON | Stage 3 Plugin, Stage 4 Auto-Remediation, Stage 5 PR Validation |
| Markdown summary | Chat | Human review |

---

## Reference Files

- `references/scoring-formulas.md` — Exact factor formulas, tag multipliers, maintenance heuristics
- `references/owasp-json-schema.md` — OWASP Dependency-Check JSON field reference
- `references/tags-format.md` — Format for uploading a `criticality-tags.json` file