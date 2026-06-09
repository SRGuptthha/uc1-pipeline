#!/usr/bin/env python3
"""
UC1 Supply Chain Security Pipeline — Full Project Documentation Generator
Produces a detailed Word document explaining every file for first-time users.
Requires: pip install python-docx
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os, datetime

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x1e, 0x29, 0x3b)
TEAL   = RGBColor(0x0d, 0x94, 0x88)
ORANGE = RGBColor(0xf9, 0x73, 0x16)
GREEN  = RGBColor(0x16, 0xa3, 0x4a)
RED    = RGBColor(0xdc, 0x26, 0x26)
WHITE  = RGBColor(0xff, 0xff, 0xff)
LGRAY  = RGBColor(0xf1, 0xf5, 0xf9)
MGRAY  = RGBColor(0x94, 0xa3, 0xb8)
BLUE   = RGBColor(0x3b, 0x82, 0xf6)
AMBER  = RGBColor(0xf5, 0x9e, 0x0b)
DARK   = RGBColor(0x0f, 0x17, 0x2a)
CREAM  = RGBColor(0xff, 0xfb, 0xeb)
DGREEN = RGBColor(0x06, 0x5f, 0x46)
LGREEN = RGBColor(0xdc, 0xfc, 0xe7)
LRED   = RGBColor(0xfe, 0xe2, 0xe2)
LBLUE  = RGBColor(0xdb, 0xea, 0xfe)

# RGBColor is a (r,g,b) tuple — convert to 6-char hex string for XML attributes
def hx(c): return "%02X%02X%02X" % (c[0], c[1], c[2])

# ── Low-level XML helpers ─────────────────────────────────────────────────────
def set_cell_bg(cell, rgb: RGBColor):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hx(rgb))
    tcPr.append(shd)

def set_para_bg(para, rgb: RGBColor):
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hx(rgb))
    pPr.append(shd)

def add_border_bottom(para, color="1e293b", sz=12):
    pPr  = para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    str(sz))
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), color)
    pBdr.append(bot)
    pPr.append(pBdr)

def cell_borders(cell, color="d1d5db"):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBdr = OxmlElement("w:tcBdr")
    for side in ("top","left","bottom","right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"),   "single")
        el.set(qn("w:sz"),    "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        tcBdr.append(el)
    tcPr.append(tcBdr)

def no_space_before(para):
    pPr = para._p.get_or_add_pPr()
    spc = OxmlElement("w:spacing")
    spc.set(qn("w:before"), "0")
    spc.set(qn("w:after"),  "60")
    pPr.append(spc)

# ── Document-level helpers ────────────────────────────────────────────────────
doc = Document()

# Page margins (2 cm all round)
for sect in doc.sections:
    sect.top_margin    = Cm(2.2)
    sect.bottom_margin = Cm(2.2)
    sect.left_margin   = Cm(2.5)
    sect.right_margin  = Cm(2.5)

def add_heading(text, level=1, color=NAVY, size=None, bold=True, underline=False):
    para = doc.add_paragraph()
    no_space_before(para)
    run  = para.add_run(text)
    run.bold      = bold
    run.underline = underline
    run.font.color.rgb = color
    run.font.size      = Pt(size or {1:22, 2:16, 3:13, 4:11}.get(level, 11))
    if level == 1:
        add_border_bottom(para, hx(color), sz=16)
    return para

def add_para(text, size=10.5, bold=False, italic=False, color=None, indent=0):
    para = doc.add_paragraph()
    no_space_before(para)
    if indent:
        para.paragraph_format.left_indent = Cm(indent)
    run = para.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    return para

def add_bullet(text, level=0, size=10.5, color=None):
    para = doc.add_paragraph(style="List Bullet")
    no_space_before(para)
    para.paragraph_format.left_indent  = Cm(0.5 + level * 0.5)
    para.paragraph_format.space_before = Pt(1)
    run = para.add_run(text)
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    return para

def add_code(text, size=9):
    para = doc.add_paragraph()
    no_space_before(para)
    para.paragraph_format.left_indent = Cm(0.5)
    set_para_bg(para, LGRAY)
    run = para.add_run(text)
    run.font.size = Pt(size)
    run.font.name = "Courier New"
    run.font.color.rgb = DARK
    return para

def page_break():
    doc.add_page_break()

def add_spacer(n=1):
    for _ in range(n):
        p = doc.add_paragraph()
        no_space_before(p)
        p.paragraph_format.space_after = Pt(4)

# ── Coloured banner ───────────────────────────────────────────────────────────
def banner(text, bg=NAVY, fg=WHITE, size=12, bold=True):
    tbl  = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    cell = tbl.rows[0].cells[0]
    set_cell_bg(cell, bg)
    cell_borders(cell, hx(bg))
    para = cell.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run  = para.add_run(text)
    run.bold       = bold
    run.font.size  = Pt(size)
    run.font.color.rgb = fg
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after  = Pt(6)
    para.paragraph_format.left_indent  = Cm(0.3)
    add_spacer()
    return tbl

# ── Info box (coloured side-strip) ────────────────────────────────────────────
def info_box(lines, strip_color=TEAL, bg=LBLUE, label=""):
    tbl  = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl.columns[0].width = Emu(180000)   # ~3 mm strip
    tbl.columns[1].width = Emu(8000000)  # wide content
    strip_cell   = tbl.rows[0].cells[0]
    content_cell = tbl.rows[0].cells[1]
    set_cell_bg(strip_cell,   strip_color)
    set_cell_bg(content_cell, bg)
    cell_borders(strip_cell,   hx(strip_color))
    cell_borders(content_cell, hx(strip_color))
    if label:
        lp  = content_cell.add_paragraph()
        lr  = lp.add_run(label)
        lr.bold = True
        lr.font.size = Pt(9)
        lr.font.color.rgb = strip_color
        lp.paragraph_format.space_before = Pt(4)
        lp.paragraph_format.space_after  = Pt(2)
        lp.paragraph_format.left_indent  = Cm(0.3)
    for line in lines:
        p   = content_cell.add_paragraph()
        run = p.add_run(line)
        run.font.size = Pt(10)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after  = Pt(2)
        p.paragraph_format.left_indent  = Cm(0.3)
    add_spacer()

# ── Two-column key-value table ────────────────────────────────────────────────
def kv_table(rows_data, col1w=3.5, col2w=11):
    tbl = doc.add_table(rows=len(rows_data), cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl.columns[0].width = Cm(col1w)
    tbl.columns[1].width = Cm(col2w)
    for i, (k, v) in enumerate(rows_data):
        bg = LGRAY if i % 2 == 0 else WHITE
        c0 = tbl.rows[i].cells[0]
        c1 = tbl.rows[i].cells[1]
        set_cell_bg(c0, bg)
        set_cell_bg(c1, bg)
        cell_borders(c0); cell_borders(c1)
        rk = c0.paragraphs[0].add_run(k)
        rk.bold = True; rk.font.size = Pt(9.5)
        rv = c1.paragraphs[0].add_run(v)
        rv.font.size = Pt(9.5)
        for c in (c0, c1):
            c.paragraphs[0].paragraph_format.space_before = Pt(3)
            c.paragraphs[0].paragraph_format.space_after  = Pt(3)
            c.paragraphs[0].paragraph_format.left_indent  = Cm(0.2)
    add_spacer()

# ── Generic data table with header row ───────────────────────────────────────
def data_table(headers, rows_data, col_widths=None):
    tbl = doc.add_table(rows=1+len(rows_data), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    if col_widths:
        for i, w in enumerate(col_widths):
            tbl.columns[i].width = Cm(w)
    # Header
    hrow = tbl.rows[0]
    for i, h in enumerate(headers):
        c = hrow.cells[i]
        set_cell_bg(c, NAVY)
        cell_borders(c, "1e293b")
        run = c.paragraphs[0].add_run(h)
        run.bold = True; run.font.size = Pt(9.5); run.font.color.rgb = WHITE
        c.paragraphs[0].paragraph_format.space_before = Pt(4)
        c.paragraphs[0].paragraph_format.space_after  = Pt(4)
        c.paragraphs[0].paragraph_format.left_indent  = Cm(0.2)
    # Data rows
    for ri, row in enumerate(rows_data):
        bg = LGRAY if ri % 2 == 0 else WHITE
        trow = tbl.rows[ri+1]
        for ci, val in enumerate(row):
            c   = trow.cells[ci]
            set_cell_bg(c, bg); cell_borders(c)
            run = c.paragraphs[0].add_run(str(val))
            run.font.size = Pt(9.5)
            c.paragraphs[0].paragraph_format.space_before = Pt(3)
            c.paragraphs[0].paragraph_format.space_after  = Pt(3)
            c.paragraphs[0].paragraph_format.left_indent  = Cm(0.2)
    add_spacer()

# ── Pipeline flow diagram (visual boxes) ─────────────────────────────────────
def pipeline_diagram():
    stages = [
        ("Setup",    "Language\nDetection",     TEAL,   WHITE),
        ("Stage 1",  "CVE Scan\n(OSV.dev)",     RED,    WHITE),
        ("Stage 1.5","SBOM\nGeneration",         BLUE,   WHITE),
        ("Stage 2",  "Risk\nScoring",            AMBER,  DARK),
        ("Stage 3",  "Supply Chain\nAudit",      NAVY,   WHITE),
        ("Stage 3.5","Secret\nDetection",        ORANGE, WHITE),
        ("Stage 3.7","Policy\nEnforcement",      MGRAY,  DARK),
        ("Stage 3.9","Drift\nDetection",         TEAL,   WHITE),
        ("Stage 4",  "Auto\nRemediation",        GREEN,  WHITE),
        ("Stage 5",  "PR\nValidation",           BLUE,   WHITE),
        ("Stage 6",  "E2E\nStress Test",         NAVY,   WHITE),
        ("Stage 7",  "Health\nReport",           DGREEN, WHITE),
        ("Stage 7a", "Unit\nTests",              MGRAY,  DARK),
    ]
    # 4 boxes per row
    per_row = 4
    rows_needed = (len(stages) + per_row - 1) // per_row
    for r in range(rows_needed):
        chunk = stages[r*per_row : r*per_row+per_row]
        cols  = len(chunk) * 2 - 1   # boxes + arrows
        tbl   = doc.add_table(rows=2, cols=cols)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        box_w = Cm(3.5); arr_w = Cm(0.5)
        for ci in range(cols):
            tbl.columns[ci].width = box_w if ci % 2 == 0 else arr_w
        for bi, (label, desc, bg, fg) in enumerate(chunk):
            col_idx = bi * 2
            # Label row
            top_cell = tbl.rows[0].cells[col_idx]
            set_cell_bg(top_cell, bg)
            cell_borders(top_cell, hx(bg))
            top_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            lp  = top_cell.paragraphs[0]
            lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            lr  = lp.add_run(label)
            lr.bold = True; lr.font.size = Pt(7.5); lr.font.color.rgb = fg
            lp.paragraph_format.space_before = Pt(4)
            # Desc row
            bot_cell = tbl.rows[1].cells[col_idx]
            set_cell_bg(bot_cell, bg)
            cell_borders(bot_cell, hx(bg))
            bot_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            dp  = bot_cell.paragraphs[0]
            dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            dr  = dp.add_run(desc)
            dr.font.size = Pt(7); dr.font.color.rgb = fg
            dp.paragraph_format.space_after = Pt(4)
            # Arrow (except last box in row)
            if bi < len(chunk) - 1:
                for rownum in range(2):
                    ac = tbl.rows[rownum].cells[col_idx + 1]
                    set_cell_bg(ac, WHITE)
                    cell_borders(ac, "ffffff")
                    ap = ac.paragraphs[0]
                    ap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    ar = ap.add_run("→" if rownum == 0 else "")
                    ar.font.size = Pt(10); ar.bold = True
                    ar.font.color.rgb = MGRAY
        add_spacer()

# ── File card ─────────────────────────────────────────────────────────────────
def file_card(filename, location, size_info, purpose, what_it_does,
              key_sections=None, output=None, when_runs=None, example_lines=None):
    # Header bar
    tbl  = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl.columns[0].width = Cm(11)
    tbl.columns[1].width = Cm(5)
    lc = tbl.rows[0].cells[0]
    rc = tbl.rows[0].cells[1]
    set_cell_bg(lc, NAVY); set_cell_bg(rc, TEAL)
    cell_borders(lc, "1e293b"); cell_borders(rc, "0d9488")
    lp = lc.paragraphs[0]
    lr = lp.add_run(f"  {filename}")
    lr.bold = True; lr.font.size = Pt(12); lr.font.color.rgb = WHITE
    lp.paragraph_format.space_before = Pt(5)
    lp.paragraph_format.space_after  = Pt(5)
    rp = rc.paragraphs[0]
    rr = rp.add_run(f"  {location}")
    rr.font.size = Pt(9); rr.font.color.rgb = WHITE
    rp.paragraph_format.space_before = Pt(5)
    rp.paragraph_format.space_after  = Pt(5)
    add_spacer()

    kv_table([
        ("File",      filename),
        ("Location",  location),
        ("Size",      size_info),
        ("Purpose",   purpose),
    ], col1w=3, col2w=13)

    add_heading("What It Does", level=3, color=TEAL)
    add_para(what_it_does, size=10.5)

    if key_sections:
        add_heading("Key Sections / Contents", level=3, color=TEAL)
        for item in key_sections:
            add_bullet(item)

    if output:
        add_heading("Output / Result", level=3, color=GREEN)
        for item in output:
            add_bullet(item)

    if when_runs:
        add_heading("When Does It Run?", level=3, color=AMBER)
        add_para(when_runs, size=10.5)

    if example_lines:
        add_heading("Sample Content", level=3, color=MGRAY)
        for line in example_lines:
            add_code(line)

    add_spacer(2)

# ══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT CONTENT STARTS HERE
# ══════════════════════════════════════════════════════════════════════════════

# ── COVER PAGE ────────────────────────────────────────────────────────────────
tbl = doc.add_table(rows=1, cols=1)
c   = tbl.rows[0].cells[0]
set_cell_bg(c, NAVY)
cell_borders(c, "1e293b")
cp = c.paragraphs[0]
cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp.paragraph_format.space_before = Pt(40)
cp.paragraph_format.space_after  = Pt(8)
t1 = cp.add_run("UC1 Supply Chain Security Pipeline")
t1.bold = True; t1.font.size = Pt(26); t1.font.color.rgb = WHITE
cp2 = c.add_paragraph()
cp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
t2  = cp2.add_run("Complete Project Documentation")
t2.font.size = Pt(16); t2.font.color.rgb = TEAL
cp2.paragraph_format.space_after = Pt(6)
cp3 = c.add_paragraph()
cp3.alignment = WD_ALIGN_PARAGRAPH.CENTER
t3  = cp3.add_run("A detailed guide for first-time users — every file explained")
t3.font.size = Pt(11); t3.font.color.rgb = MGRAY; t3.italic = True
cp3.paragraph_format.space_after = Pt(40)

add_spacer(2)
add_para(f"Generated: {datetime.date.today().strftime('%d %B %Y')}  |  Version 1.0  |  UC1 Project", size=9,
         color=MGRAY)
page_break()

# ── TABLE OF CONTENTS ─────────────────────────────────────────────────────────
add_heading("Table of Contents", level=1, color=NAVY)
toc = [
    ("1", "What Is This Project?",              "Plain-English Overview"),
    ("2", "How the Pipeline Works",             "Stage-by-Stage Visual Flow"),
    ("3", "Project Folder Structure",           "Complete Directory Tree"),
    ("4", "Core Executable — run_pipeline.py",  "Main Script (~2600 lines)"),
    ("5", "Unit Tests — test_pipeline.py",      "63 Automated Tests"),
    ("6", "Configuration Files",                "policy.json · .gitleaks.toml"),
    ("7", "HTML Dashboard — report.html",       "Interactive Report Template"),
    ("8", "Generated Output Files",             "15 Files Created Per Run"),
    ("9", "Agents",                             "pr-validation · risk-scoring"),
    ("10","Plugins",                            "policy-enforcer · supply-chain-audit"),
    ("11","Skills",                             "8 Specialist Capability Modules"),
    ("12","Documentation Files",                "README · SETUP · PIPELINE_GUIDE · FLOW_DIAGRAM"),
    ("13","Utility Scripts",                    "generate_ppt.py · e2e_language_test.py"),
    ("13a","GitHub Actions Workflow",           ".github/workflows/security-scan.yml"),
    ("13b","MCP Server",                        "pipeline-output/mcp_server.py · .mcp.json"),
    ("14","First-Run Quick Guide",              "Step-by-Step for New Users"),
    ("15","Glossary",                           "Key Terms Explained"),
]
data_table(["#", "Section", "Contents"], toc, col_widths=[1, 7, 8])
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — WHAT IS THIS PROJECT?
# ══════════════════════════════════════════════════════════════════════════════
add_heading("1. What Is This Project?", level=1)
add_para(
    "The UC1 Supply Chain Security Pipeline is an automated security scanner "
    "for software projects hosted on GitHub. In simple terms: you point it at any "
    "GitHub repository, and it automatically finds security vulnerabilities in that "
    "project's dependencies (the third-party libraries the project uses), scores how "
    "dangerous each vulnerability is, checks for licensing problems, scans for "
    "accidentally committed passwords or API keys, enforces your organisation's "
    "security policies, and even creates a pull request on GitHub to fix the problems — "
    "all automatically, in under two minutes.",
    size=10.5
)
add_spacer()

add_heading("Why Does It Exist?", level=2, color=TEAL)
add_para(
    "Most software projects rely on hundreds of third-party libraries. Each library "
    "can have security vulnerabilities (known as CVEs — Common Vulnerabilities and "
    "Exposures). Tracking these manually is impossible. UC1 automates the entire "
    "process: scan → report → fix → verify → repeat.",
    size=10.5
)
add_spacer()

add_heading("What Languages Does It Support?", level=2, color=TEAL)
data_table(
    ["Language", "Package Manager", "Manifest File Detected"],
    [
        ("Java",       "Maven",     "pom.xml"),
        ("Python",     "PyPI",      "requirements.txt  or  pyproject.toml"),
        ("Node.js",    "npm",       "package.json"),
        (".NET",       "NuGet",     "*.csproj"),
        ("Ruby",       "RubyGems",  "Gemfile"),
        ("Go",         "Go Modules","go.mod"),
    ],
    col_widths=[3.5, 4, 8.5]
)

add_heading("Key Facts for First-Time Users", level=2, color=TEAL)
info_box([
    "  No installation needed beyond Python 3.9+  — the pipeline uses only Python's built-in standard library.",
    "  One command to run:  python pipeline-output/run_pipeline.py <github-url>",
    "  Dry-run by default  — it reads the repo and generates reports without writing anything to GitHub.",
    "  Add --token <your-pat>  to enable live mode, which creates a real fix branch and pull request.",
    "  All outputs are written to the pipeline-output/ folder as JSON/HTML files.",
], strip_color=GREEN, bg=LGREEN, label="QUICK FACTS")
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — HOW THE PIPELINE WORKS
# ══════════════════════════════════════════════════════════════════════════════
add_heading("2. How the Pipeline Works — Stage by Stage", level=1)
add_para(
    "When you run the pipeline, it goes through 13 stages in sequence. Each stage "
    "builds on the results of the previous one. The diagram below shows the full flow:",
    size=10.5
)
add_spacer()

pipeline_diagram()

add_spacer()
add_heading("What Each Stage Does", level=2, color=TEAL)
stages_desc = [
    ("Setup",       "Detects the project language by probing GitHub for manifest files (pom.xml, requirements.txt, etc.), then downloads the manifest and parses all dependencies."),
    ("Stage 1",     "CVE Scan — queries OSV.dev (Google's open vulnerability database) for every dependency. Finds known security holes and their CVSS severity scores."),
    ("Stage 1.5",   "SBOM Generation — creates a Software Bill of Materials in CycloneDX 1.5 format listing every dependency with its version, licence, and hash."),
    ("Stage 2",     "Risk Scoring — ranks each vulnerable dependency by composite risk (CVE severity + business criticality + exposure + maintenance health). Outputs a 0-100 score."),
    ("Stage 3",     "Supply-Chain Audit — checks for typosquatting (fake packages with similar names), untrusted sources, and licence violations."),
    ("Stage 3.5",   "Secret Detection — scans the manifest file for accidentally committed passwords, API keys, tokens, or private keys."),
    ("Stage 3.7",   "Policy Enforcement — applies your organisation's rules from policy.json (e.g. zero Critical CVEs allowed, no GPL licences)."),
    ("Stage 3.9",   "Drift Detection — compares current dependencies against the last saved baseline. Flags newly added or changed packages."),
    ("Stage 4",     "Auto-Remediation — looks up the latest safe version for each vulnerable dependency, patches the manifest file, and creates a consolidated GitHub pull request."),
    ("Stage 5",     "PR Validation — runs 4 validation gates on the fix PR: unit tests, OWASP re-scan, Grype container scan, JaCoCo code coverage."),
    ("Stage 6",     "E2E Stress Test — re-runs the full pipeline against the same repo as a sanity check, measuring performance."),
    ("Stage 7",     "Health Report — aggregates all results into a health score (0-100, grade A-F) and generates the interactive HTML dashboard."),
    ("Stage 7a",    "Unit Tests — runs all 63 built-in unit tests to verify the pipeline itself is working correctly."),
]
data_table(["Stage", "What It Does"], stages_desc, col_widths=[2.5, 13.5])
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — PROJECT FOLDER STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════
add_heading("3. Project Folder Structure", level=1)
add_para(
    "Here is every folder and file in the project, with a brief description of its role:",
    size=10.5
)
add_spacer()

tree_lines = [
    "UC1/",
    "├── .mcp.json                 ← MCP server config (auto-loaded by Claude Code)",
    "├── .github/",
    "│   └── workflows/",
    "│       └── security-scan.yml ← Live GitHub Actions CI/CD workflow",
    "│",
    "├── pipeline-output/          ← Main working directory (run everything from here)",
    "│   ├── run_pipeline.py       ← MAIN SCRIPT — the entire pipeline in one file",
    "│   ├── mcp_server.py         ← MCP server exposing pipeline as Claude tools",
    "│   ├── test_pipeline.py      ← 63 unit tests for the pipeline helpers",
    "│   ├── policy.json           ← Security policy thresholds (edit to customise)",
    "│   ├── .gitleaks.toml        ← Secret-detection allow-list",
    "│   ├── setup_demo_repo.py    ← One-time script to seed the demo GitHub repo",
    "│   └── [generated outputs]   ← JSON/HTML/YAML files created when pipeline runs",
    "│",
    "├── skills/                   ← Documentation for 8 specialist capabilities",
    "│   ├── audit-trail-demo/     ← Health report aggregation & HTML dashboard",
    "│   ├── auto-remediation-skill/  ← GitHub PR creation & manifest patching",
    "│   ├── dependency-drift-detector/  ← Baseline comparison & drift tracking",
    "│   ├── dependency-supply-chain-hygiene/  ← OWASP/OSV CVE scanning",
    "│   ├── e2e-stress-testing/   ← End-to-end test framework",
    "│   ├── github-actions-generator/  ← CI/CD workflow generation",
    "│   ├── sbom-generator/       ← Software Bill of Materials (CycloneDX)",
    "│   └── secret-detection/     ← Leaked credential scanning",
    "│",
    "├── agents/                   ← Documentation for 2 orchestration agents",
    "│   ├── pr-validation-agent/  ← Coordinates Stage 5 validation gates",
    "│   └── risk-scoring-agent/   ← Coordinates Stage 2 risk calculation",
    "│",
    "├── plugins/                  ← Documentation for 2 enforcement plugins",
    "│   ├── policy-as-code-enforcer/   ← Stage 3.7 policy engine",
    "│   └── supply-chain-audit-plugin/ ← Stage 3 typosquatting & licence checks",
    "│",
    "├── CLAUDE.md                 ← AI assistant project context (auto-read by Claude Code)",
    "├── SETUP.md                  ← First-run setup checklist",
    "├── README.md                 ← Project overview",
    "├── PIPELINE_GUIDE.md         ← End-to-end stage documentation",
    "├── FLOW_DIAGRAM.md           ← Mermaid architecture diagrams",
    "├── generate_ppt.py           ← PowerPoint slide deck generator",
    "├── generate_docs.py          ← This Word document generator",
    "├── e2e_language_test.py      ← Multi-language end-to-end test runner",
    "└── UC1_Security_Pipeline_Demo.pptx  ← Generated 14-slide presentation",
]
for line in tree_lines:
    add_code(line, size=8.5)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — run_pipeline.py
# ══════════════════════════════════════════════════════════════════════════════
add_heading("4. Core Executable — run_pipeline.py", level=1)
banner("pipeline-output/run_pipeline.py  —  The Heart of the Project", bg=NAVY)

add_para(
    "This is the single most important file in the entire project. It is a self-contained "
    "Python script approximately 2,600 lines long that does everything: fetches the "
    "repository's dependency manifest from GitHub, calls vulnerability databases, scores "
    "risk, audits licences, detects secrets, enforces policies, patches the manifest file, "
    "creates a GitHub pull request, validates it, and produces all output reports. "
    "Nothing else needs to be installed — it uses only Python's built-in standard library.",
    size=10.5
)
add_spacer()

add_heading("How to Run It", level=2, color=TEAL)
add_code("# Dry-run (no GitHub token needed):")
add_code("python pipeline-output/run_pipeline.py https://github.com/owner/repo")
add_spacer()
add_code("# Live mode (creates a real pull request on GitHub):")
add_code("python pipeline-output/run_pipeline.py https://github.com/owner/repo --token ghp_xxx")
add_spacer()
add_code("# Write outputs to a custom directory:")
add_code("python pipeline-output/run_pipeline.py https://github.com/owner/repo --out-dir C:\\scans\\output")
add_spacer()

add_heading("Internal Architecture", level=2, color=TEAL)
add_para(
    "The file is structured in three zones. Understanding this structure helps if you "
    "ever need to read or modify the code:",
    size=10.5
)

data_table(
    ["Zone", "Lines (approx.)", "What Is In It"],
    [
        ("Imports & Constants",  "1 – 100",     "Standard library imports (json, re, os, urllib, etc.), ECOSYSTEM_MAP, MANIFEST_CANDIDATES, policy defaults, CVE severity thresholds."),
        ("Helpers Section",      "100 – 850",   "Pure functions: parse_pom(), parse_pyproject_toml(), parse_package_json(), parse_csproj(), parse_gemfile(), parse_gomod(), detect_language(), cvss_severity(), extract_cvss(), bump_type(), health_grade(), lookup_latest_version_ecosystem(), lookup_license_for_dep(), patch_manifest(), etc. These are defined BEFORE the network guard so unit tests can import them."),
        ("Pipeline Stages",      "850 – 2600",  "The main sequential execution: Setup → Stage 1 through Stage 7a. Each stage reads inputs, calls APIs, writes JSON output files. Guarded by the _UC1_IMPORT_ONLY env variable so tests don't accidentally trigger network calls."),
    ],
    col_widths=[3.5, 3, 9.5]
)

add_heading("The Import Guard — _UC1_IMPORT_ONLY", level=2, color=ORANGE)
info_box([
    "  At around line 850, just before Stage 1, there is this guard:",
    "",
    '  if os.environ.get("_UC1_IMPORT_ONLY"):',
    '      sys.exit(0)',
    "",
    "  When test_pipeline.py runs, it sets _UC1_IMPORT_ONLY=1 before importing",
    "  run_pipeline.py. This lets tests access the helper functions without",
    "  triggering any GitHub API calls or network requests.",
], strip_color=ORANGE, bg=CREAM, label="IMPORTANT: How Tests Import Without Running the Pipeline")

add_heading("Key Functions (for reference)", level=2, color=TEAL)
data_table(
    ["Function", "What It Does"],
    [
        ("detect_language()",              "Probes GitHub for manifest files; returns (language, ecosystem, filename, content, branch)."),
        ("parse_pom()",                    "Parses a Maven pom.xml XML file into a list of dependency dicts."),
        ("parse_pyproject_toml()",         "Parses a Python pyproject.toml (PEP 517 and Poetry formats) into dependency dicts."),
        ("parse_package_json()",           "Parses a Node.js package.json into dependency dicts."),
        ("parse_csproj()",                 "Parses a .NET .csproj XML file into NuGet dependency dicts."),
        ("parse_gemfile()",                "Parses a Ruby Gemfile into dependency dicts."),
        ("parse_gomod()",                  "Parses a Go go.mod file into dependency dicts."),
        ("cvss_severity(score)",           "Converts a CVSS number (0.0-10.0) to a severity string: CRITICAL/HIGH/MEDIUM/LOW/NONE."),
        ("health_grade(score)",            "Converts a 0-100 health score to a letter grade A-F with a descriptive label."),
        ("lookup_latest_version_ecosystem()", "Calls the appropriate package registry API (Maven, PyPI, npm, NuGet, etc.) to find the latest stable version of a package."),
        ("patch_manifest()",               "Rewrites the manifest file (pom.xml, requirements.txt, pyproject.toml, etc.) with upgraded versions."),
        ("create_consolidated_pr()",       "Creates a single GitHub branch + commit + pull request covering all dependency upgrades."),
    ],
    col_widths=[5.5, 10.5]
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — test_pipeline.py
# ══════════════════════════════════════════════════════════════════════════════
add_heading("5. Unit Tests — test_pipeline.py", level=1)
banner("pipeline-output/test_pipeline.py  —  63 Automated Tests", bg=DGREEN)

add_para(
    "This file contains 63 unit tests that verify all the helper functions in "
    "run_pipeline.py work correctly. It uses Python's built-in unittest framework — "
    "no additional libraries required. The pipeline runs these tests automatically at "
    "Stage 7a and includes the results in the HTML health report.",
    size=10.5
)
add_spacer()

add_heading("How to Run Tests Manually", level=2, color=TEAL)
add_code("python pipeline-output/test_pipeline.py")
add_code("# Expected output:  Ran 63 tests in 0.006s  OK")
add_spacer()

add_heading("What the Tests Cover", level=2, color=TEAL)
data_table(
    ["Test Class", "Tests", "What Is Verified"],
    [
        ("TestCvssSeverity",       "5",  "CVSS score → severity label (CRITICAL/HIGH/MEDIUM/LOW/NONE)"),
        ("TestExtractCvss",        "4",  "Extract CVSS score from OSV.dev vulnerability JSON"),
        ("TestBumpType",           "4",  "Classify version change as PATCH / MINOR / MAJOR"),
        ("TestHealthGrade",        "6",  "Health score (0-100) → letter grade (A/B/C/D/F)"),
        ("TestLookupLatestVersion","8",  "Latest stable version lookup for Maven, PyPI, npm, NuGet, etc."),
        ("TestLookupLicense",      "4",  "Licence lookup from package registries"),
        ("TestIsLicenseBlocked",   "6",  "Detect GPL/AGPL/SSPL licences against block-list"),
        ("TestParsePom",           "8",  "Parse pom.xml into dependency list"),
        ("TestParsePyproject",     "4",  "Parse pyproject.toml (PEP 517 + Poetry)"),
        ("TestParsePackageJson",   "4",  "Parse package.json dependencies"),
        ("TestParseCsproj",        "3",  "Parse .csproj NuGet references"),
        ("TestParseGemfile",       "3",  "Parse Ruby Gemfile gems"),
        ("TestParseGomod",         "3",  "Parse Go go.mod module requirements"),
        ("TestPatchPomXml",        "3",  "Patch pom.xml with upgraded versions"),
    ],
    col_widths=[5, 1.5, 9.5]
)

info_box([
    "  Why tests matter: the pipeline handles 6 different programming languages,",
    "  calls 8+ external APIs, and patches manifest files. A single wrong regex",
    "  or version-comparison bug could produce incorrect CVE reports or corrupt",
    "  pom.xml files. The 63 unit tests catch these errors before they reach production.",
], strip_color=AMBER, bg=CREAM, label="WHY THESE TESTS EXIST")
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — CONFIGURATION FILES
# ══════════════════════════════════════════════════════════════════════════════
add_heading("6. Configuration Files", level=1)

# policy.json
add_heading("6a. policy.json", level=2, color=ORANGE)
banner("pipeline-output/policy.json  —  Security Policy Rules", bg=ORANGE)
add_para(
    "This JSON file defines your organisation's security policies. The pipeline "
    "reads it at Stage 3.7 and blocks the build if any rule is violated. "
    "You can edit this file to match your team's risk tolerance.",
    size=10.5
)
add_spacer()
data_table(
    ["Policy Setting", "Default Value", "What It Means"],
    [
        ("max_critical_cves",          "0",                        "Zero CRITICAL CVEs allowed — even one fails the build."),
        ("max_high_cves",              "5",                        "Up to 5 HIGH-severity CVEs are tolerated before failing."),
        ("blocked_licenses",           "GPL-2.0, GPL-3.0, AGPL...", "These licences are legally incompatible with proprietary software."),
        ("allow_untrusted_sources",    "false",                    "All dependencies must come from approved package registries."),
        ("fail_on_secrets",            "true",                     "Any detected secret (password, API key) immediately fails the build."),
        ("allow_snapshot_versions",    "false",                    "SNAPSHOT/preview versions are not allowed in production."),
        ("max_composite_risk_score",   "90",                       "The highest risk score any single dependency may have."),
        ("require_jacoco_coverage_pct","80",                       "Unit test coverage must remain above 80% after upgrades."),
        ("auto_merge_bump_types",      "PATCH, MINOR",             "These upgrade types are merged automatically without human review."),
        ("block_major_auto_merge",     "true",                     "MAJOR version upgrades always require a human to approve."),
    ],
    col_widths=[5, 3, 8]
)

add_heading("6b. .gitleaks.toml", level=2, color=ORANGE)
banner("pipeline-output/.gitleaks.toml  —  Secret Detection Allow-List", bg=MGRAY)
add_para(
    "This file configures the secret detection scanner (Stage 3.5). It uses the "
    "gitleaks v8 format. The pipeline's built-in regex scanner uses this file as a "
    "reference for patterns to detect and, more importantly, patterns to ignore "
    "(allow-list). You do not need to install gitleaks separately — the pipeline "
    "has its own built-in scanner.",
    size=10.5
)
add_spacer()
data_table(
    ["Rule",                       "Severity", "What It Detects"],
    [
        ("generic-api-key",        "HIGH",     "Variables named api_key, apikey, or api_secret with a value"),
        ("db-password-in-properties","CRITICAL","Database passwords in .properties or .yml files"),
        ("jwt-secret",             "HIGH",     "JWT signing secret variables"),
    ],
    col_widths=[5, 2.5, 8.5]
)
add_para(
    "If the pipeline flags a false positive (e.g. a test fixture credential), "
    "add a pattern to the [allowlist] regexes section of this file.",
    size=10, italic=True, color=MGRAY
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — report.html
# ══════════════════════════════════════════════════════════════════════════════
add_heading("7. HTML Dashboard — report.html", level=1)
banner("skills/audit-trail-demo/templates/report.html  —  Interactive Report Template", bg=BLUE)

add_para(
    "This is the template for the interactive health report that the pipeline generates "
    "at Stage 7. It is an HTML file with embedded JavaScript. The pipeline reads this "
    "template, replaces one placeholder (window.REPORT_DATA = null) with the actual "
    "scan results as a JSON object, and writes the result as dependency-health-report.html "
    "in the output directory. Open the generated file in any browser — no server required.",
    size=10.5
)
add_spacer()

add_heading("What the Report Shows", level=2, color=TEAL)
add_para("The report has two tabs:", size=10.5, bold=True)

data_table(
    ["Tab", "Section", "Contents"],
    [
        ("Executive Summary", "Health Score",          "Circular badge showing grade A-F with score 0-100."),
        ("Executive Summary", "4 KPI Cards",           "Total CVEs Found / CVEs Fixed / PRs Auto-Merged / Avg Test Coverage."),
        ("Executive Summary", "CVE Severity Chart",    "Doughnut chart: Critical / High / Medium / Low counts."),
        ("Executive Summary", "Risk Tier Chart",       "Bar chart showing risk distribution across dependencies."),
        ("Executive Summary", "Key Findings",          "Auto-generated bullet points summarising the most important results."),
        ("Executive Summary", "Pipeline Stages",       "Visual timeline showing each stage as PASS or FAIL."),
        ("Executive Summary", "Top 5 Risky Deps",      "Table of the 5 highest-risk dependencies with their top CVE."),
        ("Executive Summary", "PR Approve / Reject",   "Per-dependency Accept/Skip buttons + one-click GitHub PR approval."),
        ("Technical Appendix","All CVEs",              "Full table of every CVE found with CVSS score and description."),
        ("Technical Appendix","Audit Violations",      "Supply-chain violations (licence, source, typosquatting)."),
        ("Technical Appendix","Remediation PRs",       "All proposed upgrades with old → new version and CVEs fixed."),
        ("Technical Appendix","Validation Gates",      "Per-PR results for each of the 4 validation gates."),
        ("Technical Appendix","Unit Test Results",     "All 63 unit test results with PASS/FAIL status."),
    ],
    col_widths=[3.5, 4, 8.5]
)

info_box([
    "  The Approve / Reject PR panel lets you:",
    "  1. Mark each individual dependency fix as 'Accept' (green) or 'Skip' (grey/strikethrough).",
    "  2. Connect your GitHub Personal Access Token (stored only in your browser tab).",
    "  3. Click Approve to submit a GitHub pull request review with a generated comment",
    "     listing exactly which fixes you accepted and which need further review.",
    "  4. This calls the GitHub API directly from your browser — no server involved.",
], strip_color=BLUE, bg=LBLUE, label="INTERACTIVE PR REVIEW PANEL")
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — GENERATED OUTPUT FILES
# ══════════════════════════════════════════════════════════════════════════════
add_heading("8. Generated Output Files", level=1)
add_para(
    "Every time the pipeline runs, it writes up to 15 output files to the output "
    "directory (default: pipeline-output/). Here is every file, what it contains, "
    "and which stage produces it:",
    size=10.5
)
add_spacer()

data_table(
    ["File", "Stage", "What It Contains"],
    [
        ("dependency-check-report.json", "Stage 1",  "Full list of every dependency scanned, every CVE found, CVSS scores, descriptions, and affected version ranges. This is the primary vulnerability database for the run."),
        ("sbom-cyclonedx.json",          "Stage 1.5","Software Bill of Materials in CycloneDX 1.5 JSON format. Lists every compile-scope dependency with its name, version, PURL (package URL), and licence. Required for NTIA compliance."),
        ("risk-scores.json",             "Stage 2",  "Composite risk score (0-100) and tier (CRITICAL/HIGH/MEDIUM/LOW) for each vulnerable dependency. Includes the 4-factor breakdown: CVE severity, business criticality, transitive exposure, maintenance health."),
        ("audit-report.json",            "Stage 3",  "Supply-chain audit findings: licence violations, typosquatting detections, untrusted source flags. Each violation has a component name, check type, severity, and remediation detail."),
        ("secret-scan-report.json",      "Stage 3.5","Results of the secret detection scan. Lists any detected credentials with file path, line number, rule name, severity, and a masked (redacted) copy of the matched value."),
        ("policy-report.json",           "Stage 3.7","Pass/Fail/Warn result for each of the 7 built-in policy rules. Lists which rules were evaluated, their threshold, the actual value observed, and the verdict."),
        ("drift-report.json",            "Stage 3.9","Dependency drift analysis. On the first run: records baseline. On subsequent runs: lists Added, Removed, Upgraded, and Downgraded packages compared to the baseline."),
        ("dependency-baseline.json",     "Stage 3.9","Snapshot of all current dependencies. Saved for future drift comparisons. Updated on every run."),
        ("remediation-manifest.json",    "Stage 4",  "The proposed fix plan: for each vulnerable dependency, the current version, the recommended new version, bump type (PATCH/MINOR/MAJOR), CVEs that would be fixed, and the draft PR URL."),
        ("validation-report.json",       "Stage 5",  "Results of the 4 PR validation gates (mvn test, OWASP re-scan, Grype scan, JaCoCo coverage) for each proposed fix PR. Final verdict: AUTO_MERGE, PENDING, or BLOCKED."),
        ("e2e-report.json",              "Stage 6",  "End-to-end stress test results. Per-repo timing, stage results, pass/fail status. Used to verify the pipeline itself performs within acceptable time bounds."),
        ("dependency-health-report.html","Stage 7",  "The interactive HTML dashboard (see Section 7). Open this in a browser. Self-contained — all data is embedded, no server needed."),
        ("audit-trail.json",             "Stage 7",  "Complete audit record of the entire pipeline run: all stage results, health score, key findings, language/ecosystem detected, manifest filename, timestamps."),
        ("test-results.json",            "Stage 7a", "Results of all 63 unit tests: test name, status (PASS/FAIL), and any failure detail message."),
        ("security-scan.yml",            "Stage 7",  "A ready-to-use GitHub Actions CI/CD workflow generated for the scanned repo. Copy to .github/workflows/ in any target repository. Note: the UC1 repo itself already has a live workflow at .github/workflows/security-scan.yml."),
    ],
    col_widths=[5, 2, 9]
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — AGENTS
# ══════════════════════════════════════════════════════════════════════════════
add_heading("9. Agents", level=1)
add_para(
    "Agents are orchestration modules that coordinate multi-step tasks. In this project, "
    "agent documentation lives in the agents/ folder. Each agent is documented with a "
    "SKILL.md (the agent's purpose and how to use it) and a references/ folder "
    "(schemas, API specs, and formulas the agent uses).",
    size=10.5
)
add_para(
    "Important: the agent logic is implemented inside run_pipeline.py — "
    "the SKILL.md and reference files are design documentation, not executable code.",
    size=10, italic=True, color=MGRAY
)
add_spacer()

add_heading("agents/pr-validation-agent/", level=2, color=TEAL)
banner("PR Validation Agent  —  Coordinates Stage 5 Quality Gates", bg=BLUE)
add_para("This agent manages the 4 automated quality checks run on every fix pull request:", size=10.5)
data_table(
    ["Gate", "Tool", "What It Checks", "Skipped If"],
    [
        ("Gate 1 — Unit Tests",      "mvn test",    "All Java unit tests pass after the dependency upgrade.",              "mvn or git not installed"),
        ("Gate 2 — OWASP Re-scan",   "OSV.dev API", "The upgraded dependencies have no new CVEs (always runs).",          "Never skipped"),
        ("Gate 3 — Grype Scan",      "grype",       "Container-level vulnerability check using Syft SBOM.",               "grype not installed"),
        ("Gate 4 — JaCoCo Coverage", "mvn + JaCoCo","Unit test line coverage stays above 80% after the change.",          "mvn not installed"),
    ],
    col_widths=[4, 2.5, 6, 3.5]
)
add_para("Reference files in agents/pr-validation-agent/references/:", size=10.5, bold=True)
add_bullet("github-merge-api.md — GitHub squash-merge endpoint details")
add_bullet("pr-queue-schema.md  — Structure of the PR queue from remediation-manifest.json")
add_para("Gate skill files in agents/pr-validation-agent/skills/:", size=10.5, bold=True)
add_bullet("mvn-test.md      — How the Maven test gate works")
add_bullet("owasp-scan.md    — OWASP re-scan logic and baseline comparison")
add_bullet("grype-scan.md    — Grype container scan procedure")
add_bullet("jacoco-coverage.md — JaCoCo coverage measurement setup")
add_spacer()

add_heading("agents/risk-scoring-agent/", level=2, color=TEAL)
banner("Risk Scoring Agent  —  Coordinates Stage 2 Composite Scoring", bg=AMBER)
add_para(
    "This agent calculates a composite risk score for each vulnerable dependency "
    "using a weighted 4-factor model:",
    size=10.5
)
data_table(
    ["Factor", "Weight", "What It Measures"],
    [
        ("CVE Severity",          "40%", "CVSS base score from OSV.dev (0.0–10.0)."),
        ("Business Criticality",  "30%", "How critical this library is to the application (tagged via criticality-tags.json)."),
        ("Transitive Exposure",   "20%", "Whether the vulnerable package is a direct or transitive (indirect) dependency."),
        ("Maintenance Health",    "10%", "How actively maintained the package is (recent releases, open issues)."),
    ],
    col_widths=[4.5, 2, 9.5]
)
add_para("Reference files in agents/risk-scoring-agent/references/:", size=10.5, bold=True)
add_bullet("scoring-formulas.md   — Full mathematical formula for composite risk")
add_bullet("owasp-json-schema.md  — Structure of the OWASP Dependency-Check JSON input")
add_bullet("tags-format.md        — Format for the criticality-tags.json business-criticality input")
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — PLUGINS
# ══════════════════════════════════════════════════════════════════════════════
add_heading("10. Plugins", level=1)
add_para(
    "Plugins are enforcement modules that run specific checks and block the pipeline "
    "if violations are found. Like agents, plugin logic is implemented in run_pipeline.py; "
    "the plugins/ folder contains the design documentation.",
    size=10.5
)
add_spacer()

add_heading("plugins/policy-as-code-enforcer/", level=2, color=TEAL)
banner("Policy-as-Code Enforcer  —  Stage 3.7 Rule Engine", bg=ORANGE)
add_para(
    "This plugin reads policy.json and evaluates 7 built-in rules against the pipeline's "
    "findings. Each rule produces PASS, WARN, or FAIL. A single FAIL result marks the "
    "entire policy check as FAILED.",
    size=10.5
)
data_table(
    ["Rule", "ID", "Default Threshold", "What It Checks"],
    [
        ("Max CVSS Score",         "P001", "CVSS ≥ 9.0 = FAIL",     "Any single CVE with a base score at or above the threshold."),
        ("Max Critical CVEs",      "P002", "0 = FAIL",               "Total count of CRITICAL-severity CVEs."),
        ("Max High CVEs",          "P003", "5 = FAIL",               "Total count of HIGH-severity CVEs."),
        ("Blocked Licences",       "P004", "GPL/AGPL/SSPL",          "Any dependency with a licence on the blocklist."),
        ("Secrets Detected",       "P005", "Any HIGH/CRITICAL",      "Any secret found with severity at or above the threshold."),
        ("Snapshot Versions",      "P006", "None allowed",           "Any dependency with a SNAPSHOT or dev/alpha/beta version tag."),
        ("Test Coverage",          "P007", "< 80% = WARN",           "Average JaCoCo coverage across all validated PRs."),
    ],
    col_widths=[3.5, 1.5, 3, 8]
)
add_spacer()

add_heading("plugins/supply-chain-audit-plugin/", level=2, color=TEAL)
banner("Supply-Chain Audit Plugin  —  Stage 3 Trust & Licence Checks", bg=NAVY)
add_para(
    "This plugin scans the dependency list for three categories of supply-chain risk:",
    size=10.5
)
data_table(
    ["Check", "How It Works", "Example"],
    [
        ("Typosquatting",     "Compares each package name against a list of known-safe packages using Levenshtein distance ≤ 2. A package named 'reqeusts' (instead of 'requests') would be flagged.",  "'reqeusts' flagged as typosquat of 'requests'"),
        ("Untrusted Source",  "Checks whether each package comes from an approved registry (Maven Central, PyPI, npm, NuGet, RubyGems, Go Proxy). Custom/internal repos can be added to source-allowlist.txt.", "A JAR from an internal Nexus repo"),
        ("Licence Violation", "Looks up the actual licence of each dependency from its registry and compares it against the blocked_licenses list in policy.json.",                                          "GPL-3.0 dependency blocks the build"),
    ],
    col_widths=[3, 7, 6]
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — SKILLS
# ══════════════════════════════════════════════════════════════════════════════
add_heading("11. Skills", level=1)
add_para(
    "Skills are specialist capability modules. Each skill has a SKILL.md (purpose, "
    "inputs, outputs, usage) and a references/ folder (API docs, schemas, and examples). "
    "All skill logic runs inside run_pipeline.py — the skills/ folder is documentation.",
    size=10.5
)
add_spacer()

skills = [
    ("audit-trail-demo",              TEAL,   "Stage 7",
     "Aggregates all scan results into the interactive HTML health report and a complete audit trail JSON.",
     ["Reads outputs from Stages 1–6.", "Computes the composite health score (0-100) using a weighted formula.", "Generates dependency-health-report.html by injecting JSON data into report.html template.", "Writes audit-trail.json with the full run record."]),

    ("auto-remediation-skill",        GREEN,  "Stage 4",
     "Resolves the latest safe version for each vulnerable dependency, patches the manifest file, and creates a consolidated GitHub pull request.",
     ["Calls the appropriate registry API (Maven Central, PyPI, npm, etc.) for the latest stable version.", "Classifies the change as PATCH, MINOR, or MAJOR.", "Patches the manifest file (pom.xml, requirements.txt, pyproject.toml, etc.).", "Creates one GitHub branch, one commit, and one pull request covering all upgrades."]),

    ("dependency-drift-detector",     AMBER,  "Stage 3.9",
     "Detects changes in the dependency list since the last baseline snapshot.",
     ["First run: saves current deps as dependency-baseline.json.", "Subsequent runs: compares current deps against the saved baseline.", "Reports Added, Removed, Upgraded, Downgraded, and Unchanged counts.", "Flags newly added or upgraded deps that have CVEs as risk events."]),

    ("dependency-supply-chain-hygiene", RED,  "Stage 1",
     "Scans dependencies for known CVEs using the OSV.dev batch query API.",
     ["Sends all compile-scope dependencies to OSV.dev in a single batch request.", "Fetches full vulnerability details for each CVE found.", "Supports Java, Python, Node.js, .NET, Ruby, and Go packages.", "Outputs dependency-check-report.json with all findings."]),

    ("e2e-stress-testing",            NAVY,   "Stage 6",
     "Runs the full pipeline end-to-end against the target repo as a performance and correctness test.",
     ["Re-runs Stage 1 through Stage 5 against the same repo.", "Measures per-stage timing.", "Aggregates results into e2e-report.json.", "6 test scenarios: CVE-heavy, zero-CVE, complex tree, malformed manifest, mixed, large repo."]),

    ("github-actions-generator",      BLUE,   "Stage 7",
     "Generates a GitHub Actions workflow YAML file that automates the UC1 pipeline in CI/CD.",
     ["Creates security-scan.yml in the output directory.", "Configured to run on push, pull_request, and weekly schedule.", "Covers all 6 supported ecosystems.", "Copy to .github/workflows/ in your repository to activate."]),

    ("sbom-generator",                TEAL,   "Stage 1.5",
     "Generates a Software Bill of Materials (SBOM) in CycloneDX 1.5 JSON format.",
     ["Lists every compile-scope dependency with name, version, PURL, and licence.", "Required for NTIA Minimum Elements compliance (US Executive Order 14028).", "Outputs sbom-cyclonedx.json.", "Used as input by Grype (Stage 5, Gate 3) for container scanning."]),

    ("secret-detection",              ORANGE, "Stage 3.5",
     "Scans the manifest file and surrounding files for accidentally committed secrets.",
     ["Uses regex patterns from .gitleaks.toml.", "Detects: API keys, database passwords, JWT secrets, private keys, OAuth tokens.", "Reports file path, line number, severity, and redacted matched value.", "A CRITICAL or HIGH finding fails the build (configurable in policy.json)."]),
]

for skill_name, color, stage, desc, bullets in skills:
    add_heading(f"skills/{skill_name}/", level=2, color=color)
    kv_table([("Stage", stage), ("Purpose", desc)], col1w=2.5, col2w=13.5)
    for b in bullets:
        add_bullet(b)
    add_spacer()
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 12 — DOCUMENTATION FILES
# ══════════════════════════════════════════════════════════════════════════════
add_heading("12. Documentation Files", level=1)

docs_files = [
    ("README.md",         BLUE,  "Project root",
     "The first file any new user should read. Contains the project tagline, key features, quick-start commands, and a summary of all 7 pipeline stages. Includes the CLI reference for all command-line options.",
     ["Project overview and purpose", "Feature list", "Supported languages", "Quick-start run commands", "Full CLI reference: --token, --out-dir, --e2e-repos"]),

    ("SETUP.md",          GREEN, "Project root",
     "A step-by-step checklist for first-time setup. Covers everything from Python version verification to creating a GitHub Personal Access Token. Includes a troubleshooting table for common errors.",
     ["Step 1: Verify Python 3.9+", "Step 2: Confirm internet access to required APIs", "Step 3: Create GitHub Personal Access Token", "Step 4: Identify your target repository", "Step 5: Review and customise policy.json", "Step 6: Review .gitleaks.toml", "Step 7: Install optional tools (Maven, Grype) for full gate coverage", "Step 8: Verify file layout", "Step 9-10: Run the pipeline and check expected output", "Step 11: Troubleshooting table", "Step 12: CLI reference summary"]),

    ("PIPELINE_GUIDE.md", TEAL,  "Project root",
     "The most detailed documentation in the project. Explains every pipeline stage in full, including how data flows between stages, what each output file contains, and how to interpret the HTML report. Updated to reflect multi-ecosystem support.",
     ["Setup: language detection and manifest parsing", "All stage descriptions with input/output data flow", "Policy rules P001-P007 explained", "Drift detection baseline mechanics", "Auto-remediation PR creation (idempotent — won't create duplicates)", "PR validation gate logic", "HTML report reading guide"]),

    ("FLOW_DIAGRAM.md",   AMBER, "Project root",
     "Contains 4 Mermaid flowchart diagrams that visualise the pipeline architecture. Render these in any Markdown viewer (GitHub, VS Code, Mermaid Live Editor) to see interactive diagrams.",
     ["Diagram 1: Full pipeline overview — all 13 stages with decision nodes and output files", "Diagram 2: Language detection waterfall — 7-step manifest probe sequence", "Diagram 3: Stage 4 auto-remediation detail — per-registry version lookup and PR creation", "Diagram 4: Stage 5 PR validation gates — 4 gates with tool availability checks"]),

    ("CLAUDE.md",         NAVY,  "Project root",
     "Read automatically by Claude Code (Anthropic's AI coding assistant) at the start of every session. Contains the architecture decisions that must never be undone, the list of removed code (so the AI doesn't re-add it), run commands, and ecosystem configuration.",
     ["Architecture decisions: stdlib-only, single-file, _UC1_IMPORT_ONLY guard", "Key files reference", "Ecosystem map and manifest detection priority", "Run commands", "List of cleaned-up items that must not be re-added"]),
]

for fname, color, loc, desc, contents in docs_files:
    add_heading(fname, level=2, color=color)
    kv_table([("Location", loc), ("Purpose", desc)], col1w=2.5, col2w=13.5)
    add_heading("Contents", level=3, color=MGRAY)
    for item in contents:
        add_bullet(item)
    add_spacer()
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 13 — UTILITY SCRIPTS
# ══════════════════════════════════════════════════════════════════════════════
add_heading("13. Utility Scripts", level=1)

add_heading("GitHub Actions Workflow", level=2, color=GREEN)
banner(".github/workflows/security-scan.yml  —  Live CI/CD Pipeline", bg=GREEN)
add_para(
    "A production-ready GitHub Actions workflow is already wired into this repository. "
    "It does not need to be generated or copied — it is active and triggers automatically.",
    size=10.5
)
add_spacer()
data_table(
    ["Trigger", "Condition", "What Runs"],
    [
        ("Push to main",        "run_pipeline.py, policy.json, or workflow file changed",  "Full pipeline scan (dry-run, no PRs)"),
        ("workflow_dispatch",   "Manual via Actions UI — choose repo + create_prs toggle", "Full pipeline; live PRs if DEMO_REPO_PAT secret is set"),
        ("Scheduled cron",      "Every Monday 02:00 UTC",                                  "Full pipeline scan (dry-run)"),
    ],
    col_widths=[3.5, 8.5, 4]
)
info_box([
    "  To enable live PR creation from the workflow:",
    "  1. GitHub → repo Settings → Secrets and variables → Actions",
    "  2. Add secret: DEMO_REPO_PAT = your GitHub PAT with repo scope",
    "  3. Trigger the workflow with create_prs = true",
], strip_color=GREEN, bg=LGREEN, label="ENABLING LIVE PR CREATION")
add_spacer()

add_heading("MCP Server (Claude Code integration)", level=2, color=TEAL)
banner("pipeline-output/mcp_server.py  +  .mcp.json  —  Claude Code Tools", bg=TEAL)
add_para(
    "An MCP (Model Context Protocol) server is bundled at pipeline-output/mcp_server.py "
    "and pre-configured in .mcp.json at the project root. When Claude Code opens this "
    "project the supply-chain-security MCP server starts automatically, exposing the "
    "entire pipeline as five conversational tools — no terminal commands needed.",
    size=10.5
)
add_spacer()
data_table(
    ["Tool", "What It Does"],
    [
        ("scan_repo",               "Run the full pipeline against any GitHub repo URL. Returns the health report on completion."),
        ("get_health_report",       "Return the health grade, score, and stage results from the most recent scan."),
        ("get_cve_summary",         "Return the CVE findings (counts by severity, top CVEs) from the most recent scan."),
        ("get_policy_status",       "Return the policy gate PASS/FAIL result and any violations from the most recent scan."),
        ("create_remediation_prs",  "Trigger GitHub PR creation for the most recent scan results. Requires a GitHub token."),
    ],
    col_widths=[4, 12]
)
add_para(
    "The .mcp.json config file simply points at the server script — "
    "no additional install or environment setup is required beyond Python 3.9+.",
    size=10, italic=True, color=MGRAY
)
add_spacer(2)

add_heading("generate_ppt.py", level=2, color=ORANGE)
banner("generate_ppt.py  —  PowerPoint Presentation Generator", bg=ORANGE)
add_para(
    "A standalone Python script that generates a 14-slide PowerPoint presentation "
    "(UC1_Security_Pipeline_Demo.pptx) for demos to non-technical stakeholders. "
    "Requires python-docx to be installed (pip install python-pptx). Run it once to "
    "create the .pptx file, then open in PowerPoint or Google Slides.",
    size=10.5
)
data_table(
    ["Slide", "Title"],
    [("1","Title — UC1 Supply Chain Security Pipeline"),("2","The Problem: Software Supply Chain Risk"),
     ("3","Our Solution: Automated Pipeline"),("4","How It Works — The 7-Stage Flow"),
     ("5","Stage 1: CVE Scan Results"),("6","Stage 2: Risk Scoring"),
     ("7","Stage 3-4: Audit & Remediation"),("8","Stage 5: PR Validation Gates"),
     ("9","Stage 6-7: E2E Test & Health Report"),("10","Live Demo Results"),
     ("11","Supported Ecosystems"),("12","The Health Report Dashboard"),
     ("13","Integration: GitHub Actions CI/CD"),("14","Summary & Next Steps")],
    col_widths=[1.5, 14.5]
)
add_code("python generate_ppt.py")
add_spacer()

add_heading("e2e_language_test.py", level=2, color=TEAL)
banner("e2e_language_test.py  —  Multi-Language End-to-End Test Runner", bg=TEAL)
add_para(
    "Runs the pipeline against one real GitHub repository for each of the 6 supported "
    "ecosystems and produces a summary table showing language detection, deps found, "
    "CVEs detected, health grade, and elapsed time. Used to verify that all 6 language "
    "parsers are working correctly after code changes.",
    size=10.5
)
data_table(
    ["Ecosystem",       "Test Repository",                          "Notes"],
    [("Java / Maven",   "github.com/WebGoat/WebGoat",               "47 deps, 39 CVEs — intentionally vulnerable app"),
     ("Python / PyPI",  "github.com/scrapy/scrapy",                 "pyproject.toml, PEP 517 format, 18 deps"),
     ("Node.js / npm",  "github.com/expressjs/express",             "package.json, 28 deps"),
     (".NET / NuGet",   "local fixture (App.csproj injected)",       "4 deps — no public repo with root-level .csproj"),
     ("Ruby / Gems",    "github.com/sinatra/sinatra",               "Gemfile, 35 deps"),
     ("Go",             "github.com/gin-gonic/gin",                 "go.mod, 35 deps")],
    col_widths=[3.5, 6, 6.5]
)
add_code("python e2e_language_test.py")
add_spacer()

add_heading("pipeline-output/setup_demo_repo.py", level=2, color=MGRAY)
add_para(
    "A one-time utility script that seeds the demo GitHub repository "
    "(github.com/SRGuptthha/uc1-security-demo) with a pom.xml containing 7 known-vulnerable "
    "Maven dependencies (Log4Shell, Spring4Shell, Text4Shell, H2 RCE, SnakeYAML DoS, etc.). "
    "Run this once to prepare the demo repo. Requires a GitHub token with write access.",
    size=10.5
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 14 — FIRST-RUN QUICK GUIDE
# ══════════════════════════════════════════════════════════════════════════════
add_heading("14. First-Run Quick Guide", level=1)
add_para(
    "Follow these steps in order to run the pipeline for the first time. "
    "Each step is explained so you know what to expect.",
    size=10.5
)
add_spacer()

steps = [
    ("Step 1", "Check Python Version", GREEN,
     'Open a terminal and run:  python --version\nYou need Python 3.9 or newer. If you see 3.9.x or higher, you are ready.',
     "python --version\n# Expected:  Python 3.11.x  (or 3.9+ / 3.10+ / 3.12+ / 3.13+)"),

    ("Step 2", "Navigate to the Project", BLUE,
     'Change to the project directory in your terminal.',
     "cd D:\\ClaudeUC\\UC1"),

    ("Step 3", "Run the Pipeline (Dry-Run)", TEAL,
     'Run the pipeline against the demo repository. No GitHub token needed in dry-run mode. '
     'The pipeline will scan the repo, find CVEs, and generate all reports locally. '
     'Nothing is written to GitHub.',
     "python pipeline-output/run_pipeline.py https://github.com/SRGuptthha/uc1-security-demo"),

    ("Step 4", "Watch the Output", AMBER,
     'You will see the pipeline progress through each stage printed to the terminal. '
     'A full dry-run typically takes 30-90 seconds depending on network speed. '
     'Look for  PIPELINE COMPLETE  at the end.',
     "[Setup] Detecting project language...\n[Stage 1] Querying OSV.dev for known CVEs...\n[Stage 2] Running Risk Scoring Agent...\n...\nPIPELINE COMPLETE\nHealth : 0/100 -> 26/100   Grade F -- Critical"),

    ("Step 5", "Open the HTML Report", DGREEN,
     'Open the generated HTML dashboard in your web browser. '
     'This is the main output — an interactive report showing all findings.',
     "# Windows:  start pipeline-output\\dependency-health-report.html\n# Or double-click the file in File Explorer"),

    ("Step 6", "Run with Live Mode (Optional)", ORANGE,
     'To create a real fix branch and pull request on GitHub, add your Personal Access Token. '
     'See SETUP.md Section 3 for instructions on creating a GitHub PAT.',
     "python pipeline-output/run_pipeline.py https://github.com/SRGuptthha/uc1-security-demo --token ghp_xxxx"),
]

for step_num, step_title, color, desc, code in steps:
    tbl2 = doc.add_table(rows=1, cols=2)
    tbl2.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl2.columns[0].width = Cm(2.5)
    tbl2.columns[1].width = Cm(13.5)
    sc = tbl2.rows[0].cells[0]
    dc = tbl2.rows[0].cells[1]
    set_cell_bg(sc, color)
    cell_borders(sc, hx(color))
    cell_borders(dc)
    sc.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    sp = sc.paragraphs[0]
    sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = sp.add_run(step_num)
    sr.bold = True; sr.font.size = Pt(11); sr.font.color.rgb = WHITE
    sp.paragraph_format.space_before = Pt(4)
    sp2 = sc.add_paragraph()
    sp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr2 = sp2.add_run(step_title)
    sr2.bold = True; sr2.font.size = Pt(8); sr2.font.color.rgb = WHITE
    sp2.paragraph_format.space_after = Pt(4)
    dp = dc.paragraphs[0]
    dr = dp.add_run(desc)
    dr.font.size = Pt(10)
    dp.paragraph_format.space_before = Pt(4)
    dp.paragraph_format.left_indent  = Cm(0.3)
    for cline in code.strip().split("\n"):
        cp2 = dc.add_paragraph()
        set_para_bg(cp2, LGRAY)
        cp2.paragraph_format.left_indent = Cm(0.3)
        cp2.paragraph_format.space_before = Pt(1)
        cp2.paragraph_format.space_after  = Pt(2)
        cr = cp2.add_run(cline)
        cr.font.size = Pt(8.5); cr.font.name = "Courier New"; cr.font.color.rgb = DARK
    add_spacer()

add_spacer()
add_heading("Troubleshooting Common First-Run Errors", level=2, color=RED)
data_table(
    ["Error Message", "Most Likely Cause", "Fix"],
    [
        ("No manifest file detected",       "The target repo has no supported manifest at its root",       "Check the repo has pom.xml / requirements.txt / package.json / etc. at root level."),
        ("Language detected: java-maven (stale)", "A leftover pom.xml from a previous run is in pipeline-output/", "Use --out-dir to a fresh directory, e.g. --out-dir C:\\Temp\\scan1"),
        ("OSV.dev batch query failed",       "Temporary network issue",                                    "Re-run — OSV.dev has no rate limit and the error is usually transient."),
        ("403 on GitHub API",                "Token expired or missing scope",                             "Regenerate your PAT with 'repo' scope (see SETUP.md Step 3)."),
        ("dependency-health-report.html blank", "JavaScript SyntaxError in the browser console",          "Open browser DevTools → Console tab to see the error. Ensure you opened the generated report, not the template."),
        ("Parsed 0 total deps",              "pyproject.toml uses a section that the parser did not recognise", "The parser now supports PEP 517 [project] and Poetry formats. Try requirements.txt if issues persist."),
    ],
    col_widths=[4.5, 4.5, 7]
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 15 — GLOSSARY
# ══════════════════════════════════════════════════════════════════════════════
add_heading("15. Glossary — Key Terms", level=1)
add_para("Definitions for terms used throughout this document and the pipeline output files.", size=10.5)
add_spacer()

glossary = [
    ("CVE", "Common Vulnerability and Exposure. A unique identifier for a publicly known security vulnerability, e.g. CVE-2021-44228 (Log4Shell). Published at nvd.nist.gov."),
    ("CVSS", "Common Vulnerability Scoring System. A 0.0–10.0 number measuring how severe a CVE is. 9.0–10.0 = Critical, 7.0–8.9 = High, 4.0–6.9 = Medium, 0.1–3.9 = Low."),
    ("SBOM", "Software Bill of Materials. A machine-readable list of every library a project depends on, with versions and licences. Required for US government compliance (EO 14028)."),
    ("CycloneDX", "An open standard format for SBOMs, developed by OWASP. The pipeline generates version 1.5 JSON format."),
    ("OSV.dev", "Open Source Vulnerabilities database, maintained by Google. Aggregates CVE data from NVD, GitHub Advisories, and language-specific databases. The pipeline queries it for free."),
    ("PURL", "Package URL. A standardised way to identify a software package, e.g. pkg:maven/org.apache.log4j/log4j-core@2.14.1. Used in SBOMs."),
    ("Dry-Run", "Running the pipeline without a GitHub token. Reads the repo and generates all reports locally but does not create any branches or pull requests on GitHub."),
    ("PAT", "Personal Access Token. A GitHub authentication credential you generate in your GitHub settings. Required for live mode (creating PRs)."),
    ("Typosquatting", "A supply-chain attack where a malicious package uses a name very similar to a popular library (e.g. 'reqeusts' vs 'requests') to trick developers into installing it."),
    ("Drift Detection", "Comparing the current dependency list against a previously saved snapshot (baseline) to detect which packages were added, removed, or changed."),
    ("PATCH / MINOR / MAJOR", "Semantic versioning upgrade classifications. PATCH = bug fixes only (1.0.1→1.0.2). MINOR = new features, backwards compatible (1.0→1.1). MAJOR = breaking changes (1.x→2.0)."),
    ("JaCoCo", "Java Code Coverage tool. Measures what percentage of source code lines are executed by unit tests. The pipeline uses it as Gate 4 in Stage 5."),
    ("Grype", "An open-source vulnerability scanner by Anchore that works at the container/SBOM level. Used as Gate 3 in Stage 5. Optional — skipped if not installed."),
    ("Health Score", "A 0–100 score computed from the pipeline's findings. 90–100 = Grade A (Excellent). 75–89 = B (Good). 60–74 = C (Moderate). 40–59 = D (Poor). 0–39 = F (Critical)."),
    ("Consolidated PR", "A single GitHub pull request that upgrades all vulnerable dependencies in one commit, rather than one PR per dependency. Easier to review and merge."),
    ("stdlib", "Python Standard Library. The built-in modules that come with Python (json, re, os, urllib, etc.). The pipeline uses only these — no pip install needed."),
    ("OWASP", "Open Web Application Security Project. A nonprofit that publishes security guidance. The pipeline implements OWASP Dependency-Check concepts."),
]
data_table(["Term", "Definition"], glossary, col_widths=[4, 12])

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "UC1_Project_Documentation.docx")
doc.save(out_path)
print(f"Saved: {out_path}")
print(f"Size : {os.path.getsize(out_path) // 1024} KB")


