# Scenario: Zero-CVE (Clean Baseline) — Assertions & Expected Behaviour

## Profile
A well-maintained Java project with up-to-date dependencies and no known CVEs.
Validates that the pipeline completes cleanly without false alarms, produces a
green health report, and generates no unnecessary remediation PRs.

## Recommended Repos
See `references/reference-repos.md` → "Zero-CVE (Clean Baseline) Repos" section.
Primary: `https://github.com/spring-projects/spring-petclinic`

## Pre-run Check
```bash
# Confirm deps are up to date before using this repo
mvn versions:display-dependency-updates --batch-mode 2>/dev/null | grep -c "\->" || echo "0"
# Expected: 0 or very few updates available
```

---

## Assertions

| ID    | Stage | Assertion | Expected |
|-------|-------|-----------|----------|
| ZC-1  | Stage 1 | CVE count | 0 Critical CVEs found |
| ZC-2  | Stage 1 | Scan completes | Exit code 0 |
| ZC-3  | Stage 2 | All risk scores low | All composite scores < 40 |
| ZC-4  | Stage 2 | No CRITICAL tier deps | tier_counts["CRITICAL"] == 0 |
| ZC-5  | Stage 3 | Audit passes clean | audit_result == "PASS" |
| ZC-6  | Stage 3 | SBOM generated | sbom-cyclonedx.json exists with ≥ 1 component |
| ZC-7  | Stage 4 | No upgrades needed | remediation-manifest has 0 PRs OR all skipped |
| ZC-8  | Stage 5 | All gates pass or skip | No FAIL gates in validation-report.json |
| ZC-9  | Stage 7 | Health grade A or B | score ≥ 75 |

---

## Assertion Checks (Python)

```python
def assert_zero_cve(stage1_report, risk_scores, remediation_manifest,
                    validation_report, audit_report):
    results = []

    # ZC-1
    critical_cves = [v for dep in stage1_report["dependencies"]
                     for v in dep.get("vulnerabilities", [])
                     if v.get("severity") == "CRITICAL"]
    results.append(("ZC-1", len(critical_cves) == 0,
                    f"{len(critical_cves)} Critical CVEs (expected 0)"))

    # ZC-3
    high_scores = [d for d in risk_scores["dependencies"]
                   if d["composite_risk_score"] >= 40]
    results.append(("ZC-3", len(high_scores) == 0,
                    f"{len(high_scores)} deps with score ≥ 40 (expected 0)"))

    # ZC-4
    critical_tier = [d for d in risk_scores["dependencies"]
                     if d["risk_tier"] == "CRITICAL"]
    results.append(("ZC-4", len(critical_tier) == 0,
                    f"{len(critical_tier)} CRITICAL-tier deps (expected 0)"))

    # ZC-5
    results.append(("ZC-5", audit_report.get("result") == "PASS",
                    f"Audit result: {audit_report.get('result')}"))

    # ZC-7
    upgrades = remediation_manifest.get("pull_requests", [])
    results.append(("ZC-7", len(upgrades) == 0,
                    f"{len(upgrades)} upgrades planned (expected 0)"))

    # ZC-8
    all_gates = [g for pr in validation_report.get("pull_requests", [])
                 for g in pr.get("gates", [])]
    fail_gates = [g for g in all_gates if g["status"] == "FAIL"]
    results.append(("ZC-8", len(fail_gates) == 0,
                    f"{len(fail_gates)} FAIL gates (expected 0)"))

    return results
```

---

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| False-positive CVEs found | NVD data applied to wrong artifact version | Verify pom.xml version matches scanned version |
| Stage 2 shows HIGH-tier dep | Transitive dep has old CVE; direct dep is clean | Check if CVE is fixed in the current transitive version |
| Stage 4 produces upgrade PRs on clean repo | New CVE disclosed after project was last maintained | Expected — show the user and let them decide |
| Health score below 75 | Secret or policy violation despite no CVEs | Check secret-scan-report.json and policy-report.json |
