# Version Resolution — Auto-Remediation Skill

## Resolution Priority

For each vulnerable dependency, resolve the upgrade target in this order:

1. **Latest version that fixes all CVEs** — preferred; verified against NVD vulnerable ranges
2. **Latest patch within same major** — if latest introduces new CVEs or is pre-release
3. **Latest minor within same major** — fallback if patch unavailable
4. **Latest available (any bump)** — last resort; flag as MAJOR with breaking change warning

Never recommend a pre-release version (`-alpha`, `-beta`, `-RC`, `-SNAPSHOT`) unless
the user explicitly requests it.

---

## Maven Central Version Lookup

```bash
# All available versions for an artifact, sorted desc
curl -s "https://search.maven.org/solrsearch/select?\
q=g:<GROUP>+AND+a:<ARTIFACT>&rows=50&core=gav&sort=score+desc&wt=json" \
| python3 -c "
import sys, json
docs = json.load(sys.stdin)['response']['docs']
versions = [d['v'] for d in docs]
print('\n'.join(versions))
"
```

Filter out pre-releases:
```python
import re
def is_stable(version):
    return not re.search(r'alpha|beta|rc|snapshot|m\d', version, re.IGNORECASE)
```

---

## NVD CVE Fix Verification

Confirm the target version is outside the vulnerable range:

```python
import requests

def is_version_fixed(cve_id, target_version):
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    data = requests.get(url).json()
    for vuln in data.get("vulnerabilities", []):
        for cfg in vuln["cve"].get("configurations", []):
            for node in cfg.get("nodes", []):
                for match in node.get("cpeMatch", []):
                    end_excl = match.get("versionEndExcluding")
                    end_incl = match.get("versionEndIncluding")
                    if end_excl and version_lt(target_version, end_excl):
                        return False  # still vulnerable
                    if end_incl and version_lte(target_version, end_incl):
                        return False  # still vulnerable
    return True  # not in any vulnerable range
```

Use `packaging.version.Version` for semantic comparison:
```python
from packaging.version import Version
def version_lt(a, b):
    return Version(a) < Version(b)
```

---

## Bump Type Classification

```python
from packaging.version import Version

def classify_bump(old, new):
    o, n = Version(old), Version(new)
    if n.major > o.major:
        return "MAJOR"
    elif n.minor > o.minor:
        return "MINOR"
    else:
        return "PATCH"
```

---

## Edge Cases

### Property-referenced versions (`${spring.version}`)
1. Detect: `<version>${...}</version>` in `<dependency>` block
2. Extract property name from `${}` expression
3. Resolve current value from `<properties>` block
4. Patch `<properties>` instead of the dependency version tag
5. Check for other dependencies sharing the same property — warn user if the bump affects them

### BOM (Bill of Materials) managed versions
If a dependency has no `<version>` tag (managed by a BOM import):
1. Find the BOM artifact in `<dependencyManagement><dependencies>`
2. Upgrade the BOM version itself — not the individual dependency
3. Flag in PR: "Version managed by BOM `<bom-artifact>` — upgraded BOM from X to Y"

### Multi-module projects
1. Check parent POM first — version may be declared in root `pom.xml`
2. If declared in child module only, patch that child's `pom.xml`
3. If declared in both — patch root only (child inherits)
4. Run `mvn dependency:resolve` from the **root** module to verify

### Version ranges (`[1.0,2.0)`)
Treat range declarations as manual review required — do not auto-patch.
Flag to user: "Version range detected — manual update recommended."