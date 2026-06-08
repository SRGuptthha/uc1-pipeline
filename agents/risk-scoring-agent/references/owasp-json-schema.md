# OWASP Dependency-Check JSON Schema Reference

## Top-Level Structure

```json
{
  "reportSchema": "1.1",
  "scanInfo": { "engineVersion": "...", "dataSource": [...] },
  "projectInfo": { "name": "...", "reportDate": "...", "credits": {...} },
  "dependencies": [ <dependency objects> ]
}
```

---

## Dependency Object (key fields)

```json
{
  "isVirtual": false,
  "fileName": "struts2-core-2.5.28.jar",
  "filePath": "/path/to/struts2-core-2.5.28.jar",
  "md5": "...",
  "sha1": "...",
  "packages": [
    {
      "id": "pkg:maven/org.apache.struts/struts2-core@2.5.28",
      "confidence": "HIGH",
      "url": "https://ossindex.sonatype.org/..."
    }
  ],
  "evidenceCollected": { ... },
  "vulnerabilities": [ <vulnerability objects> ],
  "suppressedVulnerabilities": [ ... ]
}
```

### Key Fields for Scoring

| Field | Type | Used For |
|-------|------|----------|
| `isVirtual` | boolean | Exposure factor — virtual = provided/test scope |
| `fileName` | string | Display name |
| `packages[].id` | string | Maven GAV in purl format (`pkg:maven/group/artifact@version`) |
| `vulnerabilities` | array | CVE list for CVSS factor |

---

## Vulnerability Object (key fields)

```json
{
  "name": "CVE-2023-50164",
  "severity": "CRITICAL",
  "cvssv3": {
    "baseScore": 9.8,
    "baseSeverity": "CRITICAL",
    "attackVector": "NETWORK",
    "attackComplexity": "LOW",
    "privilegesRequired": "NONE",
    "userInteraction": "NONE",
    "scope": "UNCHANGED",
    "confidentialityImpact": "HIGH",
    "integrityImpact": "HIGH",
    "availabilityImpact": "HIGH"
  },
  "cvssv2": {
    "score": 7.5,
    "severity": "HIGH"
  },
  "cwes": ["CWE-434"],
  "description": "...",
  "notes": "",
  "references": [ { "url": "...", "name": "..." } ],
  "vulnerableSoftware": [ { "software": { "id": "..." } } ]
}
```

### Key Fields for Scoring

| Field | Type | Used For |
|-------|------|----------|
| `name` | string | CVE ID |
| `cvssv3.baseScore` | float | Primary CVSS factor input |
| `cvssv2.score` | float | Fallback if v3 unavailable (× 0.9) |
| `severity` | string | Display / tier label |

---

## Parsing the GAV from purl

The `packages[].id` field uses purl format:
```
pkg:maven/org.apache.struts/struts2-core@2.5.28
```

To extract GAV:
```python
purl = "pkg:maven/org.apache.struts/struts2-core@2.5.28"
# Remove prefix
coords = purl.replace("pkg:maven/", "")
group_artifact, version = coords.split("@")
group, artifact = group_artifact.split("/")
gav = f"{group}:{artifact}:{version}"
# → "org.apache.struts:struts2-core:2.5.28"
```

---

## Locating the Report File

Default OWASP Dependency-Check output path (from Stage 1 skill):
```
./dependency-check-report/dependency-check-report.json
```

Load it:
```python
import json
with open("./dependency-check-report/dependency-check-report.json") as f:
    report = json.load(f)
dependencies = report["dependencies"]
```