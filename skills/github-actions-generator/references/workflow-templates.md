# GitHub Actions Workflow Templates

## Template 1: Minimal (pom.xml changes only, no PR comments)

```yaml
name: Dependency Security Scan
on:
  push:
    paths: ['pom.xml']
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: |
          git clone https://github.com/<YOUR_ORG>/UC1.git /tmp/uc1
          python /tmp/uc1/pipeline-output/run_pipeline.py \
            "https://github.com/${{ github.repository }}"
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: security-results
          path: pipeline-output/dependency-health-report.html
```

---

## Template 2: Full (all triggers, PR comments, policy gate, Slack)

See SKILL.md Step 2 for the complete full template.

---

## Template 3: Scheduled-only (weekly scan, no push trigger)

```yaml
name: Weekly Security Scan
on:
  schedule:
    - cron: '0 2 * * 1'   # MonStage 02:00 UTC
  workflow_dispatch:

jobs:
  weekly-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: |
          git clone https://github.com/<YOUR_ORG>/UC1.git /tmp/uc1
          python /tmp/uc1/pipeline-output/run_pipeline.py \
            "https://github.com/${{ github.repository }}" \
            --token "${{ secrets.GITHUB_TOKEN }}"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: weekly-security-report-${{ github.run_number }}
          path: |
            pipeline-output/dependency-health-report.html
            pipeline-output/audit-trail.json
          retention-days: 365
```

---

## Template 4: Multi-repo scan (matrix strategy)

```yaml
name: Multi-Repo Security Scan
on:
  schedule:
    - cron: '0 3 * * 0'
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        repo:
          - https://github.com/MyOrg/service-a
          - https://github.com/MyOrg/service-b
          - https://github.com/MyOrg/service-c

    steps:
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: |
          git clone https://github.com/<YOUR_ORG>/UC1.git /tmp/uc1
          python /tmp/uc1/pipeline-output/run_pipeline.py \
            "${{ matrix.repo }}" \
            --token "${{ secrets.GITHUB_TOKEN }}"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: report-${{ strategy.job-index }}
          path: pipeline-output/dependency-health-report.html
```
