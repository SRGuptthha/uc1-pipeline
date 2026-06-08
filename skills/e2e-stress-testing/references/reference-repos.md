# Reference Repos — E2E Stress Testing

Curated public Java repos suitable for each stress test scenario.
Use these if the user has not provided their own repos.

---

## CVE-Heavy Repos

Projects with known outdated / vulnerable dependencies — ideal for validating the full
CVE detection → scoring → remediation pipeline.

| Repo | URL | Why Useful |
|------|-----|-----------|
| WebGoat | `https://github.com/WebGoat/WebGoat` | Intentionally vulnerable Java app; dozens of CVEs |
| VulnerableApp | `https://github.com/SasanLabs/VulnerableApp` | Spring Boot with many outdated deps |
| DVJA | `https://github.com/appsecco/dvja` | Damn Vulnerable Java App — old Struts, Log4j etc. |

---

## Zero-CVE (Clean Baseline) Repos

Actively maintained projects with up-to-date dependencies — validates that the pipeline
completes green and generates no false alarms.

| Repo | URL | Why Useful |
|------|-----|-----------|
| Spring PetClinic | `https://github.com/spring-projects/spring-petclinic` | Well-maintained Spring Boot reference app |
| Spring Boot Actuator Samples | `https://github.com/spring-attic/spring-boot-actuator-samples` | Simple, up-to-date deps |
| Quarkus Quickstarts | `https://github.com/quarkusio/quarkus-quickstarts` | Modern Java, minimal CVE surface |

---

## Complex Dependency Tree Repos

Projects with large transitive dependency graphs — validates deep-tree SBOM generation,
transitive exposure scoring, and scan performance.

| Repo | URL | Why Useful |
|------|-----|-----------|
| Apache Kafka | `https://github.com/apache/kafka` | Massive multi-module Gradle/Maven project |
| Apache Flink | `https://github.com/apache/flink` | Deep transitive tree, 100+ deps |
| Elasticsearch | `https://github.com/elastic/elasticsearch` | Complex multi-module Maven build |

> Note: These repos may take 10–20 min for Stage 1 OWASP scan due to size.
> Flag this to the user before starting.

---

## Malformed pom.xml Edge Case Repos

Use a local synthetic project for malformed POM testing — real public repos
rarely have malformed POMs (they wouldn't build). Generate test fixtures instead:

```bash
mkdir -p /tmp/e2e/malformed-pom-project
```

Fixture variants — see `scenarios/malformed-pom.md` for exact XML content:

| Fixture | File | Edge Case |
|---------|------|-----------|
| `missing-version` | pom.xml | `<version>` tag absent on a dependency |
| `broken-xml` | pom.xml | Unclosed tag — invalid XML |
| `circular-property` | pom.xml | `${version}` references itself |
| `empty-dep-block` | pom.xml | `<dependency></dependency>` with no children |
| `snapshot-version` | pom.xml | `-SNAPSHOT` version on a production dependency |

---

## Mixed Scenario Repos

Projects with a mix of clean and vulnerable deps — validates partial remediation paths.

| Repo | URL | Why Useful |
|------|-----|-----------|
| Broad Institute GATK | `https://github.com/broadinstitute/gatk` | Mix of modern + legacy deps |
| Apache Struts Showcase | `https://github.com/apache/struts` | Mix of patched + unpatched components |