# Default Policy Definitions

All 7 built-in policies — their rule types, thresholds, and override guidance.

---

## P001 — No CRITICAL CVEs in Production

```json
{
  "id": "P001",
  "name": "No CRITICAL CVEs in production",
  "rule": "cvss_max",
  "threshold": 9.0,
  "action": "FAIL",
  "enabled": true,
  "description": "Fails the build if any dependency has a CVE with CVSS score >= threshold."
}
```

**Override examples:**
- Raise threshold: `"threshold": 10.0` (only block perfect-10 CVEs)
- Downgrade to warning: `"action": "WARN"`
- Disable entirely: `"enabled": false`

---

## P002 — High Severity CVE Count Limit

```json
{
  "id": "P002",
  "name": "High severity CVE count limit",
  "rule": "high_count_max",
  "threshold": 10,
  "action": "WARN",
  "description": "Warns when the total count of CVEs with CVSS >= 7.0 exceeds the threshold."
}
```

**Override:** Reduce to 5 for stricter enforcement; set `"action": "FAIL"` to block builds.

---

## P003 — License Allowlist

```json
{
  "id": "P003",
  "name": "No GPL/AGPL in production deps",
  "rule": "license_blocklist",
  "blocklist": ["GPL-2.0", "GPL-3.0", "AGPL-3.0", "SSPL-1.0", "EUPL-1.1"],
  "action": "FAIL",
  "enabled": true,
  "description": "Blocks licenses that are incompatible with commercial software distribution."
}
```

**Add to blocklist:** `"LGPL-2.1"` if your product distributes statically linked binaries.
**Remove from blocklist:** `"GPL-3.0"` if your product is open-source under GPL.

---

## P004 — Dependency Age Limit

```json
{
  "id": "P004",
  "name": "No deps older than 2 years without activity",
  "rule": "dep_age_max",
  "threshold": 730,
  "action": "WARN",
  "description": "Warns on dependencies whose latest release is older than N days (heuristic — uses Maven Central last-updated)."
}
```

**Note:** This rule uses a heuristic based on version string patterns. For accurate age data,
enrich via Maven Central's `/solrsearch` API (`timestamp` field).

---

## P005 — Test Coverage Floor

```json
{
  "id": "P005",
  "name": "Test coverage floor",
  "rule": "coverage_min",
  "threshold": 80,
  "action": "WARN",
  "description": "Warns when JaCoCo line coverage average across validated PRs drops below the threshold."
}
```

**Override:** Set `"action": "FAIL"` to enforce as a hard gate. Raise/lower threshold as needed.

---

## P006 — No Leaked Secrets

```json
{
  "id": "P006",
  "name": "No leaked secrets",
  "rule": "secret_count_max",
  "threshold": 0,
  "min_severity": "HIGH",
  "action": "FAIL",
  "description": "Fails if the secret detection scan found any HIGH or CRITICAL severity findings."
}
```

**Override:** Set `"min_severity": "CRITICAL"` to only fail on critical secrets; `"threshold": 1`
to allow one warning-level finding.

---

## P007 — No Untrusted Artifact Sources

```json
{
  "id": "P007",
  "name": "No untrusted artifact sources",
  "rule": "untrusted_source_count",
  "threshold": 0,
  "action": "FAIL",
  "description": "Fails if the supply-chain audit found any artifacts not resolvable from approved sources."
}
```

**Override:** `"threshold": 5` to allow a small number of known internal artifacts before
adding them to the source allowlist.

---

## Override File Format (`policy.json`)

Place in the project root to override defaults:

```json
{
  "policy_version": "1.0",
  "project": "my-java-app",
  "rules": [
    { "id": "P001", "threshold": 10.0 },
    { "id": "P002", "action": "FAIL", "threshold": 5 },
    { "id": "P004", "enabled": false },
    {
      "id": "P008",
      "name": "No snapshot dependencies in production",
      "rule": "no_snapshots",
      "action": "FAIL",
      "enabled": true
    }
  ]
}
```

Only the fields you specify are overridden — unspecified fields keep their defaults.

---

## Custom Rule Types (addable via policy.json)

| Rule Type | Checks | Parameters |
|-----------|--------|-----------|
| `cvss_max` | Max CVSS score across all CVEs | `threshold` (float) |
| `high_count_max` | Count of CVSS ≥ 7.0 findings | `threshold` (int) |
| `license_blocklist` | Presence of blocked SPDX license IDs | `blocklist` (array) |
| `dep_age_max` | Dependency last-release age in days | `threshold` (int) |
| `coverage_min` | JaCoCo line coverage percentage | `threshold` (float) |
| `secret_count_max` | Secret finding count by severity | `threshold`, `min_severity` |
| `untrusted_source_count` | Untrusted artifact count | `threshold` (int) |
| `no_snapshots` | Presence of SNAPSHOT versions | — |
| `risk_score_max` | Max composite risk score from Stage 2 | `threshold` (float) |
