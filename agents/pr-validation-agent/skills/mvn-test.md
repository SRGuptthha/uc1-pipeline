# Gate 1: mvn test — PR Validation Agent

## Run Command

```bash
mvn test \
  --batch-mode \
  --no-transfer-progress \
  -Dsurefire.failIfNoSpecifiedTests=false \
  2>&1 | tee mvn-test-output.txt
echo "EXIT_CODE:$?"
```

`--batch-mode` suppresses interactive prompts. `--no-transfer-progress` reduces log noise.

---

## Parse Results

```bash
# Total / failures / errors / skipped
grep -E "Tests run:|BUILD" mvn-test-output.txt | tail -20

# Extract summary line
SUMMARY=$(grep "Tests run:" mvn-test-output.txt | tail -1)
# e.g. "Tests run: 142, Failures: 0, Errors: 0, Skipped: 3"

FAILURES=$(echo "$SUMMARY" | grep -o 'Failures: [0-9]*' | grep -o '[0-9]*')
ERRORS=$(echo "$SUMMARY"   | grep -o 'Errors: [0-9]*'   | grep -o '[0-9]*')
```

```python
import re

def parse_mvn_test(output):
    # Find all surefire summary lines
    pattern = r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)'
    matches = re.findall(pattern, output)
    totals = [sum(int(m[i]) for m in matches) for i in range(4)]
    return {
        "tests_run": totals[0],
        "failures":  totals[1],
        "errors":    totals[2],
        "skipped":   totals[3],
    }
```

---

## Pass Condition

```python
def gate_pass(result, exit_code):
    return exit_code == 0 and result["failures"] == 0 and result["errors"] == 0
```

---

## Gate Result Object

```json
{
  "gate": "mvn-test",
  "status": "PASS",
  "tests_run": 142,
  "failures": 0,
  "errors": 0,
  "skipped": 3,
  "duration_seconds": 38,
  "detail": "142 tests passed, 3 skipped"
}
```

---

## Failure Detail

If gate fails, extract failing test names for the PR comment:

```bash
grep -A 5 "FAILED\|ERROR" mvn-test-output.txt | head -40
```

```python
def extract_failures(output):
    pattern = r'(\S+)\s+FAILED'
    return re.findall(pattern, output)
```

Include top 5 failing test class names in the PR comment failure section.

---

## Common Failures & Fixes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `NoSuchMethodError` | API removed in major bump | Check migration guide |
| `ClassNotFoundException` | Package renamed | Update import in source |
| `AssertionError` | Behaviour change | Update test assertions |
| `ConnectionRefused` | Test relies on external service | Mock or skip in CI |
| `OutOfMemoryError` | Large test suite | Add `-Xmx512m` to Maven opts |