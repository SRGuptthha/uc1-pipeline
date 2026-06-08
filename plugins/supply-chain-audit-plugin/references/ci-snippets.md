# CI Integration Snippets — Supply-Chain Audit Plugin

All snippets rely on exit code 1 to fail the pipeline step — no CI-specific APIs needed.

---

## GitHub Actions

```yaml
name: Supply-Chain Audit

on: [pull_request]

jobs:
  supply-chain-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Syft
        run: curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

      - name: Generate SBOM
        run: syft dir:. --output cyclonedx-json=./sbom.cdx.json

      - name: Run Supply-Chain Audit
        run: python3 audit.py --sbom ./sbom.cdx.json --policy references/license-policy.md
        # Exit code 1 automatically fails this step and blocks the PR

      - name: Upload Audit Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: audit-report
          path: audit-report.json
```

---

## GitLab CI

```yaml
supply-chain-audit:
  stage: test
  image: ubuntu:22.04
  script:
    - curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
    - syft dir:. --output cyclonedx-json=./sbom.cdx.json
    - python3 audit.py --sbom ./sbom.cdx.json --policy references/license-policy.md
  artifacts:
    when: always
    paths:
      - audit-report.json
      - sbom.cdx.json
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

---

## Jenkins (Declarative Pipeline)

```groovy
pipeline {
  agent any
  stages {
    stage('Supply-Chain Audit') {
      steps {
        sh 'curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin'
        sh 'syft dir:. --output cyclonedx-json=./sbom.cdx.json'
        sh 'python3 audit.py --sbom ./sbom.cdx.json --policy references/license-policy.md'
      }
      post {
        always {
          archiveArtifacts artifacts: 'audit-report.json, sbom.cdx.json'
        }
      }
    }
  }
}
```

---

## Generic Shell (any pipeline)

```bash
#!/bin/bash
set -e  # Exit on first error

# Generate SBOM
syft dir:. --output cyclonedx-json=./sbom.cdx.json

# Run audit — exits 1 if violations found
python3 audit.py --sbom ./sbom.cdx.json --policy references/license-policy.md

echo "✅ Supply-chain audit passed"
```