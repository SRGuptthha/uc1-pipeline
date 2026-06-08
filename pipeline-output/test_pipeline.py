#!/usr/bin/env python3
"""
Unit tests for run_pipeline.py pure functions.
Run: python test_pipeline.py
Results are injected into dependency-health-report.html by Stage 7.
"""
import sys, os, json, unittest

# ── Import the functions under test ──────────────────────────────────────────
# Intercept the top-level script execution so we can import without running it.
# We patch sys.argv to a minimal set so the arg-parsing block doesn't sys.exit.
_real_argv = sys.argv[:]
sys.argv = ["run_pipeline.py", "https://github.com/test/test"]

# Redirect stdout/stderr during import to suppress pipeline print output.
# _UC1_IMPORT_ONLY makes run_pipeline.py sys.exit(0) right after helpers are defined,
# so no network calls (OSV.dev, GitHub) happen during import.
os.environ["_UC1_IMPORT_ONLY"] = "1"
import io as _io
_stdout_save = sys.stdout
sys.stdout = _io.StringIO()
try:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "run_pipeline",
        os.path.join(os.path.dirname(__file__), "run_pipeline.py"))
    _mod = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
    # Prevent full execution — stop at the first stage print (after helpers are defined)
    # We monkey-patch sys.exit to raise SystemExit that we catch at import time
    _real_exit = sys.exit
    sys.exit = lambda *a: (_ for _ in ()).throw(SystemExit(*a))  # type: ignore[assignment]
    try:
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    except (SystemExit, Exception):
        pass
    finally:
        sys.exit = _real_exit
finally:
    sys.stdout = _stdout_save
    sys.argv   = _real_argv
    os.environ.pop("_UC1_IMPORT_ONLY", None)

# Pull the functions we want to test out of the partially-executed module
cvss_severity         = _mod.cvss_severity
bump_type             = _mod.bump_type
health_grade          = _mod.health_grade
extract_cvss          = _mod.extract_cvss
patch_pom_xml         = _mod.patch_pom_xml
patch_manifest        = _mod.patch_manifest
is_license_blocked    = _mod.is_license_blocked
parse_pom             = _mod.parse_pom
parse_pom_plugins     = _mod.parse_pom_plugins
parse_requirements_txt= _mod.parse_requirements_txt
parse_package_json    = _mod.parse_package_json
parse_csproj          = _mod.parse_csproj
parse_gemfile         = _mod.parse_gemfile
parse_go_mod          = _mod.parse_go_mod
_osv_package_spec     = _mod._osv_package_spec


# ─────────────────────────────────────────────────────────────────────────────
class TestCvssSeverity(unittest.TestCase):
    def test_critical(self):
        self.assertEqual(cvss_severity(9.0), "CRITICAL")
        self.assertEqual(cvss_severity(10.0), "CRITICAL")
        self.assertEqual(cvss_severity(9.8), "CRITICAL")

    def test_high(self):
        self.assertEqual(cvss_severity(7.0), "HIGH")
        self.assertEqual(cvss_severity(8.9), "HIGH")

    def test_medium(self):
        self.assertEqual(cvss_severity(4.0), "MEDIUM")
        self.assertEqual(cvss_severity(6.9), "MEDIUM")

    def test_low(self):
        self.assertEqual(cvss_severity(0.0), "LOW")
        self.assertEqual(cvss_severity(3.9), "LOW")


class TestBumpType(unittest.TestCase):
    def test_major(self):
        self.assertEqual(bump_type("1.0.0", "2.0.0"), "MAJOR")

    def test_minor(self):
        self.assertEqual(bump_type("1.0.0", "1.1.0"), "MINOR")

    def test_patch(self):
        self.assertEqual(bump_type("1.0.0", "1.0.1"), "PATCH")
        self.assertEqual(bump_type("2.3.4", "2.3.9"), "PATCH")

    def test_equal_returns_patch(self):
        # Same version — no bump possible, defaults to PATCH
        self.assertEqual(bump_type("1.0.0", "1.0.0"), "PATCH")

    def test_invalid_version_fallback(self):
        self.assertEqual(bump_type("not-a-version", "2.0"), "MINOR")


class TestHealthGrade(unittest.TestCase):
    def test_a(self):
        grade, label = health_grade(95)
        self.assertEqual(grade, "A")
        self.assertEqual(label, "Excellent")

    def test_b(self):
        grade, _ = health_grade(80)
        self.assertEqual(grade, "B")

    def test_c(self):
        grade, _ = health_grade(65)
        self.assertEqual(grade, "C")

    def test_d(self):
        grade, _ = health_grade(45)
        self.assertEqual(grade, "D")

    def test_f(self):
        grade, label = health_grade(20)
        self.assertEqual(grade, "F")
        self.assertEqual(label, "Critical")

    def test_boundaries(self):
        self.assertEqual(health_grade(90)[0], "A")
        self.assertEqual(health_grade(89)[0], "B")
        self.assertEqual(health_grade(75)[0], "B")
        self.assertEqual(health_grade(74)[0], "C")
        self.assertEqual(health_grade(60)[0], "C")
        self.assertEqual(health_grade(59)[0], "D")
        self.assertEqual(health_grade(40)[0], "D")
        self.assertEqual(health_grade(39)[0], "F")


class TestExtractCvss(unittest.TestCase):
    def test_database_specific_severity(self):
        score, sev = extract_cvss({"database_specific": {"severity": "CRITICAL"}})
        self.assertEqual(sev, "CRITICAL")
        self.assertGreaterEqual(score, 9.0)

    def test_moderate_maps_to_medium(self):
        score, sev = extract_cvss({"database_specific": {"severity": "MODERATE"}})
        self.assertEqual(sev, "MEDIUM")

    def test_empty_returns_low(self):
        score, sev = extract_cvss({})
        self.assertEqual(sev, "LOW")
        self.assertEqual(score, 0.0)

    def test_numeric_score_in_severity_list(self):
        detail = {"severity": [{"score": "8.5", "type": "CVSS_V3"}]}
        score, sev = extract_cvss(detail)
        self.assertEqual(score, 8.5)
        self.assertEqual(sev, "HIGH")


class TestPatchPomXml(unittest.TestCase):
    POM = """\
<project>
  <dependencies>
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-core</artifactId>
      <version>5.3.0</version>
    </dependency>
  </dependencies>
</project>"""

    def test_patches_direct_version(self):
        patched, changed = patch_pom_xml(self.POM, "org.springframework", "spring-core",
                                         "5.3.0", "5.3.39")
        self.assertTrue(changed)
        self.assertIn("5.3.39", patched)
        self.assertNotIn("5.3.0", patched)

    def test_no_change_when_not_found(self):
        patched, changed = patch_pom_xml(self.POM, "com.example", "missing-lib",
                                         "1.0.0", "2.0.0")
        self.assertFalse(changed)
        self.assertEqual(patched, self.POM)

    def test_property_based_version(self):
        pom = """\
<project>
  <properties>
    <spring.version>5.3.0</spring.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-core</artifactId>
      <version>${spring.version}</version>
    </dependency>
  </dependencies>
</project>"""
        patched, changed = patch_pom_xml(pom, "org.springframework", "spring-core",
                                         "5.3.0", "5.3.39")
        self.assertTrue(changed)
        self.assertIn("5.3.39", patched)


class TestPatchManifest(unittest.TestCase):
    def test_requirements_txt(self):
        content = "flask==2.0.0\nrequests>=2.28.0\n"
        dep     = {"ecosystem": "PyPI", "artifact": "flask", "group": "", "version": "2.0.0"}
        patched, changed = patch_manifest(content, dep, "3.0.0")
        self.assertTrue(changed)
        self.assertIn("flask==3.0.0", patched)

    def test_package_json(self):
        pkg     = json.dumps({"dependencies": {"express": "^4.18.0"}})
        dep     = {"ecosystem": "npm", "artifact": "express", "group": "", "version": "4.18.0"}
        patched, changed = patch_manifest(pkg, dep, "4.19.0")
        self.assertTrue(changed)
        data    = json.loads(patched)
        self.assertEqual(data["dependencies"]["express"], "^4.19.0")

    def test_go_mod(self):
        content = "module example.com/app\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.0\n)\n"
        dep     = {"ecosystem": "Go", "artifact": "github.com/gin-gonic/gin",
                   "group": "", "version": "1.9.0"}
        patched, changed = patch_manifest(content, dep, "1.9.1")
        self.assertTrue(changed)
        self.assertIn("v1.9.1", patched)

    def test_nuget_csproj(self):
        content = '<PackageReference Include="Newtonsoft.Json" Version="12.0.0" />'
        dep     = {"ecosystem": "NuGet", "artifact": "Newtonsoft.Json",
                   "group": "", "version": "12.0.0"}
        patched, changed = patch_manifest(content, dep, "13.0.0")
        self.assertTrue(changed)
        self.assertIn('Version="13.0.0"', patched)


class TestIsLicenseBlocked(unittest.TestCase):
    def test_gpl_blocked(self):
        self.assertTrue(is_license_blocked("GPL-3.0"))
        self.assertTrue(is_license_blocked("GNU GENERAL PUBLIC LICENSE"))

    def test_agpl_blocked(self):
        self.assertTrue(is_license_blocked("AGPL-3.0-only"))

    def test_mit_allowed(self):
        self.assertFalse(is_license_blocked("MIT"))

    def test_apache_allowed(self):
        self.assertFalse(is_license_blocked("Apache-2.0"))

    def test_unknown_not_blocked(self):
        self.assertFalse(is_license_blocked("UNKNOWN"))

    def test_empty_not_blocked(self):
        self.assertFalse(is_license_blocked(""))
        self.assertFalse(is_license_blocked(None))  # type: ignore[arg-type]

    def test_custom_blocklist(self):
        self.assertTrue(is_license_blocked("CUSTOM-BAD-1.0", ["CUSTOM-BAD"]))
        self.assertFalse(is_license_blocked("MIT", ["CUSTOM-BAD"]))


class TestParsePom(unittest.TestCase):
    POM = """\
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <properties>
    <junit.version>5.8.1</junit.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-core</artifactId>
      <version>5.3.20</version>
      <scope>compile</scope>
    </dependency>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>${junit.version}</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>"""

    def test_dep_count(self):
        deps, _ = parse_pom(self.POM)
        self.assertEqual(len(deps), 2)

    def test_compile_dep(self):
        deps, _ = parse_pom(self.POM)
        spring  = next(d for d in deps if d["artifact"] == "spring-core")
        self.assertEqual(spring["version"], "5.3.20")
        self.assertEqual(spring["ecosystem"], "Maven")
        self.assertFalse(spring["test"])

    def test_test_dep_marked(self):
        deps, _ = parse_pom(self.POM)
        junit   = next(d for d in deps if d["artifact"] == "junit-jupiter")
        self.assertTrue(junit["test"])

    def test_property_resolution(self):
        deps, props = parse_pom(self.POM)
        junit = next(d for d in deps if d["artifact"] == "junit-jupiter")
        self.assertEqual(junit["version"], "5.8.1")
        self.assertIn("junit.version", props)

    def test_purl_format(self):
        deps, _ = parse_pom(self.POM)
        spring  = next(d for d in deps if d["artifact"] == "spring-core")
        self.assertTrue(spring["purl"].startswith("pkg:maven/"))


class TestParsePomPlugins(unittest.TestCase):
    POM_WITH_PLUGINS = """\
<project>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.10.1</version>
      </plugin>
    </plugins>
  </build>
</project>"""

    def test_finds_plugin(self):
        plugins = parse_pom_plugins(self.POM_WITH_PLUGINS, {})
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0]["artifact"], "maven-compiler-plugin")
        self.assertEqual(plugins[0]["version"], "3.10.1")
        self.assertTrue(plugins[0].get("is_plugin"))

    def test_no_build_section(self):
        plugins = parse_pom_plugins("<project></project>", {})
        self.assertEqual(plugins, [])


class TestParseRequirementsTxt(unittest.TestCase):
    CONTENT = """\
# production deps
flask==2.3.0
requests>=2.28.0
sqlalchemy~=1.4.0
# comment line
-r other.txt
"""

    def test_parses_packages(self):
        deps = parse_requirements_txt(self.CONTENT)
        names = [d["artifact"] for d in deps]
        self.assertIn("flask", names)
        self.assertIn("requests", names)
        self.assertIn("sqlalchemy", names)

    def test_skips_comment_and_flags(self):
        deps = parse_requirements_txt(self.CONTENT)
        self.assertEqual(len(deps), 3)

    def test_ecosystem_is_pypi(self):
        deps = parse_requirements_txt("numpy==1.24.0\n")
        self.assertEqual(deps[0]["ecosystem"], "PyPI")

    def test_version_captured(self):
        deps = parse_requirements_txt("flask==2.3.0\n")
        self.assertEqual(deps[0]["version"], "2.3.0")


class TestParsePackageJson(unittest.TestCase):
    PKG = json.dumps({
        "dependencies": {"express": "^4.18.0", "axios": "~1.4.0"},
        "devDependencies": {"jest": "29.0.0"},
    })

    def test_prod_deps(self):
        deps = parse_package_json(self.PKG)
        names = [d["artifact"] for d in deps]
        self.assertIn("express", names)
        self.assertIn("axios", names)

    def test_dev_dep_marked(self):
        deps = parse_package_json(self.PKG)
        jest = next(d for d in deps if d["artifact"] == "jest")
        self.assertTrue(jest["test"])

    def test_ecosystem_npm(self):
        deps = parse_package_json(self.PKG)
        self.assertTrue(all(d["ecosystem"] == "npm" for d in deps))

    def test_version_strips_prefix(self):
        deps = parse_package_json(self.PKG)
        express = next(d for d in deps if d["artifact"] == "express")
        self.assertEqual(express["version"], "4.18.0")

    def test_invalid_json_returns_empty(self):
        self.assertEqual(parse_package_json("not json"), [])


class TestParseCsproj(unittest.TestCase):
    CSPROJ = """\
<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
    <PackageReference Include="Microsoft.Extensions.Logging" Version="7.0.0" />
  </ItemGroup>
</Project>"""

    def test_finds_packages(self):
        deps = parse_csproj(self.CSPROJ)
        names = [d["artifact"] for d in deps]
        self.assertIn("Newtonsoft.Json", names)
        self.assertIn("Microsoft.Extensions.Logging", names)

    def test_ecosystem_nuget(self):
        deps = parse_csproj(self.CSPROJ)
        self.assertTrue(all(d["ecosystem"] == "NuGet" for d in deps))

    def test_version_correct(self):
        deps = parse_csproj(self.CSPROJ)
        nj   = next(d for d in deps if d["artifact"] == "Newtonsoft.Json")
        self.assertEqual(nj["version"], "13.0.1")


class TestParseGemfile(unittest.TestCase):
    GEMFILE = """\
source 'https://rubygems.org'
gem 'rails', '~> 7.0'
gem 'pg', '>= 0.18', '< 2.0'
gem 'puma', '5.6.5'
# comment
"""

    def test_finds_gems(self):
        deps = parse_gemfile(self.GEMFILE)
        names = [d["artifact"] for d in deps]
        self.assertIn("rails", names)
        self.assertIn("puma", names)

    def test_ecosystem_rubygems(self):
        deps = parse_gemfile(self.GEMFILE)
        self.assertTrue(all(d["ecosystem"] == "RubyGems" for d in deps))

    def test_version_extracted(self):
        deps = parse_gemfile(self.GEMFILE)
        puma = next(d for d in deps if d["artifact"] == "puma")
        self.assertEqual(puma["version"], "5.6.5")


class TestParseGoMod(unittest.TestCase):
    GO_MOD = """\
module github.com/myorg/myapp

go 1.21

require (
\tgithub.com/gin-gonic/gin v1.9.1
\tgolang.org/x/net v0.15.0
)
"""

    def test_finds_modules(self):
        deps = parse_go_mod(self.GO_MOD)
        names = [d["artifact"] for d in deps]
        self.assertIn("github.com/gin-gonic/gin", names)
        self.assertIn("golang.org/x/net", names)

    def test_ecosystem_go(self):
        deps = parse_go_mod(self.GO_MOD)
        self.assertTrue(all(d["ecosystem"] == "Go" for d in deps))

    def test_version_strips_v_prefix(self):
        deps = parse_go_mod(self.GO_MOD)
        gin  = next(d for d in deps if "gin-gonic" in d["artifact"])
        self.assertEqual(gin["version"], "1.9.1")

    def test_single_line_require(self):
        content = "module x\nrequire golang.org/x/text v0.13.0\n"
        deps = parse_go_mod(content)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0]["version"], "0.13.0")


class TestOsvPackageSpec(unittest.TestCase):
    def test_maven_uses_group_artifact(self):
        dep  = {"ecosystem": "Maven", "group": "org.springframework", "artifact": "spring-core"}
        spec = _osv_package_spec(dep)
        self.assertEqual(spec["name"], "org.springframework:spring-core")
        self.assertEqual(spec["ecosystem"], "Maven")

    def test_pypi_uses_artifact_only(self):
        dep  = {"ecosystem": "PyPI", "group": "", "artifact": "flask"}
        spec = _osv_package_spec(dep)
        self.assertEqual(spec["name"], "flask")
        self.assertEqual(spec["ecosystem"], "PyPI")

    def test_npm(self):
        dep  = {"ecosystem": "npm", "group": "", "artifact": "express"}
        spec = _osv_package_spec(dep)
        self.assertEqual(spec["ecosystem"], "npm")
        self.assertEqual(spec["name"], "express")

    def test_go(self):
        dep  = {"ecosystem": "Go", "group": "", "artifact": "github.com/gin-gonic/gin"}
        spec = _osv_package_spec(dep)
        self.assertEqual(spec["ecosystem"], "Go")


# ─────────────────────────────────────────────────────────────────────────────
# Runner — collects results and writes test-results.json for Stage 7 injection
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loader  = unittest.TestLoader()
    suite   = loader.loadTestsFromModule(sys.modules[__name__])
    runner  = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result  = runner.run(suite)

    total   = result.testsRun
    failed  = len(result.failures) + len(result.errors)
    passed  = total - failed

    test_details = []
    for case, tb in result.failures:
        test_details.append({"name": str(case), "status": "FAIL", "detail": tb[:300]})
    for case, tb in result.errors:
        test_details.append({"name": str(case), "status": "ERROR", "detail": tb[:300]})

    # Collect passed names: all tests minus failures/errors
    fail_names = {str(c) for c, _ in result.failures + result.errors}
    for test in suite:
        if hasattr(test, "__iter__"):
            for sub in test:
                if str(sub) not in fail_names:
                    test_details.append({"name": str(sub), "status": "PASS", "detail": ""})
        else:
            if str(test) not in fail_names:
                test_details.append({"name": str(test), "status": "PASS", "detail": ""})

    out = {
        "total": total, "passed": passed, "failed": failed,
        "success": failed == 0,
        "tests":  test_details,
    }
    results_path = os.path.join(os.path.dirname(__file__), "test-results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nTest results written to {results_path}")
    sys.exit(0 if result.wasSuccessful() else 1)
