# PDF Generation — Audit Trail & Demo Readiness

## Primary: WeasyPrint

WeasyPrint renders the HTML report to PDF with full CSS support including charts.

### Installation

```bash
# Ubuntu / Debian
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0
pip install weasyprint --break-system-packages

# macOS
brew install pango
pip install weasyprint --break-system-packages

# Verify
python3 -c "import weasyprint; print(weasyprint.__version__)"
```

### Generate PDF

```python
from weasyprint import HTML, CSS

HTML(filename="dependency-health-report.html").write_pdf(
    "dependency-health-report.pdf",
    stylesheets=[CSS(string="@page { size: A4; margin: 1.5cm; }")]
)
```

### Chart Rendering Note

WeasyPrint does not execute JavaScript — Chart.js charts won't render.
Use static SVG charts in the PDF version instead. The `templates/report.html`
template includes both a `<canvas>` (for interactive HTML) and an `<svg>` fallback
(for PDF). The PDF CSS hides canvas and shows SVG:

```css
@media print {
  canvas { display: none; }
  .svg-chart { display: block; }
}
```

---

## Fallback: Markdown → HTML → PDF (if WeasyPrint unavailable)

```bash
pip install markdown2 pdfkit --break-system-packages
# Requires wkhtmltopdf: https://wkhtmltopdf.org/downloads.html

python3 - <<'EOF'
import markdown2, pdfkit

with open("dependency-health-report.md") as f:
    md = f.read()

html = markdown2.markdown(md, extras=["tables", "fenced-code-blocks"])
full_html = f"""
<html><head>
<style>
  body {{ font-family: sans-serif; max-width: 900px; margin: 2cm auto; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
  th {{ background: #f4f4f4; }}
  h1 {{ color: #1a1a2e; }} h2 {{ color: #16213e; }}
</style>
</head><body>{html}</body></html>
"""
pdfkit.from_string(full_html, "dependency-health-report.pdf")
print("PDF generated via fallback")
EOF
```

---

## Page Structure (PDF)

| Page | Content |
|------|---------|
| 1 | Cover: project name, date, health score + grade |
| 2 | Executive Summary: KPI cards, key findings, CVE donut (SVG) |
| 3 | Risk Tier breakdown, Top 5 risky deps table |
| 4 | Remediation summary, before/after comparison |
| 5+ | Technical Appendix: full CVE table, validation results, audit violations |
| Last | Compliance notes, tool versions, scan scope |