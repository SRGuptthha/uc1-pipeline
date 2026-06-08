# GitHub Merge API — PR Validation Agent

## Merge a PR (squash)

```bash
curl -s -X PUT \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/merge" \
  -d '{
    "commit_title": "fix(deps): merge <ARTIFACT> <OLD> → <NEW> [validated]",
    "commit_message": "All 4 validation gates passed (mvn test ✅ OWASP ✅ Grype ✅ JaCoCo 84.3% ✅). Auto-merged by PR Validation Agent.",
    "merge_method": "squash"
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('MERGED' if d.get('merged') else 'FAILED:', d.get('message',''))
"
```

Merge methods: `squash` (default, recommended) | `merge` | `rebase`

---

## Check for Merge Conflicts Before Attempting

```bash
curl -s \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>" \
  | python3 -c "
import sys, json
pr = json.load(sys.stdin)
print('mergeable:', pr.get('mergeable'))
print('mergeable_state:', pr.get('mergeable_state'))
"
```

| `mergeable_state` | Meaning | Action |
|-------------------|---------|--------|
| `clean` | No conflicts, all checks pass | Safe to merge |
| `blocked` | Required status checks failing | Wait or investigate |
| `behind` | Branch behind base | Rebase first |
| `dirty` | Merge conflict | Flag to user — manual resolution needed |
| `unknown` | GitHub still computing | Retry after 2s |

---

## Delete Branch After Merge

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/git/refs/heads/<BRANCH_NAME>"
```

---

## Handle Merge Errors

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| 200 | Merged successfully | Record `merge_sha`, delete branch |
| 405 | Not mergeable (conflict) | Flag to user, skip auto-merge |
| 409 | Head branch modified since PR opened | Re-fetch PR, retry once |
| 422 | PR already closed/merged | Mark as done, skip |
| 403 | Token lacks merge permission | Ask user to merge manually |

---

## Post-Merge Verification

After merge, confirm main branch has the new commit:

```bash
curl -s \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<OWNER>/<REPO>/commits/main" \
  | python3 -c "
import sys, json
c = json.load(sys.stdin)
print(c['sha'][:8], c['commit']['message'][:80])
"
```