# Install — Syft & Grype

## Syft (SBOM Generator)

### Linux / macOS
```bash
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
syft version
```

### Windows (PowerShell)
```powershell
winget install Anchore.Syft
# or
choco install syft
```

### Docker
```bash
docker run --rm -v $(pwd):/workspace anchore/syft:latest \
  dir:/workspace --output cyclonedx-json=/workspace/sbom.cdx.json
```

### Maven Plugin
```xml
<plugin>
  <groupId>io.github.anchore</groupId>
  <artifactId>syft-maven-plugin</artifactId>
  <version>0.4.0</version>
</plugin>
```

---

## Grype (Vulnerability Scanner — optional for source check enrichment)

### Linux / macOS
```bash
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
grype version
```

### Windows (PowerShell)
```powershell
winget install Anchore.Grype
```

### Scan an existing SBOM
```bash
grype sbom:./sbom.cdx.json --output json > grype-results.json
```

---

## Verify Installations
```bash
syft version && echo "Syft OK"
grype version && echo "Grype OK"
```