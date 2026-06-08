# Business Criticality Tags — Format Reference

Users can supply tags either interactively (in chat) or by uploading a `criticality-tags.json` file.

---

## File Format: `criticality-tags.json`

```json
{
  "tags": [
    {
      "artifact": "org.springframework:spring-core",
      "tags": ["core"]
    },
    {
      "artifact": "com.stripe:stripe-java",
      "tags": ["payment"]
    },
    {
      "artifact": "org.springframework.security:spring-security-core",
      "tags": ["auth", "core"]
    },
    {
      "artifact": "ch.qos.logback:logback-classic",
      "tags": ["logging"]
    }
  ]
}
```

### Notes
- `artifact` is matched as a **prefix** against the full GAV — version is optional.
  - `"org.springframework:spring-core"` matches `org.springframework:spring-core:5.3.20`
- Multiple tags are allowed; the **highest** factor among them is used (see `scoring-formulas.md`).
- Unmatched dependencies default to the neutral factor (0.50).

---

## Accepted Tag Values

| Tag | biz_factor |
|-----|-----------|
| `payment` | 1.00 |
| `auth` | 1.00 |
| `core` | 0.90 |
| `public-api` | 0.85 |
| `data-storage` | 0.80 |
| `internal-api` | 0.60 |
| `logging` | 0.40 |
| `test` | 0.10 |

Any unrecognized tag defaults to **0.50**.

---

## Interactive Tagging (chat)

If no file is provided, Claude presents a numbered list of dependencies and asks for tags inline.
The user can respond naturally, e.g.:

```
1 → payment
3 → auth, core
5 → logging
```

Or skip with: `"no tags"` / `"default all"` to accept neutral (0.50) for all.