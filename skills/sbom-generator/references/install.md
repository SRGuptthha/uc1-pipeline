# SBOM Tool Installation

## Syft (Anchore) — Recommended

### Linux / macOS
```bash
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
syft version
```

### Windows (PowerShell)
```powershell
# Via Scoop
scoop install syft

# Or manual download
$ver = (Invoke-RestMethod "https://api.github.com/repos/anchore/syft/releases/latest").tag_name
Invoke-WebRequest -Uri "https://github.com/anchore/syft/releases/download/$ver/syft_${ver}_windows_amd64.zip" -OutFile syft.zip
Expand-Archive syft.zip -DestinationPath $env:USERPROFILE\bin
```

### Docker
```bash
docker pull anchore/syft:latest
docker run --rm -v $(pwd):/project anchore/syft:latest dir:/project \
  --output cyclonedx-json=/project/sbom.cdx.json
```

---

## CycloneDX CLI — For validation

```bash
# Linux / macOS
curl -sSfL https://github.com/CycloneDX/cyclonedx-cli/releases/latest/download/cyclonedx-linux-x64 \
  -o /usr/local/bin/cyclonedx-cli && chmod +x /usr/local/bin/cyclonedx-cli

# Validate
cyclonedx-cli validate --input-file sbom.cdx.json --fail-on-errors
```

---

## CycloneDX Maven Plugin (generate without Syft)

Add to `pom.xml`:
```xml
<plugin>
  <groupId>org.cyclonedx</groupId>
  <artifactId>cyclonedx-maven-plugin</artifactId>
  <version>2.8.0</version>
  <executions>
    <execution>
      <phase>package</phase>
      <goals><goal>makeAggregateBom</goal></goals>
    </execution>
  </executions>
  <configuration>
    <projectType>library</projectType>
    <schemaVersion>1.5</schemaVersion>
    <includeBomSerialNumber>true</includeBomSerialNumber>
    <includeCompileScope>true</includeCompileScope>
    <includeTestScope>false</includeTestScope>
    <includeRuntimeScope>true</includeRuntimeScope>
    <outputFormat>json</outputFormat>
    <outputName>sbom-cyclonedx</outputName>
  </configuration>
</plugin>
```

Run: `mvn cyclonedx:makeAggregateBom`  
Output: `target/sbom-cyclonedx.json`
