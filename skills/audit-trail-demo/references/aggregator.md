# Aggregator — Extraction Functions

All functions return dicts safe to pass directly into the report template.

---

## Stage 1 — OWASP CVE Summary

```python
import json
from collections import Counter

def extract_cve_summary(owasp_path):
    with open(owasp_path) as f:
        report = json.load(f)

    all_cves = []
    for dep in report["dependencies"]:
        for vuln in dep.get("vulnerabilities", []):
            all_cves.append({
                "id":       vuln["name"],
                "artifact": dep.get("fileName", "unknown"),
                "cvss":     vuln.get("cvssv3", {}).get("baseScore")
                            or vuln.get("cvssv2", {}).get("score", 0),
                "severity": vuln.get("severity", "UNKNOWN"),
                "description": vuln.get("description", "")[:200],
            })

    severity_counts = Counter(c["severity"] for c in all_cves)
    return {
        "total_cves":      len(all_cves),
        "critical_count":  severity_counts.get("CRITICAL", 0),
        "high_count":      severity_counts.get("HIGH", 0),
        "medium_count":    severity_counts.get("MEDIUM", 0),
        "low_count":       severity_counts.get("LOW", 0),
        "top_cves":        sorted(all_cves, key=lambda x: x["cvss"], reverse=True)[:10],
        "total_deps_scanned": len(report["dependencies"]),
        "project":         report.get("projectInfo", {}).get("name", "unknown"),
        "scan_date":       report.get("projectInfo", {}).get("reportDate", "unknown"),
    }
```

---

## Stage 2 — Risk Score Summary

```python
def extract_risk_summary(risk_path):
    with open(risk_path) as f:
        data = json.load(f)

    deps = data["dependencies"]
    tier_counts = Counter(d["risk_tier"] for d in deps)
    top5 = sorted(deps, key=lambda d: d["composite_risk_score"], reverse=True)[:5]

    return {
        "total_scored":    len(deps),
        "critical_count":  tier_counts.get("CRITICAL", 0),
        "high_count":      tier_counts.get("HIGH", 0),
        "medium_count":    tier_counts.get("MEDIUM", 0),
        "low_count":       tier_counts.get("LOW", 0),
        "avg_score":       round(sum(d["composite_risk_score"] for d in deps) / len(deps), 1) if deps else 0,
        "top5_risky_deps": [
            {
                "artifact": d["artifact"],
                "score":    d["composite_risk_score"],
                "tier":     d["risk_tier"],
                "top_cve":  d["cves"][0]["id"] if d.get("cves") else "—",
            }
            for d in top5
        ],
    }
```

---

## Stage 3 — Audit Summary

```python
def extract_audit_summary(audit_path):
    with open(audit_path) as f:
        data = json.load(f)

    violations = data.get("violations", [])
    by_check = Counter(v["check"] for v in violations)
    return {
        "result":                  data.get("result", "UNKNOWN"),
        "total_components":        data.get("total_components", 0),
        "typosquat_count":         by_check.get("typosquatting", 0),
        "untrusted_source_count":  by_check.get("untrusted_source", 0),
        "license_violation_count": by_check.get("license_violation", 0),
        "total_violations":        len(violations),
        "warning_count":           len(data.get("warnings", [])),
        "violations":              violations[:10],  # top 10 for appendix
    }
```

---

## Stage 4 — Remediation Summary

```python
def extract_remediation_summary(manifest_path):
    if not manifest_path or not os.path.exists(manifest_path):
        return {"available": False}

    with open(manifest_path) as f:
        data = json.load(f)

    prs = data.get("pull_requests", [])
    bump_counts = Counter(pr["bump_type"] for pr in prs)
    cves_fixed = [cve for pr in prs for cve in pr.get("cves_fixed", [])]

    return {
        "available":       True,
        "total_upgrades":  len(prs),
        "patch_count":     bump_counts.get("PATCH", 0),
        "minor_count":     bump_counts.get("MINOR", 0),
        "major_count":     bump_counts.get("MAJOR", 0),
        "cves_fixed_count": len(set(cves_fixed)),
        "skipped_count":   len(data.get("skipped", [])),
        "upgrades":        prs,   # full list for technical appendix
    }
```

---

## Stage 5 — Validation Summary

```python
def extract_validation_summary(validation_path):
    if not validation_path or not os.path.exists(validation_path):
        return {"available": False}

    with open(validation_path) as f:
        data = json.load(f)

    prs = data.get("pull_requests", [])
    coverages = [
        g["line_coverage_pct"]
        for pr in prs
        for g in pr.get("gates", [])
        if g["gate"] == "jacoco-coverage" and g["status"] == "PASS"
    ]

    return {
        "available":       True,
        "total_prs":       data["total_prs"],
        "auto_merged":     data["summary"]["auto_merged"],
        "pending_approval":data["summary"]["pending_approval"],
        "blocked":         data["summary"]["blocked"],
        "prs_merged":      data["summary"]["auto_merged"],
        "avg_jacoco_coverage": round(sum(coverages) / len(coverages), 1) if coverages else 0,
        "pull_requests":   prs,
    }
```

---

## Stage 6 — E2E Summary (optional)

```python
def extract_e2e_summary(e2e_path):
    if not e2e_path or not os.path.exists(e2e_path):
        return {"available": False}

    with open(e2e_path) as f:
        data = json.load(f)

    return {
        "available":           True,
        "repos_tested":        data["total_repos"],
        "repos_fully_passed":  data["summary"]["repos_fully_passed"],
        "repos_errored":       data["summary"]["repos_errored"],
        "scenarios_covered":   data["summary"]["scenarios_covered"],
        "total_duration_seconds": data["summary"]["total_duration_seconds"],
    }
```

---

## Plain-English Key Findings Generator

Called for the Executive Summary "Key Findings" section:

```python
def generate_key_findings(agg):
    findings = []
    c = agg["cve_summary"]
    r = agg["remediation_summary"]
    v = agg["validation_summary"]

    if c["critical_count"] > 0:
        findings.append(
            f"🔴 {c['critical_count']} critical vulnerabilities were found across "
            f"{c['total_deps_scanned']} scanned dependencies."
        )
    if r.get("cves_fixed_count", 0) > 0:
        findings.append(
            f"✅ {r['cves_fixed_count']} CVEs were remediated through "
            f"{r['total_upgrades']} dependency upgrades."
        )
    if v.get("prs_merged", 0) > 0:
        findings.append(
            f"🔀 {v['prs_merged']} pull requests were automatically validated "
            f"and merged after passing all security and test gates."
        )
    if agg["audit_summary"]["license_violation_count"] > 0:
        findings.append(
            f"⚖️ {agg['audit_summary']['license_violation_count']} license violations "
            f"were detected and flagged for legal review."
        )
    coverage = v.get("avg_jacoco_coverage", 0)
    if coverage > 0:
        findings.append(
            f"🧪 Average test coverage across validated PRs: {coverage}% "
            f"({'above' if coverage >= 80 else 'below'} the 80% threshold)."
        )
    return findings
```