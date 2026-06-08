# Input Schema & Remediation Manifest — Auto-Remediation Skill

## Merging Stage 1 + Stage 2 Inputs

### Stage 1 key fields (OWASP JSON)
```
dependencies[].packages[].id        → GAV purl
dependencies[].vulnerabilities[].name       → CVE ID
dependencies[].vulnerabilities[].cvssv3.baseScore → CVSS score
dependencies[].vulnerabilities[].severity   → severity label
dependencies[].vulnerabilities[].description → plain-English description
```

### Stage 2 key fields (risk-scores.json)
```
dependencies[].artifact             → GAV string "g:a:v"
dependencies[].composite_risk_score → 0–100
dependencies[].risk_tier            → CRITICAL / HIGH / MEDIUM / LOW
dependencies[].cves[]               → CVE list with cvss
```

### Merge Logic

```python
import json

def merge_inputs(owasp_path, risk_path):
    with open(owasp_path) as f:
        owasp = json.load(f)
    with open(risk_path) as f:
        risk = json.load(f)

    # Build risk lookup by artifact GAV
    risk_lookup = {d["artifact"]: d for d in risk["dependencies"]}

    merged = []
    for dep in owasp["dependencies"]:
        if not dep.get("vulnerabilities"):
            continue
        # Extract GAV from purl
        purl = dep.get("packages", [{}])[0].get("id", "")
        gav = purl.replace("pkg:maven/", "").replace("/", ":").replace("@", ":")

        risk_data = risk_lookup.get(gav, {})
        merged.append({
            "artifact": gav,
            "current_version": gav.split(":")[-1],
            "composite_risk_score": risk_data.get("composite_risk_score", 0),
            "risk_tier": risk_data.get("risk_tier", "UNKNOWN"),
            "cves": [
                {
                    "id": v["name"],
                    "cvss": v.get("cvssv3", {}).get("baseScore")
                           or v.get("cvssv2", {}).get("score", 0),
                    "severity": v.get("severity", "UNKNOWN"),
                    "description": v.get("description", "")
                }
                for v in dep["vulnerabilities"]
            ]
        })

    # Sort by composite_risk_score desc, fall back to max CVE CVSS
    merged.sort(
        key=lambda x: x["composite_risk_score"] or max(c["cvss"] for c in x["cves"]),
        reverse=True
    )
    return merged
```

---

## remediation-manifest.json Schema

Output after PRs are created — consumed by Stage 5 PR Validation Agent.

```json
{
  "generated_date": "<ISO-DATE>",
  "project": "<PROJECT_NAME>",
  "repo": "<OWNER>/<REPO>",
  "base_branch": "main",
  "strategy": "one_pr_per_dep | consolidated",
  "pull_requests": [
    {
      "pr_number": 42,
      "pr_url": "https://github.com/<OWNER>/<REPO>/pull/42",
      "branch": "fix/cve-struts2-core-6.3.0.2",
      "artifact": "org.apache.struts:struts2-core",
      "old_version": "2.5.28",
      "new_version": "6.3.0.2",
      "bump_type": "MAJOR",
      "composite_risk_score": 91.4,
      "risk_tier": "CRITICAL",
      "cves_fixed": ["CVE-2023-50164"],
      "mvn_resolve_passed": true,
      "status": "OPEN"
    }
  ],
  "skipped": [
    {
      "artifact": "ch.qos.logback:logback-classic:1.2.9",
      "reason": "Skipped by user"
    }
  ]
}
```