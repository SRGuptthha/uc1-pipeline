# CI/CD Integration

## Key Principles for All Pipelines
- **Cache the NVD database** — saves 10–15 min per run
- **Store NVD API key as a secret** — never hardcode it
- **Fail on CVSS >= 7** for High/Critical gating
- **Archive reports as artifacts** for auditability
- **Run on PRs and main branch** at minimum

---

## GitHub Actions

```yaml
name: Dependency Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday

jobs:
  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Cache NVD Database
        uses: actions/cache@v4
        with:
          path: ~/.dependency-check/data
          key: nvd-db-${{ github.run_id }}
          restore-keys: nvd-db-

      - name: Run OWASP Dependency-Check
        uses: dependency-check/Dependency-Check_Action@main
        with:
          project: ${{ github.repository }}
          path: '.'
          format: 'HTML JSON'
          out: 'reports'
          args: >
            --failOnCVSS 7
            --enableExperimental
            --nvdApiKey ${{ secrets.NVD_API_KEY }}

      - name: Upload Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: dependency-check-report
          path: reports/

      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: reports/dependency-check-report.sarif
```

---

## Jenkins (Declarative Pipeline)

```groovy
pipeline {
    agent any

    environment {
        NVD_API_KEY = credentials('nvd-api-key')
    }

    stages {
        stage('Dependency Check') {
            steps {
                dependencyCheck(
                    additionalArguments: """
                        --format HTML
                        --format JSON
                        --nvdApiKey ${NVD_API_KEY}
                        --failOnCVSS 7
                        --enableExperimental
                        --out ./dc-reports
                    """,
                    odcInstallation: 'dependency-check'
                )
            }
        }
    }

    post {
        always {
            dependencyCheckPublisher(
                pattern: 'dc-reports/dependency-check-report.xml',
                failedTotalCritical: 1,
                failedTotalHigh: 5
            )
            archiveArtifacts artifacts: 'dc-reports/**', fingerprint: true
        }
    }
}
```

> Requires the OWASP Dependency-Check Jenkins Plugin.

---

## GitLab CI

```yaml
dependency-check:
  image: owasp/dependency-check:latest
  stage: security
  cache:
    key: nvd-db
    paths:
      - /usr/share/dependency-check/data/
  script:
    - /usr/share/dependency-check/bin/dependency-check.sh
        --project "$CI_PROJECT_NAME"
        --scan .
        --format HTML --format JSON
        --out ./dc-reports
        --nvdApiKey "$NVD_API_KEY"
        --failOnCVSS 7
        --enableExperimental
  artifacts:
    when: always
    paths:
      - dc-reports/
    expire_in: 30 days
  variables:
    NVD_API_KEY: $NVD_API_KEY  # Set in GitLab CI/CD Variables
```

---

## Azure DevOps

```yaml
trigger:
  - main

pool:
  vmImage: ubuntu-latest

steps:
  - task: Cache@2
    inputs:
      key: nvd-db
      path: $(HOME)/.dependency-check/data

  - script: |
      docker run --rm \
        -v $(Build.SourcesDirectory):/src \
        -v $(Build.ArtifactStagingDirectory)/reports:/report \
        owasp/dependency-check \
        --scan /src \
        --project "$(Build.Repository.Name)" \
        --format HTML --format JSON \
        --out /report \
        --nvdApiKey $(NVD_API_KEY) \
        --failOnCVSS 7
    displayName: 'OWASP Dependency-Check'
    env:
      NVD_API_KEY: $(NVD_API_KEY)  # Set in Azure Pipeline Variables

  - task: PublishBuildArtifacts@1
    condition: always()
    inputs:
      pathToPublish: $(Build.ArtifactStagingDirectory)/reports
      artifactName: DependencyCheckReports
```