---
name: audit-trail-demo
description: >
  Aggregate all scan results into a single dependency health report (PDF + HTML) and run a
  live or replay demo of the full supply-chain pipeline. Use this skill whenever the user
  wants to generate a final audit report, create an executive summary of CVE findings,
  demonstrate the full pipeline end-to-end, produce a dependency health report for
  stakeholders, replay scan results for a presentation, or show the journey from vulnerable
  project to fixed PRs. Trigger for "generate the audit report", "create the health report",
  "run the demo", "show the pipeline", "executive summary", "present the findings", or
  "demo readiness".
---

# Audit Trail & Demo Readiness — Stage 7

Aggregate outputs from all previous days into a single tiered report (executive summary +
technical appendix) delivered as both PDF and HTML. Run the pipeline as a live step-by-step
demo or replay from existing artifacts — no re-scanning required in replay mode.

---

## Two Modes

### Mode A — Replay (default)
Aggregate existing Stage 1–6 artifacts. No tools re-run. Fast — typically < 2 minutes.
Use when artifacts already exist from a previous run.

### Mode B — Live Demo
Run the full Stage 1→5 pipeline live against a chosen repo, narrating each step as it
executes. Use for real-time demonstrations to an audience.

Ask the user which mode to use if not specified:
```
Which demo mode?
  • "replay"  — aggregate existing artifacts (fast, uses Stage 1–6 outputs)
  • "live"    — run the full pipeline live against a repo (real-time demo)
```

---

## Workflow

### Step 1 — Collect Artifacts (Both Modes)

#### Replay mode — locate existing outputs:

```python
ARTIFACT_MAP = {
    "day1": "./dependency-check-report/dependency-check-report.json",
    "day2": "./risk-scores.json",
    "day3": "./audit-report.json",
    "day4": "./remediation-manifest.json",
    "day5": "./validation-report.json",
    "day6": "./e2e-report.json",   # optional — include if exists
}

def collect_artifacts(artifact_map):
    found, missing = {}, []
    for day, path in artifact_map.items():
        if os.path.exists(path):
            found[day] = path
        else:
            missing.append(day)
    return found, missing
```

If any Stage 1–5 artifacts are missing, ask the user to provide paths or re-run that day.
Stage 6 (`e2e-report.json`) is optional — include stress test results if present.

#### Live mode — run pipeline then collect:

Invoke each stage in sequence using the stage-runner pattern from Stage 6
(`references/live-demo-runner.md`). Narrate each step to the audience as it runs.
After all stages complete, collect artifacts as above.

---

### Step 2 — Aggregate Findings

Parse all artifacts and build a unified findings object:

```python
def aggregate(artifacts):
    return {
        "project":           extract_project_name(artifacts["day1"]),
        "scan_date":         extract_scan_date(artifacts["day1"]),
        "total_deps_scanned": count_deps(artifacts["day1"]),
        "cve_summary":       extract_cve_summary(artifacts["day1"]),
        "risk_summary":      extract_risk_summary(artifacts["day2"]),
        "audit_summary":     extract_audit_summary(artifacts["day3"]),
        "remediation_summary": extract_remediation_summary(artifacts["day4"]),
        "validation_summary":  extract_validation_summary(artifacts["day5"]),
        "e2e_summary":       extract_e2e_summary(artifacts.get("day6")),
        "pipeline_health":   compute_pipeline_health(artifacts),
    }
```

See `references/aggregator.md` for all extraction function implementations.

---

### Step 3 — Compute Pipeline Health Score

A single 0–100 health score summarising the project's supply-chain posture:

```python
def compute_pipeline_health(data):
    # Start at 100, deduct for issues
    score = 100

    # CVE deductions
    score -= data["cve_summary"]["critical_count"] * 15
    score -= data["cve_summary"]["high_count"] * 8
    score -= data["cve_summary"]["medium_count"] * 2

    # Audit deductions
    score -= data["audit_summary"]["typosquat_count"] * 10
    score -= data["audit_summary"]["untrusted_source_count"] * 8
    score -= data["audit_summary"]["license_violation_count"] * 5

    # Remediation credit (fixed issues restore points)
    score += data["remediation_summary"]["cves_fixed_count"] * 10
    score += data["validation_summary"]["prs_merged"] * 5

    # Coverage penalty
    coverage = data["validation_summary"].get("avg_jacoco_coverage", 80)
    if coverage < 80:
        score -= int((80 - coverage) * 0.5)

    return max(0, min(100, round(score)))

def health_grade(score):
    if score >= 90: return "A", "🟢 Excellent"
    if score >= 75: return "B", "🟢 Good"
    if score >= 60: return "C", "🟡 Moderate"
    if score >= 40: return "D", "🟠 Poor"
    return "F", "🔴 Critical"
```

---

### Step 4 — Generate HTML Report

Build a self-contained interactive HTML report from `templates/report.html`.

The HTML report contains two tiers toggled by tabs:

**Tab 1 — Executive Summary**
- Pipeline health score + grade (large, prominent)
- 4 KPI cards: Total CVEs | CVEs Fixed | PRs Merged | Coverage %
- CVE severity donut chart (Critical / High / Medium / Low)
- Risk tier breakdown bar chart
- Top 5 highest-risk dependencies table
- Remediation status timeline (Before → After)
- Key findings in plain English (3–5 bullets, no jargon)

**Tab 2 — Technical Appendix**
- Full CVE table (sortable: by CVSS, by artifact, by severity)
- Risk score table (all deps, all factors)
- Supply-chain audit violations table
- Remediation manifest (artifact | old → new | bump type | PR link)
- Validation gate results per PR
- Stage 6 stress test summary (if available)
- Raw artifact links (download JSON outputs)

Read `templates/report.html` for the base template with CSS variables, chart placeholders,
and data injection points. Inject aggregated data as a `<script>` block:

```html
<script>
  window.REPORT_DATA = {{ REPORT_DATA_JSON }};
</script>
```

Output: `dependency-health-report.html`

---

### Step 5 — Generate PDF Report

Convert the HTML report to PDF using `weasyprint`:

```bash
pip install weasyprint --break-system-packages -q

python3 -c "
from weasyprint import HTML
HTML('dependency-health-report.html').write_pdf('dependency-health-report.pdf')
print('PDF generated')
"
```

If weasyprint is unavailable, fall back to a Markdown-to-PDF approach:

```bash
pip install markdown2 --break-system-packages -q
python3 references/md_to_pdf_fallback.py \
  --input dependency-health-report.md \
  --output dependency-health-report.pdf
```

Read `references/pdf-generation.md` for weasyprint setup, font handling, and fallback options.

Output: `dependency-health-report.pdf`

---

### Step 6 — Live Demo Narration Script (Live Mode Only)

If running in live mode, narrate each pipeline stage to the audience using this script.
Read `references/demo-script.md` for the full narration with talking points per stage.

High-level flow:
```
1. "Here's our vulnerable project — let's see what's lurking..."
   → Run Stage 1 OWASP scan live, show CVEs appearing in real time

2. "Now let's understand which of these actually matter most..."
   → Run Stage 2 risk scoring, show composite scores

3. "Are there any supply-chain risks beyond CVEs?"
   → Run Stage 3 audit, show typosquat + license check

4. "Let's fix them — automatically."
   → Run Stage 4 dry-run, show upgrade plan

5. "Before we merge, does everything still work?"
   → Run Stage 5 gates, show all passing

6. "Here's the full picture — before and after."
   → Show HTML report, highlight health score improvement
```

---

### Step 7 — Human Approval Gate ⛔ STOP BEFORE DELIVERING

Present output files and wait for approval before finalising:

```
---
⛔ Report ready — approval required

Output files generated:
  • dependency-health-report.html   (<SIZE>)
  • dependency-health-report.pdf    (<SIZE>)

Pipeline Health Score: <SCORE>/100 (<GRADE>)

Please review the report. Reply with:
  • "approve"                  — finalise and deliver
  • "regenerate executive summary" — rewrite the key findings section
  • "add repo [name]"          — include another repo's results
  • "export raw data"          — also output aggregated-findings.json
---
```

---

### Step 8 — Deliver Final Outputs

Present all output files to the user. Write `audit-trail.json` as the permanent
machine-readable record of the full pipeline run.

```
✅ Stage 7 complete — full supply-chain audit trail ready.

Outputs:
  📄 dependency-health-report.pdf   — shareable report (exec + technical)
  🌐 dependency-health-report.html  — interactive browser report
  📦 audit-trail.json               — machine-readable full audit record
```

See `references/audit-trail-schema.md` for the `audit-trail.json` structure.

---

## Output Files

| File | Format | Audience |
|------|--------|----------|
| `dependency-health-report.pdf` | PDF | Executives, auditors, stakeholders |
| `dependency-health-report.html` | HTML | Engineers, interactive review |
| `audit-trail.json` | JSON | Compliance, archiving, future pipeline runs |

---

## Reference & Template Files

- `references/aggregator.md` — All extraction functions for each day's artifacts
- `references/live-demo-runner.md` — Live mode stage invocation + audience narration timing
- `references/demo-script.md` — Full talking-point script for live demo presentation
- `references/pdf-generation.md` — weasyprint setup, font config, fallback options
- `references/audit-trail-schema.md` — Full `audit-trail.json` schema
- `templates/report.html` — Base HTML report template with charts, tabs, CSS variables