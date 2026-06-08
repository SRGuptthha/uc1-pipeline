# Report Parsing Reference

## JSON Report Structure

The OWASP Dependency-Check JSON report follows this top-level schema:

```json
{
  "reportSchema": "1.1",
  "scanInfo": {
    "engineVersion": "9.x.x",
    "dataSource": [...]
  },
  "projectInfo": {
    "name": "MyProject",
    "reportDate": "2024-01-15T10:30:00Z",
    "credits": {...}
  },
  "dependencies": [ <DependencyObject>, ... ]
}
```

### DependencyObject

```json
{
  "fileName": "log4j-core-2.14.1.jar",
  "filePath": "/path/to/log4j-core-2.14.1.jar",
  "md5": "...",
  "sha1": "...",
  "projectReferences": ["MyProject"],
  "packages": [
    {
      "id": "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1",
      "confidence": "HIGH",
      "url": "https://ossindex.sonatype.org/..."
    }
  ],
  "vulnerabilities": [ <VulnerabilityObject>, ... ],
  "vulnerabilityIds": [...]
}
```

### VulnerabilityObject

```json
{
  "name": "CVE-2021-44228",
  "severity": "CRITICAL",
  "cvssv3": {
    "baseScore": 10.0,
    "attackVector": "NETWORK",
    "attackComplexity": "LOW",
    "privilegesRequired": "NONE",
    "userInteraction": "NONE",
    "scope": "CHANGED",
    "confidentialityImpact": "HIGH",
    "integrityImpact": "HIGH",
    "availabilityImpact": "HIGH",
    "baseSeverity": "CRITICAL",
    "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
  },
  "cvssv2": { ... },
  "cwes": ["CWE-502"],
  "description": "Apache Log4j2 2.0-beta9 through 2.15.0 ...",
  "notes": "",
  "references": [
    {
      "source": "NVD",
      "url": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228",
      "name": "CVE-2021-44228"
    }
  ],
  "vulnerableSoftware": [
    {
      "software": {
        "id": "cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*",
        "vulnerabilityIdMatched": true,
        "versionStartIncluding": "2.0",
        "versionEndExcluding": "2.15.0"
      }
    }
  ]
}
```

---

## Parsing Strategy

### Extract all vulnerabilities (Python example)
```python
import json

with open('dependency-check-report.json') as f:
    report = json.load(f)

vulns = []
for dep in report.get('dependencies', []):
    for vuln in dep.get('vulnerabilities', []):
        cvss = vuln.get('cvssv3', {}).get('baseScore') \
               or vuln.get('cvssv2', {}).get('score', 0)
        vulns.append({
            'cve': vuln['name'],
            'dependency': dep['fileName'],
            'cvss': cvss,
            'severity': vuln.get('severity', 'UNKNOWN'),
            'description': vuln.get('description', ''),
        })

# Sort: Critical → High → Medium → Low
severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
vulns.sort(key=lambda v: (severity_order.get(v['severity'], 9), -v['cvss']))
```

---

## Confidence Levels

| Level  | Meaning |
|--------|---------|
| HIGH   | Strong match on package name, version, and vendor — very likely accurate |
| MEDIUM | Partial match — review recommended |
| LOW    | Weak match — likely a false positive; verify before acting |

Always call out LOW confidence findings separately in the summary and recommend manual verification before suppressing.

---

## Severity Mapping

| CVSS v3 Score | Dependency-Check `severity` field |
|---------------|-----------------------------------|
| 9.0 – 10.0    | CRITICAL                          |
| 7.0 – 8.9     | HIGH                              |
| 4.0 – 6.9     | MEDIUM                            |
| 0.1 – 3.9     | LOW                               |
| N/A           | INFORMATIONAL                     |

When CVSS v3 is unavailable, fall back to CVSS v2. When neither is available, treat as HIGH until NVD publishes a score.