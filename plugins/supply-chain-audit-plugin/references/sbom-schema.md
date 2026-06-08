# SBOM Schema — CycloneDX JSON Reference

## Top-Level Structure

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "serialNumber": "urn:uuid:...",
  "version": 1,
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "tools": [ { "name": "syft", "version": "0.98.0" } ],
    "component": { "name": "my-project", "version": "1.0.0" }
  },
  "components": [ <component objects> ]
}
```

---

## Component Object (key fields)

```json
{
  "type": "library",
  "bom-ref": "pkg:maven/org.springframework/spring-core@5.3.20",
  "group": "org.springframework",
  "name": "spring-core",
  "version": "5.3.20",
  "purl": "pkg:maven/org.springframework/spring-core@5.3.20",
  "licenses": [
    { "license": { "id": "Apache-2.0" } }
  ],
  "externalReferences": [
    { "type": "website", "url": "https://spring.io" }
  ]
}
```

### Key Fields for Audit Checks

| Field | Used For |
|-------|----------|
| `group` | groupId — typosquat + source check |
| `name` | artifactId — typosquat check |
| `version` | version — source check (Maven Central lookup) |
| `purl` | Full artifact identity |
| `licenses[].license.id` | License check — SPDX ID |
| `licenses[].license.name` | License check — fallback if no SPDX ID |

---

## Parsing the SBOM in Python

```python
import json

with open("./sbom.cdx.json") as f:
    sbom = json.load(f)

for component in sbom.get("components", []):
    group    = component.get("group", "")
    name     = component.get("name", "")
    version  = component.get("version", "")
    purl     = component.get("purl", "")
    licenses = component.get("licenses", [])

    # Extract SPDX license IDs
    license_ids = []
    for lic in licenses:
        if "license" in lic:
            lid = lic["license"].get("id") or lic["license"].get("name", "UNKNOWN")
            license_ids.append(lid)
```

---

## Generating the SBOM with Syft

```bash
# CycloneDX JSON (preferred for this plugin)
syft dir:<PROJECT_PATH> --output cyclonedx-json=./sbom.cdx.json

# With explicit scope (include dev/test deps)
syft dir:<PROJECT_PATH> --output cyclonedx-json=./sbom.cdx.json --scope all-layers

# From a built JAR/WAR instead of source
syft <PROJECT_PATH>/target/myapp.war --output cyclonedx-json=./sbom.cdx.json
```

Syft auto-detects `pom.xml` and resolves both direct and transitive dependencies.