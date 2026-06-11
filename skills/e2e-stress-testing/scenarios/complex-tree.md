# Scenario: Complex Dependency Tree — Assertions & Expected Behaviour

## Profile
A large Java project with deep transitive dependencies (50+ compile deps) and
multi-module Maven structure. Validates that SBOM generation handles depth correctly,
risk scoring weights transitive vs direct deps, and scan performance stays within
acceptable bounds on large repos.

## Recommended Repos
See `references/reference-repos.md` → "Complex Dependency Tree Repos" section.
Primary: `https://github.com/apache/flink`

> Note: First-run OWASP scans on repos this size can take 10–20 min (DB download).
> Warn the user before starting. Subsequent runs use the cached NVD DB (2–4 min).

## Pre-run Check
```bash
# Count compile-scope dependencies
mvn dependency:list -DincludeScope=compile --batch-mode 2>/dev/null \
  | grep -c "compile$" || echo "0"
# Expected: ≥ 50
```

---

## Assertions

| ID    | Stage | Assertion | Expected |
|-------|-------|-----------|----------|
| CT-1  | Stage 1 | Deps scanned | ≥ 50 compile-scope dependencies scanned |
| CT-2  | Stage 1 | Scan completes without crash | Exit code 0 or 1 (not 2+) |
| CT-3  | Stage 2 | Transitive deps scored | risk-scores.json has ≥ 50 entries |
| CT-4  | Stage 2 | Score ordering | Deps sorted by composite_risk_score descending |
| CT-5  | Stage 3 | SBOM component count | sbom-cyclonedx.json has ≥ 50 components |
| CT-6  | Stage 3 | No crash on large SBOM | audit-report.json exists and is valid JSON |
| CT-7  | Stage 4 | Version resolution handles bulk | ≥ 5 version lookups attempted |
| CT-8  | Stage 1 | Timing acceptable | Scan completes within timing threshold (see timing-thresholds.md) |

---

## Assertion Checks (Python)

```python
import json, time

def assert_complex_tree(stage1_report, risk_scores, sbom, audit_report,
                        remediation_manifest, stage_timings):
    results = []

    # CT-1
    total_deps = len(stage1_report.get("dependencies", []))
    results.append(("CT-1", total_deps >= 50,
                    f"{total_deps} deps scanned (expected ≥ 50)"))

    # CT-3
    scored_deps = len(risk_scores.get("dependencies", []))
    results.append(("CT-3", scored_deps >= 50,
                    f"{scored_deps} deps scored (expected ≥ 50)"))

    # CT-4
    scores = [d["composite_risk_score"] for d in risk_scores.get("dependencies", [])]
    sorted_ok = scores == sorted(scores, reverse=True)
    results.append(("CT-4", sorted_ok, "Deps sorted by score desc" if sorted_ok
                    else "Deps NOT sorted correctly"))

    # CT-5
    components = len(sbom.get("components", []))
    results.append(("CT-5", components >= 50,
                    f"{components} SBOM components (expected ≥ 50)"))

    # CT-6
    audit_valid = isinstance(audit_report, dict) and "result" in audit_report
    results.append(("CT-6", audit_valid,
                    "audit-report.json is valid" if audit_valid else "Invalid audit JSON"))

    # CT-7
    upgrades_attempted = len(remediation_manifest.get("pull_requests", [])) + \
                         len(remediation_manifest.get("skipped", []))
    results.append(("CT-7", upgrades_attempted >= 5,
                    f"{upgrades_attempted} version lookups attempted"))

    # CT-8 — timing check
    stage1_duration = stage_timings.get("stage1", 0)
    # 25 min = 1500s WARNING threshold from timing-thresholds.md
    results.append(("CT-8", stage1_duration <= 1500,
                    f"Stage 1 took {stage1_duration}s ({'OK' if stage1_duration <= 1500 else 'WARNING: exceeded 25min'})"))

    return results
```

---

## Multi-Module Project Handling

If the repo has child `pom.xml` files, the pipeline fetches the **root** `pom.xml`.
Deps declared only in child modules may not appear in the root scan. This is expected
behaviour for the current pipeline version; flag if root pom has 0 dependencies.

```python
# Detect likely multi-module projects
root_deps = [d for d in all_deps if d["version"] != "UNKNOWN"]
if len(root_deps) < 5:
    print("WARNING: Root pom.xml has <5 resolved deps — likely multi-module project")
    print("         Pipeline scans root pom only; child module deps not included")
```

---

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| SBOM has < 50 components but repo has 100+ deps | Root pom scanned only; children ignored | Flag to user; multi-module support is a known limitation |
| Stage 1 times out | Very large NVD DB download on first run | Restart with `--nvdApiKey` to speed up DB sync |
| Stage 4 version resolution takes > 5 min | Too many sequential Maven Central calls | Normal for 50+ deps; pipeline batches 15 at a time |
| OOM during OWASP scan | Default Java heap too small | Set `JAVA_OPTS=-Xmx2g` before running |
