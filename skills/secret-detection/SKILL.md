---
name: secret-detection
description: >
  Scan a codebase and git history for leaked API keys, passwords, tokens, private keys, and
  other credentials using gitleaks or truffleHog. Integrates as Stage 3.5 in the UC1supply
  chain pipeline. Use this skill whenever the user wants to find leaked secrets, scan for
  hardcoded credentials, check for exposed API keys, audit for sensitive data in code or
  git history, or detect tokens in configuration files. Trigger for requests like "scan for
  secrets", "find leaked credentials", "check for hardcoded passwords", "run secret detection",
  "are there any API keys in my repo?", "truffleHog scan", "gitleaks scan", or "did I
  accidentally commit a token?".
---

# Secret Detection Skill — Stage 3.5

Scan source code, configuration files, and git commit history for accidentally committed
credentials, API keys, tokens, and private keys. Reports findings with file path, line number,
masked secret value, and remediation steps. Blocks pipeline on HIGH severity findings.

---

## What Gets Detected

| Secret Type | Examples | Severity |
|-------------|---------|---------|
| Cloud provider keys | AWS `AKIA*`, GCP service account JSON, Azure SAS tokens | CRITICAL |
| Version control tokens | GitHub PAT `ghp_*`, GitLab `glpat-*`, Bitbucket app passwords | HIGH |
| Private keys | RSA, EC, DSA, OpenSSH PEM blocks | CRITICAL |
| Database credentials | Hardcoded `password=`, `DATABASE_URL` with credentials | HIGH |
| API keys (generic) | `api_key=`, `apikey=`, `x-api-key:` with values | HIGH |
| JWT secrets | Hardcoded signing secrets in code | HIGH |
| Webhook URLs | Slack, Discord, Teams webhook URLs | MEDIUM |
| Internal URLs with creds | `https://user:pass@host/` | HIGH |
| `.env` file patterns | `SECRET_KEY=`, `TOKEN=` in tracked `.env` files | HIGH |

---

## Workflow

### Step 1 — Check Tool Availability

```bash
gitleaks version 2>/dev/null  && echo "GITLEAKS_OK" || echo "GITLEAKS_MISSING"
trufflehog --version 2>/dev/null && echo "TRUFFLE_OK"  || echo "TRUFFLE_MISSING"
```

If neither is installed, fall back to the built-in regex scanner (Step 3B).
Read `references/install.md` for installation instructions.

---

### Step 2A — Gitleaks Scan (preferred)

```bash
# Scan working directory (uncommitted files + tracked files)
gitleaks detect \
  --source . \
  --report-path ./secret-scan-report.json \
  --report-format json \
  --no-git \
  --verbose

# Scan full git history
gitleaks detect \
  --source . \
  --report-path ./secret-scan-history.json \
  --report-format json \
  --log-opts "--all" \
  --verbose

echo "Exit code: $?"   # 0 = clean, 1 = secrets found
```

#### Gitleaks config file (`.gitleaks.toml`) — generate if missing:

```toml
title = "UC1 Secret Detection Config"

[extend]
useDefault = true

[[rules]]
description = "UC1 internal API key pattern"
id = "uc1-api-key"
regex = '''(?i)(uc1|internal)[_-]?(api|access)[_-]?key\s*[=:]\s*["']?([A-Za-z0-9_\-]{20,})["']?'''
severity = "HIGH"
tags = ["api-key", "internal"]

[allowlist]
description = "Test fixtures and example files"
paths = [
    '''tests?/fixtures/.*''',
    '''docs?/examples?/.*''',
    '''.*\.example''',
    '''.*\.sample''',
]
regexes = [
    '''EXAMPLE_KEY_DO_NOT_USE''',
    '''your[_-]?api[_-]?key[_-]?here''',
    '''<YOUR_.*>''',
]
```

---

### Step 2B — TruffleHog Scan (alternative)

```bash
# Scan local filesystem
trufflehog filesystem . \
  --json \
  --only-verified \
  2>/dev/null > ./trufflehog-report.json

# Scan git history
trufflehog git file://. \
  --json \
  --only-verified \
  2>/dev/null >> ./trufflehog-report.json
```

---

### Step 3B — Built-in Regex Scanner (no tools required)

If no external scanner is available, run built-in regex detection across all non-binary files:

```python
import os, re, json

SECRET_PATTERNS = [
    ("AWS_ACCESS_KEY",    r'AKIA[0-9A-Z]{16}',                                       "CRITICAL"),
    ("PRIVATE_KEY",       r'-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----',       "CRITICAL"),
    ("GITHUB_TOKEN",      r'ghp_[A-Za-z0-9]{36}',                                    "HIGH"),
    ("GITLAB_TOKEN",      r'glpat-[A-Za-z0-9_\-]{20}',                              "HIGH"),
    ("GENERIC_API_KEY",   r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([A-Za-z0-9_\-]{20,})["\']', "HIGH"),
    ("PASSWORD",          r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,})["\']',          "HIGH"),
    ("JWT_SECRET",        r'(?i)(jwt|signing)[_-]?secret\s*[=:]\s*["\']([^"\']{16,})["\']',      "HIGH"),
    ("SLACK_WEBHOOK",     r'https://hooks\.slack\.com/services/T[A-Za-z0-9]+/B[A-Za-z0-9]+/',    "MEDIUM"),
    ("DATABASE_URL",      r'(?i)(mysql|postgresql|mongodb)://[^:]+:[^@]+@',                       "HIGH"),
    ("GENERIC_TOKEN",     r'(?i)(token|auth[_-]?key)\s*[=:]\s*["\']([A-Za-z0-9_\-\.]{24,})["\']',"HIGH"),
]

SKIP_EXTENSIONS = {".jar", ".class", ".png", ".jpg", ".gif", ".zip", ".tar", ".gz", ".bin",
                   ".exe", ".dll", ".so", ".dylib", ".pdf", ".lock"}
SKIP_DIRS       = {".git", "node_modules", "target", "build", ".gradle", "__pycache__"}

def scan_file(filepath, patterns):
    findings = []
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                for secret_type, pattern, severity in patterns:
                    if re.search(pattern, line):
                        masked = re.sub(r'(["\'])([A-Za-z0-9_\-]{4})[A-Za-z0-9_\-]+(["\'])',
                                        r'\1\2****\3', line)
                        findings.append({
                            "file":        filepath,
                            "line":        line_num,
                            "type":        secret_type,
                            "severity":    severity,
                            "description": masked.strip()[:120],
                        })
    except (IOError, PermissionError):
        pass
    return findings

def scan_directory(root, patterns):
    all_findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SKIP_EXTENSIONS:
                continue
            fpath = os.path.join(dirpath, fname)
            all_findings.extend(scan_file(fpath, patterns))
    return all_findings
```

---

### Step 4 — Parse & Normalize Results

Normalize output from any scanner into a common schema:

```json
{
  "scan_date": "<ISO-DATE>",
  "project": "<PROJECT_NAME>",
  "scanner": "gitleaks | trufflehog | built-in",
  "result": "BLOCKED | PASSED",
  "summary": {
    "total_findings": 3,
    "critical_count": 1,
    "high_count": 2,
    "medium_count": 0
  },
  "findings": [
    {
      "rule_id": "AWS_ACCESS_KEY",
      "type": "AWS Access Key ID",
      "severity": "CRITICAL",
      "file": "src/main/resources/application.properties",
      "line": 42,
      "commit": "abc123",
      "description": "AWS access key detected — rotate immediately",
      "masked_value": "AKIAJ****EXAMPLE",
      "remediation": "Remove from code. Rotate key in AWS IAM. Add to .gitignore."
    }
  ],
  "files_scanned": 84,
  "history_scanned": true
}
```

See `references/output-schema.md` for the full field specification.

---

### Step 5 — Generate Markdown Summary

```markdown
## 🔑 Secret Detection Report — <PROJECT_NAME>
**Scan date:** <DATE> | **Scanner:** <TOOL> | **Files scanned:** <N>
**Result:** 🔴 BLOCKED / 🟢 CLEAN

### Summary
| Severity | Count |
|----------|-------|
| 🔴 Critical | X |
| 🟠 High     | X |
| 🟡 Medium   | X |

### 🚨 Findings

**[CRITICAL]** `AKIA*` — AWS Access Key ID
- **File:** `src/main/resources/application.properties:42`
- **Masked:** `AKIAJ****EXAMPLE`
- **Action:** Rotate key in AWS IAM immediately. Remove from file. Add file to `.gitignore`.

### ✅ Remediation Steps

1. **Rotate all exposed credentials immediately** — treat every detected secret as compromised.
2. For each finding:
   - Remove the hardcoded value from the source file.
   - Replace with an environment variable or secrets manager reference.
   - Add the file to `.gitignore` if it should never be committed.
3. **Purge from git history** if the secret was committed:
   ```bash
   # Using git-filter-repo (recommended)
   pip install git-filter-repo
   git filter-repo --path src/main/resources/application.properties --invert-paths
   # Then force-push all branches
   ```
4. After rotating and purging, re-run this scan to confirm clean.
```

---

### Step 6 — Approval Gate ⛔ STOP

```
---
⛔ Secret scan complete — approval required

Result: BLOCKED / CLEAN
Findings: <N> total  (CRITICAL: X, HIGH: Y, MEDIUM: Z)

Reply with one of:
  • "approve"                 — accept results, continue pipeline
  • "show finding [N]"        — show full context for finding number N
  • "false positive [N]"      — mark finding N as a false positive with reason
  • "stop here"               — end session, keep report files only
---
```

---

### Step 7 — CI/CD Integration

Read `references/cicd.md` for pipeline snippets. Key CI/CD considerations:
- Run secret detection **before** any other step — prevent secrets from reaching logs.
- Use `--no-git` to scan only working tree files in CI (git history should be scanned on merge).
- Cache `.gitleaks.toml` in the repo so all developers use the same ruleset.
- For pre-commit enforcement, see `references/pre-commit.md`.

---

## Output Files

| File | Format | Consumer |
|------|--------|----------|
| `secret-scan-report.json` | JSON | Policy enforcer, HTML report |
| Markdown summary | Chat / stdout | Human |
| Exit code | Shell | CI pipeline (0 = clean, 1 = findings) |

---

## Reference Files

- `references/install.md` — Gitleaks and TruffleHog installation (Linux, macOS, Windows, Docker)
- `references/patterns.md` — Full pattern library for built-in scanner; custom rule authoring
- `references/cicd.md` — GitHub Actions, GitLab CI, Jenkins integration snippets
- `references/pre-commit.md` — Pre-commit hook setup to block secrets at commit time
- `references/output-schema.md` — Normalized output JSON schema
