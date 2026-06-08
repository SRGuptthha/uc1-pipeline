# GitHub PR API — Auto-Remediation Skill

## Auth Setup

Requires a GitHub Personal Access Token (PAT) or GitHub Actions token with:
- `repo` scope (read + write code, PRs)
- `pull_requests: write` (fine-grained token)

```bash
# Set token in environment
export GITHUB_TOKEN=<your-token>

# Verify auth
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])"
```

---

## Step 1: Create Branch

```bash
# Get current SHA of base branch
BASE_SHA=$(curl -s \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/git/ref/heads/main" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['object']['sha'])")

# Create new branch from base SHA
curl -s -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/<OWNER>/<REPO>/git/refs" \
  -d "{
    \"ref\": \"refs/heads/fix/cve-<ARTIFACT_ID>-<NEW_VERSION>\",
    \"sha\": \"$BASE_SHA\"
  }"
```

---

## Step 2: Commit Patched pom.xml

```bash
# Get current file SHA (needed for update)
FILE_SHA=$(curl -s \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/contents/pom.xml?ref=main" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])")

# Base64-encode the patched pom.xml
CONTENT=$(base64 -w 0 pom.xml)

# Push commit
curl -s -X PUT \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/<OWNER>/<REPO>/contents/pom.xml" \
  -d "{
    \"message\": \"fix(deps): upgrade <ARTIFACT_ID> <OLD> → <NEW> (fixes <CVE_IDS>)\",
    \"content\": \"$CONTENT\",
    \"sha\": \"$FILE_SHA\",
    \"branch\": \"fix/cve-<ARTIFACT_ID>-<NEW_VERSION>\"
  }"
```

---

## Step 3: Open Pull Request

```bash
curl -s -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/<OWNER>/<REPO>/pulls" \
  -d "{
    \"title\": \"fix(deps): upgrade <ARTIFACT_ID> <OLD> → <NEW> [<CVE_IDS>]\",
    \"head\":  \"fix/cve-<ARTIFACT_ID>-<NEW_VERSION>\",
    \"base\":  \"main\",
    \"body\":  \"<PR_BODY_ESCAPED>\",
    \"draft\": false
  }" \
| python3 -c "import sys,json; d=json.load(sys.stdin); print(d['number'], d['html_url'])"
```

---

## Error Handling

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| 201 | PR created | Record PR number + URL |
| 422 | Branch already exists or PR already open | Check existing PRs, skip duplicate |
| 401 | Bad token | Ask user to re-set `GITHUB_TOKEN` |
| 403 | Token lacks permissions | Ask user to add `repo` scope |
| 404 | Repo not found | Verify `OWNER/REPO` |

---

## Detecting Existing Open PRs

Before creating, check if a PR for this branch already exists:

```bash
curl -s \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/pulls?state=open&head=<OWNER>:fix/cve-<ARTIFACT_ID>-<NEW_VERSION>" \
| python3 -c "
import sys, json
prs = json.load(sys.stdin)
print(prs[0]['html_url'] if prs else 'NONE')
"
```

If a PR already exists for this branch, skip creation and report the existing PR URL.

---

## Labels (optional)

Add `security` and `dependencies` labels to the PR:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/issues/<PR_NUMBER>/labels" \
  -d '{"labels": ["security", "dependencies"]}'
```