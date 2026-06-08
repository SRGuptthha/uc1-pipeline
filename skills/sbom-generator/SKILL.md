---
name: sbom-generator
description: >
  Generate a CycloneDX 1.5 or SPDX 2.3 Software Bill of Materials (SBOM) from Maven, Node.js,
  Python, .NET, and Ruby projects. Produces machine-readable SBOMs required by enterprise
  procurement, US Executive Order 14028, and software supply-chain compliance frameworks. Use
  this skill whenever the user wants to generate an SBOM, produce a software bill of materials,
  export dependency inventory, comply with NTIA SBOM requirements, or integrate SBOM generation
  into CI/CD pipelines. Trigger for requests like "generate an SBOM", "produce a CycloneDX
  SBOM", "create an SPDX file", "export my dependencies as SBOM", "I need SBOM for compliance",
  "what's in my software?", or "dependency inventory".
---

# SBOM Generator

Produce a complete Software Bill of Materials in CycloneDX 1.5 JSON or SPDX 2.3 JSON/tag-value
format, covering all direct and transitive dependencies with component metadata, license info,
and vulnerability cross-references. Integrates as Stage 1.5 in the UC1 supply chain pipeline
alongside CVE scanning and audit outputs.

---

## Supported Formats

| Format | Version | File Extension | Primary Use |
|--------|---------|----------------|-------------|
| CycloneDX JSON | 1.5 | `.cdx.json` | Tooling (Grype, Trivy, Dependency-Track) |
| SPDX JSON | 2.3 | `.spdx.json` | Legal/compliance, GitHub SBOM API |
| SPDX tag-value | 2.3 | `.spdx` | Legacy tools, NTIA SBOM minimum elements |

Always generate CycloneDX JSON by default. Add SPDX if the user mentions compliance, legal, or GitHub.

---

## Workflow

### Step 1 — Understand the Context

Ask (or infer from context):
1. **Project path** — where is the manifest file (`pom.xml`, `package.json`, etc.)?
2. **Format** — CycloneDX, SPDX, or both? (default: CycloneDX)
3. **Scope** — include test/dev dependencies? (default: no — production only)
4. **Transitive deps** — include indirect dependencies? (default: yes)
5. **License enrichment** — fetch license info from registries? (default: yes if online)

---

### Step 2 — Choose Generation Method

Two paths depending on tooling availability:

#### Path A — Syft (preferred, most complete)
```bash
# Check if Syft is installed
syft version 2>/dev/null || echo "NOT_INSTALLED"

# CycloneDX output
syft dir:<PROJECT_PATH> --output cyclonedx-json=./sbom.cdx.json

# SPDX output
syft dir:<PROJECT_PATH> --output spdx-json=./sbom.spdx.json

# Both formats
syft dir:<PROJECT_PATH> \
  --output cyclonedx-json=./sbom.cdx.json \
  --output spdx-json=./sbom.spdx.json
```

If Syft is not installed, read `references/install.md` for installation instructions.

#### Path B — Pipeline-native (no external tool needed)
Generate CycloneDX JSON directly from parsed pom.xml / package.json data using the pipeline's
already-parsed dependency list. This produces a valid but metadata-limited SBOM (no transitive
deps beyond what the manifest declares, no license data unless enriched via API call).

```python
import json, uuid

def build_cyclonedx_sbom(project_name, deps, scan_date):
    components = []
    for dep in deps:
        comp = {
            "type": "library",
            "bom-ref": dep["purl"],
            "group": dep.get("group", ""),
            "name": dep["artifact"],
            "version": dep["version"],
            "purl": dep["purl"],
            "scope": "required" if not dep.get("test") else "excluded",
        }
        if dep.get("license"):
            comp["licenses"] = [{"license": {"id": dep["license"]}}]
        components.append(comp)

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": scan_date,
            "tools": [{"vendor": "UC1", "name": "Supply Chain Security Pipeline", "version": "1.0"}],
            "component": {
                "type": "application",
                "name": project_name,
                "version": "1.0.0",
            },
        },
        "components": components,
    }
```

See `references/cyclonedx-schema.md` for the full CycloneDX 1.5 field reference.

---

### Step 3 — License Enrichment (optional)

If online, enrich each component with its declared license by querying the Maven Central or
npm registry API:

```bash
# Maven Central license lookup
curl -s "https://search.maven.org/solrsearch/select?\
q=g:<GROUP_ID>+AND+a:<ARTIFACT_ID>+AND+v:<VERSION>&rows=1&wt=json" \
| python3 -c "
import sys, json
d = json.load(sys.stdin)['response']['docs']
print(d[0].get('l', 'UNKNOWN') if d else 'NOT_FOUND')
"
```

Common license SPDX IDs to look for: `Apache-2.0`, `MIT`, `EPL-2.0`, `LGPL-2.1`, `GPL-3.0`.
Flag any `GPL-*`, `AGPL-*`, or `UNKNOWN` licenses for the license compliance check.

---

### Step 4 — Generate & Validate SBOM

After generation, validate the SBOM has the NTIA minimum elements:

| NTIA Required Element | CycloneDX Field | SPDX Field |
|-----------------------|-----------------|------------|
| Supplier name | `supplier` | `PackageSupplier` |
| Component name | `name` | `PackageName` |
| Component version | `version` | `PackageVersion` |
| Other unique identifiers | `purl` | `SPDXID` |
| Dependency relationships | `dependencies[]` | `Relationship` |
| Author of SBOM data | `metadata.tools` | `Creator` |
| Timestamp | `metadata.timestamp` | `Created` |

```bash
# Validate with Syft or CycloneDX CLI
cyclonedx-cli validate --input-file sbom.cdx.json --fail-on-errors
```

---

### Step 5 — Approval Gate ⛔ STOP

After generating the SBOM, present a summary and wait for explicit approval before continuing.

```
---
⛔ SBOM generated — review required

Output files:
  • sbom-cyclonedx.json   (<N> components, <SIZE> KB)

Summary:
  • Total components      : <N>
  • With license data     : <M>
  • Unknown licenses      : <K>  ← review for GPL/AGPL
  • NTIA minimum elements : ✅ PASS / ❌ MISSING: <fields>

Reply with:
  • "approve"             — accept SBOM, continue pipeline
  • "enrich licenses"     — fetch license data from registries
  • "add spdx"            — also generate SPDX format
  • "stop here"           — end session, keep output files
---
```

---

### Step 6 — Cross-Reference with CVE Scan

If Stage 1 CVE scan output (`dependency-check-report.json`) exists, annotate SBOM components
with their vulnerability status:

```python
# Enrich each SBOM component with its CVE count
for comp in sbom["components"]:
    purl = comp.get("purl", "")
    cves = vuln_map.get(purl, [])
    if cves:
        comp["vulnerabilities"] = [
            {"ref": purl, "id": v["name"], "ratings": [{"score": v["cvssv3"]["baseScore"]}]}
            for v in cves
        ]
```

---

### Step 7 — CI/CD Integration

Read `references/cicd.md` for ready-to-paste pipeline snippets. Key points:
- Run SBOM generation before the CVE scan so results can be cross-referenced.
- Store the SBOM as a pipeline artifact and publish to GitHub's dependency graph via the
  Dependency Submission API.
- For GitHub Advanced Security, output in SPDX format.

---

## Output Files

| File | Format | Consumer |
|------|--------|----------|
| `sbom-cyclonedx.json` | CycloneDX 1.5 JSON | Grype, Trivy, Dependency-Track, Stage 3 |
| `sbom.spdx.json` | SPDX 2.3 JSON | GitHub SBOM API, legal team |
| `sbom.spdx` | SPDX tag-value | NTIA compliance, legacy tools |

---

## Reference Files

- `references/install.md` — Syft, CycloneDX CLI installation (Linux, macOS, Windows, Docker)
- `references/cyclonedx-schema.md` — CycloneDX 1.5 full field reference and examples
- `references/spdx-schema.md` — SPDX 2.3 tag-value and JSON format reference
- `references/cicd.md` — Pipeline integration snippets for GitHub Actions, Jenkins, GitLab CI
