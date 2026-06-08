# License Policy — Supply-Chain Audit Plugin

## Default Allowlist (Permitted Licenses)

These SPDX license identifiers are permitted by default for commercial Java projects:

```
Apache-2.0
MIT
BSD-2-Clause
BSD-3-Clause
ISC
CDDL-1.0
CDDL-1.1
EPL-1.0
EPL-2.0
MPL-2.0
CC0-1.0
Unlicense
```

---

## Blocked Licenses (Copyleft — not permitted in commercial projects by default)

```
GPL-2.0
GPL-2.0-only
GPL-2.0-or-later
GPL-3.0
GPL-3.0-only
GPL-3.0-or-later
LGPL-2.0
LGPL-2.1
LGPL-3.0
AGPL-3.0
SSPL-1.0
EUPL-1.1
EUPL-1.2
```

---

## Unknown License Handling

| Setting | Behavior |
|---------|----------|
| `warn` (default) | Flag as warning — does not block PR |
| `block` | Treat missing license as a violation — blocks PR |

To change: edit the `unknown_license_action` value below.

```
unknown_license_action: warn
```

---

## Customising the Allowlist

To add a license (e.g. a dual-licensed commercial artifact):

1. Add the SPDX identifier to the allowlist above
2. Add a comment explaining why it was approved:
   ```
   LGPL-2.1   # Approved for dynamically-linked use only — approved by Legal 2024-03-01
   ```

To add a per-artifact license exception:

```json
{
  "exceptions": [
    {
      "artifact": "org.example:special-lib",
      "license": "GPL-2.0",
      "reason": "Dynamically linked, legal approved 2024-01-15",
      "approved_by": "legal@company.com"
    }
  ]
}
```

Save exceptions to `references/license-exceptions.json`.

---

## SPDX Reference

Full SPDX license list: https://spdx.org/licenses/

Common Maven artifact licenses and their SPDX identifiers:

| Artifact Family | Common License | SPDX ID | Permitted? |
|-----------------|---------------|---------|-----------|
| Spring Framework | Apache 2.0 | `Apache-2.0` | ✅ |
| Jackson | Apache 2.0 | `Apache-2.0` | ✅ |
| Guava | Apache 2.0 | `Apache-2.0` | ✅ |
| JUnit 5 | EPL 2.0 | `EPL-2.0` | ✅ |
| Hibernate ORM | LGPL 2.1 | `LGPL-2.1` | ❌ (default) |
| GNU Classpath | GPL 2.0 | `GPL-2.0` | ❌ |
| MySQL Connector/J | GPL 2.0 | `GPL-2.0` | ❌ (use commercial license) |