# policy.json Schema Reference

## Full Schema

```json
{
  "$schema": "https://uc1-pipeline/schemas/policy-v1.json",
  "policy_version": "1.0",
  "project": "<string — project name>",
  "rules": [
    {
      "id":          "<string — unique rule ID, e.g. P001>",
      "name":        "<string — human-readable rule name>",
      "rule":        "<enum — see Rule Types below>",
      "threshold":   "<number — numeric threshold for comparison rules>",
      "blocklist":   "<string[] — for license_blocklist rule>",
      "min_severity":"<enum: CRITICAL | HIGH | MEDIUM | LOW — for secret_count_max>",
      "action":      "<enum: FAIL | WARN>",
      "enabled":     "<boolean — default true>",
      "description": "<string — optional human note>"
    }
  ]
}
```

## Rule Types

| value | Description | Required fields |
|-------|-------------|-----------------|
| `cvss_max` | Fail if max CVE CVSS score ≥ threshold | `threshold` |
| `high_count_max` | Fail if count of CVSS ≥ 7.0 CVEs > threshold | `threshold` |
| `license_blocklist` | Fail if any component has a listed license | `blocklist` |
| `dep_age_max` | Warn/fail if any dep's last release is older than N days | `threshold` |
| `coverage_min` | Warn/fail if avg JaCoCo coverage < threshold% | `threshold` |
| `secret_count_max` | Fail if secret scan has > threshold findings at min_severity | `threshold`, `min_severity` |
| `untrusted_source_count` | Fail if supply-chain audit found > threshold untrusted sources | `threshold` |
| `no_snapshots` | Fail if any dependency version contains "SNAPSHOT" | — |
| `risk_score_max` | Fail if any dependency's composite risk score ≥ threshold | `threshold` |

## policy-report.json Schema (output)

```json
{
  "evaluation_date": "<ISO-8601>",
  "project":         "<string>",
  "policy_version":  "1.0",
  "overall_result":  "FAIL | WARN | PASS",
  "summary": {
    "rules_evaluated": "<int>",
    "rules_passed":    "<int>",
    "violations":      "<int — FAIL-action violations>",
    "warnings":        "<int — WARN-action violations>"
  },
  "violations": [
    {
      "policy_id":    "<string>",
      "policy_name":  "<string>",
      "action":       "FAIL",
      "detail":       "<string — human-readable explanation>",
      "actual_value": "<number | string>",
      "threshold":    "<number | null>"
    }
  ],
  "warnings": [ "<same structure as violations>" ],
  "passed_rules": ["<rule_id>", "..."]
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All policies passed (or only WARN-level violations) |
| `1` | One or more FAIL-action policies violated |
