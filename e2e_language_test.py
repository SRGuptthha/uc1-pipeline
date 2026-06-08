#!/usr/bin/env python3
"""
UC1 Pipeline — End-to-End Language Coverage Test
Runs the pipeline (dry-run, no token) against one real GitHub repo per ecosystem.
Reports language detection, deps found, CVEs found, health grade, and elapsed time.
"""
import subprocess, tempfile, os, sys, json, time, shutil

PIPELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "pipeline-output", "run_pipeline.py")

# One repo per ecosystem — all public, manifest at repo root.
# .NET uses a local fixture (most .NET repos have .csproj in subdirs, not root).
TEST_CASES = [
    ("Java / Maven",    "java-maven",  "https://github.com/WebGoat/WebGoat"),
    ("Python / PyPI",   "python",      "https://github.com/scrapy/scrapy"),
    ("Node.js / npm",   "nodejs",      "https://github.com/expressjs/express"),
    (".NET / NuGet",    "dotnet",      "https://github.com/dotnet/dotnet-fixture-local"),
    ("Ruby / RubyGems", "ruby",        "https://github.com/sinatra/sinatra"),
    ("Go",              "go",          "https://github.com/gin-gonic/gin"),
]

# Seed a minimal .csproj into the .NET temp dir before running
DOTNET_CSPROJ = """\
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Newtonsoft.Json" Version="12.0.1" />
    <PackageReference Include="log4net" Version="2.0.10" />
    <PackageReference Include="Microsoft.AspNetCore.Server.Kestrel" Version="2.0.0" />
    <PackageReference Include="System.Text.RegularExpressions" Version="4.3.0" />
  </ItemGroup>
</Project>
"""

W = 80

def bar(char="-", n=W): return char * n

def section(title):
    print(f"\n{bar()}")
    print(f"  {title}")
    print(bar())

def run_test(label, expected_eco, url, tmpdir):
    """Run pipeline against url, return result dict."""
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, PIPELINE, url, "--out-dir", tmpdir],
        timeout=240,
    )
    elapsed = round(time.time() - t0, 1)

    result = {
        "label": label, "url": url, "expected": expected_eco,
        "success": proc.returncode == 0,
        "language": "—", "ecosystem": "—", "manifest": "—",
        "deps": "—", "cves": "—", "critical": "—", "high": "—",
        "grade": "—", "score": "—", "elapsed": elapsed,
        "lang_ok": False, "error": None,
    }

    # ── parse audit-trail.json ────────────────────────────────────────────────
    trail_path = os.path.join(tmpdir, "audit-trail.json")
    if os.path.exists(trail_path):
        try:
            with open(trail_path, encoding="utf-8") as f:
                trail = json.load(f)
            result["language"]  = trail.get("language", "—")
            result["ecosystem"] = trail.get("ecosystem", "—")
            result["manifest"]  = trail.get("manifest_filename", "—")
            ph = trail.get("pipeline_health", {})
            result["grade"] = ph.get("grade", "—")
            result["score"] = ph.get("score", "—")
        except Exception as e:
            result["error"] = f"audit-trail parse error: {e}"

    # ── parse dependency-check-report.json ───────────────────────────────────
    cve_path = os.path.join(tmpdir, "dependency-check-report.json")
    if os.path.exists(cve_path):
        try:
            with open(cve_path, encoding="utf-8") as f:
                cve_data = json.load(f)
            deps = cve_data.get("dependencies", [])
            result["deps"] = len(deps)
            all_cves = [v for d in deps for v in d.get("vulnerabilities", [])]
            result["cves"]     = len(all_cves)
            result["critical"] = sum(
                1 for v in all_cves
                if float((v.get("cvssv3") or {}).get("baseScore", 0)) >= 9.0)
            result["high"]     = sum(
                1 for v in all_cves
                if 7.0 <= float((v.get("cvssv3") or {}).get("baseScore", 0)) < 9.0)
        except Exception as e:
            result["error"] = f"CVE report parse error: {e}"

    result["lang_ok"] = (result["ecosystem"] == expected_eco or
                         result["language"]  == expected_eco)
    return result


# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*W}")
print(f"  UC1 Supply Chain Security Pipeline -- End-to-End Language Coverage Test")
print(f"  Mode: DRY-RUN (no GitHub token)   Repos: {len(TEST_CASES)}")
print(f"{'='*W}")

results = []
tmpdirs = []

for i, (label, eco, url) in enumerate(TEST_CASES, 1):
    tmpdir = tempfile.mkdtemp(prefix=f"uc1_e2e_{eco}_")
    tmpdirs.append(tmpdir)
    # Seed .NET fixture — place .csproj locally so detect_language uses it
    if eco == "dotnet":
        with open(os.path.join(tmpdir, "App.csproj"), "w") as f:
            f.write(DOTNET_CSPROJ)
    section(f"[{i}/{len(TEST_CASES)}]  {label}  →  {url}")
    print(f"  Output dir: {tmpdir}\n")

    try:
        r = run_test(label, eco, url, tmpdir)
    except subprocess.TimeoutExpired:
        r = {"label": label, "url": url, "expected": eco,
             "success": False, "language": "TIMEOUT", "ecosystem": "—",
             "manifest": "—", "deps": "—", "cves": "—",
             "critical": "—", "high": "—", "grade": "—", "score": "—",
             "elapsed": 240, "lang_ok": False, "error": "Timed out after 240s"}
    except Exception as e:
        r = {"label": label, "url": url, "expected": eco,
             "success": False, "language": "ERROR", "ecosystem": "—",
             "manifest": "—", "deps": "—", "cves": "—",
             "critical": "—", "high": "—", "grade": "—", "score": "—",
             "elapsed": 0, "lang_ok": False, "error": str(e)}

    results.append(r)
    status = "PASS" if r["success"] else "FAIL"
    print(f"\n  ── Quick result: {status}  |  Language detected: {r['language']}  "
          f"|  CVEs: {r['cves']}  |  Grade: {r['grade']}  "
          f"|  Time: {r['elapsed']}s")

# ── Clean up temp dirs ────────────────────────────────────────────────────────
for d in tmpdirs:
    try: shutil.rmtree(d)
    except: pass

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY TABLE
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n\n{'='*W}")
print(f"  E2E TEST SUMMARY")
print(f"{'='*W}")

HDR = (f"{'Ecosystem':<18} {'Manifest':<22} {'Deps':>5} "
       f"{'CVEs':>5} {'Crit':>5} {'High':>5} "
       f"{'Grade':>6} {'Score':>6} {'Time':>7}  {'Status'}")
print(HDR)
print(bar("─"))

for r in results:
    lang_flag = "" if r["lang_ok"] else " ⚠ wrong lang"
    status    = "PASS" if r["success"] else "FAIL"
    print(
        f"{r['label']:<18} "
        f"{str(r['manifest']):<22} "
        f"{str(r['deps']):>5} "
        f"{str(r['cves']):>5} "
        f"{str(r['critical']):>5} "
        f"{str(r['high']):>5} "
        f"{str(r['grade']):>6} "
        f"{str(r['score']):>6} "
        f"{str(r['elapsed']):>6}s  "
        f"{status}{lang_flag}"
    )

print(bar("─"))
passed  = sum(1 for r in results if r["success"])
lang_ok = sum(1 for r in results if r["lang_ok"])
total   = len(results)
print(f"\n  Pipeline run:       {passed}/{total} ecosystems completed successfully")
print(f"  Language detection: {lang_ok}/{total} ecosystems detected correctly")

total_elapsed = sum(r["elapsed"] for r in results)
print(f"  Total elapsed:      {round(total_elapsed, 1)}s  "
      f"({round(total_elapsed/60, 1)} min)")

if passed == total:
    print(f"\n  [PASS] ALL {total} ECOSYSTEMS PASSED")
else:
    failed = [r for r in results if not r["success"]]
    print(f"\n  [FAIL] {len(failed)} ecosystem(s) failed:")
    for r in failed:
        print(f"     - {r['label']}: {r.get('error') or 'pipeline returned non-zero'}")

print()
