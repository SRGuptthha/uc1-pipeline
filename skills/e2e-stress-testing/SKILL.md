---
name: e2e-stress-testing
description: >
  Full end-to-end pipeline stress test across 5+ real Java repos — CVE-heavy, zero-CVE,
  complex dependency trees, and malformed pom.xml edge cases — run sequentially with per-repo
  timing metrics and a consolidated pass/fail report. Use this skill whenever the user wants
  to stress test the full supply-chain pipeline, validate all days end-to-end, run integration
  tests across multiple Java repos, test edge cases like malformed POMs or deep dependency
  trees, verify the pipeline handles real-world scenarios, or generate a cross-repo health
  report. Trigger for requests like "test the full pipeline", "run e2e tests", "stress test
  across repos", "validate all days work together", or "integration test".
---

# End-to-End Integration & Stress Testing — Stage 6

Run the full Stage 1→5 pipeline sequentially across 5+ Java repos covering all stress
scenarios. Collect per-repo timing, gate results, and failures into a single
`e2e-report.json` and Markdown summary for Stage 7's audit trail.

---

## Repo Input Format

Accept repos as a mixed list of GitHub URLs and local paths:

```json
{
  "repos": [
    { "id": "repo-1", "source": "https://github.com/org/cve-heavy-app",   "scenario": "cve-heavy" },
    { "id": "repo-2", "source": "https://github.com/org/clean-baseline",   "scenario": "zero-cve" },
    { "id": "repo-3", "source": "https://github.com/org/complex-tree-app", "scenario": "complex-tree" },
    { "id": "repo-4", "source": "/local/path/to/malformed-pom-project",    "scenario": "malformed-pom" },
    { "id": "repo-5", "source": "https://github.com/org/mixed-issues-app", "scenario": "mixed" }
  ],
  "batch_label": "day6-stress-run-<DATE>",
  "pipeline_stages": ["day1", "day2", "day3", "day4", "day5"]
}
```

If the user hasn't provided repos, ask for them. Alternatively, suggest the built-in
reference repos in `references/reference-repos.md` — curated public repos per scenario.

See `references/repo-input-schema.md` for the full config format.

---

## Workflow

### Step 1 — Validate & Prepare Repos

For each repo in the list:

#### GitHub URL repos:
```bash
REPO_DIR="/tmp/e2e/<REPO_ID>"
git clone --depth 1 "<GITHUB_URL>" "$REPO_DIR" 2>&1
echo "CLONE_EXIT:$?"
```

Use `--depth 1` (shallow clone) — we only need the current state, not history.
For private repos, ensure `GITHUB_TOKEN` is set and use:
```bash
git clone --depth 1 "https://$GITHUB_TOKEN@github.com/<OWNER>/<REPO>.git" "$REPO_DIR"
```

#### Local path repos:
```bash
# Verify path exists and contains a pom.xml
[ -f "<LOCAL_PATH>/pom.xml" ] && echo "POM_FOUND" || echo "POM_MISSING"
```

If clone or path validation fails, mark repo as `SETUP_FAILED` and continue.
Record setup duration.

---

### Step 2 — Run Pipeline Sequentially Per Repo

For each repo, run all pipeline stages in order. Read the relevant Day skill before
each stage and follow its workflow. Collect timing and result for every stage.

```
For each repo:
  ├── Stage: Stage 1 — OWASP Dependency-Check scan
  ├── Stage: Stage 2 — Risk Scoring Agent
  ├── Stage: Stage 3 — Supply-Chain Audit Plugin
  ├── Stage: Stage 4 — Auto-Remediation (dry-run mode — no PRs created)
  └── Stage: Stage 5 — PR Validation gates only (no merge)
```

> ⚠️ **Stage 4 runs in dry-run mode during stress testing** — generate the upgrade plan and
> `remediation-manifest.json` but do NOT create GitHub PRs or patch pom.xml.
> Stage 5 runs validation gates only — no auto-merge.

Record per stage:
```json
{
  "stage": "day1",
  "status": "PASS | FAIL | ERROR | SKIP",
  "duration_seconds": 47,
  "detail": "<brief summary>",
  "artifacts": ["dependency-check-report.json"]
}
```

See `references/stage-runner.md` for invocation details per stage.

---

### Step 3 — Apply Scenario-Specific Assertions

Each scenario has expected outcomes. After each repo completes, assert the pipeline
behaved correctly. Read `scenarios/<SCENARIO>.md` for full assertion sets.

| Scenario | Key Assertions |
|----------|---------------|
| `cve-heavy` | Stage 1 finds ≥ 5 Critical/High CVEs; Stage 2 scores ≥ 1 dep at 80+; Stage 4 produces upgrade plan |
| `zero-cve` | Stage 1 finds 0 CVEs; Stage 2 all scores < 40; Stage 3 passes cleanly; pipeline completes green |
| `complex-tree` | Stage 1 scans ≥ 50 transitive deps; Stage 2 correctly scores transitive vs direct; Stage 3 SBOM ≥ 50 components |
| `malformed-pom` | Pipeline detects and reports the malformation gracefully; no unhandled crash; error surfaced in report |
| `mixed` | At least one CVE found; at least one clean dep; partial remediation plan generated |

Assertion result:
```json
{
  "assertion": "day1_finds_critical_cves",
  "expected": "≥ 5 Critical/High CVEs",
  "actual": "8 Critical/High CVEs found",
  "passed": true
}
```

---

### Step 4 — Collect Timing Metrics

After each repo completes, record wall-clock timings per stage and total:

```python
import time

def time_stage(fn, *args):
    start = time.time()
    result = fn(*args)
    duration = round(time.time() - start, 1)
    return result, duration
```

Timing summary per repo:

| Stage | Duration |
|-------|----------|
| Setup (clone/validate) | Xs |
| Stage 1 — OWASP scan | Xs |
| Stage 2 — Risk scoring | Xs |
| Stage 3 — Supply-chain audit | Xs |
| Stage 4 — Remediation (dry-run) | Xs |
| Stage 5 — Validation gates | Xs |
| **Total** | **Xs** |

Flag any stage exceeding expected thresholds (see `references/timing-thresholds.md`).

---

### Step 5 — Human Checkpoint ⛔ STOP AFTER EACH REPO

After each repo completes (not after all — after each), present a brief status update
and ask whether to continue:

```
---
✅ Repo 2/5 complete: clean-baseline (zero-cve)
  All stages: PASS | Total time: 3m 42s
  All scenario assertions: PASS (4/4)

Proceed to repo 3/5 (complex-tree-app)?
  • "yes" / "continue" — run next repo
  • "stop" — end stress test, generate report with results so far
  • "retry <stage>" — re-run a failed stage on this repo before continuing
---
```

This allows the user to investigate failures without waiting for all repos to complete.

---

### Step 6 — Generate E2E Report

After all repos complete (or user stops), generate `e2e-report.json` and Markdown summary.

#### Markdown Summary:

```markdown
## 🧪 End-to-End Stress Test Report
**Run:** <BATCH_LABEL> | **Date:** <DATE> | **Repos tested:** <N>

### Overall Results

| Repo | Scenario | Day1 | Day2 | Day3 | Day4 | Day5 | Assertions | Total Time |
|------|----------|------|------|------|------|------|------------|------------|
| cve-heavy-app | cve-heavy | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5 ✅ | 8m 14s |
| clean-baseline | zero-cve | ✅ | ✅ | ✅ | ✅ | ✅ | 4/4 ✅ | 3m 42s |
| complex-tree-app | complex-tree | ✅ | ✅ | ⚠️ | ✅ | ✅ | 3/4 ⚠️ | 11m 03s |
| malformed-pom-proj | malformed-pom | ✅ | ❌ | – | – | – | 2/3 ⚠️ | 1m 18s |
| mixed-issues-app | mixed | ✅ | ✅ | ✅ | ✅ | ⚠️ | 4/5 ⚠️ | 6m 55s |

### ❌ Failures & Errors

**complex-tree-app — Stage 3 (Supply-Chain Audit)**
- Assertion failed: expected SBOM ≥ 50 components, got 31
- Possible cause: Syft depth limit on deeply nested Maven modules

**malformed-pom-proj — Stage 2 (Risk Scoring)**
- ERROR: JSON parse failure on OWASP output — malformed pom.xml caused partial scan
- Pipeline correctly surfaced error and halted gracefully ✅

### ⏱️ Timing Summary

| Stage | Min | Max | Avg |
|-------|-----|-----|-----|
| Stage 1 — OWASP scan | 47s | 4m 12s | 2m 18s |
| Stage 2 — Risk scoring | 8s | 34s | 19s |
| Stage 3 — Supply-chain audit | 12s | 1m 03s | 38s |
| Stage 4 — Remediation dry-run | 5s | 48s | 24s |
| Stage 5 — Validation gates | 1m 12s | 4m 55s | 2m 41s |

### ✅ Scenario Coverage

| Scenario | Status | Notes |
|----------|--------|-------|
| CVE-heavy | ✅ Full pass | 8 CVEs detected, scored, remediation plan generated |
| Zero-CVE | ✅ Full pass | Clean pipeline confirmed |
| Complex tree | ⚠️ Partial | SBOM component count lower than expected |
| Malformed pom.xml | ⚠️ Graceful fail | Error surfaced correctly, no crash |
| Mixed | ⚠️ Partial | Stage 5 JaCoCo below threshold |
```

Output `e2e-report.json` for Stage 7 audit trail.
See `references/e2e-report-schema.md` for the full output schema.

---

## Output Files

| File | Format | Consumer |
|------|--------|----------|
| `e2e-report.json` | JSON | Stage 7 Audit Trail |
| Markdown summary | Chat | Human |
| Per-repo stage artifacts | Various | Debug / rerun |

---

## Reference & Scenario Files

- `references/repo-input-schema.md` — Full repo config format, private repo auth
- `references/reference-repos.md` — Curated public repos per scenario (ready to use)
- `references/stage-runner.md` — How to invoke each Day skill in stress-test mode
- `references/timing-thresholds.md` — Expected duration ranges per stage
- `references/e2e-report-schema.md` — Full `e2e-report.json` schema
- `scenarios/cve-heavy.md` — Assertions + expected outputs for CVE-heavy repos
- `scenarios/zero-cve.md` — Assertions for clean repos
- `scenarios/complex-tree.md` — Assertions for deep dependency trees
- `scenarios/malformed-pom.md` — Edge cases and expected graceful failure modes
- `scenarios/mixed.md` — Assertions for mixed repos