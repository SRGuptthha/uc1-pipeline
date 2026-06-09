"""Push a vulnerable pom.xml to the uc1-security-demo repo."""
import json, urllib.request, ssl, base64, time, sys

TOKEN = sys.argv[1]
OWNER = "SRGuptthha"
REPO  = "uc1-security-demo"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode    = ssl.CERT_NONE

HDRS = {
    "Authorization":        f"Bearer {TOKEN}",
    "Accept":               "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent":           "UC1/1.0",
    "Content-Type":         "application/json",
}

def gh(method, path, payload=None):
    url  = f"https://api.github.com{path}"
    data = json.dumps(payload).encode() if payload else None
    req  = urllib.request.Request(url, data=data, method=method, headers=HDRS)
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}"), e.code

# Wait for repo to be ready
print("Waiting for repo to initialise...")
time.sleep(3)

# Check repo exists
repo_data, status = gh("GET", f"/repos/{OWNER}/{REPO}")
if status != 200:
    print(f"Repo not ready ({status}): {repo_data}")
    sys.exit(1)
print(f"Repo: {repo_data.get('html_url')}")
default_branch = repo_data.get("default_branch", "main")

POM = """\
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.SRGuptthha</groupId>
  <artifactId>uc1-security-demo</artifactId>
  <version>1.0.0</version>
  <packaging>jar</packaging>
  <name>UC1 Security Demo App</name>

  <properties>
    <java.version>17</java.version>
    <spring-framework.version>5.3.20</spring-framework.version>
    <jackson.version>2.13.0</jackson.version>
  </properties>

  <dependencies>

    <!-- Spring Core — CVE-2022-22965 Spring4Shell (CVSS 9.8) -->
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-core</artifactId>
      <version>${spring-framework.version}</version>
    </dependency>

    <!-- Spring Web -->
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-webmvc</artifactId>
      <version>${spring-framework.version}</version>
    </dependency>

    <!-- Log4j Core — CVE-2021-44228 Log4Shell (CVSS 10.0) -->
    <dependency>
      <groupId>org.apache.logging.log4j</groupId>
      <artifactId>log4j-core</artifactId>
      <version>2.14.1</version>
    </dependency>

    <!-- Jackson Databind — CVE-2022-42003 (CVSS 7.5) -->
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
      <version>${jackson.version}</version>
    </dependency>

    <!-- Commons Text — CVE-2022-42889 Text4Shell (CVSS 9.8) -->
    <dependency>
      <groupId>org.apache.commons</groupId>
      <artifactId>commons-text</artifactId>
      <version>1.9</version>
    </dependency>

    <!-- SnakeYAML — CVE-2022-25857 DoS (CVSS 7.5) -->
    <dependency>
      <groupId>org.yaml</groupId>
      <artifactId>snakeyaml</artifactId>
      <version>1.30</version>
    </dependency>

    <!-- H2 Database — CVE-2022-23221 RCE (CVSS 9.8) -->
    <dependency>
      <groupId>com.h2database</groupId>
      <artifactId>h2</artifactId>
      <version>2.1.210</version>
    </dependency>

  </dependencies>
</project>
"""

# Get current README SHA (needed to know default branch exists)
readme_data, _ = gh("GET", f"/repos/{OWNER}/{REPO}/contents/README.md?ref={default_branch}")
readme_sha = readme_data.get("sha", "")

# Commit pom.xml
print("Committing pom.xml...")
encoded = base64.b64encode(POM.encode("utf-8")).decode("ascii")
result, status = gh("PUT", f"/repos/{OWNER}/{REPO}/contents/pom.xml", {
    "message": "chore: add vulnerable pom.xml for UC1 security pipeline demo",
    "content": encoded,
    "branch":  default_branch,
})
if status in (200, 201):
    print(f"pom.xml committed on branch '{default_branch}'")
    print(f"View: https://github.com/{OWNER}/{REPO}/blob/{default_branch}/pom.xml")
else:
    print(f"Failed ({status}): {result}")
    sys.exit(1)

print(f"\nRepo ready: https://github.com/{OWNER}/{REPO}")
print(f"Default branch: {default_branch}")
