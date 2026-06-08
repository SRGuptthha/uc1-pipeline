# Secret Detection Tool Installation

## Gitleaks (Recommended)

### Linux / macOS
```bash
# Via brew
brew install gitleaks

# Or direct download
VERSION=8.18.4
curl -sSfL \
  "https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/gitleaks_${VERSION}_linux_x64.tar.gz" \
  | tar -xz -C /usr/local/bin gitleaks
gitleaks version
```

### Windows (PowerShell)
```powershell
# Via Scoop
scoop install gitleaks

# Or manual download
$ver = "8.18.4"
Invoke-WebRequest -Uri "https://github.com/gitleaks/gitleaks/releases/download/v$ver/gitleaks_${ver}_windows_x64.zip" `
  -OutFile gitleaks.zip
Expand-Archive gitleaks.zip -DestinationPath $env:USERPROFILE\bin
```

### Docker
```bash
docker pull zricethezav/gitleaks:latest
docker run --rm -v $(pwd):/path zricethezav/gitleaks:latest detect \
  --source /path \
  --report-path /path/secret-scan-report.json \
  --report-format json
```

---

## TruffleHog (Alternative)

```bash
# Linux / macOS
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
  | sh -s -- -b /usr/local/bin

# Or pip
pip install trufflehog3

# Run
trufflehog filesystem . --json > secret-scan-report.json
trufflehog git file://. --json --only-verified >> secret-scan-report.json
```

---

## Pre-commit Hook (developer machine)

```bash
pip install pre-commit

# .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks
EOF

pre-commit install
# Now gitleaks runs on every `git commit`
```
