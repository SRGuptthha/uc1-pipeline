# UC1 — Supply Chain Security Pipeline

## Project in one line
Single-file Python pipeline (`pipeline-output/run_pipeline.py`, ~2600 lines, stdlib only)
that scans GitHub repos for CVEs, audits supply chain, enforces policy, and creates
remediation PRs — across Java, Python, Node.js, .NET, Ruby, and Go.

## Key files
- `pipeline-output/run_pipeline.py` — main executable, all logic lives here
- `pipeline-output/test_pipeline.py` — 63 unit tests, run with `python test_pipeline.py`
- `pipeline-output/policy.json` — policy thresholds (editable)
- `pipeline-output/.gitleaks.toml` — secret detection allow-list
- `skills/audit-trail-demo/templates/report.html` — HTML dashboard template
- `SETUP.md` — first-run checklist
- `PIPELINE_GUIDE.md` — full end-to-end stage documentation

## Architecture decisions (do not undo)
- **stdlib only** — no pip installs, no external dependencies ever
- **Single file** — everything in run_pipeline.py; no splitting into modules
- **`_UC1_IMPORT_ONLY` env guard** — sits just before STEP 1; allows test_pipeline.py
  to import helpers without triggering network calls. Do not move it earlier (helpers
  must be defined first).
- **`_PIPELINE_STAGES` constant** — single source of truth for stage list used in
  two places. Do not duplicate it inline.
- **Helpers section** — pure functions (`cvss_severity`, `extract_cvss`, `bump_type`,
  `health_grade`, `lookup_latest_version_ecosystem`, `lookup_license_for_dep`,
  `is_license_blocked`, `patch_manifest`) live before the env guard so tests can use them.

## Ecosystem support
Language detection priority order: pom.xml → requirements.txt → pyproject.toml →
package.json → *.csproj → Gemfile → go.mod

`ECOSYSTEM_MAP = {"java-maven":"Maven","python":"PyPI","nodejs":"npm","dotnet":"NuGet","ruby":"RubyGems","go":"Go"}`

## Test isolation pattern
```python
# test_pipeline.py sets this BEFORE importing run_pipeline
os.environ["_UC1_IMPORT_ONLY"] = "1"
# run_pipeline.py exits cleanly at the guard, helpers are already defined
```

## Demo repo
`https://github.com/SRGuptha/uc1-security-demo` — pre-seeded with 7 vulnerable
Maven deps (Log4Shell, Spring4Shell, Text4Shell, H2 RCE, SnakeYAML DoS, etc.)

## Run commands
```powershell
# Dry-run
python pipeline-output/run_pipeline.py https://github.com/SRGuptha/uc1-security-demo

# Live (creates PR)
python pipeline-output/run_pipeline.py https://github.com/SRGuptha/uc1-security-demo --token ghp_xxx

# Unit tests only
python pipeline-output/test_pipeline.py
```

## What has been cleaned up (do not re-add)
- `findall()` helper — was defined but never called; removed
- `dep_map` dict — unused; removed
- `_blocked_lics` variable — unused; removed
- `LGPL_GROUPS` / `GPL_GROUPS` heuristic — replaced with real registry license lookup
- Duplicate `cvss_severity`/`extract_cvss`/`bump_type`/`health_grade` inline definitions
- `.svg-chart` CSS class in report.html — no SVG charts exist
- `import shutil as _shutil2` — duplicate import; using `_shutil_mod` throughout
