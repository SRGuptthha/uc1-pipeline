---
name: dependency-drift-detector
description: >
  Compare the current pom.xml (or other manifest) against the last saved baseline to surface
  newly added, removed, and upgraded dependencies since the previous audit. Integrates as Stage
  3.9 in the UC1 supply chain pipeline. Use this skill whenever the user wants to detect
  dependency changes between scans, find what was added or upgraded since last audit, track
  dependency drift over time, compare current and previous dependency snapshots, or get
  notified of silent dependency additions. Trigger for requests like "what changed since last
  scan?", "detect dependency drift", "compare against baseline", "what's new in my deps?",
  "diff my dependencies", "track dependency changes", or "what was added or removed?".
---

# Dependency Drift Detector — Stage 3.9

Compare the current dependency manifest against the last saved baseline snapshot to identify:
- **New** dependencies added since the last scan
- **Removed** dependencies no longer present
- **Upgraded** dependencies with version changes
- **Downgraded** dependencies (potentially risky rollbacks)

Saves a new baseline after each run so the next scan has an accurate starting point.

---

## Workflow

### Step 1 — Locate Baseline

Look for a saved baseline at the default path:

```
./dependency-baseline.json
```

If no baseline exists, this is the **first run** — create the baseline and report it.
If a baseline exists, compare it against the current dependency list.

```python
import os, json

BASELINE_PATH = "dependency-baseline.json"

if os.path.exists(BASELINE_PATH):
    with open(BASELINE_PATH, encoding="utf-8") as f:
        baseline = json.load(f)
    print(f"Baseline found: {baseline['snapshot_date']}  ({len(baseline['dependencies'])} deps)")
    mode = "DIFF"
else:
    print("No baseline found — first run, creating initial baseline")
    mode = "INIT"
```

---

### Step 2 — Parse Current Dependencies

If running as part of the pipeline, the current dependency list is already in memory.
If running standalone, parse from the manifest:

```python
def load_current_deps(pom_path):
    """Parse pom.xml and return a normalized dep map: 'group:artifact' -> version."""
    from pipeline_utils import parse_pom  # UC1 shared parser
    deps, _ = parse_pom(open(pom_path).read())
    return {
        f"{d['group']}:{d['artifact']}": {
            "version": d["version"],
            "scope":   d["scope"],
            "test":    d["test"],
            "purl":    d["purl"],
        }
        for d in deps
    }

current_dep_map = load_current_deps("pom.xml")
```

---

### Step 3 — Diff Against Baseline

```python
def compute_drift(baseline_deps, current_deps):
    """
    baseline_deps: list of {"key": "group:artifact", "version": "x.y.z", "scope": "..."}
    current_deps:  dict of "group:artifact" -> {"version": ..., "scope": ...}
    """
    prev = {d["key"]: d for d in baseline_deps}
    curr = current_deps   # dict

    added    = []
    removed  = []
    upgraded = []
    downgraded = []
    unchanged  = []

    all_keys = set(prev.keys()) | set(curr.keys())

    for key in sorted(all_keys):
        in_prev = key in prev
        in_curr = key in curr

        if in_curr and not in_prev:
            added.append({
                "dependency": key,
                "version":    curr[key]["version"],
                "scope":      curr[key].get("scope", "compile"),
                "purl":       curr[key].get("purl", ""),
            })

        elif in_prev and not in_curr:
            removed.append({
                "dependency":   key,
                "last_version": prev[key]["version"],
                "scope":        prev[key].get("scope", "compile"),
            })

        elif in_prev and in_curr:
            pv = prev[key]["version"]
            cv = curr[key]["version"]
            if pv != cv:
                direction = classify_version_change(pv, cv)
                entry = {
                    "dependency":   key,
                    "from_version": pv,
                    "to_version":   cv,
                    "bump_type":    direction,
                    "scope":        curr[key].get("scope", "compile"),
                    "purl":         curr[key].get("purl", ""),
                }
                if direction == "DOWNGRADE":
                    downgraded.append(entry)
                else:
                    upgraded.append(entry)
            else:
                unchanged.append(key)

    return added, removed, upgraded, downgraded, unchanged


def classify_version_change(old_v, new_v):
    """Returns MAJOR, MINOR, PATCH, DOWNGRADE, or UNKNOWN."""
    try:
        def parts(v):
            return [int(x) for x in v.split(".")[:3]]
        o, n = parts(old_v), parts(new_v)
        # Pad to 3 parts
        while len(o) < 3: o.append(0)
        while len(n) < 3: n.append(0)
        if n < o:   return "DOWNGRADE"
        if n[0] > o[0]: return "MAJOR"
        if n[1] > o[1]: return "MINOR"
        if n[2] > o[2]: return "PATCH"
        return "UNKNOWN"
    except Exception:
        return "UNKNOWN"
```

---

### Step 4 — CVE Cross-Reference (if Stage 1 output available)

For each newly added or upgraded dependency, check whether it has known CVEs in the current scan:

```python
def enrich_with_cves(dep_list, cve_report):
    """Add CVE count to each dep entry that has CVEs in the current scan."""
    if not cve_report:
        return dep_list
    # Build a purl → [cves] index from the scan report
    vuln_index = {}
    for d in cve_report.get("dependencies", []):
        purl = (d.get("packages") or [{}])[0].get("id", "")
        vuln_index[purl] = d.get("vulnerabilities", [])
    for dep in dep_list:
        purl = dep.get("purl", "")
        cves = vuln_index.get(purl, [])
        if cves:
            dep["cve_count"]    = len(cves)
            dep["top_cve"]      = cves[0]["name"] if cves else None
            dep["top_cvss"]     = cves[0].get("cvssv3", {}).get("baseScore", 0) if cves else 0
            dep["has_critical"] = any(
                float((v.get("cvssv3") or {}).get("baseScore", 0)) >= 9.0 for v in cves)
    return dep_list
```

---

### Step 5 — Generate Drift Report

```json
{
  "snapshot_date": "<ISO-DATE>",
  "baseline_date": "<ISO-DATE>",
  "project": "<PROJECT_NAME>",
  "mode": "DIFF | INIT",
  "summary": {
    "total_current":  42,
    "total_previous": 40,
    "added":          3,
    "removed":        1,
    "upgraded":       4,
    "downgraded":     0,
    "unchanged":      35
  },
  "added": [
    {
      "dependency": "com.example:new-lib",
      "version": "2.0.0",
      "scope": "compile",
      "cve_count": 2,
      "top_cve": "CVE-2024-12345",
      "top_cvss": 8.5,
      "has_critical": false
    }
  ],
  "removed": [
    { "dependency": "org.legacy:old-lib", "last_version": "1.0.0", "scope": "compile" }
  ],
  "upgraded": [
    {
      "dependency": "org.springframework:spring-core",
      "from_version": "5.3.20",
      "to_version": "6.1.4",
      "bump_type": "MAJOR",
      "has_critical": false
    }
  ],
  "downgraded": [],
  "risk_flag": false
}
```

---

### Step 6 — Generate Markdown Summary

```markdown
## 📊 Dependency Drift Report — <PROJECT_NAME>
**Snapshot date:** <NOW> | **Baseline date:** <PREV> | **Mode:** DIFF

### Changes Since Last Scan

| Change Type | Count |
|-------------|-------|
| ➕ Added    | 3 |
| ➖ Removed  | 1 |
| ⬆️ Upgraded | 4 |
| ⬇️ Downgraded | 0 |
| ✅ Unchanged | 35 |

### ➕ Newly Added Dependencies
| Dependency | Version | Scope | CVEs |
|------------|---------|-------|------|
| `com.example:new-lib` | 2.0.0 | compile | ⚠️ 2 (HIGH: CVE-2024-12345) |

### ⬆️ Upgraded Dependencies
| Dependency | From | To | Bump |
|------------|------|----|------|
| `spring-core` | 5.3.20 | 6.1.4 | MAJOR ⚠️ |

### ⚠️ Risk Flags
- `com.example:new-lib` is newly added and has 2 CVEs — review before merging.
- `spring-core` received a MAJOR upgrade — verify compatibility.
```

---

### Step 7 — Save New Baseline

After reporting drift, always save the current state as the new baseline:

```python
new_baseline = {
    "snapshot_date": SCAN_DATE,
    "project":       project,
    "dependencies": [
        {
            "key":     f"{d['group']}:{d['artifact']}",
            "version": d["version"],
            "scope":   d["scope"],
            "purl":    d["purl"],
        }
        for d in compile_deps
    ],
}
with open(BASELINE_PATH, "w", encoding="utf-8") as f:
    json.dump(new_baseline, f, indent=2)
print(f"Baseline updated: {len(compile_deps)} dependencies saved")
```

---

### Step 8 — Approval Gate ⛔ STOP

```
---
⛔ Drift detection complete — review required

Changes since <BASELINE_DATE>:
  Added:    X  |  Removed:  Y  |  Upgraded: Z  |  Downgraded: W

⚠️ Risk flags: <N> (newly added deps with CVEs)

Reply with one of:
  • "approve"                 — accept drift report, update baseline, continue
  • "show added details"      — list all newly added deps with full metadata
  • "show upgraded details"   — list all upgrades with version diff
  • "reset baseline"          — discard current baseline, start fresh
  • "stop here"               — keep report without updating baseline
---
```

---

## Output Files

| File | Format | Consumer |
|------|--------|----------|
| `drift-report.json` | JSON | HTML report, audit trail |
| `dependency-baseline.json` | JSON | Next scan's diff starting point |
| Markdown summary | Chat / stdout | Human |

---

## Reference Files

- `references/diff-format.md` — Drift report JSON schema, version classification logic
- `references/storage.md` — Baseline file location, multi-project support, baseline reset guide
- `references/cicd.md` — Integrating drift detection alerts into Slack/Teams notifications
