---
name: pr-validation-agent
description: >
  Orchestrates full PR validation for Java dependency upgrades: mvn test → OWASP scan →
  Grype scan → JaCoCo coverage ≥ 80% → auto-merge (patch/minor) or human approval (major).
  Use this skill whenever the user wants to validate a dependency upgrade PR, run the full
  security + test gate pipeline, check if a PR is safe to merge, enforce JaCoCo coverage
  thresholds, orchestrate OWASP + Grype scans on a branch, or automate PR merging after
  security checks. Triggers from Stage 4 remediation-manifest.json or standalone on any PR.
  Trigger even for "is this PR safe to merge?", "run the checks on PR #42", "validate my
  dependency PRs", or "gate this PR on test coverage".
---

# PR Validation Agent — Stage 5

Orchestrate the full validation pipeline across every open PR from Stage 4 (or any standalone
PR). Run all four gates in sequence per PR, collect results, auto-merge patch/minor passes,
and present a human approval prompt for major bumps or partial failures.

---

## Architecture

This agent coordinates four sub-skills, each responsible for one gate:

```
pr-validation-agent (orchestrator)
├── skills/mvn-test.md         — Gate 1: mvn test
├── skills/owasp-scan.md       — Gate 2: OWASP Dependency-Check
├── skills/grype-scan.md       — Gate 3: Grype vulnerability scan
└── skills/jacoco-coverage.md  — Gate 4: JaCoCo coverage ≥ 80%
```

Read the relevant skill file before executing each gate.

---

## Workflow

### Step 1 — Load PR List

**From Stage 4 manifest:**
```python
import json
with open("./remediation-manifest.json") as f:
    manifest = json.load(f)
prs = manifest["pull_requests"]  # list of {pr_number, branch, artifact, bump_type, ...}
```

**Standalone mode** (no manifest): ask the user for PR numbers or branch names:
```
Which PRs should I validate? Provide PR numbers (e.g. "42, 43, 44") or branch names.
```

Build a unified PR queue sorted by `composite_risk_score` descending (highest risk first).
See `references/pr-queue-schema.md` for the full queue structure.

---

### Step 2 — Checkout & Prepare Each PR Branch

For each PR in the queue:

```bash
# Fetch the PR branch
git fetch origin pull/<PR_NUMBER>/head:pr-<PR_NUMBER>
git checkout pr-<PR_NUMBER>

# Confirm we're on the right branch
git log --oneline -3
```

If checkout fails, mark PR as `VALIDATION_ERROR` and continue to next PR.

---

### Step 3 — Run All Four Gates

Run gates **sequentially** per PR. Do not skip later gates on early failure — collect all
results so the human sees the full picture.

For each gate, read the corresponding skill file and execute:

| Gate | Skill File | Pass Condition |
|------|-----------|----------------|
| 1 — mvn test | `skills/mvn-test.md` | Exit code 0, zero test failures |
| 2 — OWASP scan | `skills/owasp-scan.md` | Zero Critical/High CVEs introduced |
| 3 — Grype scan | `skills/grype-scan.md` | Zero Critical/High findings |
| 4 — JaCoCo coverage | `skills/jacoco-coverage.md` | Line coverage ≥ 80% |

Collect per-gate result:
```json
{
  "gate": "mvn-test",
  "status": "PASS | FAIL | ERROR",
  "detail": "<summary of output>",
  "duration_seconds": 42
}
```

---

### Step 4 — Aggregate Results & Determine PR Verdict

After all four gates complete for a PR, compute the verdict:

```python
def verdict(gates, bump_type):
    all_pass = all(g["status"] == "PASS" for g in gates)
    if all_pass and bump_type in ("PATCH", "MINOR"):
        return "AUTO_MERGE"
    elif all_pass and bump_type == "MAJOR":
        return "HUMAN_APPROVAL_REQUIRED"
    else:
        return "BLOCKED"
```

| Condition | Verdict |
|-----------|---------|
| All gates pass + PATCH or MINOR bump | `AUTO_MERGE` |
| All gates pass + MAJOR bump | `HUMAN_APPROVAL_REQUIRED` |
| Any gate fails | `BLOCKED` |
| Any gate errors | `VALIDATION_ERROR` — re-run that gate |

---

### Step 5 — Post Results as PR Comment

For every PR, post a validation summary comment via GitHub API:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/issues/<PR_NUMBER>/comments" \
  -d "{\"body\": \"<COMMENT_BODY>\"}"
```

#### Comment template:

```markdown
## 🤖 PR Validation Report — Auto-Remediation Agent

**PR:** #<NUMBER> | **Artifact:** `<artifact>` `<old>` → `<new>` (<bump_type>)
**Verdict:** ✅ AUTO-MERGE / ⚠️ NEEDS APPROVAL / ❌ BLOCKED

### Gate Results

| Gate | Status | Detail |
|------|--------|--------|
| 🧪 mvn test | ✅ PASS / ❌ FAIL | <X tests, Y failures, Zs> |
| 🔐 OWASP scan | ✅ PASS / ❌ FAIL | <N CVEs found, severity breakdown> |
| 🛡️ Grype scan | ✅ PASS / ❌ FAIL | <N findings, severity breakdown> |
| 📊 JaCoCo coverage | ✅ PASS / ❌ FAIL | <X% line coverage (threshold: 80%)> |

### ❌ Failure Details
<Only present if any gate failed — bullet points per failure>

### ⚠️ Breaking Change Note
<Only present for MAJOR bumps — migration guide link>

---
*Validated by PR Validation Agent (Stage 5) — <ISO-DATE>*
```

---

### Step 6 — Merge or Block

#### AUTO_MERGE (patch/minor, all gates pass)

Merge via GitHub API:

```bash
curl -s -X PUT \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/merge" \
  -d '{
    "commit_title": "fix(deps): merge <ARTIFACT> <OLD> → <NEW> [validated]",
    "commit_message": "All validation gates passed. Auto-merged by PR Validation Agent.",
    "merge_method": "squash"
  }'
```

After merge: delete the feature branch.

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/git/refs/heads/<BRANCH>"
```

#### HUMAN_APPROVAL_REQUIRED (major bump, all gates pass)

Present to the user:

```
---
⚠️ Human approval required — MAJOR version bump

PR #<N>: <artifact> <old> → <new> (MAJOR)
All 4 validation gates passed ✅

This is a major version bump — auto-merge is disabled.
Please review the PR and breaking changes before approving.

PR URL: https://github.com/<OWNER>/<REPO>/pull/<N>

Reply with:
  • "merge <PR_NUMBER>"   — proceed with merge
  • "skip <PR_NUMBER>"   — leave PR open for manual review
---
```

#### BLOCKED (any gate failed)

Do not merge. The PR comment (Step 5) already explains the failures.
Present a summary to the user and ask if they want to re-run after fixes.

---

### Step 7 — Final Validation Report

After processing all PRs, present a consolidated summary and write `validation-report.json`:

```markdown
## 📋 PR Validation Summary

| PR | Artifact | Bump | mvn test | OWASP | Grype | JaCoCo | Verdict |
|----|----------|------|----------|-------|-------|--------|---------|
| #42 | struts2-core | MAJOR | ✅ | ✅ | ✅ | ✅ | ⚠️ Pending approval |
| #43 | jackson-databind | MINOR | ✅ | ✅ | ✅ | ✅ | ✅ Merged |
| #44 | log4j-core | MINOR | ❌ | ✅ | ✅ | ⚠️ 74% | ❌ Blocked |

### Next Steps
- PR #42: Awaiting your approval (major bump)
- PR #44: Fix 3 test failures + improve coverage to ≥ 80%, then re-run validation
```

Output `validation-report.json` for Stage 6 stress testing and Stage 7 audit trail.
See `references/pr-queue-schema.md` for the output schema.

---

## Output Files

| File | Format | Consumer |
|------|--------|----------|
| `validation-report.json` | JSON | Stage 6, Stage 7 |
| PR comments | GitHub API | Human reviewers |
| Merged PRs | GitHub | Main branch |

---

## Reference & Sub-Skill Files

- `references/pr-queue-schema.md` — PR queue + validation-report.json schemas
- `references/github-merge-api.md` — Merge, squash, branch deletion, conflict detection
- `skills/mvn-test.md` — Gate 1: run mvn test, parse failures
- `skills/owasp-scan.md` — Gate 2: run OWASP scan, compare against baseline
- `skills/grype-scan.md` — Gate 3: run Grype, parse Critical/High findings
- `skills/jacoco-coverage.md` — Gate 4: run JaCoCo, parse line coverage %