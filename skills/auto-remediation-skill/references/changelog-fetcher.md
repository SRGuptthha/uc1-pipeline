# Changelog Fetcher — Auto-Remediation Skill

## Source Lookup Priority

For each artifact, try sources in this order until one returns content:

1. GitHub Releases API (if artifact has a GitHub repo)
2. Maven Central `url` metadata field
3. Known changelog URLs for common artifact families (table below)
4. Fallback: NVD CVE descriptions only (no changelog)

---

## Step 1: GitHub Releases API

```bash
# Detect GitHub repo from Maven Central POM
curl -s "https://search.maven.org/remotecontent?\
filepath=<GROUP_PATH>/<ARTIFACT>/<VERSION>/<ARTIFACT>-<VERSION>.pom" \
| grep -o '<url>https://github.com/[^<]*</url>' | head -1

# Fetch releases between old and new version
curl -s "https://api.github.com/repos/<OWNER>/<REPO>/releases?per_page=50" \
-H "Authorization: Bearer $GITHUB_TOKEN" \
| python3 -c "
import sys, json
from packaging.version import Version
releases = json.load(sys.stdin)
old_v, new_v = '$OLD_VERSION', '$NEW_VERSION'
relevant = [
    r for r in releases
    if Version(old_v) < Version(r['tag_name'].lstrip('v')) <= Version(new_v)
]
for r in relevant:
    print(f\"### {r['tag_name']}\")
    print(r['body'][:500])
    print()
"
```

---

## Step 2: Known Changelog URLs by Artifact Family

| Group / Artifact | Changelog URL Pattern |
|------------------|-----------------------|
| `org.springframework*` | `https://github.com/spring-projects/spring-framework/releases` |
| `org.springframework.boot*` | `https://github.com/spring-projects/spring-boot/releases` |
| `org.springframework.security*` | `https://github.com/spring-projects/spring-security/releases` |
| `com.fasterxml.jackson*` | `https://github.com/FasterXML/jackson-databind/releases` |
| `org.apache.struts*` | `https://struts.apache.org/announce/` |
| `org.apache.logging.log4j*` | `https://logging.apache.org/log4j/2.x/changes-report.html` |
| `ch.qos.logback*` | `https://logback.qos.ch/news.html` |
| `io.netty*` | `https://netty.io/news/` |
| `org.hibernate*` | `https://github.com/hibernate/hibernate-orm/releases` |
| `org.apache.commons*` | `https://commons.apache.org/<component>/changes-report.html` |
| `com.google.guava*` | `https://github.com/google/guava/releases` |
| `org.bouncycastle*` | `https://www.bouncycastle.org/releasenotes.html` |

---

## Summarising the Changelog

After fetching raw release notes, summarise into 3–5 bullets:

System prompt for summarisation call:
```
You are a changelog summariser. Given raw release notes between version OLD and NEW
of a Java library, extract only:
1. Security fixes (CVE patches)
2. Breaking API changes
3. The 2–3 most significant feature changes

Format as bullet points. Be concise — one line per bullet. Ignore minor bugfixes,
dependency bumps, and test/CI changes.
```

---

## Breaking Change Detection (Major Bumps)

For major version bumps, scan the changelog for migration guide links:

```python
import re

migration_patterns = [
    r'migration guide',
    r'upgrade guide',
    r'breaking change',
    r'removed.{0,30}API',
    r'deprecated.{0,30}removed',
]

def find_breaking_changes(changelog_text):
    findings = []
    for pattern in migration_patterns:
        matches = re.findall(rf'.{{0,100}}{pattern}.{{0,100}}', changelog_text, re.IGNORECASE)
        findings.extend(matches)
    return findings
```

Include all breaking change findings verbatim in the PR body under the `⚠️ Breaking Changes` section.