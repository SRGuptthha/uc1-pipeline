# Scan Command Reference

## Universal Flags

| Flag | Description |
|------|-------------|
| `--project` | Project name (appears in report) |
| `--scan` | Path to scan (file, dir, or glob) |
| `--out` | Output directory for reports |
| `--format` | Output format (HTML, JSON, XML, SARIF, SPDX, CSV); repeatable |
| `--failOnCVSS` | Exit non-zero if any CVE >= this score (use 7 for High+) |
| `--nvdApiKey` | NVD API key (strongly recommended) |
| `--suppression` | Path to suppression XML file |
| `--enableExperimental` | Enable experimental analyzers (required for some ecosystems) |
| `--disableAssembly` | Skip .NET assembly analysis (if mono not available) |
| `--log` | Log file path |

---

## Per-Ecosystem Scan Examples

### Java — Maven project
```bash
dependency-check \
  --project "my-java-app" \
  --scan "./pom.xml" \
  --format HTML --format JSON \
  --out "./dc-reports" \
  --nvdApiKey "$NVD_API_KEY" \
  --failOnCVSS 7
```

Or use the Maven plugin (see install.md) — preferred for Maven projects.

### Java — Gradle project
```bash
dependency-check \
  --project "my-gradle-app" \
  --scan "." \
  --format HTML --format JSON \
  --out "./dc-reports" \
  --nvdApiKey "$NVD_API_KEY"
```

Or use the Gradle plugin (see install.md).

### Node.js
```bash
dependency-check \
  --project "my-node-app" \
  --scan "./package.json" \
  --enableExperimental \
  --format HTML --format JSON \
  --out "./dc-reports" \
  --nvdApiKey "$NVD_API_KEY" \
  --failOnCVSS 7
```

Also run alongside:
```bash
npm audit --json > npm-audit.json
```

### Python
```bash
dependency-check \
  --project "my-python-app" \
  --scan "./requirements.txt" \
  --enableExperimental \
  --format HTML --format JSON \
  --out "./dc-reports" \
  --nvdApiKey "$NVD_API_KEY"
```

Also consider `pip-audit` for Python-native scanning:
```bash
pip install pip-audit
pip-audit -r requirements.txt --format json -o pip-audit.json
```

### .NET
```bash
dependency-check \
  --project "my-dotnet-app" \
  --scan "." \
  --format HTML --format JSON \
  --out "./dc-reports" \
  --nvdApiKey "$NVD_API_KEY" \
  --disableAssembly   # add if mono is not installed
```

Also run:
```bash
dotnet list package --vulnerable
```

### Ruby
```bash
dependency-check \
  --project "my-ruby-app" \
  --scan "./Gemfile.lock" \
  --enableExperimental \
  --format HTML --format JSON \
  --out "./dc-reports" \
  --nvdApiKey "$NVD_API_KEY"
```

Also consider `bundler-audit`:
```bash
gem install bundler-audit
bundle-audit check --update
```

---

## Multi-Ecosystem Monorepo
```bash
dependency-check \
  --project "monorepo" \
  --scan "./services/java-service/pom.xml" \
  --scan "./services/node-service/package.json" \
  --scan "./services/python-service/requirements.txt" \
  --enableExperimental \
  --format HTML --format JSON \
  --out "./dc-reports" \
  --nvdApiKey "$NVD_API_KEY" \
  --failOnCVSS 7
```

---

## Suppression File

To suppress known false positives, create `suppressions.xml` and pass `--suppression ./suppressions.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<suppressions xmlns="https://jeremylong.github.io/DependencyCheck/dependency-suppression.1.3.xsd">
  <suppress>
    <notes>False positive — CVE does not apply to this usage</notes>
    <gav regex="true">^com\.example:my-lib:.*$</gav>
    <cve>CVE-2021-12345</cve>
  </suppress>
</suppressions>
```