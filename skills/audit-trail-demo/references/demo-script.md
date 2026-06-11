# Live Demo Script — Audit Trail & Demo Readiness

Full talking-point narration for a live audience demo. Estimated total runtime: 25–40 min
depending on scan speed. Each stage has a setup note, audience line, and what to show.

---

## Opening (2 min)

**Say:**
> "Today I'm going to show you how we've automated the entire supply-chain security
> lifecycle for Java projects — from detecting a CVE to a verified, merged fix — without
> a human touching a single config file.
> We'll go from a deliberately vulnerable project to a clean, audited codebase in real time."

**Show:** The project's `pom.xml` — scroll through to highlight some obviously old version numbers.

---

## Stage 1 — Stage 1: CVE Detection (8–15 min)

**Setup:** Ensure NVD API key is set and DB is cached (pre-warm if possible).

**Say:**
> "First, let's find out what's lurking. We run OWASP Dependency-Check — it cross-references
> every dependency against the National Vulnerability Database."

**Run:**
```bash
dependency-check --project "live-demo" --scan . --format JSON \
  --out ./demo-stage1 --nvdApiKey $NVD_API_KEY
```

**While running, say:**
> "This is checking every JAR — direct and transitive — against hundreds of thousands
> of known CVEs. On a first run it downloads the NVD database; subsequent runs are
> much faster thanks to caching."

**When complete, show:** The CVE count in the terminal output. Then open the JSON and
highlight one Critical CVE — read the CVE ID and CVSS score to the audience.

**Say:**
> "That's [N] vulnerabilities. Let's find out which ones actually matter."

---

## Stage 2 — Stage 2: Risk Scoring (1–2 min)

**Say:**
> "Raw CVE counts don't tell you where to focus. Our risk scoring agent combines
> CVSS severity with how critical this library is to your business, whether it's a
> direct or transitive dependency, and how well-maintained the project is."

**Run:** Risk scorer (show the command briefly, then skip to results)

**Show:** The top 5 risk scores table — highlight the #1 entry with its composite score.

**Say:**
> "This [artifact] scores [X]/100 — it's a direct dependency in our payment module,
> it has a CVSS 9.8 CVE, and the last release was three years ago. That's why it's first."

---

## Stage 3 — Stage 3: Supply-Chain Audit (1–2 min)

**Say:**
> "CVEs are just one type of supply-chain risk. We also check for typosquatting —
> malicious packages with names almost identical to legitimate ones — untrusted artifact
> sources, and license violations that could expose us to legal risk."

**Run:** Syft + audit (show SBOM component count, then audit result)

**Show:** If any violations found — highlight one. If clean — say:
> "Clean bill of health on the supply-chain side. No suspicious packages, everything
> from Maven Central, all licenses compliant."

---

## Stage 4 — Stage 4: Auto-Remediation (2–3 min)

**Say:**
> "Now the interesting part — fixing them. Our remediation agent looks up the safest
> available version for each vulnerable dependency, verifies it against the NVD fix
> ranges, and generates a pull request with a full changelog summary."

**Show:** The upgrade plan table from the approval gate — walk through one row:
> "For [artifact], we're upgrading from [old] to [new]. That's a [MAJOR/MINOR/PATCH]
> bump — it fixes [CVE-ID] which had a CVSS of [score]. The PR description includes
> the relevant release notes and any breaking change warnings."

**Say:** "I'll approve all patch and minor upgrades. Major bumps I'll review manually."

**Action:** Type `"approve all — one PR per dep"` — show PRs being created.

---

## Stage 5 — Stage 5: PR Validation (5–10 min)

**Say:**
> "We don't just create PRs and hope for the best. Every PR goes through four gates:
> unit tests, a fresh OWASP scan to make sure we haven't introduced new CVEs,
> a Grype scan as a second opinion, and JaCoCo coverage to make sure we haven't
> broken any tests."

**Run:** Validation gates (show each gate result as it completes)

**Show:** The PR comment being posted — open the GitHub PR in the browser.

**Say:**
> "Patch and minor bumps that pass all four gates are merged automatically.
> Major bumps — like this Struts upgrade — wait for my explicit approval
> because they may have API changes."

---

## Stage 6 — Stage 7: The Report (2–3 min)

**Say:**
> "Finally, everything we just did is aggregated into a single audit report —
> an executive summary for leadership and a full technical appendix for the team."

**Show:** Open `dependency-health-report.html` in browser.

**Walk through:**
1. Health score: "We went from [N] critical CVEs to [M] — health score [X]/100, grade [G]."
2. KPI cards: "Fixed [N] CVEs, merged [M] PRs, [K]% average test coverage."
3. CVE donut: "Before — mostly red. After remediation — the critical slice is gone."
4. Switch to Technical tab: "The full CVE table, risk scores, validation results — all here."

**Close:**
> "That's the full pipeline — from vulnerable to verified in under [X] minutes,
> fully automated, with a complete audit trail. Any questions?"

---

## Audience Q&A Prep

| Likely Question | Answer |
|-----------------|--------|
| "What if a fix breaks the build?" | "Stage 5 gates catch that — if mvn test fails, the PR is blocked and we report exactly which tests failed." |
| "How do you handle false positives?" | "Stage 1 has a suppression XML mechanism. Stage 5's OWASP diff only flags net-new CVEs introduced by the upgrade, not pre-existing ones." |
| "What about non-Maven projects?" | "Stage 1 supports Node.js, Python, .NET, Ruby. Days 3–5 are Java/Maven-focused today but the architecture extends." |
| "Is this running in CI?" | "Yes — Stage 3's audit plugin exits code 1 on violations, which fails any CI step natively. No CI-specific integration needed." |
| "Who approves the major bumps?" | "A human always approves major version bumps — the agent flags the PR and waits. Patch and minor are auto-merged after all gates pass." |