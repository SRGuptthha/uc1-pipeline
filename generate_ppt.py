#!/usr/bin/env python3
"""Generate UC1 Supply Chain Security Pipeline — Non-Technical Demo PPT."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

OUT = r"d:\ClaudeUC\UC1\UC1_Security_Pipeline_Demo.pptx"

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x0f, 0x2d, 0x5c)
TEAL   = RGBColor(0x0d, 0x94, 0x88)
ORANGE = RGBColor(0xea, 0x58, 0x0c)
GREEN  = RGBColor(0x16, 0xa3, 0x4a)
RED    = RGBColor(0xb9, 0x1c, 0x1c)
WHITE  = RGBColor(0xff, 0xff, 0xff)
DARK   = RGBColor(0x1f, 0x29, 0x37)
LGRAY  = RGBColor(0xf1, 0xf5, 0xf9)
MGRAY  = RGBColor(0x94, 0xa3, 0xb8)
CREAM  = RGBColor(0xff, 0xfd, 0xf0)
AMBER  = RGBColor(0xd9, 0x7f, 0x06)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

# ── Drawing helpers ───────────────────────────────────────────────────────────
def R(slide, x, y, w, h, fill=None, line_rgb=None, lw=0.75):
    sh = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    else:
        sh.fill.background()
    if line_rgb:
        sh.line.color.rgb = line_rgb; sh.line.width = Pt(lw)
    else:
        sh.line.fill.background()
    return sh

def T(slide, text, x, y, w, h, size=18, bold=False, color=DARK,
      align=PP_ALIGN.LEFT, italic=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p  = tf.paragraphs[0]; p.alignment = align
    r  = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold
    r.font.italic = italic; r.font.color.rgb = color
    return tb

def BL(slide, items, x, y, w, h, size=16, gap=6):
    """Multi-line bullet text box.
    Prefix item with '!' for green check, '*' for bold header, '@' for orange highlight.
    """
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        r = p.add_run()
        if item.startswith("*"):
            r.text = item[1:]; r.font.bold = True
            r.font.size = Pt(size + 1); r.font.color.rgb = NAVY
        elif item.startswith("!"):
            r.text = "  ✔  " + item[1:]
            r.font.size = Pt(size); r.font.color.rgb = GREEN; r.font.bold = True
        elif item.startswith("@"):
            r.text = "  ►  " + item[1:]
            r.font.size = Pt(size); r.font.color.rgb = ORANGE; r.font.bold = True
        elif item.startswith("~"):
            r.text = item[1:]
            r.font.size = Pt(size - 2); r.font.color.rgb = MGRAY; r.font.italic = True
        else:
            r.text = "      •   " + item
            r.font.size = Pt(size); r.font.color.rgb = DARK
    return tb

def HDR(slide, title, sub=None):
    R(slide, 0, 0, 13.33, 1.3, fill=NAVY)
    R(slide, 0, 1.3, 13.33, 0.06, fill=TEAL)
    T(slide, title, 0.45, 0.1, 12.4, 0.75, size=30, bold=True, color=WHITE)
    if sub:
        T(slide, sub, 0.45, 0.82, 12.4, 0.42, size=15, color=TEAL, italic=True)

def NUM_CARD(slide, x, y, w, h, number, label, num_color=ORANGE):
    R(slide, x, y, w, h, fill=LGRAY, line_rgb=MGRAY)
    T(slide, number, x + 0.1, y + 0.12, w - 0.2, h * 0.55,
      size=36, bold=True, color=num_color, align=PP_ALIGN.CENTER)
    T(slide, label,  x + 0.1, y + h * 0.58, w - 0.2, h * 0.38,
      size=13, color=DARK, align=PP_ALIGN.CENTER)

def STAGE_BOX(slide, x, y, w, num, title, body, bg=LGRAY):
    R(slide, x, y, w, 2.7, fill=bg, line_rgb=MGRAY, lw=0.5)
    R(slide, x, y, w, 0.42, fill=NAVY)
    T(slide, num, x + 0.1, y + 0.05, 0.5, 0.32, size=14, bold=True, color=TEAL)
    T(slide, title, x + 0.55, y + 0.05, w - 0.65, 0.32, size=14, bold=True, color=WHITE)
    BL(slide, body, x + 0.15, y + 0.52, w - 0.25, 2.1, size=12, gap=3)

def FOOTER(slide, text="UC1 Supply Chain Security Pipeline  |  Confidential"):
    R(slide, 0, 7.2, 13.33, 0.3, fill=NAVY)
    T(slide, text, 0.3, 7.22, 12.5, 0.25, size=10, color=MGRAY, italic=True)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 1 — TITLE
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
R(s, 0, 0, 13.33, 7.5, fill=NAVY)
R(s, 0, 0, 13.33, 0.08, fill=TEAL)
R(s, 0, 7.42, 13.33, 0.08, fill=TEAL)
R(s, 0.4, 1.5, 12.53, 0.08, fill=TEAL)
R(s, 0.4, 5.0, 12.53, 0.08, fill=TEAL)

T(s, "UC1 Supply Chain", 0.5, 1.8, 12.0, 1.0, size=52, bold=True, color=WHITE,
  align=PP_ALIGN.CENTER)
T(s, "Security Pipeline", 0.5, 2.75, 12.0, 1.0, size=52, bold=True, color=TEAL,
  align=PP_ALIGN.CENTER)
T(s, "Automated Vulnerability Detection, Risk Scoring & Remediation",
  0.5, 3.85, 12.0, 0.6, size=20, color=MGRAY, align=PP_ALIGN.CENTER, italic=True)
T(s, "Demo for Leadership & Business Stakeholders",
  0.5, 4.5, 12.0, 0.4, size=16, color=MGRAY, align=PP_ALIGN.CENTER)
T(s, "UC1 Pipeline  ·  2026", 0.5, 6.9, 12.0, 0.4,
  size=12, color=MGRAY, align=PP_ALIGN.CENTER)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 2 — THE PROBLEM
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "The Problem",
    "Every software project relies on third-party libraries — and any one of them could be compromised")
FOOTER(s)

R(s, 0.4, 1.55, 12.5, 5.45, fill=CREAM, line_rgb=AMBER, lw=1)

T(s, "⚠  Real Incident: Log4Shell (December 2021)",
  0.65, 1.75, 12.0, 0.5, size=20, bold=True, color=RED)

BL(s, [
    "A single vulnerable library — log4j-core — was found in millions of applications worldwide",
    "CVSS Score: 10.0 out of 10  (the maximum possible — Remote Code Execution)",
    "Attackers could take full control of any server running the affected version",
    "Over 100 million devices were exposed within days of public disclosure",
    "Organisations scrambled for weeks to find and fix every affected system",
], 0.65, 2.35, 11.8, 3.0, size=17, gap=10)

T(s, "The Challenge", 0.65, 5.1, 5.5, 0.38, size=16, bold=True, color=NAVY)
BL(s, [
    "A typical enterprise project has 50–200 third-party libraries",
    "Each library can have its own vulnerabilities at any time",
    "Manual tracking is impossible — new CVEs are published daily",
], 0.65, 5.5, 5.8, 1.6, size=15, gap=6)

T(s, "The Cost of Inaction", 7.2, 5.1, 5.5, 0.38, size=16, bold=True, color=NAVY)
BL(s, [
    "Breach discovery time: avg. 194 days (IBM Cost of a Data Breach 2023)",
    "Average breach cost: $4.45 million",
    "Regulatory fines for known-vulnerability exploitation",
], 7.2, 5.5, 5.8, 1.6, size=15, gap=6)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 3 — OUR SOLUTION
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "Our Solution — UC1 Pipeline",
    "One command. Full security audit. Automated fix. In under 90 seconds.")
FOOTER(s)

T(s, "What it does in plain English:",
  0.4, 1.55, 12.5, 0.45, size=18, bold=True, color=NAVY)

BL(s, [
    "!Reads your project's list of third-party libraries automatically",
    "!Checks every library against 800,000+ known vulnerabilities",
    "!Scores each risk from 0–100 so you know what to fix first",
    "!Detects leaked passwords, licence violations, and suspicious packages",
    "!Creates a ready-to-merge fix on GitHub — no manual effort required",
    "!Verifies the fix is safe before allowing it to merge",
], 0.4, 2.1, 8.2, 4.5, size=17, gap=9)

R(s, 8.9, 1.55, 4.0, 5.6, fill=LGRAY, line_rgb=MGRAY)
T(s, "Key Facts", 9.1, 1.75, 3.6, 0.4, size=16, bold=True, color=NAVY)
BL(s, [
    "*Runs in < 90 seconds",
    "~for a typical project",
    "*No installation required",
    "~Python 3.9+ only",
    "*Supports 6 languages",
    "~Java · Python · Node.js",
    "~.NET · Ruby · Go",
    "*Zero external tools",
    "~no expensive licences",
    "*100% automated",
    "~from scan to PR",
], 9.1, 2.2, 3.6, 4.7, size=14, gap=2)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 4 — HOW IT WORKS
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "How It Works — 7 Automated Stages",
    "The pipeline runs from start to finish without any human intervention")
FOOTER(s)

stages = [
    ("Setup",   "Detect language & read dependency list"),
    ("Stage 1", "Scan all libraries for known CVEs"),
    ("Stage 2", "Score each risk from 0–100"),
    ("Stage 3", "Audit supply chain & check licences"),
    ("3.5–3.9", "Detect secrets, enforce policy, track drift"),
    ("Stage 4", "Create automated fix PR on GitHub"),
    ("Stage 5", "Validate the fix is safe to merge"),
]
colors = [TEAL, NAVY, NAVY, NAVY, AMBER, GREEN, TEAL]
bx = 0.4
for i, (num, desc) in enumerate(stages):
    col = colors[i]
    R(s, bx, 1.55, 1.6, 0.55, fill=col)
    T(s, num, bx + 0.05, 1.58, 1.5, 0.28, size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    R(s, bx + 1.6, 1.72, 0.3, 0.08, fill=MGRAY)
    bx += 1.85

bx = 0.4
for i, (num, desc) in enumerate(stages):
    col = colors[i]
    R(s, bx, 2.3, 1.6, 4.7, fill=LGRAY, line_rgb=col, lw=1.5)
    T(s, desc, bx + 0.1, 2.45, 1.4, 4.3, size=12, color=DARK, align=PP_ALIGN.CENTER)
    bx += 1.85

T(s, "Each stage feeds its results into the next — the pipeline is fully connected end-to-end.",
  0.4, 7.1, 12.5, 0.3, size=13, color=MGRAY, italic=True)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 5 — WHAT IT DETECTS
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "What the Pipeline Detects",
    "Six categories of risk — all checked automatically in every run")
FOOTER(s)

categories = [
    ("🔴", "Known Vulnerabilities (CVEs)",
     ["Libraries with published security flaws",
      "Severity scored using CVSS (0–10 scale)",
      "Data from Google's OSV database — 800k+ CVEs",
      "Example: Log4Shell scored 10.0 / Critical"]),
    ("🟠", "Supply Chain Risks",
     ["Packages from unrecognised publishers",
      "Typosquatted names (e.g. 'djano' vs 'django')",
      "Untrusted or unofficial sources",
      "Example: fake packages that steal data"]),
    ("🟡", "Leaked Secrets",
     ["Passwords accidentally committed to code",
      "API keys, GitHub tokens, AWS credentials",
      "Database connection strings with passwords",
      "Example: AWS key exposed in config file"]),
    ("🟢", "Licence Violations",
     ["GPL / AGPL licences in commercial products",
      "Verified against the real package registry",
      "Triggered if a blocked licence is found",
      "Example: GPL code in a proprietary product"]),
    ("🔵", "Dependency Drift",
     ["Libraries added or changed since last scan",
      "Version upgrades or downgrades tracked",
      "Alerts when a new CVE-carrying dep appears",
      "Example: developer quietly bumps a version"]),
    ("⚫", "Policy Violations",
     ["Customisable rules set by your organisation",
      "E.g. zero tolerance for Critical CVEs",
      "E.g. max 5 High-severity vulnerabilities",
      "Blocks pipeline if policy is breached"]),
]

positions = [(0.3, 1.55), (4.55, 1.55), (8.8, 1.55),
             (0.3,  4.35), (4.55, 4.35), (8.8,  4.35)]

for (x, y), (icon, title, body) in zip(positions, categories):
    R(s, x, y, 3.85, 2.6, fill=LGRAY, line_rgb=MGRAY, lw=0.5)
    T(s, icon + "  " + title, x + 0.15, y + 0.1, 3.55, 0.4,
      size=13, bold=True, color=NAVY)
    R(s, x, y + 0.5, 3.85, 0.04, fill=TEAL)
    BL(s, body, x + 0.15, y + 0.6, 3.55, 1.85, size=11, gap=3)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 6 — THE HEALTH REPORT
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "The Health Report — Your Security Dashboard",
    "An interactive report delivered after every scan — open in any browser, no login required")
FOOTER(s)

grades = [("A", "90–100", GREEN), ("B", "75–89", TEAL),
          ("C", "50–74", AMBER),  ("D", "25–49", ORANGE), ("F", "0–24", RED)]
gx = 0.4
for grade, rng, col in grades:
    R(s, gx, 1.55, 2.3, 1.3, fill=col)
    T(s, grade, gx + 0.3, 1.6, 1.0, 0.75, size=40, bold=True, color=WHITE,
      align=PP_ALIGN.CENTER)
    T(s, rng, gx + 0.1, 2.3, 2.1, 0.42, size=13, color=WHITE,
      align=PP_ALIGN.CENTER)
    gx += 2.42

T(s, "The report shows:", 0.4, 3.1, 5.5, 0.4, size=16, bold=True, color=NAVY)
BL(s, [
    "Health score before and after the automated fix",
    "Full list of vulnerabilities found with severity",
    "Risk ranking — most dangerous dependencies first",
    "Details of the fix PR (what was upgraded, why)",
    "Validation gate results — was the fix safe?",
    "Unit test results from the pipeline itself",
], 0.4, 3.55, 5.5, 3.2, size=15, gap=7)

R(s, 6.3, 3.05, 6.7, 3.7, fill=LGRAY, line_rgb=NAVY, lw=1)
T(s, "Real Example — uc1-security-demo Repo",
  6.5, 3.15, 6.3, 0.4, size=14, bold=True, color=NAVY)
R(s, 6.3, 3.55, 6.7, 0.04, fill=TEAL)

NUM_CARD(s, 6.45, 3.7,  2.0, 1.25, "28",       "CVEs Found",         ORANGE)
NUM_CARD(s, 8.55, 3.7,  2.0, 1.25, "5",        "Critical",           RED)
NUM_CARD(s,10.65, 3.7,  1.9, 1.25, "12",       "High Severity",      AMBER)
NUM_CARD(s, 6.45, 5.05, 2.0, 1.25, "F → A",    "Grade After Fix",    GREEN)
NUM_CARD(s, 8.55, 5.05, 2.0, 1.25, "6",        "Upgrades Proposed",  TEAL)
NUM_CARD(s,10.65, 5.05, 1.9, 1.25, "< 90s",    "Total Scan Time",    NAVY)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 7 — AUTOMATED FIX (THE PR)
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "Automated Fix — One Pull Request, All Upgrades",
    "The pipeline creates a single GitHub PR covering every unsafe library — ready for review or auto-merge")
FOOTER(s)

T(s, "What the PR contains:", 0.4, 1.55, 6.0, 0.4, size=16, bold=True, color=NAVY)
BL(s, [
    "!A table of every unsafe library with old and new version",
    "!Details of every CVE that will be fixed by the upgrade",
    "!Clear flag for MAJOR upgrades that need human sign-off",
    "!A review checklist so nothing is forgotten",
    "!Validation gate results posted as a comment",
], 0.4, 2.0, 6.0, 3.5, size=15, gap=9)

T(s, "Smart merge policy:", 0.4, 5.55, 6.0, 0.4, size=16, bold=True, color=NAVY)
BL(s, [
    "@PATCH upgrades  (bug-fix only)  →  auto-merged",
    "@MINOR upgrades  (new features)  →  auto-merged",
    "@MAJOR upgrades  (breaking changes)  →  human review required",
], 0.4, 6.0, 6.0, 1.3, size=15, gap=6)

R(s, 6.8, 1.55, 6.1, 5.7, fill=LGRAY, line_rgb=MGRAY)
T(s, "Example upgrades from demo scan:",
  7.0, 1.65, 5.7, 0.4, size=14, bold=True, color=NAVY)
R(s, 6.8, 2.1, 6.1, 0.04, fill=TEAL)

rows = [
    ("Library",        "Old Ver",   "New Ver",   "Bump",  "CVEs Fixed"),
    ("log4j-core",     "2.14.1",    "2.26.0",    "MINOR", "7  ✔"),
    ("spring-core",    "5.3.20",    "7.0.7",     "MAJOR", "1  ⚠"),
    ("jackson-databind","2.13.0",   "2.22.0",    "MINOR", "4  ✔"),
    ("h2",             "2.1.210",   "2.4.240",   "MINOR", "1  ✔"),
    ("commons-text",   "1.9",       "1.15.0",    "MINOR", "3  ✔"),
    ("snakeyaml",      "1.30",      "2.6",       "MAJOR", "5  ⚠"),
]
col_x = [7.0, 8.2, 9.25, 10.25, 11.15]
col_w = [1.15, 1.0, 0.95, 0.85, 1.55]
ry = 2.15
for ri, row in enumerate(rows):
    bg = NAVY if ri == 0 else (WHITE if ri % 2 == 0 else LGRAY)
    R(s, 6.82, ry, 6.06, 0.52, fill=bg)
    for ci, (cell, cx, cw) in enumerate(zip(row, col_x, col_w)):
        is_hdr = ri == 0
        col_ = WHITE if is_hdr else (RED if "⚠" in cell else (GREEN if "✔" in cell else DARK))
        T(s, cell, cx, ry + 0.06, cw, 0.4, size=12, bold=is_hdr, color=col_)
    ry += 0.54

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 8 — VALIDATION GATES
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "Safety First — 4 Validation Gates",
    "Every fix is independently verified before it is allowed to merge into your codebase")
FOOTER(s)

gates = [
    ("Gate 1", "Unit Tests",
     ["Runs your project's existing test suite",
      "Ensures no existing feature is broken by the upgrade",
      "Result: PASS / FAIL / SKIPPED"],
     TEAL),
    ("Gate 2", "Vulnerability Re-scan",
     ["Re-checks the upgraded libraries for NEW vulnerabilities",
      "Confirms the upgrade does not introduce a new CVE",
      "Always runs — no tools required"],
     GREEN),
    ("Gate 3", "Container Security Scan",
     ["Scans the upgraded code with Grype (Anchore)",
      "Checks for Critical/High findings in container layers",
      "Result: PASS / FAIL / SKIPPED"],
     NAVY),
    ("Gate 4", "Code Coverage",
     ["Verifies test coverage has not dropped below threshold",
      "Default threshold: 80% line coverage",
      "Result: PASS / FAIL / SKIPPED"],
     AMBER),
]

gx = 0.35
for num, title, body, col in gates:
    R(s, gx, 1.55, 3.1, 3.7, fill=LGRAY, line_rgb=col, lw=2)
    R(s, gx, 1.55, 3.1, 0.5, fill=col)
    T(s, num, gx + 0.1, 1.6, 0.7, 0.4, size=13, bold=True, color=WHITE)
    T(s, title, gx + 0.75, 1.6, 2.25, 0.4, size=14, bold=True, color=WHITE)
    BL(s, body, gx + 0.15, 2.15, 2.8, 2.9, size=13, gap=6)
    gx += 3.22

T(s, "Verdict Logic:", 0.35, 5.5, 12.5, 0.4, size=16, bold=True, color=NAVY)

boxes = [
    ("All gates PASS  +  PATCH or MINOR upgrade", "AUTO-MERGE  ✔", GREEN),
    ("All gates PASS  +  MAJOR upgrade",          "Human Review Required  ⚠", AMBER),
    ("Any gate FAILS",                            "BLOCKED  ✗  (details in PR comment)", RED),
    ("Gate tool not installed",                   "SKIPPED  —  Does not block merge", MGRAY),
]
bx = 0.35
for cond, verdict, col in boxes:
    R(s, bx, 6.0, 3.1, 1.0, fill=LGRAY, line_rgb=col, lw=1.5)
    T(s, cond,    bx + 0.1, 6.05, 2.9, 0.4, size=11, color=DARK)
    T(s, verdict, bx + 0.1, 6.5,  2.9, 0.4, size=12, bold=True, color=col)
    bx += 3.22

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 9 — LIVE DEMO RESULTS
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "Live Demo — Real Results",
    "Scanned: github.com/SRGuptthha/uc1-security-demo  |  Language: Java / Maven  |  Duration: < 90 seconds")
FOOTER(s)

R(s, 0.3, 1.55, 8.5, 1.4, fill=RED)
T(s, "BEFORE  —  Health Grade: F", 0.5, 1.62, 8.0, 0.45, size=18, bold=True, color=WHITE)
T(s, "Score: 0 / 100   (too many critical vulnerabilities — floor reached)",
  0.5, 2.08, 8.0, 0.5, size=14, color=WHITE)

R(s, 0.3, 3.1, 8.5, 1.4, fill=GREEN)
T(s, "AFTER   —  Health Grade: A", 0.5, 3.17, 8.0, 0.45, size=18, bold=True, color=WHITE)
T(s, "Score: 100 / 100   (all 28 CVEs resolved by the automated upgrades)",
  0.5, 3.63, 5.0, 0.5, size=14, color=WHITE)

BL(s, [
    "*What was found:",
    "28 CVEs across 7 libraries",
    "5 Critical severity  (CVSS ≥ 9.0) including Log4Shell (10.0)",
    "12 High severity  (CVSS ≥ 7.0)",
    "*What the pipeline did:",
    "Created 1 consolidated GitHub PR",
    "Upgraded 6 libraries to safe versions",
    "Auto-merged 4 MINOR upgrades",
    "Flagged 2 MAJOR upgrades for human review",
    "*Time taken:  < 90 seconds end-to-end",
], 0.4, 4.65, 5.5, 2.6, size=13, gap=3)

R(s, 6.2, 1.55, 6.9, 5.7, fill=LGRAY, line_rgb=MGRAY)
T(s, "Security Improvement Summary", 6.4, 1.65, 6.5, 0.4, size=14, bold=True, color=NAVY)
R(s, 6.2, 2.1, 6.9, 0.04, fill=TEAL)

NUM_CARD(s,  6.35, 2.2,  3.1, 1.45, "28 → 0",   "CVEs Resolved",         GREEN)
NUM_CARD(s,  9.6,  2.2,  3.1, 1.45, "F → A",    "Health Grade",          GREEN)
NUM_CARD(s,  6.35, 3.8,  3.1, 1.45, "6",        "Libraries Upgraded",    TEAL)
NUM_CARD(s,  9.6,  3.8,  3.1, 1.45, "4",        "Auto-Merged PRs",       TEAL)
NUM_CARD(s,  6.35, 5.4,  3.1, 1.3,  "2",        "Awaiting Human Review", AMBER)
NUM_CARD(s,  9.6,  5.4,  3.1, 1.3,  "63 / 63",  "Unit Tests Passed",     GREEN)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 10 — BUSINESS BENEFITS
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "Business Benefits",
    "Why this matters beyond the technical details")
FOOTER(s)

benefits = [
    ("⏱", "Speed",
     "Scan + fix delivered in < 90 seconds\nvs days of manual security review",
     "< 90s per scan"),
    ("💰", "Cost",
     "No security tool licences needed\nAll data sources are free and open",
     "£0 tooling cost"),
    ("🛡", "Risk Reduction",
     "Known vulnerabilities fixed before\nthey can be exploited in production",
     "0 known CVEs"),
    ("📋", "Compliance",
     "Automatic SBOM for EU CRA / US EO 14028\nLicence compliance enforced per policy",
     "Audit-ready"),
    ("🔄", "Continuity",
     "Runs in CI/CD on every code push\nWeekly scheduled scans catch new CVEs",
     "Always current"),
    ("👥", "Transparency",
     "Clear HTML report for any audience\nHealth score tells the story at a glance",
     "Board-ready"),
]

bx = 0.35
by = 1.55
for i, (icon, title, body, stat) in enumerate(benefits):
    if i == 3:
        bx = 0.35; by = 4.3
    R(s, bx, by, 3.95, 2.55, fill=LGRAY, line_rgb=MGRAY, lw=0.5)
    R(s, bx, by, 3.95, 0.5, fill=NAVY)
    T(s, icon + "  " + title, bx + 0.12, by + 0.07, 3.7, 0.4,
      size=16, bold=True, color=WHITE)
    T(s, body, bx + 0.15, by + 0.62, 3.65, 1.2, size=13, color=DARK)
    R(s, bx + 0.15, by + 1.9, 3.65, 0.42, fill=TEAL)
    T(s, stat, bx + 0.15, by + 1.93, 3.65, 0.35, size=13, bold=True,
      color=WHITE, align=PP_ALIGN.CENTER)
    bx += 4.22

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 11 — SUPPORTED TECHNOLOGIES
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "Works With Your Technology Stack",
    "Automatic language detection — no configuration needed")
FOOTER(s)

T(s, "The pipeline detects your project language automatically and uses the correct approach for each:",
  0.4, 1.55, 12.5, 0.45, size=16, color=DARK)

techs = [
    ("☕  Java",       "Maven",    "pom.xml",          ORANGE),
    ("🐍  Python",     "PyPI",     "requirements.txt", TEAL),
    ("🟢  Node.js",    "npm",      "package.json",     GREEN),
    ("🔷  .NET",       "NuGet",    "*.csproj",         NAVY),
    ("💎  Ruby",       "RubyGems", "Gemfile",          RED),
    ("🐹  Go",         "Go Proxy", "go.mod",           TEAL),
]
tx = 0.4
for lang, registry, manifest, col in techs:
    R(s, tx, 2.2, 2.1, 3.5, fill=col)
    T(s, lang,     tx+0.1, 2.35, 1.9, 0.55, size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    T(s, registry, tx+0.1, 2.95, 1.9, 0.45, size=14, color=WHITE, align=PP_ALIGN.CENTER, italic=True)
    R(s, tx+0.1, 3.45, 1.9, 0.04, fill=WHITE)
    T(s, manifest, tx+0.1, 3.55, 1.9, 0.4,  size=12, color=WHITE, align=PP_ALIGN.CENTER)
    T(s, "Auto-detected", tx+0.1, 3.9, 1.9, 0.3, size=10, color=WHITE,
      align=PP_ALIGN.CENTER, italic=True)
    tx += 2.2

T(s, "Each language uses the correct vulnerability database, package registry, and version resolver:",
  0.4, 5.88, 12.5, 0.4, size=14, color=DARK)
BL(s, [
    "Maven  →  OSV.dev (Maven ecosystem)  +  Maven Central version lookup",
    "PyPI   →  OSV.dev (PyPI ecosystem)   +  pypi.org version lookup",
    "npm    →  OSV.dev (npm ecosystem)    +  registry.npmjs.org version lookup",
], 0.4, 6.3, 6.0, 1.0, size=13, gap=2)
BL(s, [
    "NuGet    →  OSV.dev (NuGet)      +  api.nuget.org version lookup",
    "RubyGems →  OSV.dev (RubyGems)  +  rubygems.org version lookup",
    "Go       →  OSV.dev (Go)        +  proxy.golang.org version lookup",
], 6.5, 6.3, 6.4, 1.0, size=13, gap=2)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 12 — CI/CD INTEGRATION + MCP
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "Fits Into Your Existing Workflow",
    "GitHub Actions is live in this repo — and Claude Code can drive the pipeline via MCP")
FOOTER(s)

T(s, "GitHub Actions (already live):", 0.4, 1.55, 5.5, 0.4, size=16, bold=True, color=NAVY)
BL(s, [
    "!Workflow at .github/workflows/security-scan.yml — active now",
    "!Triggers on push to main, manual run, and weekly Monday scan",
    "!Add DEMO_REPO_PAT secret to enable live PR creation",
    "!Also generates security-scan.yml for any other target repo",
    "!Works in Jenkins, GitLab CI, and Azure DevOps too",
], 0.4, 2.05, 5.5, 3.0, size=15, gap=8)

T(s, "MCP Server (Claude Code):", 0.4, 5.2, 5.5, 0.4, size=16, bold=True, color=TEAL)
BL(s, [
    "scan_repo  —  run full pipeline from a conversation",
    "get_health_report  /  get_cve_summary  /  get_policy_status",
    "create_remediation_prs  —  create GitHub PRs via Claude",
    "~Pre-configured in .mcp.json — no setup needed",
], 0.4, 5.65, 5.5, 1.6, size=13, gap=4)

R(s, 6.3, 1.55, 6.7, 5.7, fill=LGRAY, line_rgb=MGRAY)
T(s, "Trigger → Action → Result",
  6.5, 1.65, 6.3, 0.4, size=15, bold=True, color=NAVY)
R(s, 6.3, 2.1, 6.7, 0.04, fill=TEAL)

triggers = [
    ("Push to main branch",       "→", "Full scan runs automatically",    "HTML report artifact uploaded"),
    ("Manual workflow dispatch",  "→", "Scan + optional PR creation",     "PR merged or flagged for review"),
    ("Every Monday 02:00 UTC",    "→", "Scheduled scan for new CVEs",     "Findings caught before exploitation"),
    ("Claude: scan_repo (MCP)",   "→", "Full pipeline via conversation",  "Health report returned instantly"),
]
ry = 2.2
for trigger, arrow, action, result in triggers:
    R(s, 6.35, ry, 6.6, 0.85, fill=WHITE, line_rgb=LGRAY)
    T(s, trigger, 6.48, ry + 0.05, 2.1, 0.35, size=11, bold=True, color=NAVY)
    T(s, action,  8.75, ry + 0.05, 2.2, 0.35, size=11, color=DARK)
    T(s, result,  6.48, ry + 0.45, 6.3, 0.3,  size=10, color=TEAL, italic=True)
    R(s, 8.62, ry + 0.12, 0.12, 0.12, fill=ORANGE)
    ry += 1.0

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 13 — GETTING STARTED
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
HDR(s, "Getting Started — 3 Simple Steps",
    "From zero to full security scan in under 5 minutes")
FOOTER(s)

steps = [
    ("1", "Run the Pipeline",
     "Open a terminal and run one command pointing at any GitHub repository:",
     "python run_pipeline.py https://github.com/your-org/your-repo",
     "No installation. No configuration. Works immediately.", TEAL),
    ("2", "Review the Report",
     "Open the generated HTML report in any browser to see your security posture:",
     "dependency-health-report.html — generated in the same folder",
     "Health grade, CVE list, risk scores, and upgrade plan — all in one place.", NAVY),
    ("3", "Merge the Fix PR",
     "If you provided a GitHub token, a fix PR was already created for you:",
     "PATCH and MINOR upgrades are auto-merged  |  MAJOR upgrades await your approval",
     "Your security posture improves from the moment you press merge.", GREEN),
]

sy = 1.55
for num, title, desc, cmd, outcome, col in steps:
    R(s, 0.4, sy, 12.5, 1.7, fill=LGRAY, line_rgb=col, lw=2)
    R(s, 0.4, sy, 0.65, 1.7, fill=col)
    T(s, num, 0.4, sy + 0.5, 0.65, 0.65, size=28, bold=True, color=WHITE,
      align=PP_ALIGN.CENTER)
    T(s, title, 1.2, sy + 0.08, 11.4, 0.45, size=18, bold=True, color=NAVY)
    T(s, desc,  1.2, sy + 0.52, 11.4, 0.4, size=13, color=DARK)
    R(s, 1.2, sy + 0.95, 11.4, 0.38, fill=NAVY)
    T(s, cmd, 1.3, sy + 0.98, 11.2, 0.32, size=12, color=TEAL)
    T(s, "✔  " + outcome, 1.2, sy + 1.36, 11.4, 0.28, size=11, color=GREEN, italic=True)
    sy += 1.9

T(s, "Need help?  See SETUP.md for the full pre-flight checklist, or PIPELINE_GUIDE.md for stage-by-stage documentation.",
  0.4, 7.1, 12.5, 0.32, size=11, color=MGRAY, italic=True)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 14 — CLOSING / Q&A
# ─────────────────────────────────────────────────────────────────────────────
s = prs.slides.add_slide(BLANK)
R(s, 0, 0, 13.33, 7.5, fill=NAVY)
R(s, 0, 0, 13.33, 0.08, fill=TEAL)
R(s, 0, 7.42, 13.33, 0.08, fill=TEAL)
R(s, 0.4, 2.8, 12.53, 0.08, fill=TEAL)

T(s, "Questions?", 0.5, 1.3, 12.0, 1.0, size=52, bold=True,
  color=WHITE, align=PP_ALIGN.CENTER)
T(s, "Key Takeaways", 0.5, 3.1, 12.0, 0.5, size=20, bold=True,
  color=TEAL, align=PP_ALIGN.CENTER)

takeaways = [
    "Vulnerabilities in third-party libraries are the #1 supply chain attack vector",
    "UC1 Pipeline finds, scores, and fixes them automatically in < 90 seconds",
    "Works across Java, Python, Node.js, .NET, Ruby, and Go — zero configuration",
    "Delivers a board-ready health score, audit trail, and SBOM in every run",
    "One command away from securing any GitHub repository today",
]
ty = 3.75
for t in takeaways:
    T(s, "✔  " + t, 1.5, ty, 10.3, 0.42, size=16, color=WHITE)
    ty += 0.5

T(s, "Demo repo: github.com/SRGuptthha/uc1-security-demo  ·  Docs: SETUP.md  ·  Guide: PIPELINE_GUIDE.md",
  0.5, 6.95, 12.0, 0.35, size=11, color=MGRAY, align=PP_ALIGN.CENTER)

# ─────────────────────────────────────────────────────────────────────────────
prs.save(OUT)
print(f"Saved: {OUT}")
print(f"Slides: {len(prs.slides)}")
