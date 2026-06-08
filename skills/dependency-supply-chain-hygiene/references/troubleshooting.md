# Troubleshooting

## Common Errors & Fixes

### "Connection refused" / NVD download fails
**Cause:** Rate limited or no NVD API key.
**Fix:**
```bash
# Get an API key: https://nvd.nist.gov/developers/request-an-api-key
dependency-check --nvdApiKey YOUR_KEY ...
```
Without a key, the tool is limited to 5 requests/30 seconds — scans will time out on large projects.

---

### Database is locked
**Cause:** Another scan is running, or a previous run crashed mid-update.
**Fix:**
```bash
rm -f ~/.dependency-check/data/*.lock
```

---

### "Unable to determine project info" (Node.js / Python)
**Cause:** Experimental analyzers are off by default.
**Fix:** Add `--enableExperimental` to the scan command.

---

### False positives (LOW confidence matches)
**Cause:** Dependency-Check matches on file name/version patterns, not always exact package identity.
**Fix:** Review confidence level in JSON (`"confidence": "LOW"`). For confirmed false positives, add a suppression entry (see scan-commands.md).

---

### .NET scan fails — "mono not found"
**Cause:** Assembly analysis requires Mono on Linux/macOS.
**Fix:** Either install Mono, or skip assembly analysis:
```bash
dependency-check --disableAssembly ...
```

---

### Scan is extremely slow (first run)
**Cause:** Downloading the full NVD database (~500MB).
**Expected duration:** 10–20 minutes on first run, 1–3 minutes thereafter.
**Fix for CI:** Cache `~/.dependency-check/data` between pipeline runs.

---

### "CVSS score not available" for a CVE
**Cause:** NVD has not yet assigned a CVSS score to a newly published CVE.
**Fix:** Treat as High severity by default until CVSS is published. Check https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXXX manually.

---

### Report shows 0 vulnerabilities (unexpectedly)
**Checklist:**
1. Is the NVD database up to date? Run with `--updateOnly` first.
2. Are the correct manifest files being scanned? Verify `--scan` paths.
3. Is `--enableExperimental` set for Node.js / Python / Ruby?
4. Is the database populated? Delete and re-download: `rm -rf ~/.dependency-check/data`

---

### Maven plugin: `BUILD FAILURE` on `dependency-check:check`
**Cause:** `failBuildOnCVSS` threshold breached — this is intentional behaviour.
**Fix:** Either fix the vulnerable dependencies, or temporarily suppress specific CVEs with a suppression file while a fix is in progress.