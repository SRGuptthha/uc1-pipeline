# Scenario: Malformed pom.xml — Assertions & Expected Behaviour

## Profile
A synthetic Java project with a deliberately broken `pom.xml`. Validates that the
pipeline handles parse errors **gracefully** — surfaces the error clearly in the report,
does not crash with an unhandled exception, and continues to produce whatever output it
can before the error point.

## Setup — Generate Test Fixtures

Since real public repos rarely have malformed POMs, create local fixtures:

```bash
mkdir -p /tmp/e2e/malformed-pom-project
```

### Fixture 1: Broken XML (unclosed tag)
```xml
<!-- /tmp/e2e/malformed-pom-project/pom.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>malformed-app</artifactId>
  <version>1.0.0</version>
  <dependencies>
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-core</artifactId>
      <version>5.3.39
    </dependency>      <!-- missing </version> — XML is invalid -->
  </dependencies>
</project>
```

### Fixture 2: Missing version tag
```xml
<dependency>
  <groupId>com.fasterxml.jackson.core</groupId>
  <artifactId>jackson-databind</artifactId>
  <!-- no <version> tag -->
</dependency>
```

### Fixture 3: Circular property reference
```xml
<properties>
  <app.version>${app.version}</app.version>   <!-- circular -->
</properties>
```

### Fixture 4: Empty dependency block
```xml
<dependency></dependency>
```

### Fixture 5: SNAPSHOT on production dependency
```xml
<version>2.5.28-SNAPSHOT</version>
```

---

## Assertions

| ID    | Stage | Assertion | Expected |
|-------|-------|-----------|----------|
| MP-1  | Setup | Pipeline starts without crash | No unhandled Python exception |
| MP-2  | Stage 1 | Parse error surfaced | Error message in stdout or report mentions pom.xml parse failure |
| MP-3  | Stage 1 | Graceful halt or partial scan | Pipeline exits with non-zero code OR continues with 0 deps |
| MP-4  | Stage 1 | No silent failure | Output does NOT say "0 CVEs found" without explaining why |
| MP-5  | Stage 2 | Handles empty dep list | risk-scores.json produced even with 0 entries |
| MP-6  | Stage 3 | SBOM reflects partial scan | sbom-cyclonedx.json produced (may have 0 components) |
| MP-7  | All   | No Python traceback in stdout | `Traceback` string absent from pipeline output |
| MP-8  | Fixture 5 | SNAPSHOT version handled | SNAPSHOT deps skipped gracefully in Stage 4 version lookup |

---

## Assertion Checks (Python)

```python
def assert_malformed_pom(pipeline_stdout, pipeline_exit_code,
                          day1_report, risk_scores, sbom):
    results = []

    # MP-1: no unhandled crash (exit 0 or 1 — not exception traceback)
    results.append(("MP-1", "Traceback" not in pipeline_stdout,
                    "No Python traceback" if "Traceback" not in pipeline_stdout
                    else "FAIL: Python traceback found in output"))

    # MP-2: parse error mentioned
    parse_err_mentioned = any(kw in pipeline_stdout.lower()
                              for kw in ("parse", "xml", "invalid", "error", "malformed"))
    results.append(("MP-2", parse_err_mentioned,
                    "Parse error surfaced" if parse_err_mentioned
                    else "FAIL: no parse error message in output"))

    # MP-3: graceful exit
    results.append(("MP-3", pipeline_exit_code in (0, 1),
                    f"Exit code {pipeline_exit_code} (expected 0 or 1)"))

    # MP-5: risk-scores.json exists and is valid
    risk_valid = isinstance(risk_scores, dict)
    results.append(("MP-5", risk_valid, "risk-scores.json valid JSON"))

    # MP-6: sbom exists
    sbom_valid = isinstance(sbom, dict)
    results.append(("MP-6", sbom_valid, "sbom-cyclonedx.json valid JSON"))

    # MP-8: SNAPSHOT handling (check skipped list in remediation manifest)
    # Tested separately — fixture 5 only

    return results
```

---

## Running Against Local Fixtures

```bash
# Copy a fixture pom.xml into the pipeline-output dir, then run:
cp /tmp/e2e/malformed-pom-project/pom.xml /path/to/pipeline-output/pom.xml

# The pipeline uses local pom.xml if present (bypasses GitHub fetch)
python run_pipeline.py https://github.com/placeholder/placeholder
```

The pipeline checks `os.path.exists(os.path.join(OUT, "pom.xml"))` before fetching
from GitHub — a pre-placed local pom.xml is used directly (see Stage 1 setup code).

---

## Common Failure Modes

| Symptom | Expected | Not Expected |
|---------|----------|-------------|
| `ET.ParseError` raised | Caught and reported | Unhandled traceback |
| 0 dependencies parsed | Warning in output | Silent "0 CVEs found" |
| Pipeline halts at pom.xml stage | Acceptable | Halt without any output |
| SNAPSHOT version causes lookup failure | Logged as skipped | Traceback |
