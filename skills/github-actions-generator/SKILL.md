---
name: github-actions-generator
description: >
  Auto-generate a production-ready .github/workflows/security-scan.yml that runs the full
  UC1 supply chain pipeline (CVE scan → SBOM → risk score → audit → secret detection →
  policy enforcement → auto-PR) on every push and pull request. Use this skill whenever
  the user wants to automate the security pipeline in CI/CD, generate a GitHub Actions
  workflow, set up automated dependency scanning, create a workflow file, configure PR gates,
  or integrate security scanning with GitHub. Trigger for requests like "generate a GitHub
  Actions workflow", "automate the pipeline in CI", "create a security-scan workflow",
  "add this to my CI", "set up automated scans", or "how do I run this on every PR?".
---

# GitHub Actions Workflow Generator

Generate a production-ready `.github/workflows/security-scan.yml` that runs the full UC1
supply chain security pipeline on every push and pull request. Configurable for any Java
Maven project with optional GitHub token for live PR creation.

---

## Workflow Triggers

The generated workflow runs on:
- **Push** to `main` / `master` / `develop`
- **Pull requests** targeting those branches
- **Weekly schedule** (SunStage 02:00 UTC) for proactive scanning even without code changes
- **Manual dispatch** (`workflow_dispatch`) with optional `github-url` input

---

## Workflow

### Step 1 — Understand the Context

Ask (or infer):
1. **Repo URL** — the GitHub repo to scan (can be self-referential or an external target)
2. **GitHub token** — does the user have a PAT with `repo` scope for PR creation?
3. **Fail threshold** — what CVSS score should fail the build? (default: 9.0)
4. **Notification target** — Slack webhook? Email? (default: none)
5. **Schedule** — keep weekly default or change frequency?

---

### Step 2 — Generate the Workflow File

Output a single `.github/workflows/security-scan.yml`:

```yaml
name: Supply Chain Security Scan

on:
  push:
    branches: [main, master, develop]
    paths:
      - 'pom.xml'
      - '.github/workflows/security-scan.yml'
  pull_request:
    branches: [main, master, develop]
  schedule:
    - cron: '0 2 * * 0'   # weekly, SunStage 02:00 UTC
  workflow_dispatch:
    inputs:
      github_url:
        description: 'GitHub repo URL to scan (defaults to this repo)'
        required: false
        default: ''
      create_prs:
        description: 'Create remediation PRs?'
        required: false
        default: 'true'
        type: boolean

jobs:
  security-scan:
    name: Security Pipeline
    runs-on: ubuntu-latest
    permissions:
      contents: write        # for PR creation
      pull-requests: write   # for PR creation
      security-events: write # for SARIF upload

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}

      - name: Install pipeline
        run: |
          # Clone the UC1 pipeline tooling
          git clone https://github.com/<YOUR_ORG>/UC1.git /tmp/uc1-pipeline
          pip install -r /tmp/uc1-pipeline/requirements.txt 2>/dev/null || true

      - name: Determine scan target
        id: target
        run: |
          URL="${{ inputs.github_url }}"
          if [ -z "$URL" ]; then
            URL="https://github.com/${{ github.repository }}"
          fi
          echo "url=$URL" >> $GITHUB_OUTPUT

      - name: Run Supply Chain Pipeline
        id: pipeline
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          POLICY_MAX_CVSS: '9.0'
          POLICY_MAX_HIGH_COUNT: '10'
        run: |
          python /tmp/uc1-pipeline/pipeline-output/run_pipeline.py \
            "${{ steps.target.outputs.url }}" \
            --token "$GITHUB_TOKEN"

      - name: Upload pipeline artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: security-pipeline-results-${{ github.run_number }}
          path: |
            pipeline-output/dependency-check-report.json
            pipeline-output/risk-scores.json
            pipeline-output/audit-report.json
            pipeline-output/sbom-cyclonedx.json
            pipeline-output/secret-scan-report.json
            pipeline-output/policy-report.json
            pipeline-output/drift-report.json
            pipeline-output/remediation-manifest.json
            pipeline-output/dependency-health-report.html
            pipeline-output/audit-trail.json
          retention-days: 90

      - name: Upload HTML report as Pages artifact
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: dependency-health-report
          path: pipeline-output/dependency-health-report.html

      - name: Check policy gate
        run: |
          python3 - <<'EOF'
          import json, sys
          try:
              report = json.load(open('pipeline-output/policy-report.json'))
              failures = [v for v in report.get('violations', []) if v.get('action') == 'FAIL']
              if failures:
                  print(f"❌ {len(failures)} policy violation(s) — build FAILED")
                  for v in failures:
                      print(f"  [{v['policy_id']}] {v['policy_name']}: {v['detail']}")
                  sys.exit(1)
              else:
                  print("✅ All policies passed")
          except FileNotFoundError:
              print("⚠️  policy-report.json not found — skipping gate")
          EOF

      - name: Comment PR with security summary
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            let body = '## 🔐 Security Scan Results\n\n';
            try {
              const trail = JSON.parse(fs.readFileSync('pipeline-output/audit-trail.json', 'utf8'));
              const health = trail.pipeline_health;
              body += `**Health Score:** ${health.score}/100 (Grade ${health.grade} — ${health.label})\n\n`;
              const findings = trail.key_findings || [];
              if (findings.length) {
                body += '### Key Findings\n';
                findings.forEach(f => { body += `- ${f}\n`; });
              }
            } catch(e) {
              body += '_Pipeline results not available._';
            }
            body += '\n\n_Generated by UC1 Supply Chain Security Pipeline_';
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body
            });
```

---

### Step 3 — Secrets Configuration

Inform the user which GitHub secrets to configure:

| Secret | Required | Purpose |
|--------|----------|---------|
| `GITHUB_TOKEN` | Auto-provided | PR creation, PR commenting |
| `SLACK_WEBHOOK_URL` | Optional | Slack notifications |
| `NVD_API_KEY` | Optional | Faster NVD data fetching (avoids rate limits) |

```bash
# Add optional secrets via GitHub CLI
gh secret set SLACK_WEBHOOK_URL --body "https://hooks.slack.com/services/..."
gh secret set NVD_API_KEY --body "your-nvd-api-key"
```

---

### Step 4 — Slack Notification Step (optional)

If the user wants Slack notifications, append this step after the policy gate:

```yaml
      - name: Notify Slack
        if: always() && secrets.SLACK_WEBHOOK_URL != ''
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Security scan for *${{ github.repository }}*",
              "attachments": [{
                "color": "${{ job.status == 'success' && '#36a64f' || '#ff0000' }}",
                "fields": [
                  {"title": "Status", "value": "${{ job.status }}", "short": true},
                  {"title": "Branch", "value": "${{ github.ref_name }}", "short": true},
                  {"title": "Run", "value": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}", "short": false}
                ]
              }]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          SLACK_WEBHOOK_TYPE: INCOMING_WEBHOOK
```

---

### Step 5 — Approval Gate ⛔

After generating the workflow, present for review:

```
---
⛔ Workflow generated — review required

File: .github/workflows/security-scan.yml

Configuration:
  • Triggers     : push (pom.xml changes), PR, weekly schedule, manual
  • Policy gate  : fail on CVSS ≥ 9.0
  • Artifacts    : 90-day retention, all pipeline outputs
  • PR commenting: ✅ enabled
  • Slack        : ❌ not configured (add SLACK_WEBHOOK_URL secret to enable)

Reply with one of:
  • "approve"                   — write the file to .github/workflows/
  • "add slack [webhook-url]"   — include Slack notification step
  • "change threshold to [N]"   — adjust CVSS fail threshold
  • "weekly only"               — remove push/PR triggers, keep only schedule
  • "stop here"                 — show the YAML only, don't write it
---
```

---

### Step 6 — Write & Commit

After approval, write and optionally commit:

```bash
mkdir -p .github/workflows
cat > .github/workflows/security-scan.yml << 'YAML'
<GENERATED_YAML>
YAML

# Commit if desired
git add .github/workflows/security-scan.yml
git commit -m "ci: add UC1 supply chain security scan workflow"
git push
```

---

## Output Files

| File | Purpose |
|------|---------|
| `.github/workflows/security-scan.yml` | CI workflow — commit to the target repo |

---

## Reference Files

- `references/workflow-templates.md` — Full workflow YAML variants (minimal, full, scheduled-only)
- `references/configuration.md` — All configurable env vars, secrets, and trigger options
- `references/pr-commenting.md` — PR comment formatting and GitHub Actions Script examples
