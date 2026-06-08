# CycloneDX 1.5 JSON Schema Reference

## Top-Level Structure

```json
{
  "bomFormat":    "CycloneDX",
  "specVersion":  "1.5",
  "serialNumber": "urn:uuid:<UUID4>",
  "version":      1,
  "metadata":     { ... },
  "components":   [ ... ],
  "dependencies": [ ... ],
  "vulnerabilities": [ ... ]
}
```

## metadata

```json
{
  "timestamp": "2026-06-04T09:00:00Z",
  "tools": [
    {
      "vendor":  "UC1",
      "name":    "Supply Chain Security Pipeline",
      "version": "1.0"
    }
  ],
  "authors": [
    { "name": "Security Team" }
  ],
  "component": {
    "type":    "application",
    "name":    "<PROJECT_NAME>",
    "version": "1.0.0",
    "purl":    "pkg:maven/<GROUP>/<ARTIFACT>@<VERSION>"
  }
}
```

## component (library entry)

```json
{
  "type":    "library",
  "bom-ref": "pkg:maven/org.springframework/spring-core@5.3.20",
  "group":   "org.springframework",
  "name":    "spring-core",
  "version": "5.3.20",
  "purl":    "pkg:maven/org.springframework/spring-core@5.3.20",
  "scope":   "required",
  "hashes": [
    { "alg": "SHA-256", "content": "<SHA256_HEX>" }
  ],
  "licenses": [
    { "license": { "id": "Apache-2.0" } }
  ],
  "description": "Spring Core",
  "externalReferences": [
    { "type": "website", "url": "https://spring.io/projects/spring-framework" }
  ]
}
```

### scope values
| Value | Meaning |
|-------|---------|
| `required` | Compile/runtime dependency |
| `optional` | Optional dependency |
| `excluded` | Test/provided scope — not in production |

## dependencies (relationship graph)

```json
[
  {
    "ref": "pkg:maven/com.example/my-app@1.0.0",
    "dependsOn": [
      "pkg:maven/org.springframework/spring-core@5.3.20",
      "pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.15.4"
    ]
  }
]
```

## vulnerabilities (cross-reference from CVE scan)

```json
[
  {
    "bom-ref":    "vuln-CVE-2021-44228",
    "id":         "CVE-2021-44228",
    "source":     { "name": "NVD", "url": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228" },
    "ratings": [
      {
        "source":   { "name": "NVD" },
        "score":    10.0,
        "severity": "critical",
        "method":   "CVSSv3"
      }
    ],
    "description": "Apache Log4j2 2.0-beta9 through 2.15.0 JNDI features used in configuration...",
    "affects": [
      {
        "ref":     "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1",
        "versions": [{ "version": "2.14.1", "status": "affected" }]
      }
    ]
  }
]
```

## PURL Format for Maven

```
pkg:maven/<groupId>/<artifactId>@<version>

Examples:
  pkg:maven/org.apache.struts/struts2-core@2.5.28
  pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.13.0
  pkg:maven/org.springframework/spring-core@5.3.20
```

## License SPDX IDs (common)

| SPDX ID | License Name | Commercial OK? |
|---------|-------------|---------------|
| Apache-2.0 | Apache License 2.0 | ✅ Yes |
| MIT | MIT License | ✅ Yes |
| EPL-2.0 | Eclipse Public License 2.0 | ✅ Yes (with conditions) |
| LGPL-2.1 | GNU Lesser GPL 2.1 | ⚠️ Dynamic linking OK |
| GPL-2.0 | GNU General Public License 2.0 | ❌ Copyleft — infects product |
| GPL-3.0 | GNU General Public License 3.0 | ❌ Copyleft — infects product |
| AGPL-3.0 | GNU Affero GPL 3.0 | ❌ Network use triggers copyleft |
| SSPL-1.0 | Server Side Public License | ❌ Cloud/service use restricted |
