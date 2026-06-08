# pom.xml Patching — Auto-Remediation Skill

## Always Backup First

```bash
cp pom.xml pom.xml.bak
```

Restore on failure:
```bash
cp pom.xml.bak pom.xml
```

---

## Case 1: Direct Version Tag

```xml
<dependency>
  <groupId>org.apache.struts</groupId>
  <artifactId>struts2-core</artifactId>
  <version>2.5.28</version>   <!-- patch this -->
</dependency>
```

```python
import re

def patch_direct(content, artifact_id, old_version, new_version):
    pattern = (
        rf'(<artifactId>{re.escape(artifact_id)}</artifactId>'
        rf'\s*<version>){re.escape(old_version)}(</version>)'
    )
    result, count = re.subn(pattern, rf'\g<1>{new_version}\g<2>', content)
    return result, count > 0
```

---

## Case 2: Property Reference

```xml
<properties>
  <struts.version>2.5.28</struts.version>   <!-- patch this -->
</properties>
<dependencies>
  <dependency>
    <artifactId>struts2-core</artifactId>
    <version>${struts.version}</version>
  </dependency>
</dependencies>
```

```python
def patch_property(content, prop_name, old_version, new_version):
    pattern = rf'(<{re.escape(prop_name)}>){re.escape(old_version)}(</{re.escape(prop_name)}>)'
    result, count = re.subn(pattern, rf'\g<1>{new_version}\g<2>', content)
    return result, count > 0

def detect_property_ref(content, artifact_id):
    # Find version value for this artifactId
    m = re.search(
        rf'<artifactId>{re.escape(artifact_id)}</artifactId>\s*<version>\$\{{([^}}]+)\}}</version>',
        content
    )
    return m.group(1) if m else None
```

---

## Case 3: BOM-Managed Version

```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-dependencies</artifactId>
      <version>2.7.0</version>   <!-- patch BOM version here -->
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
```

Patch the BOM `<version>` tag using the same `patch_direct` approach targeting the BOM `artifactId`.
Always confirm the new BOM version includes the fixed dependency version before patching.

---

## Verification After Patch

```bash
# 1. Resolve all dependencies
mvn dependency:resolve -q
echo "Resolve exit code: $?"

# 2. Check for version conflicts
mvn dependency:tree -Dverbose 2>&1 | grep -i "conflict\|omitted"

# 3. Quick compile check (no tests)
mvn compile -q
echo "Compile exit code: $?"
```

If any step fails:
1. Restore backup: `cp pom.xml.bak pom.xml`
2. Report failure to user with the Maven error output
3. Mark this artifact as `PATCH_FAILED` in `remediation-manifest.json`
4. Continue with remaining approved artifacts

---

## Multi-Module Project Layout

```
root/
├── pom.xml              ← Check here first
├── module-a/
│   └── pom.xml
└── module-b/
    └── pom.xml
```

Resolution order:
1. Search root `pom.xml` `<dependencyManagement>` for the artifact
2. If found → patch root only
3. If not found → search each child `pom.xml`
4. If found in child → patch child only
5. Run `mvn dependency:resolve` from root after any patch