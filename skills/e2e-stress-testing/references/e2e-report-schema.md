# E2E Report Schema — e2e-report.json

Consumed by Stage 7 Audit Trail skill.

```json
{
  "batch_label": "day6-stress-run-2024-01-15",
  "run_date": "<ISO-DATE>",
  "total_repos": 5,
  "pipeline_stages": ["day1", "day2", "day3", "day4", "day5"],
  "summary": {
    "repos_fully_passed": 2,
    "repos_partially_passed": 2,
    "repos_failed": 0,
    "repos_errored": 1,
    "total_duration_seconds": 1872,
    "scenarios_covered": ["cve-heavy", "zero-cve", "complex-tree", "malformed-pom", "mixed"]
  },
  "repos": [
    {
      "id": "repo-1",
      "source": "https://github.com/WebGoat/WebGoat",
      "scenario": "cve-heavy",
      "overall_status": "PASS",
      "total_duration_seconds": 494,
      "stages": [
        {
          "stage": "day1",
          "status": "PASS",
          "duration_seconds": 187,
          "timing_flag": null,
          "detail": "23 CVEs found (8 Critical, 11 High, 4 Medium)",
          "artifacts": ["repo-1-day1-output/dependency-check-report.json"]
        },
        {
          "stage": "day2",
          "status": "PASS",
          "duration_seconds": 12,
          "timing_flag": null,
          "detail": "31 deps scored. 3 CRITICAL (score ≥ 80), 8 HIGH.",
          "artifacts": ["repo-1-risk-scores.json"]
        },
        {
          "stage": "day3",
          "status": "PASS",
          "duration_seconds": 38,
          "timing_flag": null,
          "detail": "2 license violations, 0 typosquats, 1 untrusted source. PR blocked.",
          "artifacts": ["repo-1-sbom.cdx.json", "repo-1-audit-report.json"]
        },
        {
          "stage": "day4",
          "status": "PASS",
          "duration_seconds": 43,
          "timing_flag": null,
          "detail": "Dry-run: 8 upgrade plans generated. No PRs created.",
          "artifacts": ["repo-1-remediation-manifest.json"]
        },
        {
          "stage": "day5",
          "status": "PASS",
          "duration_seconds": 214,
          "timing_flag": null,
          "detail": "mvn test ✅ OWASP ✅ Grype ✅ JaCoCo 82.1% ✅",
          "artifacts": ["repo-1-validation-result.json"]
        }
      ],
      "scenario_assertions": [
        {
          "assertion": "day1_finds_critical_cves",
          "expected": "≥ 5 Critical/High CVEs",
          "actual": "19 Critical/High CVEs",
          "passed": true
        },
        {
          "assertion": "day2_scores_critical_deps",
          "expected": "≥ 1 dep with score ≥ 80",
          "actual": "3 deps with score ≥ 80",
          "passed": true
        },
        {
          "assertion": "day4_produces_upgrade_plan",
          "expected": "≥ 1 upgrade in remediation manifest",
          "actual": "8 upgrades planned",
          "passed": true
        }
      ]
    }
  ],
  "timing_summary": {
    "by_stage": {
      "day1": { "min_seconds": 47, "max_seconds": 252, "avg_seconds": 138 },
      "day2": { "min_seconds": 8,  "max_seconds": 34,  "avg_seconds": 19  },
      "day3": { "min_seconds": 12, "max_seconds": 63,  "avg_seconds": 38  },
      "day4": { "min_seconds": 5,  "max_seconds": 48,  "avg_seconds": 24  },
      "day5": { "min_seconds": 72, "max_seconds": 295, "avg_seconds": 161 }
    },
    "timing_flags": [
      {
        "repo_id": "repo-3",
        "stage": "day1",
        "flag": "WARNING",
        "duration_seconds": 412,
        "note": "First run with DB download on large repo (100+ deps)"
      }
    ]
  },
  "failures": [
    {
      "repo_id": "repo-4",
      "stage": "day2",
      "type": "ERROR",
      "message": "JSON parse failure on OWASP output — partial scan due to malformed pom.xml",
      "graceful": true,
      "note": "Pipeline correctly surfaced error and halted this repo's pipeline"
    }
  ]
}
```