# PR Queue & Validation Report Schemas

## PR Queue (runtime, built from remediation-manifest.json)

```json
{
  "queue": [
    {
      "pr_number": 42,
      "pr_url": "https://github.com/<OWNER>/<REPO>/pull/42",
      "branch": "fix/cve-struts2-core-6.3.0.2",
      "artifact": "org.apache.struts:struts2-core",
      "old_version": "2.5.28",
      "new_version": "6.3.0.2",
      "bump_type": "MAJOR",
      "composite_risk_score": 91.4,
      "risk_tier": "CRITICAL"
    },
    {
      "pr_number": 43,
      "branch": "fix/cve-jackson-databind-2.15.4",
      "artifact": "com.fasterxml.jackson.core:jackson-databind",
      "old_version": "2.13.0",
      "new_version": "2.15.4",
      "bump_type": "MINOR",
      "composite_risk_score": 74.2,
      "risk_tier": "HIGH"
    }
  ]
}
```

---

## validation-report.json (output, consumed by Stage 6 + Stage 7)

```json
{
  "report_date": "<ISO-DATE>",
  "project": "<PROJECT_NAME>",
  "repo": "<OWNER>/<REPO>",
  "total_prs": 3,
  "summary": {
    "auto_merged": 1,
    "pending_approval": 1,
    "blocked": 1,
    "errors": 0
  },
  "pull_requests": [
    {
      "pr_number": 42,
      "artifact": "org.apache.struts:struts2-core",
      "old_version": "2.5.28",
      "new_version": "6.3.0.2",
      "bump_type": "MAJOR",
      "verdict": "HUMAN_APPROVAL_REQUIRED",
      "merged": false,
      "gates": [
        {
          "gate": "mvn-test",
          "status": "PASS",
          "tests_run": 142,
          "failures": 0,
          "errors": 0,
          "detail": "142 tests passed"
        },
        {
          "gate": "owasp-scan",
          "status": "PASS",
          "new_critical": 0,
          "new_high": 0,
          "resolved_cves": ["CVE-2023-50164"],
          "detail": "0 new CVEs. 1 resolved."
        },
        {
          "gate": "grype-scan",
          "status": "PASS",
          "new_critical": 0,
          "new_high": 0,
          "detail": "0 new Critical/High findings."
        },
        {
          "gate": "jacoco-coverage",
          "status": "PASS",
          "line_coverage_pct": 84.3,
          "threshold": 80.0,
          "detail": "84.3% line coverage ✅"
        }
      ],
      "pr_comment_url": "https://github.com/<OWNER>/<REPO>/issues/42/comments/999"
    },
    {
      "pr_number": 43,
      "artifact": "com.fasterxml.jackson.core:jackson-databind",
      "old_version": "2.13.0",
      "new_version": "2.15.4",
      "bump_type": "MINOR",
      "verdict": "AUTO_MERGE",
      "merged": true,
      "merge_sha": "abc123def456",
      "gates": [ ... ]
    },
    {
      "pr_number": 44,
      "artifact": "ch.qos.logback:logback-classic",
      "old_version": "1.2.9",
      "new_version": "1.4.14",
      "bump_type": "MINOR",
      "verdict": "BLOCKED",
      "merged": false,
      "blocked_by": ["mvn-test", "jacoco-coverage"],
      "gates": [ ... ]
    }
  ]
}
```