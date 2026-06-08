# Gate 4: JaCoCo Coverage — PR Validation Agent

## Purpose

Ensure the PR branch maintains ≥ 80% line coverage after the dependency upgrade.
A major version bump may break existing tests or require new ones; this gate catches regressions.

---

## Run Command

JaCoCo runs as part of the Maven test lifecycle. Ensure the project has JaCoCo configured
(check `pom.xml` for the plugin — add if missing):

```xml
<!-- Add to pom.xml if not present -->
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.11</version>
  <executions>
    <execution>
      <goals><goal>prepare-agent</goal></goals>
    </execution>
    <execution>
      <id>report</id>
      <phase>test</phase>
      <goals><goal>report</goal></goals>
    </execution>
  </executions>
</plugin>
```

Run tests with JaCoCo agent:

```bash
mvn test jacoco:report \
  --batch-mode \
  --no-transfer-progress \
  2>&1 | tee jacoco-output.txt
echo "EXIT_CODE:$?"
```

This generates: `target/site/jacoco/jacoco.xml`

---

## Parse Coverage from jacoco.xml

```python
import xml.etree.ElementTree as ET

def parse_jacoco(xml_path, threshold=80.0):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Find LINE counter at report level (aggregate)
    for counter in root.findall("counter"):
        if counter.attrib.get("type") == "LINE":
            covered = int(counter.attrib["covered"])
            missed  = int(counter.attrib["missed"])
            total   = covered + missed
            pct     = round((covered / total) * 100, 1) if total > 0 else 0.0
            return {
                "covered": covered,
                "missed":  missed,
                "total":   total,
                "line_coverage_pct": pct,
                "threshold": threshold,
                "passed": pct >= threshold
            }
    return None
```

Fallback — parse from Maven console output if XML missing:

```bash
grep -E "LINE|BRANCH" jacoco-output.txt | tail -5
```

---

## Pass Condition

```python
def gate_pass(coverage):
    return coverage["line_coverage_pct"] >= coverage["threshold"]
```

Threshold is **80%** line coverage. Branch coverage is reported but not gated.

---

## Gate Result Object

```json
{
  "gate": "jacoco-coverage",
  "status": "PASS",
  "line_coverage_pct": 84.3,
  "threshold": 80.0,
  "lines_covered": 1243,
  "lines_missed": 231,
  "lines_total": 1474,
  "detail": "Line coverage: 84.3% (threshold: 80%) ✅"
}
```

---

## PR Comment Section (on failure)

```markdown
**📊 JaCoCo Coverage — ❌ FAIL**
Line coverage: **74.2%** (required: ≥ 80%)

Lines covered: 1,093 / 1,474 (381 lines uncovered)

Action: Add or fix tests to bring coverage above 80%.
Run `mvn jacoco:report` locally and open `target/site/jacoco/index.html` to see uncovered lines.
```

---

## JaCoCo Not Configured

If `target/site/jacoco/jacoco.xml` doesn't exist after the test run:

1. Check if JaCoCo plugin is present in `pom.xml`
2. If missing — offer to add it automatically (ask user first)
3. If present but report missing — check `target/jacoco.exec` exists (agent ran but report not generated)
   - Fix: `mvn jacoco:report` explicitly after tests
4. If no `jacoco.exec` — JaCoCo agent didn't run; check Surefire argLine config:
   ```xml
   <plugin>
     <artifactId>maven-surefire-plugin</artifactId>
     <configuration>
       <argLine>@{argLine}</argLine>
     </configuration>
   </plugin>
   ```