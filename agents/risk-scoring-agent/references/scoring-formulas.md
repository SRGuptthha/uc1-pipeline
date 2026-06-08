# Scoring Formulas — Risk Scoring Agent

## Composite Risk Score Formula

```
composite_score = (
  (cvss_factor   * 0.40) +
  (biz_factor    * 0.30) +
  (exposure_factor * 0.20) +
  (maintenance_factor * 0.10)
) * 100
```

Round to one decimal place.

---

## Factor 1: CVSS Severity (weight 40%)

Use the **highest CVSS v3 baseScore** across all CVEs for the dependency.
If only CVSS v2 is available, multiply by 0.9 as a conservative approximation.
If no CVEs exist, score = 0.

```
cvss_factor = max_cvss_score / 10.0
```

| CVSS Score | cvss_factor |
|------------|-------------|
| 9.0–10.0   | 0.90–1.00   |
| 7.0–8.9    | 0.70–0.89   |
| 4.0–6.9    | 0.40–0.69   |
| 0.1–3.9    | 0.01–0.39   |
| 0.0 (none) | 0.00        |

---

## Factor 2: Business Criticality (weight 30%)

Map user-provided tags to a factor score:

| Tag | biz_factor | Rationale |
|-----|-----------|-----------|
| `payment` | 1.00 | Highest impact — financial data |
| `auth` | 1.00 | Highest impact — identity/access |
| `core` | 0.90 | Central business logic |
| `public-api` | 0.85 | External-facing surface |
| `data-storage` | 0.80 | Persistence layer |
| `internal-api` | 0.60 | Internal service boundary |
| `logging` | 0.40 | Supporting infrastructure |
| `test` | 0.10 | Test-scope only |
| (untagged) | 0.50 | Neutral default |

Multiple tags: use the **highest** factor among all assigned tags.

---

## Factor 3: Dependency Exposure (weight 20%)

Determined from the OWASP JSON `isVirtual` field and Maven dependency tree depth.

| Exposure Type | exposure_factor | How to Detect |
|---------------|----------------|---------------|
| Direct | 1.00 | `isVirtual = false` AND depth = 1 in tree |
| Transitive (depth 2) | 0.65 | `isVirtual = false`, depth = 2 |
| Transitive (depth 3+) | 0.40 | `isVirtual = false`, depth ≥ 3 |
| Virtual/Provided | 0.20 | `isVirtual = true` |

If dependency tree depth is unavailable, use:
- `isVirtual = false` → exposure_factor = 0.80 (assume mixed)
- `isVirtual = true`  → exposure_factor = 0.20

---

## Factor 4: Maintenance Status (weight 10%)

Score based on artifact age and recency of the last published release.
Use the artifact version's release date from Maven Central metadata where available;
otherwise estimate from version string patterns.

| Condition | maintenance_factor |
|-----------|--------------------|
| Released < 6 months ago | 0.10 (well maintained) |
| Released 6–12 months ago | 0.30 |
| Released 1–2 years ago | 0.50 |
| Released 2–4 years ago | 0.70 |
| Released > 4 years ago | 1.00 (stale/unmaintained) |

If release date cannot be determined, default to **0.50**.

To check Maven Central release date (bash):
```bash
GROUP=$(echo "$GAV" | cut -d: -f1 | tr '.' '/')
ARTIFACT=$(echo "$GAV" | cut -d: -f2)
VERSION=$(echo "$GAV" | cut -d: -f3)
curl -s "https://search.maven.org/solrsearch/select?q=g:${GROUP}+AND+a:${ARTIFACT}+AND+v:${VERSION}&rows=1&wt=json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['response']['docs']; print(d[0]['timestamp'] if d else 'UNKNOWN')"
```

---

## Score → Risk Tier Mapping

| Composite Score | Risk Tier | Action |
|-----------------|-----------|--------|
| 80–100 | 🔴 Critical | Fix immediately, block deployment |
| 60–79  | 🟠 High     | Fix within current sprint |
| 40–59  | 🟡 Medium   | Fix in next release cycle |
| 0–39   | 🟢 Low      | Track, fix when convenient |