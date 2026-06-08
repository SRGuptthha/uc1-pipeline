# Audit Trail Schema — audit-trail.json

The permanent machine-readable record of the full pipeline run. Suitable for compliance
archiving, future pipeline comparisons, and audit queries.

```json
{
  "audit_id": "audit-<PROJECT>-<ISO-DATE>",
  "generated_date": "<ISO-DATE>",
  "pipeline_version": "1.0",
  "project": "<PROJECT_NAME>",
  "repo": "<OWNER>/<REPO>",
  "demo_mode": "replay | live",

  "pipeline_health": {
    "score": 78,
    "grade": "B",
    "label": "Good",
    "score_before_remediation": 32,
    "score_after_remediation": 78,
    "improvement": 46
  },

  "day1_owasp": {
    "scan_date": "<ISO-DATE>",
    "total_deps_scanned": 142,
    "cve_summary": {
      "total": 23,
      "critical": 3,
      "high": 8,
      "medium": 9,
      "low": 3
    },
    "top_cves": [
      { "id": "CVE-2023-50164", "cvss": 9.8, "severity": "CRITICAL", "artifact": "struts2-core:2.5.28" }
    ],
    "artifact": "dependency-check-report/dependency-check-report.json"
  },

  "day2_risk_scoring": {
    "total_scored": 142,
    "tier_breakdown": {
      "CRITICAL": 3, "HIGH": 8, "MEDIUM": 21, "LOW": 110
    },
    "avg_composite_score": 28.4,
    "top5_risky": [
      { "artifact": "org.apache.struts:struts2-core:2.5.28", "score": 91.4, "tier": "CRITICAL" }
    ],
    "artifact": "risk-scores.json"
  },

  "day3_audit": {
    "result": "BLOCKED | PASSED",
    "total_components": 142,
    "violations": {
      "typosquatting": 0,
      "untrusted_source": 1,
      "license_violation": 2
    },
    "warnings": 3,
    "artifact": "audit-report.json"
  },

  "day4_remediation": {
    "dry_run": false,
    "total_upgrades": 11,
    "bump_breakdown": { "PATCH": 6, "MINOR": 4, "MAJOR": 1 },
    "cves_fixed": 18,
    "skipped": 2,
    "prs_created": 11,
    "artifact": "remediation-manifest.json"
  },

  "day5_validation": {
    "total_prs": 11,
    "auto_merged": 9,
    "pending_human_approval": 1,
    "blocked": 1,
    "gate_summary": {
      "mvn_test":       { "pass": 10, "fail": 1 },
      "owasp_scan":     { "pass": 11, "fail": 0 },
      "grype_scan":     { "pass": 11, "fail": 0 },
      "jacoco_coverage":{ "pass": 9,  "fail": 2 }
    },
    "avg_coverage_pct": 83.2,
    "artifact": "validation-report.json"
  },

  "day6_e2e": {
    "available": true,
    "repos_tested": 5,
    "repos_fully_passed": 3,
    "scenarios_covered": ["cve-heavy", "zero-cve", "complex-tree", "malformed-pom", "mixed"],
    "total_duration_seconds": 1872,
    "artifact": "e2e-report.json"
  },

  "report_outputs": {
    "html": "dependency-health-report.html",
    "pdf":  "dependency-health-report.pdf"
  },

  "key_findings": [
    "3 critical vulnerabilities found across 142 scanned dependencies.",
    "18 CVEs remediated through 11 dependency upgrades.",
    "9 pull requests automatically validated and merged.",
    "2 license violations flagged for legal review.",
    "Average test coverage across validated PRs: 83.2%."
  ],

  "compliance_notes": {
    "nvd_database_date": "<ISO-DATE>",
    "owasp_version": "8.x",
    "syft_version": "0.98.x",
    "grype_version": "0.74.x",
    "scan_scope": "direct + transitive dependencies",
    "remediation_strategy": "upgrade to latest stable; human approval required for major bumps"
  }
}
```