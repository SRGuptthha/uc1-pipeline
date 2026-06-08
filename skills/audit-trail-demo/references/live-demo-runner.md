# Live Demo Runner — Audit Trail & Demo Readiness

Step-by-step invocation guide for live mode. Each stage includes estimated duration,
audience pause points, and what to show on screen.

---

## Pre-Demo Checklist

Before the audience arrives:

```bash
# 1. Pre-warm NVD database (avoid 15-min download during demo)
dependency-check --updateOnly --nvdApiKey $NVD_API_KEY
echo "NVD DB ready"

# 2. Verify all tools installed
dependency-check --version && echo "OWASP OK"
syft version         && echo "Syft OK"
grype version        && echo "Grype OK"
mvn --version        && echo "Maven OK"

# 3. Clone the demo repo fresh
git clone --depth 1 <DEMO_REPO_URL> /tmp/live-demo-repo
cd /tmp/live-demo-repo

# 4. Confirm it has vulnerable deps (quick check)
grep -c "version" pom.xml
echo "pom.xml ready"

# 5. Set env vars
export GITHUB_TOKEN=<token>
export NVD_API_KEY=<key>
```

---

## Stage Timings (Live Mode)

| Stage | Estimated Duration | Audience Action |
|-------|--------------------|-----------------|
| Setup + intro | 2 min | None |
| Stage 1 OWASP scan | 3–5 min (cached DB) | Watch terminal, ask questions |
| Stage 2 Risk scoring | 30s | None (fast) |
| Stage 3 Supply-chain audit | 1–2 min | None |
| Stage 4 Remediation plan | 1–2 min | User types "approve all" |
| Stage 5 Validation gates | 5–10 min | Watch gate results |
| Stage 7 Report reveal | 2–3 min | Browser screen share |
| Q&A | 5–10 min | — |
| **Total** | **~25–35 min** | |

---

## Narration Timing Cues

Use these cues to pace narration while tools run:

**During Stage 1 scan (3–5 min):**
- Explain what NVD is and how OWASP uses it (1 min)
- Explain direct vs transitive dependencies (1 min)
- Take audience questions (remaining time)

**During Stage 5 mvn test (2–5 min):**
- Explain why we re-run tests after upgrading (not just compile) (1 min)
- Explain JaCoCo coverage and the 80% threshold (1 min)
- Show the PR on GitHub while tests run (remaining time)

---

## Fallback Plan (if live run fails)

If any stage errors during the live demo:

1. **Stage 1 fails** (NVD timeout): Switch to replay mode — use pre-generated artifacts.
   Say: "Let me show you the results from our earlier run — same project, same output."

2. **Stage 4 GitHub API error** (token issue): Show the dry-run manifest instead.
   Say: "In a real run this creates the PRs automatically. Here's the upgrade plan it generated."

3. **Stage 5 mvn test fails** (test flakiness): Acknowledge it.
   Say: "This is exactly what the gate is for — it caught a test failure introduced by the
   upgrade. In practice we'd review the failure and fix the test before re-running."

Always have pre-generated artifacts at `/tmp/demo-artifacts/` as a fallback.