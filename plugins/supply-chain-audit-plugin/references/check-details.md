# Check Details — Supply-Chain Audit Plugin

## Check A: Typosquatting Detection

### What It Catches
Attackers publish malicious artifacts with names nearly identical to popular ones, hoping
developers mistype the dependency. Examples:
- `com.fastexml.jackson.core:jackson-databind` (extra 'e')
- `org.springframewok:spring-core` (missing 'r')
- `log4j:log4j2` (suffix addition mimicking log4j)

### Detection Method

1. Extract all components from SBOM: `groupId`, `artifactId`, `version`
2. For each component, compute Levenshtein distance against every entry in `known-safe-artifacts.txt`
3. Flag if: distance ≤ 2 AND the component is **not** an exact match

```python
# Pseudocode
from Levenshtein import distance

def is_typosquat(artifact_id, corpus, threshold=2):
    for known in corpus:
        d = distance(artifact_id.lower(), known.lower())
        if 0 < d <= threshold:
            return True, known, d
    return False, None, None
```

### False Positive Reduction
- Exact matches are never flagged
- Internal artifacts in `source-allowlist.txt` are exempt
- Common legitimate suffixes (`-api`, `-impl`, `-core`, `-test`) are stripped before comparison
- Minimum artifact name length: 6 characters (very short names skipped)

### Severity Assignment
| Edit Distance | Severity |
|--------------|----------|
| 1 | HIGH |
| 2 | MEDIUM |

---

## Check B: Untrusted Source Detection

### What It Catches
Dependencies resolved from unknown registries, private repositories not on the allowlist,
or artifacts that simply don't exist in Maven Central (potential phantom dependency attack).

### Detection Method

For each `pkg:maven/...` component in the SBOM:

1. Extract `groupId`, `artifactId`, `version`
2. Query Maven Central search API:

```bash
curl -s "https://search.maven.org/solrsearch/select?\
q=g:<GROUP>+AND+a:<ARTIFACT>+AND+v:<VERSION>&rows=1&wt=json" \
| python3 -c "
import sys, json
d = json.load(sys.stdin)
print('FOUND' if d['response']['numFound'] > 0 else 'NOT_FOUND')
"
```

3. If `NOT_FOUND` and not in `source-allowlist.txt` → flag as untrusted

### Rate Limiting
Maven Central search allows ~10 req/s. For large SBOMs (>100 deps), batch with 0.1s delay:
```bash
sleep 0.1  # between each curl call
```

### Source Allowlist
`references/source-allowlist.txt` — one `groupId:artifactId` per line, for known-safe
internal/private artifacts:
```
com.mycompany:internal-utils
com.mycompany:shared-models
```

### Severity Assignment
| Condition | Severity |
|-----------|----------|
| Not in Central, not allowlisted | MEDIUM |
| Flagged by Grype as malicious | HIGH |

---

## Check C: License Violation Detection

### What It Catches
Dependencies declared with licenses that violate the project's policy — typically copyleft
licenses (GPL, LGPL, AGPL) in a commercial/proprietary codebase.

### Detection Method

1. For each component, extract the `licenses` array from the CycloneDX SBOM:

```json
{
  "licenses": [
    { "license": { "id": "GPL-3.0" } }
  ]
}
```

2. Check each license ID against the allowlist in `references/license-policy.md`
3. If **any** license is not in the allowlist → violation
4. If licenses array is empty or missing → apply `unknown_license_action` setting

### Multi-License Components
If a component declares multiple licenses (e.g. `Apache-2.0 OR GPL-2.0`):
- If **any** permitted license is present → treat as permitted (OR semantics)
- If **all** licenses are blocked → violation

### SPDX Normalisation
Normalise before comparison:
- `Apache 2.0` → `Apache-2.0`
- `The MIT License` → `MIT`
- `GNU General Public License v3` → `GPL-3.0`

Use the SPDX identifier map in `references/license-policy.md` for common aliases.

### Per-Artifact Exceptions
Check `references/license-exceptions.json` before flagging. If the artifact+license
combination has an approved exception, skip it (log as INFO, not violation).