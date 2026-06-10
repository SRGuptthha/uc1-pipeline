"""
UC1 Supply Chain Security — MCP Server
Exposes the pipeline as 8 Claude-callable tools.
Run: python pipeline-output/mcp_server.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

HERE     = Path(__file__).parent
PIPELINE = HERE / "run_pipeline.py"
OUT_DIR  = HERE  # pipeline writes output files here

mcp = FastMCP("supply-chain-security")


def _run_pipeline(repo_url: str, token: str | None = None, scan_only: bool = True,
                  timeout: int = 300) -> dict:
    """Run run_pipeline.py as a subprocess and return parsed audit-trail.json."""
    cmd = [sys.executable, str(PIPELINE), repo_url, "--out-dir", str(OUT_DIR)]
    if token:
        cmd += ["--token", token]
    if scan_only:
        cmd += ["--scan-only"]

    env = os.environ.copy()
    env.pop("_UC1_IMPORT_ONLY", None)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env,
                                timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": f"Pipeline timed out after {timeout}s. "
                         "Try a smaller repo or increase the timeout."}
    except Exception as exc:
        return {"error": f"Failed to launch pipeline: {exc}"}

    audit_path = OUT_DIR / "audit-trail.json"
    if audit_path.exists():
        try:
            with open(audit_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            return {"error": f"Could not parse audit-trail.json: {exc}"}

    return {
        "error": "Pipeline did not produce audit-trail.json",
        "stdout": result.stdout[-3000:],
        "stderr": result.stderr[-2000:],
        "returncode": result.returncode,
    }


def _read_json(filename: str) -> dict:
    path = OUT_DIR / filename
    if not path.exists():
        return {"error": f"{filename} not found — run scan_repo first"}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def scan_repo(repo_url: str, token: str = "", timeout: int = 300) -> str:
    """
    Scan a GitHub repository for CVEs, generate health report and policy status.
    Dry-run (no PRs created). Returns health grade, CVE summary and key findings.

    Args:
        repo_url: Full GitHub URL, e.g. https://github.com/owner/repo
        token:    Optional GitHub PAT (improves rate limits; not required for public repos)
        timeout:  Max seconds to wait for the pipeline (default 300)
    """
    data = _run_pipeline(repo_url, token or None, scan_only=True, timeout=timeout)
    if "error" in data:
        return f"Pipeline error: {data['error']}\n\nStdout:\n{data.get('stdout','')}"

    health  = data.get("pipeline_health", {})
    cve_sum = data.get("stage1_cve_scan", {}).get("cve_summary", {})
    policy  = data.get("stage6_policy_gate", {})
    findings = data.get("key_findings", [])

    lines = [
        f"Repo    : {data.get('github_url', repo_url)}",
        f"Language: {data.get('language','?')} / {data.get('ecosystem','?')}",
        "",
        f"Health Grade : {health.get('grade','?')}  ({health.get('score','?')}/100)  {health.get('label','')}",
        "",
        "CVE Summary:",
        f"  Total    : {cve_sum.get('total_cves', 0)}",
        f"  Critical : {cve_sum.get('critical_count', 0)}",
        f"  High     : {cve_sum.get('high_count', 0)}",
        f"  Medium   : {cve_sum.get('medium_count', 0)}",
        "",
        f"Policy Gate  : {policy.get('result', 'N/A')}",
    ]
    if findings:
        lines += ["", "Key Findings:"] + [f"  • {f}" for f in findings]

    return "\n".join(lines)


@mcp.tool()
def get_health_report(repo_url: str = "") -> str:
    """
    Return the dependency health report from the most recent scan.
    Run scan_repo first to get fresh results.

    Args:
        repo_url: Optional — shown in output for context only
    """
    data = _read_json("audit-trail.json")
    if "error" in data:
        return data["error"]

    health = data.get("pipeline_health", {})
    stages = {k: v for k, v in data.items() if k.startswith("stage")}

    lines = [
        f"Project : {data.get('project','?')}",
        f"Repo    : {data.get('github_url','?')}",
        f"Scanned : {data.get('generated_date','?')}",
        "",
        f"Grade  : {health.get('grade','?')}",
        f"Score  : {health.get('score','?')} / 100  ({health.get('label','')})",
        f"Before : {health.get('score_before_remediation','?')} / 100",
        f"After  : {health.get('score_after_remediation','?')} / 100",
        f"Gain   : +{health.get('improvement','?')} points",
        "",
        "Stage Results:",
    ]
    for stage, info in stages.items():
        label = stage.replace("_", " ").title()
        artifact = info.get("artifact", "")
        lines.append(f"  {label}: {artifact}")

    return "\n".join(lines)


@mcp.tool()
def get_cve_summary(repo_url: str = "") -> str:
    """
    Return detailed CVE findings from the most recent scan.
    Run scan_repo first to get fresh results.

    Args:
        repo_url: Optional — shown in output for context only
    """
    data = _read_json("dependency-check-report.json")
    if "error" in data:
        return data["error"]

    vulns = data.get("vulnerabilities", [])
    if not vulns:
        return "No CVEs found in the most recent scan."

    lines = [f"CVEs found: {len(vulns)}", ""]
    for v in sorted(vulns, key=lambda x: x.get("cvss", 0), reverse=True):
        cvss = v.get("cvss", "?")
        sev  = v.get("severity", "?")
        cve  = v.get("cve_id", v.get("id", "?"))
        pkg  = v.get("package", v.get("artifact", "?"))
        ver  = v.get("version", "")
        fix  = v.get("fixed_version", "")
        desc = v.get("description", "")[:120]
        lines.append(f"[{sev}] CVSS {cvss}  {cve}")
        lines.append(f"  Package : {pkg} {ver}")
        if fix:
            lines.append(f"  Fix     : upgrade to {fix}")
        if desc:
            lines.append(f"  Summary : {desc}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def get_policy_status(repo_url: str = "") -> str:
    """
    Return policy gate results from the most recent scan.
    Run scan_repo first to get fresh results.

    Args:
        repo_url: Optional — shown in output for context only
    """
    data = _read_json("policy-report.json")
    if "error" in data:
        return data["error"]

    summary    = data.get("summary", {})
    violations = data.get("violations", [])
    warnings   = data.get("warnings", [])
    overall    = data.get("overall_result", "?")

    lines = [
        f"Overall : {overall}",
        f"Rules evaluated : {summary.get('rules_evaluated', '?')}",
        f"Passed          : {summary.get('rules_passed', '?')}",
        f"Violations      : {summary.get('violations', 0)}",
        f"Warnings        : {summary.get('warnings', 0)}",
    ]
    if violations:
        lines += ["", "VIOLATIONS (build fails):"]
        for v in violations:
            lines.append(f"  [{v.get('policy_id','?')}] {v.get('policy_name','?')}")
            lines.append(f"    {v.get('detail','')}")
    if warnings:
        lines += ["", "WARNINGS:"]
        for w in warnings:
            lines.append(f"  [{w.get('policy_id','?')}] {w.get('policy_name','?')}")
            lines.append(f"    {w.get('detail','')}")

    return "\n".join(lines)


@mcp.tool()
def create_remediation_prs(repo_url: str, token: str) -> str:
    """
    Run a live pipeline scan and create fix PRs on the target repo.
    Requires a GitHub PAT with contents + pull_requests write access.

    Args:
        repo_url: Full GitHub URL of the repo to remediate
        token:    GitHub PAT with write access to the target repo
    """
    if not token:
        return "Error: token is required to create PRs."

    data = _run_pipeline(repo_url, token, scan_only=False)
    if "error" in data:
        return f"Pipeline error: {data['error']}\n\nStdout:\n{data.get('stdout','')}"

    stage5 = data.get("stage5_auto_remediation", {})
    prs    = stage5.get("prs_created", [])
    health = data.get("pipeline_health", {})

    if not prs:
        return (
            f"Pipeline ran successfully but no PRs were created.\n"
            f"Health grade: {health.get('grade','?')}  ({health.get('score','?')}/100)\n"
            f"This may mean all dependencies are already up-to-date."
        )

    lines = [
        f"Created {len(prs)} remediation PR(s):",
        "",
    ]
    for pr in prs:
        lines.append(f"  {pr.get('artifact', '?')}")
        lines.append(f"  → {pr.get('pr_url', '?')}")
        lines.append("")

    lines += [
        f"Health after remediation: {health.get('grade','?')}  ({health.get('score','?')}/100)",
    ]
    return "\n".join(lines)


@mcp.tool()
def get_sbom(repo_url: str = "") -> str:
    """
    Return the CycloneDX SBOM component list from the most recent scan.
    Run scan_repo first to get fresh results.

    Args:
        repo_url: Optional — shown in output for context only
    """
    data = _read_json("sbom-cyclonedx.json")
    if "error" in data:
        return data["error"]

    components = data.get("components", [])
    metadata   = data.get("metadata", {})
    component_meta = metadata.get("component", {})

    lines = [
        f"SBOM Format : CycloneDX {data.get('specVersion', '?')}",
        f"Project     : {component_meta.get('name', '?')} {component_meta.get('version', '')}",
        f"Components  : {len(components)}",
        "",
    ]
    for c in components:
        purl = c.get("purl", "")
        name = c.get("name", "?")
        ver  = c.get("version", "?")
        lic_list = c.get("licenses", [])
        lic = lic_list[0].get("license", {}).get("id", "?") if lic_list else "?"
        lines.append(f"  {name} @ {ver}  (license: {lic})")
        if purl:
            lines.append(f"    purl: {purl}")

    return "\n".join(lines)


@mcp.tool()
def get_drift_report(repo_url: str = "") -> str:
    """
    Return the dependency drift report (added / removed / changed deps vs baseline).
    Run scan_repo first to get fresh results.

    Args:
        repo_url: Optional — shown in output for context only
    """
    data = _read_json("drift-report.json")
    if "error" in data:
        return data["error"]

    added   = data.get("added",   [])
    removed = data.get("removed", [])
    changed = data.get("changed", [])
    summary = data.get("summary", {})

    lines = [
        f"Drift Report  —  {data.get('scan_date', '?')}",
        f"Baseline date : {data.get('baseline_date', 'n/a')}",
        f"Added: {len(added)}  Removed: {len(removed)}  Changed: {len(changed)}",
        f"Drift score   : {summary.get('drift_score', '?')}",
        "",
    ]
    if added:
        lines.append("ADDED:")
        for d in added:
            lines.append(f"  + {d.get('artifact', d.get('name', '?'))} @ {d.get('version', '?')}")
    if removed:
        lines.append("REMOVED:")
        for d in removed:
            lines.append(f"  - {d.get('artifact', d.get('name', '?'))} @ {d.get('version', '?')}")
    if changed:
        lines.append("CHANGED:")
        for d in changed:
            lines.append(f"  ~ {d.get('artifact', d.get('name', '?'))}: "
                         f"{d.get('old_version', '?')} → {d.get('new_version', '?')}")
    if not (added or removed or changed):
        lines.append("No drift detected — dependency set matches baseline.")

    return "\n".join(lines)


@mcp.tool()
def update_policy(field: str, value: str) -> str:
    """
    Update a single field in policy.json and return the new policy.
    Numeric strings are cast to numbers automatically.

    Supported fields: max_critical_cves, max_high_cves, blocked_licenses,
    allow_snapshot_versions, require_jacoco_coverage_pct, max_composite_risk_score,
    auto_merge_bump_types, block_major_auto_merge, trusted_group_prefixes.

    Args:
        field: The policy.json key to update
        value: New value as a string (lists: comma-separated; booleans: true/false)
    """
    policy_path = OUT_DIR / "policy.json"
    if not policy_path.exists():
        return f"policy.json not found at {policy_path}"

    with open(policy_path, encoding="utf-8") as f:
        policy = json.load(f)

    ALLOWED = {
        "max_critical_cves", "max_high_cves", "blocked_licenses",
        "allow_snapshot_versions", "require_jacoco_coverage_pct",
        "max_composite_risk_score", "auto_merge_bump_types",
        "block_major_auto_merge", "trusted_group_prefixes",
    }
    if field not in ALLOWED:
        return (f"Unknown field '{field}'. Allowed fields: "
                + ", ".join(sorted(ALLOWED)))

    # Parse the value based on existing type or heuristics
    existing = policy.get(field)
    if isinstance(existing, bool) or value.lower() in ("true", "false"):
        parsed = value.lower() == "true"
    elif isinstance(existing, (int, float)):
        try:
            parsed = int(value) if "." not in value else float(value)
        except ValueError:
            return f"Field '{field}' expects a number; got '{value}'"
    elif isinstance(existing, list):
        parsed = [v.strip() for v in value.split(",") if v.strip()]
    else:
        try:
            parsed = int(value)
        except ValueError:
            try:
                parsed = float(value)
            except ValueError:
                parsed = value

    old_value = policy.get(field, "<not set>")
    policy[field] = parsed

    with open(policy_path, "w", encoding="utf-8") as f:
        json.dump(policy, f, indent=2)

    return (f"Updated policy.json:\n"
            f"  {field}: {old_value!r} → {parsed!r}\n\n"
            f"Run scan_repo to apply the new policy to the next scan.")


if __name__ == "__main__":
    mcp.run()
