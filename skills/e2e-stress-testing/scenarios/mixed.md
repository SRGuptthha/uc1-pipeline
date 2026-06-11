# Scenario: Mixed — Assertions & Expected Behaviour

## Profile
A Java project with a mix of clean and vulnerable dependencies — some up-to-date,
some outdated with CVEs, some on non-standard sources. Validates that the pipeline
correctly identifies the vulnerable subset without flagging clean deps as risky,
generates a partial (not all-or-nothing) remediation plan, and handles partial gate
results gracefully.

## Recommended Repos
See `references/reference-repos.md` → "Mixed Scenario Repos" section.
Primary: `https://github.com/broadinstitute/gatk`

---

## Assertions

| ID    | Stage | Assertion | Expected |
|-------|-------|-----------|----------|
| MX-1  | Stage 1 | At least one CVE found | ≥ 1 CVE in dependency-check-report.json |
| MX-2  | Stage 1 | At least one clean dep | ≥ 1 dependency with 0 vulnerabilities |
| MX-3  | Stage 2 | Mixed risk tiers | risk-scores.json contains both HIGH/CRITICAL and LOW/MEDIUM deps |
| MX-4  | Stage 3 | Partial audit result | May be PASS or WARNING (not all FAIL) |
| MX-5  | Stage 4 | Partial remediation | 1 ≤ upgrades ≤ total_deps (not all or none) |
| MX-6  | Stage 5 | Mixed gate verdicts | Validation report has a mix of AUTO_MERGE and PENDING_HUMAN (or BLOCKED) |
| MX-7  | Stage 7 | Score reflects partial state | Health score between 40 and 90 (neither perfect nor catastrophic) |
| MX-8  | Stage 4 | Skipped list populated | remediation-manifest.json has ≥ 1 skipped entry (clean dep not upgraded) |

---

## Assertion Checks (Python)

```python
def assert_mixed(stage1_report, risk_scores, remediation_manifest,
                 validation_report, health_score):
    results = []

    # MX-1
    all_vulns = [v for dep in stage1_report["dependencies"]
                 for v in dep.get("vulnerabilities", [])]
    results.append(("MX-1", len(all_vulns) >= 1,
                    f"{len(all_vulns)} total CVEs found"))

    # MX-2
    clean_deps = [dep for dep in stage1_report["dependencies"]
                  if len(dep.get("vulnerabilities", [])) == 0]
    results.append(("MX-2", len(clean_deps) >= 1,
                    f"{len(clean_deps)} clean deps (expected ≥ 1)"))

    # MX-3
    tiers = {d["risk_tier"] for d in risk_scores.get("dependencies", [])}
    has_high    = bool(tiers & {"HIGH", "CRITICAL"})
    has_low     = bool(tiers & {"LOW", "MEDIUM"})
    results.append(("MX-3", has_high and has_low,
                    f"Tiers present: {tiers}"))

    # MX-5
    total_deps    = len(stage1_report.get("dependencies", []))
    upgrade_count = len(remediation_manifest.get("pull_requests", []))
    results.append(("MX-5", 1 <= upgrade_count < total_deps,
                    f"{upgrade_count} upgrades out of {total_deps} deps"))

    # MX-7
    results.append(("MX-7", 40 <= health_score <= 90,
                    f"Health score: {health_score} (expected 40–90)"))

    return results
```

---

## Partial Remediation Validation

The key distinction for the mixed scenario is that Stage 4 should upgrade **only the
vulnerable deps** and leave clean deps untouched. Verify this explicitly:

```python
upgraded_artifacts = {pr["artifact"] for pr in remediation_manifest["pull_requests"]}
clean_artifacts    = {dep["groupId"] + ":" + dep["artifactId"]
                      for dep in stage1_report["dependencies"]
                      if len(dep.get("vulnerabilities", [])) == 0}

overlap = upgraded_artifacts & clean_artifacts
assert len(overlap) == 0, f"Clean deps incorrectly included in upgrade plan: {overlap}"
```

---

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| All deps flagged as CRITICAL | NVD score inflation on transitive deps | Check if direct deps are actually vulnerable; adjust business criticality tags |
| 0 upgrades in remediation | All vulnerable versions are the latest available | Known limitation — flag to user with "no patched version" note |
| Stage 5 all AUTO_MERGE | No MAJOR bumps in mixed repo | Acceptable — find a repo with at least one major bump to stress the PENDING_HUMAN path |
| Health score > 90 on mixed repo | CVEs are Low/Medium only | Select a repo with at least one Critical CVE for better coverage |
