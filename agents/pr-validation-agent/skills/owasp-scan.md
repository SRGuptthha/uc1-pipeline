# Gate 2: OWASP Scan — PR Validation Agent

## Purpose

Re-run OWASP Dependency-Check on the PR branch and compare against the Stage 1 baseline.
The gate passes if the upgrade has not introduced **any new** Critical or High CVEs
(existing known CVEs already tracked in baseline are ignored).

---

## Run Command

```bash
dependency-check \
  --project "<PROJECT_NAME>-pr-<PR_NUMBER>" \
  --scan . \
  --format JSON \
  --out ./owasp-pr-<PR_NUMBER> \
  --nvdApiKey "$NVD_API_KEY" \
  --failOnCVSS 7 \
  2>&1 | tee owasp-output.txt
echo "EXIT_CODE:$?"
```

Use `--failOnCVSS 7` — exit code 1 if any High/Critical CVE found (used for quick check only;
we also do diff-based analysis below).

---

## Diff Against Baseline

Compare PR branch results against the Stage 1 OWASP report to find **net-new** CVEs:

```python
import json

def load_cves(report_path):
    with open(report_path) as f:
        report = json.load(f)
    cves = set()
    for dep in report["dependencies"]:
        for vuln in dep.get("vulnerabilities", []):
            cves.add(vuln["name"])
    return cves

baseline_cves = load_cves("./dependency-check-report/dependency-check-report.json")
pr_cves       = load_cves(f"./owasp-pr-<PR_NUMBER>/dependency-check-report.json")

new_cves     = pr_cves - baseline_cves   # introduced by this PR — FAIL if any Critical/High
resolved_cves = baseline_cves - pr_cves  # fixed by this PR — good news
```

---

## Pass Condition

```python
def gate_pass(new_cves, nvd_data):
    # Pass if zero new Critical or High CVEs introduced
    for cve_id in new_cves:
        score = nvd_data[cve_id]["cvss"]
        if score >= 7.0:
            return False
    return True
```

New Medium/Low CVEs are flagged as warnings but do not block.

---

## Gate Result Object

```json
{
  "gate": "owasp-scan",
  "status": "PASS",
  "new_cves": [],
  "resolved_cves": ["CVE-2023-50164"],
  "new_critical": 0,
  "new_high": 0,
  "new_medium": 0,
  "detail": "0 new CVEs introduced. 1 CVE resolved by this upgrade."
}
```

---

## PR Comment Section (on failure)

```markdown
**🔐 OWASP Scan — ❌ FAIL**
New CVEs introduced by this upgrade:

| CVE | CVSS | Severity | Affected Dependency |
|-----|------|----------|---------------------|
| CVE-XXXX-XXXXX | 8.1 | High | new-transitive-dep:1.0.0 |

Action: Review whether the new transitive dependency can be excluded or overridden.
```