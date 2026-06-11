# Timing Thresholds — E2E Stress Testing

Flag any stage that exceeds its WARNING or CRITICAL threshold in the e2e report.
Thresholds are per-repo; repos with 100+ deps may legitimately exceed WARNING.

| Stage | Expected | WARNING | CRITICAL |
|-------|----------|---------|----------|
| Setup (clone) | < 30s | > 2 min | > 5 min |
| Stage 1 — OWASP scan (first run, DB download) | < 20 min | > 25 min | > 40 min |
| Stage 1 — OWASP scan (subsequent, cached DB) | < 3 min | > 6 min | > 12 min |
| Stage 2 — Risk scoring | < 30s | > 2 min | > 5 min |
| Stage 3 — Syft SBOM generation | < 1 min | > 3 min | > 8 min |
| Stage 3 — Audit checks | < 2 min | > 5 min | > 10 min |
| Stage 4 — Version resolution (dry-run) | < 1 min | > 3 min | > 8 min |
| Stage 5 — mvn test | < 5 min | > 10 min | > 20 min |
| Stage 5 — OWASP re-scan | < 3 min | > 6 min | > 12 min |
| Stage 5 — Grype scan | < 1 min | > 3 min | > 6 min |
| Stage 5 — JaCoCo | < 6 min | > 12 min | > 25 min |

---

## NVD API Rate Limits

OWASP Dependency-Check calls the NVD API during database updates.
With an API key: 50 req/30s. Without: 5 req/30s.

If multiple repos run back-to-back, the NVD DB is cached after the first scan —
subsequent repo scans skip the DB download (much faster).

Ensure `$NVD_API_KEY` is set before running stress tests to avoid throttling.

---

## Maven Central Rate Limits

Stage 4 version resolution calls Maven Central search API.
Limit: ~10 req/s. Add `sleep 0.1` between calls for large dependency lists (> 50 deps).

---

## Timing Flag in Report

```json
{
  "stage": "stage1",
  "duration_seconds": 847,
  "timing_flag": "WARNING",
  "timing_note": "Exceeded 6 min threshold — likely first run with DB download"
}
```