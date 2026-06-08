# Stage Runner — E2E Stress Testing

How to invoke each Day skill during stress testing. All stages run from the repo's
working directory. Stage 4 always runs in dry-run mode; Stage 5 runs gate checks only.

---

## Stage: Stage 1 — OWASP Dependency-Check

```bash
cd <REPO_DIR>

dependency-check \
  --project "<REPO_ID>" \
  --scan . \
  --format JSON \
  --out "./<REPO_ID>-day1-output" \
  --nvdApiKey "$NVD_API_KEY" \
  --failOnCVSS 7 \
  2>&1 | tee <REPO_ID>-day1.log
```

Expected output: `./<REPO_ID>-day1-output/dependency-check-report.json`
Pass condition: command completes (exit 0 or 1 — both are valid; exit 2+ = tool error)

---

## Stage: Stage 2 — Risk Scoring

```bash
cd <REPO_DIR>

python3 /path/to/risk_scorer.py \
  --owasp ./<REPO_ID>-day1-output/dependency-check-report.json \
  --tags <REPO_ID>-tags.json \
  --output ./<REPO_ID>-risk-scores.json \
  2>&1 | tee <REPO_ID>-day2.log
```

If no tags file exists, scorer defaults all business criticality to 0.5 (neutral).
Expected output: `./<REPO_ID>-risk-scores.json`

---

## Stage: Stage 3 — Supply-Chain Audit

```bash
cd <REPO_DIR>

# Generate SBOM
syft dir:. --output cyclonedx-json=./<REPO_ID>-sbom.cdx.json -q

# Run audit
python3 /path/to/audit.py \
  --sbom ./<REPO_ID>-sbom.cdx.json \
  --policy /path/to/license-policy.md \
  --source-allowlist /path/to/source-allowlist.txt \
  --output ./<REPO_ID>-audit-report.json \
  2>&1 | tee <REPO_ID>-day3.log

# Capture exit code separately (1 = violations found, not an error)
AUDIT_EXIT=$?
```

Pass condition for stress test: tool completes without crash (exit 0 or 1 both valid).

---

## Stage: Stage 4 — Remediation Dry-Run

⚠️ DRY-RUN MODE: resolve upgrade versions and generate the manifest, but do NOT:
- Patch pom.xml
- Create git branches
- Open GitHub PRs

```bash
python3 /path/to/remediation.py \
  --owasp ./<REPO_ID>-day1-output/dependency-check-report.json \
  --risk-scores ./<REPO_ID>-risk-scores.json \
  --dry-run \
  --output ./<REPO_ID>-remediation-manifest.json \
  2>&1 | tee <REPO_ID>-day4.log
```

Expected output: `./<REPO_ID>-remediation-manifest.json` with `"dry_run": true`

---

## Stage: Stage 5 — Validation Gates Only

Run all 4 gates against the current branch state (no merge):

```bash
# Gate 1: mvn test
cd <REPO_DIR>
mvn test --batch-mode --no-transfer-progress 2>&1 | tee <REPO_ID>-mvn-test.log

# Gate 2: OWASP re-scan (compare against day1 baseline)
dependency-check --project "<REPO_ID>-recheck" --scan . \
  --format JSON --out ./<REPO_ID>-day5-owasp \
  --nvdApiKey "$NVD_API_KEY" 2>&1 | tee <REPO_ID>-day5-owasp.log

# Gate 3: Grype
grype sbom:./<REPO_ID>-sbom.cdx.json --output json \
  --file ./<REPO_ID>-grype.json 2>&1 | tee <REPO_ID>-day5-grype.log

# Gate 4: JaCoCo
mvn test jacoco:report --batch-mode --no-transfer-progress 2>&1 | tee <REPO_ID>-jacoco.log
```

Collect gate results into `./<REPO_ID>-validation-result.json` — no merge attempted.

---

## Artifact Inventory Per Repo

After all stages complete, the following files should exist under `<REPO_DIR>`:

```
<REPO_ID>-day1-output/dependency-check-report.json
<REPO_ID>-risk-scores.json
<REPO_ID>-sbom.cdx.json
<REPO_ID>-audit-report.json
<REPO_ID>-remediation-manifest.json
<REPO_ID>-grype.json
<REPO_ID>-validation-result.json
*.log  (one per stage)
```

Missing files → mark that stage as `ERROR` in the e2e report.