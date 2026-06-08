# Secret Detection Pattern Library

## Built-in Regex Patterns

Used by the pipeline-native scanner when gitleaks/truffleHog are unavailable.

```python
SECRET_PATTERNS = [
    # Cloud provider credentials
    ("AWS_ACCESS_KEY_ID",
     r'(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])',
     "CRITICAL"),

    ("AWS_SECRET_ACCESS_KEY",
     r'(?i)aws[_\-\.]?secret[_\-\.]?(access[_\-\.]?)?key\s*[=:]\s*["\']?([A-Za-z0-9/+]{40})["\']?',
     "CRITICAL"),

    ("GCP_SERVICE_ACCOUNT",
     r'"type"\s*:\s*"service_account"',
     "CRITICAL"),

    # VCS tokens
    ("GITHUB_PAT",
     r'ghp_[A-Za-z0-9]{36}',
     "HIGH"),

    ("GITHUB_OAUTH",
     r'gho_[A-Za-z0-9]{36}',
     "HIGH"),

    ("GITLAB_TOKEN",
     r'glpat-[A-Za-z0-9_\-]{20}',
     "HIGH"),

    ("BITBUCKET_APP_PASSWORD",
     r'(?i)bitbucket[_\-\.]?(app[_\-\.]?)?password\s*[=:]\s*["\']?([A-Za-z0-9]{32,})["\']?',
     "HIGH"),

    # Private keys
    ("RSA_PRIVATE_KEY",
     r'-----BEGIN RSA PRIVATE KEY-----',
     "CRITICAL"),

    ("EC_PRIVATE_KEY",
     r'-----BEGIN EC PRIVATE KEY-----',
     "CRITICAL"),

    ("OPENSSH_PRIVATE_KEY",
     r'-----BEGIN OPENSSH PRIVATE KEY-----',
     "CRITICAL"),

    # Application secrets
    ("GENERIC_API_KEY",
     r'(?i)(api[_\-\.]?key|apikey)\s*[=:]\s*["\']([A-Za-z0-9_\-\.]{20,})["\']',
     "HIGH"),

    ("GENERIC_SECRET",
     r'(?i)(secret[_\-\.]?key|app[_\-\.]?secret)\s*[=:]\s*["\']([A-Za-z0-9_\-\.]{16,})["\']',
     "HIGH"),

    ("HARDCODED_PASSWORD",
     r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\'$\{\}]{8,})["\']',
     "HIGH"),

    ("JWT_SECRET",
     r'(?i)(jwt[_\-\.]?secret|signing[_\-\.]?key)\s*[=:]\s*["\']([^"\']{16,})["\']',
     "HIGH"),

    # Database URLs with embedded credentials
    ("DATABASE_URL_WITH_CREDS",
     r'(?i)(mysql|postgresql|mongodb|redis|mssql)://[^:@/]+:[^@/]+@',
     "HIGH"),

    # Webhooks and notification URLs
    ("SLACK_WEBHOOK",
     r'https://hooks\.slack\.com/services/T[A-Za-z0-9]+/B[A-Za-z0-9]+/[A-Za-z0-9]+',
     "MEDIUM"),

    ("DISCORD_WEBHOOK",
     r'https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_\-]+',
     "MEDIUM"),

    # Bearer tokens in code
    ("BEARER_TOKEN",
     r'(?i)Bearer\s+([A-Za-z0-9_\-\.]{32,})',
     "HIGH"),

    # npm auth tokens
    ("NPM_TOKEN",
     r'(?i)npm[_\-\.]?token\s*[=:]\s*["\']?(npm_[A-Za-z0-9]{36}|[A-Fa-f0-9]{64})["\']?',
     "HIGH"),
]
```

## Files and Extensions to Skip

```python
SKIP_EXTENSIONS = {
    # Compiled artifacts
    ".jar", ".class", ".war", ".ear", ".aar",
    # Binaries
    ".exe", ".dll", ".so", ".dylib", ".bin",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    # Images / media
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".mp3", ".mp4", ".wav", ".mov",
    # Documents
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    # Lock files (legitimate hashes)
    ".lock",
    # Compiled Python
    ".pyc", ".pyo",
}

SKIP_DIRS = {
    ".git", "node_modules", "target", "build",
    ".gradle", ".mvn", "__pycache__", "dist",
    ".idea", ".vscode", "vendor", "venv", ".env",
}
```

## Allowlist Patterns (known false positives)

```python
ALLOWLIST_PATTERNS = [
    r'EXAMPLE_KEY_DO_NOT_USE',
    r'your[_\-]?api[_\-]?key[_\-]?here',
    r'<YOUR_.*?>',
    r'\$\{.*?\}',          # template variables ${MY_KEY}
    r'\{\{.*?\}\}',         # Ansible/Jinja2 {{ MY_KEY }}
    r'xxxx+',               # redacted placeholders
    r'test[_\-]?only',
    r'(?i)placeholder',
    r'(?i)changeme',
    r'(?i)yourpassword',
]
```

## Custom Rule Format (for .gitleaks.toml)

```toml
[[rules]]
description = "Internal service token"
id = "internal-service-token"
regex = '''(?i)svc[_\-]?token\s*[=:]\s*["\']?([A-Za-z0-9_\-]{32,})["\']?'''
severity = "HIGH"
tags = ["token", "internal"]

[[rules.allowlist]]
regexes = ['test_token', 'fake_token', 'example_token']
```
