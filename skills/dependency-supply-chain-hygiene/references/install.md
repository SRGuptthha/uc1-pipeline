# Installing OWASP Dependency-Check

## Option 1 — Standalone CLI (Recommended)

### Linux / macOS
```bash
# Download latest release
VERSION=$(curl -s https://api.github.com/repos/jeremylong/DependencyCheck/releases/latest | grep tag_name | cut -d'"' -f4 | tr -d 'v')
curl -L "https://github.com/jeremylong/DependencyCheck/releases/download/v${VERSION}/dependency-check-${VERSION}-release.zip" -o dc.zip
unzip dc.zip -d /opt/dependency-check
ln -s /opt/dependency-check/dependency-check/bin/dependency-check.sh /usr/local/bin/dependency-check
dependency-check --version
```

### Windows (PowerShell)
```powershell
$VERSION = (Invoke-RestMethod https://api.github.com/repos/jeremylong/DependencyCheck/releases/latest).tag_name.TrimStart('v')
Invoke-WebRequest "https://github.com/jeremylong/DependencyCheck/releases/download/v$VERSION/dependency-check-$VERSION-release.zip" -OutFile dc.zip
Expand-Archive dc.zip -DestinationPath "C:\Tools\dependency-check"
# Add C:\Tools\dependency-check\dependency-check\bin to PATH
```

### Homebrew (macOS)
```bash
brew install dependency-check
```

### Docker (no install required)
```bash
docker run --rm \
  -v $(pwd):/src \
  -v $(pwd)/reports:/report \
  owasp/dependency-check \
  --scan /src \
  --format HTML --format JSON \
  --out /report \
  --project "MyProject"
```

---

## Option 2 — Maven Plugin (Java projects)

Add to `pom.xml`:
```xml
<plugin>
  <groupId>org.owasp</groupId>
  <artifactId>dependency-check-maven</artifactId>
  <version>9.0.9</version>
  <executions>
    <execution>
      <goals><goal>check</goal></goals>
    </execution>
  </executions>
  <configuration>
    <failBuildOnCVSS>7</failBuildOnCVSS>
    <formats>HTML,JSON</formats>
    <nvdApiKey>${env.NVD_API_KEY}</nvdApiKey>
  </configuration>
</plugin>
```

Run: `mvn dependency-check:check`

---

## Option 3 — Gradle Plugin (Java projects)

`build.gradle`:
```groovy
plugins {
    id 'org.owasp.dependencycheck' version '9.0.9'
}

dependencyCheck {
    failBuildOnCVSS = 7
    formats = ['HTML', 'JSON']
    nvd { apiKey = System.getenv('NVD_API_KEY') }
}
```

Run: `./gradlew dependencyCheckAnalyze`

---

## Option 4 — npm / Node.js (npm audit wrapper)

For quick Node.js scans, `npm audit` is built-in and covers many CVEs:
```bash
npm audit
npm audit --json > audit-report.json
npm audit fix       # auto-fix safe upgrades
npm audit fix --force  # force major version upgrades (review carefully)
```

OWASP Dependency-Check also supports Node.js with `--enableExperimental` for deeper analysis.

---

## NVD API Key Setup

Required for reliable scanning (avoids rate limits):
1. Register at https://nvd.nist.gov/developers/request-an-api-key
2. Pass via flag: `--nvdApiKey YOUR_KEY`
3. Or set environment variable: `export NVD_API_KEY=YOUR_KEY`
4. In CI/CD: store as a secret and inject as env var

First-run database download: ~500MB, 10–20 minutes.
Subsequent runs: incremental, 1–3 minutes.