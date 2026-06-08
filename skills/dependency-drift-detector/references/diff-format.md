# Drift Report JSON Schema Reference

## drift-report.json

```json
{
  "snapshot_date": "<ISO-8601 — current scan time>",
  "baseline_date": "<ISO-8601 — previous baseline time | null if first run>",
  "project":       "<string>",
  "mode":          "DIFF | INIT",
  "summary": {
    "total_current":  "<int — deps in current scan>",
    "total_previous": "<int — deps in baseline | 0 if INIT>",
    "added":          "<int>",
    "removed":        "<int>",
    "upgraded":       "<int>",
    "downgraded":     "<int>",
    "unchanged":      "<int>",
    "risk_flags":     "<int — newly added or upgraded deps with CVEs>"
  },
  "added": [
    {
      "dependency": "<group:artifact>",
      "version":    "<string>",
      "scope":      "compile | test | provided | runtime",
      "purl":       "<pkg:maven/...>",
      "cve_count":  "<int | 0>",
      "top_cve":    "<CVE-ID | null>",
      "top_cvss":   "<float | 0>",
      "has_critical": "<boolean>"
    }
  ],
  "removed": [
    {
      "dependency":   "<group:artifact>",
      "last_version": "<string>",
      "scope":        "<string>"
    }
  ],
  "upgraded": [
    {
      "dependency":   "<group:artifact>",
      "from_version": "<string>",
      "to_version":   "<string>",
      "bump_type":    "MAJOR | MINOR | PATCH | UNKNOWN",
      "scope":        "<string>",
      "purl":         "<pkg:maven/...>",
      "cve_count":    "<int | 0>",
      "has_critical": "<boolean>"
    }
  ],
  "downgraded": [ "<same structure as upgraded>" ],
  "risk_flag":  "<boolean — true if any added/upgraded dep has CVEs>"
}
```

## dependency-baseline.json

```json
{
  "snapshot_date": "<ISO-8601>",
  "project":       "<string>",
  "dependencies": [
    {
      "key":     "<group:artifact>",
      "version": "<string>",
      "scope":   "<string>",
      "purl":    "<pkg:maven/...>"
    }
  ]
}
```

## bump_type Classification Logic

```python
def classify_version_change(old_v: str, new_v: str) -> str:
    """
    Compares two semantic version strings.
    Returns: MAJOR, MINOR, PATCH, DOWNGRADE, or UNKNOWN
    """
    try:
        def parse(v):
            parts = v.split(".")[:3]
            return [int(x) for x in parts] + [0] * (3 - len(parts))

        o, n = parse(old_v), parse(new_v)
        if n < o:   return "DOWNGRADE"
        if n[0] > o[0]: return "MAJOR"
        if n[1] > o[1]: return "MINOR"
        if n[2] > o[2]: return "PATCH"
        return "UNKNOWN"
    except (ValueError, AttributeError):
        return "UNKNOWN"
```

## Risk Flagging Logic

A dep is risk-flagged if:
- It was **added** in this scan AND has ≥ 1 CVE in the Stage 1 scan
- It was **upgraded** AND the new version introduced new CVEs not present in the previous version
- It was **downgraded** (any downgrade is automatically flagged — rollbacks can reintroduce CVEs)
