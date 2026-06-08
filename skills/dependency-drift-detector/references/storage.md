# Baseline Storage Guide

## Default Storage Location

```
<pipeline-output-dir>/dependency-baseline.json
```

The baseline is co-located with other pipeline outputs so it persists between runs in the
same working directory.

---

## Multi-Project Support

If scanning multiple repos from the same working directory, use project-scoped baseline files:

```python
BASELINE_PATH = os.path.join(OUT, f"dependency-baseline-{project}.json")
```

This prevents baselines from different repos from overwriting each other.

---

## Baseline Rotation

By default, the baseline is updated after **every** run. To keep a rolling history:

```python
import shutil, datetime

def rotate_baseline(baseline_path):
    """Keep last 5 baselines as dated snapshots before overwriting."""
    if os.path.exists(baseline_path):
        date_str = datetime.date.today().isoformat()
        archive  = baseline_path.replace(".json", f"-{date_str}.json")
        # Keep only if no archive for today yet
        if not os.path.exists(archive):
            shutil.copy2(baseline_path, archive)
        # Prune archives older than 30 days
        archive_dir = os.path.dirname(baseline_path)
        for f in os.listdir(archive_dir):
            if f.startswith("dependency-baseline-20") and f.endswith(".json"):
                fpath = os.path.join(archive_dir, f)
                age_days = (datetime.date.today() - datetime.date.fromisoformat(
                    f.split("-baseline-")[1].replace(".json", ""))).days
                if age_days > 30:
                    os.remove(fpath)
```

---

## Resetting the Baseline

To force a fresh baseline (treat all current deps as "new"):

```bash
# Delete the baseline file
rm pipeline-output/dependency-baseline.json

# Next run will be in INIT mode — creates a new baseline from scratch
python run_pipeline.py <github-url>
```

---

## Git-tracking the Baseline

Commit the baseline to the repo so the CI pipeline always has an accurate starting point:

```bash
# .gitignore — DO track the baseline
# (remove from ignore list if present)
!pipeline-output/dependency-baseline.json

# After each pipeline run in CI, commit the updated baseline
git add pipeline-output/dependency-baseline.json
git commit -m "chore: update dependency baseline [skip ci]"
git push
```

The `[skip ci]` tag prevents a CI loop triggered by the baseline commit.

---

## Drift Alert Thresholds

Configure in `policy.json` to alert on large drift:

```json
{
  "id": "P008",
  "name": "Dependency drift alert",
  "rule": "drift_added_max",
  "threshold": 5,
  "action": "WARN",
  "description": "Warn when more than 5 new dependencies are added in a single scan"
}
```
