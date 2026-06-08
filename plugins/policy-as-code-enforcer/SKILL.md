---
name: policy-as-code-enforcer
description: >
  Enforce security and compliance policies as code — define rules like "no CVSS > 9.0 in
  production deps", "no GPL licenses", "no deps older than 2 years" — and fail CI builds
  automatically on violation. Integrates as Stage 3.7 in the UC1 supply chain pipeline.
  Use this skill whenever the user wants to define security policies, enforce thresholds,
  fail builds on CVE severity, block incompatible licenses, set dependency age limits,
  require minimum test coverage, or automate compliance gates. Trigger for requests like
  "enforce policies", "fail on CRITICAL CVEs", "add a policy gate", "block on high CVSS",
  "define security rules", "policy as code", "compliance enforcement", or "fail the build if...".
---

# Policy-as-Code Enforcer — Stage 3.7

Evaluate all pipeline outputs (CVE scan, risk scores, supply-chain audit, secret scan) against
a set of configurable policy rules. Produce a structured policy report and enforce via exit code.
Designed as a hard gate before auto-remediation — block the pipeline when violations require
human review before any automated changes.

---

## Default Policy Set

Five built-in policies applied to every run. All are overridable via `policy.json`.

| ID | Name | Rule | Default Threshold | Default Action |
|----|------|------|-------------------|----------------|
| P001 | No CRITICAL CVEs in production | Max CVSS score | 9.0 | FAIL |
| P002 | High severity CVE count limit | Count of CVSS ≥ 7.0 | 10 | WARN |
| P003 | No GPL/AGPL in production deps | License blocklist | GPL, AGPL | FAIL |
| P004 | No deps older than 2 years | Dependency age heuristic | 730 days | WARN |
| P005 | Test coverage floor | JaCoCo line coverage | 80% | WARN |
| P006 | No leaked secrets | Secret scan findings | 0 CRITICAL/HIGH | FAIL |
| P007 | No untrusted artifact sources | Supply-chain audit | 0 BLOCK violations | FAIL |

See `references/default-policies.md` for full rule definitions and override syntax.

---

## Workflow

### Step 1 — Load Policy Config

Check for a `policy.json` override file in the project root:

```bash
[ -f policy.json ] && echo "USING_CUSTOM_POLICY" || echo "USING_DEFAULTS"
```

If `policy.json` exists, merge it with the defaults — custom rules override matching IDs,
new IDs are added. Missing IDs keep their defaults.

Policy config format:
```json
{
  "policy_version": "1.0",
  "project": "<PROJECT_NAME>",
  "rules": [
    {
      "id": "P001",
      "name": "No CRITICAL CVEs in production",
      "rule": "cvss_max",
      "threshold": 9.0,
      "action": "FAIL",
      "enabled": true
    },
    {
      "id": "P003",
      "name": "License allowlist",
      "rule": "license_blocklist",
      "blocklist": ["GPL-2.0", "GPL-3.0", "AGPL-3.0", "SSPL-1.0"],
      "action": "FAIL",
      "enabled": true
    }
  ]
}
```

See `references/policy-schema.md` for the complete schema definition.

---

### Step 2 — Collect Inputs

Load all available pipeline outputs for evaluation:

```python
import json, os

def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

cve_report    = load_json("dependency-check-report.json")  # Stage 1
risk_scores   = load_json("risk-scores.json")              # Stage 2
audit_report  = load_json("audit-report.json")             # Stage 3
secret_report = load_json("secret-scan-report.json")       # Stage 3.5
val_report    = load_json("validation-report.json")        # Stage 5 (if available)
```

---

### Step 3 — Evaluate Rules

Evaluate each enabled policy rule against the loaded data:

```python
def evaluate_policies(rules, cve_report, risk_scores, audit_report, secret_report, val_report):
    violations = []
    warnings   = []

    for rule in rules:
        if not rule.get("enabled", True):
            continue

        finding = evaluate_rule(rule, cve_report, risk_scores, audit_report,
                                secret_report, val_report)
        if finding:
            if rule["action"] == "FAIL":
                violations.append(finding)
            else:
                warnings.append(finding)

    return violations, warnings


def evaluate_rule(rule, cve_report, risk_scores, audit_report, secret_report, val_report):
    """Returns a finding dict if the rule is violated, None if it passes."""

    rid = rule["id"]

    # P001 / cvss_max — no CVE above threshold
    if rule["rule"] == "cvss_max":
        all_cves = [v for d in (cve_report or {}).get("dependencies", [])
                    for v in d.get("vulnerabilities", [])]
        max_cvss = max((float((v.get("cvssv3") or {}).get("baseScore", 0))
                        for v in all_cves), default=0.0)
        if max_cvss >= rule["threshold"]:
            return {
                "policy_id":   rid,
                "policy_name": rule["name"],
                "action":      rule["action"],
                "detail":      f"Max CVSS {max_cvss:.1f} exceeds threshold {rule['threshold']}",
                "actual_value": max_cvss,
                "threshold":   rule["threshold"],
            }

    # P002 / high_count_max — too many HIGH/CRITICAL CVEs
    elif rule["rule"] == "high_count_max":
        all_cves  = [v for d in (cve_report or {}).get("dependencies", [])
                     for v in d.get("vulnerabilities", [])]
        high_count = sum(1 for v in all_cves
                         if float((v.get("cvssv3") or {}).get("baseScore", 0)) >= 7.0)
        if high_count > rule["threshold"]:
            return {
                "policy_id":   rid,
                "policy_name": rule["name"],
                "action":      rule["action"],
                "detail":      f"{high_count} HIGH/CRITICAL CVEs exceeds limit of {int(rule['threshold'])}",
                "actual_value": high_count,
                "threshold":   rule["threshold"],
            }

    # P003 / license_blocklist — no blocklisted licenses
    elif rule["rule"] == "license_blocklist":
        blocklist = [l.upper() for l in rule.get("blocklist", [])]
        violations_lic = [v for v in (audit_report or {}).get("violations", [])
                          if v.get("check") == "license_violation"]
        blocked = []
        for v in violations_lic:
            for bl in blocklist:
                if bl in (v.get("detail", "") + v.get("component", "")).upper():
                    blocked.append(v["component"])
        if blocked:
            return {
                "policy_id":   rid,
                "policy_name": rule["name"],
                "action":      rule["action"],
                "detail":      f"Blocklisted license(s) found in: {', '.join(blocked[:3])}",
                "actual_value": len(blocked),
                "threshold":   0,
            }

    # P006 / secret_count_max — no leaked secrets above severity
    elif rule["rule"] == "secret_count_max":
        if secret_report:
            findings = secret_report.get("findings", [])
            sev_filter = rule.get("min_severity", "HIGH")
            sev_order  = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
            min_sev    = sev_order.get(sev_filter, 2)
            blocking   = [f for f in findings
                          if sev_order.get(f.get("severity", ""), 0) >= min_sev]
            if len(blocking) > rule.get("threshold", 0):
                return {
                    "policy_id":   rid,
                    "policy_name": rule["name"],
                    "action":      rule["action"],
                    "detail":      f"{len(blocking)} secret(s) at or above {sev_filter} severity detected",
                    "actual_value": len(blocking),
                    "threshold":   rule.get("threshold", 0),
                }

    # P007 / untrusted_source_count — no untrusted artifacts
    elif rule["rule"] == "untrusted_source_count":
        untrusted = [v for v in (audit_report or {}).get("violations", [])
                     if v.get("check") == "untrusted_source"]
        if len(untrusted) > rule.get("threshold", 0):
            return {
                "policy_id":   rid,
                "policy_name": rule["name"],
                "action":      rule["action"],
                "detail":      f"{len(untrusted)} artifact(s) from untrusted sources",
                "actual_value": len(untrusted),
                "threshold":   rule.get("threshold", 0),
            }

    # P005 / coverage_min — test coverage floor
    elif rule["rule"] == "coverage_min":
        if val_report:
            prs = val_report.get("pull_requests", [])
            covs = [g.get("line_coverage_pct")
                    for p in prs for g in p.get("gates", [])
                    if g.get("gate") == "jacoco-coverage" and g.get("line_coverage_pct")]
            if covs:
                avg_cov = sum(covs) / len(covs)
                if avg_cov < rule["threshold"]:
                    return {
                        "policy_id":   rid,
                        "policy_name": rule["name"],
                        "action":      rule["action"],
                        "detail":      f"Average coverage {avg_cov:.1f}% below minimum {rule['threshold']}%",
                        "actual_value": round(avg_cov, 1),
                        "threshold":   rule["threshold"],
                    }

    return None   # rule passed
```

---

### Step 4 — Generate Report

```json
{
  "evaluation_date": "<ISO-DATE>",
  "project": "<PROJECT_NAME>",
  "policy_version": "1.0",
  "overall_result": "FAIL | WARN | PASS",
  "summary": {
    "rules_evaluated": 7,
    "rules_passed": 5,
    "violations": 1,
    "warnings": 1
  },
  "violations": [
    {
      "policy_id": "P001",
      "policy_name": "No CRITICAL CVEs in production",
      "action": "FAIL",
      "detail": "Max CVSS 9.8 exceeds threshold 9.0",
      "actual_value": 9.8,
      "threshold": 9.0
    }
  ],
  "warnings": [
    {
      "policy_id": "P002",
      "policy_name": "High severity CVE count limit",
      "action": "WARN",
      "detail": "12 HIGH/CRITICAL CVEs exceeds guideline of 10",
      "actual_value": 12,
      "threshold": 10
    }
  ],
  "passed_rules": ["P003", "P004", "P005", "P006", "P007"]
}
```

---

### Step 5 — Approval Gate ⛔ STOP

```
---
⛔ Policy evaluation complete — approval required

Overall result: FAIL / WARN / PASS
Rules evaluated: 7  |  Violations: X  |  Warnings: Y

BLOCKING VIOLATIONS:
  [P001] No CRITICAL CVEs in production
         Max CVSS 9.8 exceeds threshold 9.0

WARNINGS (non-blocking):
  [P002] High severity CVE count limit
         12 HIGH/CRITICAL CVEs (guideline: 10)

Reply with one of:
  • "approve"                        — accept results, continue pipeline
  • "override [P001] reason: <text>" — accept violation with documented reason
  • "adjust P001 threshold to 10"    — change threshold in policy.json
  • "disable P002"                   — disable a non-critical rule
  • "stop here"                      — end session, keep report files only
---
```

---

### Step 6 — Enforce: Exit Code

```bash
FAIL_COUNT=$(python3 -c "
import json
r = json.load(open('policy-report.json'))
print(len(r.get('violations', [])))
")

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo "❌ POLICY GATE FAILED — $FAIL_COUNT violation(s). See policy-report.json."
  exit 1
else
  echo "✅ POLICY GATE PASSED"
  exit 0
fi
```

---

## Output Files

| File | Format | Consumer |
|------|--------|----------|
| `policy-report.json` | JSON | HTML report, audit trail, CI gate |
| `policy.json` | JSON | Persisted custom policy config |
| Markdown summary | stdout | Human / CI log |
| Exit code | Shell | Any CI pipeline |

---

## Reference Files

- `references/default-policies.md` — Built-in policy definitions, thresholds, override guidance
- `references/policy-schema.md` — Full `policy.json` schema with all rule types
- `references/ci-snippets.md` — GitHub Actions, GitLab CI, Jenkins gate integration
