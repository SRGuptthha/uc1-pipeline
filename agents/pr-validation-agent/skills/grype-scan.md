# Gate 3: Grype Scan — PR Validation Agent

## Purpose

Run Grype against the PR branch SBOM to catch vulnerabilities that OWASP may miss
(different matcher engines catch different CVEs). Gate passes if zero new Critical or
High findings are introduced vs. the Stage 3 baseline.

---

## Run Command

```bash
# Generate fresh SBOM for this branch
syft dir:. --output cyclonedx-json=./sbom-pr-<PR_NUMBER>.cdx.json -q

# Scan with Grype
grype sbom:./sbom-pr-<PR_NUMBER>.cdx.json \
  --output json \
  --file ./grype-pr-<PR_NUMBER>.json \
  --fail-on high \
  2>&1 | tee grype-output.txt
echo "EXIT_CODE:$?"
```

`--fail-on high` exits 1 if any High or Critical finding — used as a quick gate signal.

---

## Parse Results

```python
import json

def parse_grype(report_path):
    with open(report_path) as f:
        report = json.load(f)

    findings = []
    for match in report.get("matches", []):
        vuln = match["vulnerability"]
        findings.append({
            "id":       vuln["id"],
            "severity": vuln["severity"],     # Critical / High / Medium / Low / Negligible
            "cvss":     vuln.get("cvss", [{}])[0].get("metrics", {}).get("baseScore", 0),
            "package":  match["artifact"]["name"] + ":" + match["artifact"]["version"],
            "fixed_in": vuln.get("fix", {}).get("versions", [])
        })
    return findings
```

---

## Diff Against Stage 3 Baseline

```python
def load_grype_ids(report_path):
    with open(report_path) as f:
        report = json.load(f)
    return {m["vulnerability"]["id"] for m in report.get("matches", [])}

baseline_ids = load_grype_ids("./grype-baseline.json")   # Stage 3 output
pr_ids       = load_grype_ids(f"./grype-pr-<PR_NUMBER>.json")

new_findings     = pr_ids - baseline_ids
resolved_findings = baseline_ids - pr_ids
```

If Stage 3 baseline doesn't exist, treat current PR branch as the first scan (no diff).

---

## Pass Condition

```python
def gate_pass(findings, new_finding_ids):
    new = [f for f in findings if f["id"] in new_finding_ids]
    return all(f["severity"] not in ("Critical", "High") for f in new)
```

New Medium / Low / Negligible findings → warning only, no block.

---

## Gate Result Object

```json
{
  "gate": "grype-scan",
  "status": "PASS",
  "new_findings": [],
  "resolved_findings": ["CVE-2023-50164"],
  "new_critical": 0,
  "new_high": 0,
  "new_medium": 1,
  "detail": "0 new Critical/High findings. 1 Medium finding (informational). 1 CVE resolved."
}
```

---

## PR Comment Section (on failure)

```markdown
**🛡️ Grype Scan — ❌ FAIL**
New Critical/High findings introduced by this upgrade:

| ID | Severity | Package | Fixed In |
|----|----------|---------|---------|
| CVE-XXXX-XXXXX | Critical | new-dep:2.0.0 | 2.0.1 |

Action: The upgraded artifact pulls in a vulnerable transitive dependency.
Consider adding a `<dependencyManagement>` override to force the fixed version.
```