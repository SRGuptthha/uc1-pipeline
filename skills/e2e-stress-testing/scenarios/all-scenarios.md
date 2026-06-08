# Scenario: Zero-CVE — Assertions

## Profile
A well-maintained Java project with up-to-date dependencies. Validates that the pipeline
completes cleanly with no false positives, no spurious blocks, and green gates throughout.

## Assertions

| ID | Stage | Assertion | Expected |
|----|-------|-----------|----------|
| ZC-1 | Stage 1 | CVE count | 0 Critical or High CVEs |
| ZC-2 | Stage 2 | Risk tiers | All deps score < 40 (LOW tier) |
| ZC-3 | Stage 3 | Audit result | `audit-report.json` result = "PASSED", exit code 0 |
| ZC-4 | Stage 4 | Upgrade plan | 0 upgrades needed — manifest is empty or not generated |
| ZC-5 | Stage 5 | All gates | mvn test ✅ OWASP ✅ Grype ✅ JaCoCo ≥ 80% ✅ |

```python
def assert_zero_cve(day1_report, risk_scores, audit_report):
    cves = [v for dep in day1_report["dependencies"]
              for v in dep.get("vulnerabilities", [])
              if v.get("severity") in ("CRITICAL", "HIGH")]
    assert_zc1 = ("ZC-1", len(cves) == 0, f"{len(cves)} Critical/High CVEs (expected 0)")

    max_score = max((d["composite_risk_score"] for d in risk_scores["dependencies"]), default=0)
    assert_zc2 = ("ZC-2", max_score < 40, f"Max score: {max_score} (expected < 40)")

    assert_zc3 = ("ZC-3", audit_report["result"] == "PASSED", audit_report["result"])

    return [assert_zc1, assert_zc2, assert_zc3]
```

---

---

# Scenario: Complex Dependency Tree — Assertions

## Profile
A large multi-module Maven project with deep transitive dependency chains (depth 3+).
Validates SBOM completeness, transitive scoring accuracy, and scan performance under load.

## Assertions

| ID | Stage | Assertion | Expected |
|----|-------|-----------|----------|
| CT-1 | Stage 1 | Dep count | ≥ 50 dependencies scanned |
| CT-2 | Stage 2 | Transitive scoring | ≥ 1 dep with `exposure = "transitive"` and `exposure_factor < 1.0` |
| CT-3 | Stage 3 | SBOM completeness | `sbom.cdx.json` contains ≥ 50 components |
| CT-4 | Stage 3 | No Syft crash | Syft exits 0 even on deep tree |
| CT-5 | Stage 5 | OWASP scan time | Completes within WARNING threshold (6 min) |

```python
def assert_complex_tree(day1_report, risk_scores, sbom):
    dep_count = len(day1_report["dependencies"])
    assert_ct1 = ("CT-1", dep_count >= 50, f"{dep_count} deps scanned")

    transitive = [d for d in risk_scores["dependencies"]
                  if d["factors"]["exposure"] == "transitive"]
    assert_ct2 = ("CT-2", len(transitive) >= 1,
                  f"{len(transitive)} transitive deps scored")

    component_count = len(sbom.get("components", []))
    assert_ct3 = ("CT-3", component_count >= 50,
                  f"{component_count} components in SBOM")

    return [assert_ct1, assert_ct2, assert_ct3]
```

---

---

# Scenario: Malformed pom.xml — Edge Cases & Expected Behaviour

## Profile
Synthetic fixtures with intentionally broken POMs. Validates that every pipeline stage
surfaces errors gracefully — no unhandled crashes, no silent failures, clear error messages.

## Fixture Definitions

Create these under `/tmp/e2e/malformed-pom-project/`:

### Fixture 1: Missing version tag
```xml
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.test</groupId>
  <artifactId>missing-version</artifactId>
  <!-- <version> intentionally missing -->
  <dependencies>
    <dependency>
      <groupId>org.apache.struts</groupId>
      <artifactId>struts2-core</artifactId>
      <!-- no <version> and no BOM — invalid -->
    </dependency>
  </dependencies>
</project>
```

### Fixture 2: Broken XML (unclosed tag)
```xml
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.test</groupId>
  <artifactId>broken-xml</artifactId>
  <version>1.0.0</version>
  <dependencies>
    <dependency>
      <groupId>log4j</groupId>
      <!-- unclosed tag below -->
      <artifactId>log4j
    </dependency>
  </dependencies>
</project>
```

### Fixture 3: Circular property reference
```xml
<properties>
  <app.version>${app.version}</app.version>  <!-- references itself -->
</properties>
```

### Fixture 4: Snapshot in production
```xml
<dependency>
  <groupId>com.example</groupId>
  <artifactId>core-lib</artifactId>
  <version>1.0.0-SNAPSHOT</version>
</dependency>
```

## Assertions

| ID | Fixture | Stage | Expected Behaviour |
|----|---------|-------|--------------------|
| MP-1 | missing-version | Stage 1 | OWASP reports partial scan; JSON output still generated |
| MP-2 | broken-xml | Stage 1 | OWASP exits with error; error captured in log; stage = ERROR |
| MP-3 | broken-xml | Pipeline | Pipeline halts this repo gracefully; continues to next repo |
| MP-4 | circular-property | Stage 4 | Remediation detects circular ref; flags as manual-review; no crash |
| MP-5 | snapshot-version | Stage 4 | Flagged as warning: "SNAPSHOT in production dep" |
| MP-6 | Any | All | No unhandled Python/bash exceptions; all errors caught and logged |

The key success criterion for malformed-pom is **graceful failure** — the pipeline must
never crash silently. Every error must appear in the stage log and e2e-report.json.

---

---

# Scenario: Mixed — Assertions

## Profile
A Java project with a blend of clean deps and a handful of CVEs. Validates partial
remediation paths — only some deps get upgrades, others are already safe.

## Assertions

| ID | Stage | Assertion | Expected |
|----|-------|-----------|----------|
| MX-1 | Stage 1 | CVE mix | 1–10 CVEs found (not zero, not overwhelming) |
| MX-2 | Stage 2 | Score spread | At least one dep in HIGH tier AND one in LOW tier |
| MX-3 | Stage 4 | Partial plan | ≥ 1 but not all deps have upgrades planned |
| MX-4 | Stage 5 | Gate results | At least 3 of 4 gates pass |

```python
def assert_mixed(day1_report, risk_scores, remediation_manifest, validation_result):
    cve_count = len([v for dep in day1_report["dependencies"]
                       for v in dep.get("vulnerabilities", [])])
    assert_mx1 = ("MX-1", 1 <= cve_count <= 10, f"{cve_count} CVEs found")

    tiers = {d["risk_tier"] for d in risk_scores["dependencies"]}
    assert_mx2 = ("MX-2", "HIGH" in tiers and "LOW" in tiers,
                  f"Tiers present: {tiers}")

    upgrades = len(remediation_manifest.get("pull_requests", []))
    total_deps = len(risk_scores["dependencies"])
    assert_mx3 = ("MX-3", 0 < upgrades < total_deps,
                  f"{upgrades} of {total_deps} deps have upgrades")

    gates_passed = sum(1 for g in validation_result["gates"] if g["status"] == "PASS")
    assert_mx4 = ("MX-4", gates_passed >= 3, f"{gates_passed}/4 gates passed")

    return [assert_mx1, assert_mx2, assert_mx3, assert_mx4]
```