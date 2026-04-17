"""
PDF report generator for CEFR Reading report.
Design mirrors the iMocha AI-English Pro sample report.

Width budget (A4):
  Page width W = 595 pt
  Left/Right margins = 40 pt each  →  usable = 515 pt
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.platypus.flowables import Flowable

W, H = A4          # 595 × 842 pt
USABLE = W - 80    # 515 pt  (margins 40 each side)

# ── Brand colours ──────────────────────────────────────────────────────────────
ORANGE   = colors.HexColor("#FF6B35")
PURPLE   = colors.HexColor("#6B4EFF")
HEADING  = colors.HexColor("#2D2D6B")
SUBTEXT  = colors.HexColor("#6B7280")
RULE     = colors.HexColor("#E5E7EB")
ROW_ALT  = colors.HexColor("#F9FAFB")
DARK_HDR = colors.HexColor("#1F2937")

BADGE_COLORS = {
    "BelowA2": colors.HexColor("#B0BEC5"),
    "A1":      colors.HexColor("#90CAF9"),
    "A2":      colors.HexColor("#64B5F6"),
    "B1":      colors.HexColor("#4A90D9"),
    "B2":      colors.HexColor("#2C6DB5"),
    "B2+":     colors.HexColor("#1E4FA0"),
    "C1":      colors.HexColor("#1A237E"),
    "C2":      colors.HexColor("#0D0D3D"),
}


# ── Reusable styles ────────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

STYLES = {
    "logo":       S("logo",   fontName="Helvetica-Bold", fontSize=16, textColor=ORANGE),
    "title":      S("title",  fontName="Helvetica-Bold", fontSize=26, textColor=PURPLE, spaceAfter=6),
    "lbl":        S("lbl",    fontName="Helvetica-Bold", fontSize=10, textColor=PURPLE, spaceBefore=8),
    "val":        S("val",    fontName="Helvetica",      fontSize=11, textColor=colors.HexColor("#374151")),
    "sec_head":   S("sh",     fontName="Helvetica-Bold", fontSize=14, textColor=HEADING, spaceBefore=6, spaceAfter=4),
    "col_head":   S("ch",     fontName="Helvetica-Bold", fontSize=10, textColor=HEADING),
    "skill_lbl":  S("sl",     fontName="Helvetica",      fontSize=10, textColor=SUBTEXT),
    "skill_bold": S("sb",     fontName="Helvetica-Bold", fontSize=11, textColor=HEADING),
    "score":      S("sc",     fontName="Helvetica-Bold", fontSize=11, textColor=HEADING),
    "prof":       S("pr",     fontName="Helvetica",      fontSize=10, textColor=SUBTEXT),
    "cap":        S("ca",     fontName="Helvetica",      fontSize=9,  textColor=colors.HexColor("#374151"), leading=14),
    "sb_head":    S("sbh",    fontName="Helvetica-Bold", fontSize=10, textColor=HEADING, spaceAfter=3),
    "sb_body":    S("sbb",    fontName="Helvetica",      fontSize=8,  textColor=SUBTEXT, leading=12),
    "blurb":      S("bl",     fontName="Helvetica",      fontSize=9,  textColor=SUBTEXT, leading=13, spaceAfter=8),
    "pg_num":     S("pn",     fontName="Helvetica",      fontSize=8,  textColor=SUBTEXT, alignment=TA_RIGHT),
    "log_hdr":    S("lh",     fontName="Helvetica-Bold", fontSize=9,  textColor=colors.white),
    "log_cell":   S("lc",     fontName="Helvetica",      fontSize=9,  textColor=colors.HexColor("#374151")),
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=4)


def _footer(page_num: int):
    """Footer row: logo left, page number right. Total = USABLE."""
    data = [[
        Paragraph("⬡ iMocha", STYLES["logo"]),
        Paragraph(f"Page {page_num}", STYLES["pg_num"]),
    ]]
    t = Table(data, colWidths=[450, 65])   # 450+65 = 515 = USABLE
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


def _section_heading(text: str):
    """Orange left-bar heading — uses LINEBEFORE to avoid nested-table width issues."""
    t = Table(
        [[Paragraph(text, STYLES["sec_head"])]],
        colWidths=[USABLE],
    )
    t.setStyle(TableStyle([
        ("LINEBEFORE",    (0, 0), (0, -1), 4, ORANGE),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


# ── Cambridge English Scale profile chart ─────────────────────────────────────
class CEFRProfileChart(Flowable):
    """
    Horizontal profile chart matching the iMocha reference design:
      - Left panel: coloured CEFR band strip + rotated proficiency group labels
      - Centre:     Cambridge scale numbers (80-230) + dashed gridlines
      - Right:      4 skill columns (Speaking / Listening / Reading / Writing)
                    with left-pointing arrow markers at each scored position
    """

    _BANDS = [
        # (bottom_score, label, panel_color)
        (80,  "Pre A1", colors.HexColor("#D6E4F7")),
        (100, "A1",     colors.HexColor("#AECEF0")),
        (120, "A2",     colors.HexColor("#7DB8E8")),
        (140, "B1",     colors.HexColor("#4A90D9")),
        (160, "B2",     colors.HexColor("#1C5FAA")),
        (180, "C1",     colors.HexColor("#1A3A6B")),
        (200, "C2",     colors.HexColor("#0D1B4E")),
        (230, None,     None),   # top sentinel
    ]

    _PROFICIENCY = [
        (80,  140, "Basic"),
        (140, 180, "Independent"),
        (180, 230, "Proficient"),
    ]

    _SKILLS = ["Speaking", "Listening", "Reading", "Writing"]

    def __init__(self, skills, width=490, height=280):
        """
        skills: list of (skill_name, scale_score, fill_color)
                Only named skills will have an arrow drawn; others left empty.
        """
        super().__init__()
        self.skills_map = {s[0]: s for s in skills}
        self.width  = width
        self.height = height

        self._prof_w  = 26     # rotated proficiency label column
        self._band_w  = 52     # coloured CEFR band strip
        self._scale_w = 32     # Cambridge scale numbers
        self._hdr_h   = 22     # column header area at top
        self._grid_x  = self._prof_w + self._band_w + self._scale_w
        self._grid_w  = width - self._grid_x
        self._ch_bot  = 6
        self._ch_top  = height - self._hdr_h - 6
        self._ch_h    = self._ch_top - self._ch_bot

    def _y(self, val):
        """Map Cambridge scale value (80-230) to canvas y-coordinate."""
        return self._ch_bot + (val - 80) / (230 - 80) * self._ch_h

    def draw(self):
        c    = self.canv
        col_w = self._grid_w / len(self._SKILLS)

        # ── Left panel: coloured CEFR band stripes ────────────────────────────
        for i in range(len(self._BANDS) - 1):
            bot, lbl, bg = self._BANDS[i]
            top = self._BANDS[i + 1][0]
            yb  = self._y(bot)
            bh  = self._y(top) - yb

            c.setFillColor(bg)
            c.rect(self._prof_w, yb, self._band_w, bh, fill=1, stroke=0)

            txt_col = colors.white if i >= 3 else colors.HexColor("#1F2937")
            c.setFillColor(txt_col)
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(self._prof_w + self._band_w / 2, yb + bh / 2 - 3, lbl)

        # ── Left panel: rotated proficiency group labels ───────────────────────
        for bot, top, lbl in self._PROFICIENCY:
            mid = (self._y(bot) + self._y(top)) / 2
            c.saveState()
            c.setFillColor(HEADING)
            c.setFont("Helvetica-Bold", 7)
            c.translate(self._prof_w / 2, mid)
            c.rotate(90)
            c.drawCentredString(0, 0, lbl)
            c.restoreState()

        # ── Grid area: subtle alternating band backgrounds ────────────────────
        for i in range(len(self._BANDS) - 1):
            bot = self._BANDS[i][0]
            top = self._BANDS[i + 1][0]
            yb  = self._y(bot)
            bh  = self._y(top) - yb
            bg  = colors.HexColor("#F5F7FF") if i % 2 == 0 else colors.HexColor("#EAEDFA")
            c.setFillColor(bg)
            c.rect(self._grid_x, yb, self._grid_w, bh, fill=1, stroke=0)

        # ── Scale numbers + dashed horizontal gridlines ───────────────────────
        for val in range(80, 231, 10):
            y = self._y(val)
            c.setFillColor(SUBTEXT)
            c.setFont("Helvetica", 6)
            c.drawRightString(self._grid_x - 4, y - 2.5, str(val))
            c.setStrokeColor(colors.HexColor("#D1D5DB"))
            c.setLineWidth(0.3)
            c.setDash(2, 3)
            c.line(self._grid_x, y, self.width, y)
        c.setDash()

        # ── Vertical column dividers ──────────────────────────────────────────
        for i in range(1, len(self._SKILLS)):
            x = self._grid_x + i * col_w
            c.setStrokeColor(colors.HexColor("#E5E7EB"))
            c.setLineWidth(0.5)
            c.line(x, self._ch_bot, x, self._ch_top)

        # ── Column headers ────────────────────────────────────────────────────
        for i, name in enumerate(self._SKILLS):
            cx = self._grid_x + i * col_w + col_w / 2
            c.setFillColor(HEADING)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(cx, self._ch_top + 8, name)

        # ── Left-pointing arrow markers for each scored skill ─────────────────
        col_idx = {n: i for i, n in enumerate(self._SKILLS)}
        aw  = col_w * 0.75   # arrow body width
        ah  = 16             # arrow total height
        tip = ah * 0.5       # how far the tip protrudes left of body

        for name, (_, scale_score, fill) in self.skills_map.items():
            idx = col_idx.get(name)
            if idx is None:
                continue
            col_cx = self._grid_x + idx * col_w + col_w / 2
            y      = self._y(scale_score)

            lx = col_cx - aw / 2        # left edge of rectangular body
            rx = col_cx + aw / 2        # right edge
            tx = lx - tip               # tip x (leftmost point)

            c.setFillColor(fill)
            c.setStrokeColor(fill)
            p = c.beginPath()
            p.moveTo(tx, y)             # tip
            p.lineTo(lx, y + ah / 2)   # body top-left
            p.lineTo(rx, y + ah / 2)   # body top-right
            p.lineTo(rx, y - ah / 2)   # body bottom-right
            p.lineTo(lx, y - ah / 2)   # body bottom-left
            p.close()
            c.drawPath(p, fill=1, stroke=0)

            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(col_cx + tip / 2, y - 3.5, str(scale_score))


# ── CEFR badge flowable ────────────────────────────────────────────────────────
class CEFRBadge(Flowable):
    def __init__(self, level, width=72, height=22):
        super().__init__()
        self.level  = level
        self.width  = width
        self.height = height

    def draw(self):
        bg = BADGE_COLORS.get(self.level, PURPLE)
        self.canv.setFillColor(bg)
        self.canv.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=0)
        self.canv.setFillColor(colors.white)
        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.drawCentredString(self.width / 2, 6, f"CEFR: {self.level}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Cover
# ══════════════════════════════════════════════════════════════════════════════
def _cover_page(candidate: dict) -> list:
    e = []

    # Top accent bar
    e.append(Table([[""]], colWidths=[USABLE], rowHeights=[4],
                   style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), ORANGE),
                                     ("TOPPADDING", (0, 0), (-1, -1), 0),
                                     ("BOTTOMPADDING", (0, 0), (-1, -1), 0)])))
    e.append(Spacer(1, 18))
    e.append(Paragraph("⬡ iMocha", STYLES["logo"]))
    e.append(Spacer(1, 55))
    e.append(Paragraph("AI-English Pro", STYLES["title"]))
    e.append(_hr())
    e.append(Spacer(1, 16))

    # 2-column info grid  (240 + 240 = 480 < 515)
    COL = 240
    info = [
        [Paragraph("Company",        STYLES["lbl"]),  Paragraph("Candidate Name", STYLES["lbl"])],
        [Paragraph(candidate.get("company", "—"),  STYLES["val"]),
         Paragraph(candidate.get("name",    "—"),  STYLES["val"])],
        [Paragraph("Date of Attempt", STYLES["lbl"]), Paragraph("Candidate ID",   STYLES["lbl"])],
        [Paragraph(candidate.get("appeared_on","—"), STYLES["val"]),
         Paragraph(str(candidate.get("id","—")),   STYLES["val"])],
    ]
    t = Table(info, colWidths=[COL, COL])
    t.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    e.append(t)
    e.append(Spacer(1, 200))
    e.append(_hr())
    e.append(_footer(1))
    return e


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Score Analysis
# ══════════════════════════════════════════════════════════════════════════════
def _score_analysis_page(reading_scoring: dict, listening_scoring: dict) -> list:
    e = []
    e.append(Spacer(1, 10))
    e.append(_section_heading("Score Analysis"))
    e.append(Spacer(1, 8))

    # Chart title row  (matches the reference report header)
    title_row = Table([[
        Paragraph("<b>CEFR Assessment Profile</b>", STYLES["col_head"]),
        Paragraph("Cambridge English Scale &middot; Skills breakdown", STYLES["blurb"]),
    ]], colWidths=[180, USABLE - 180])
    title_row.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",(0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
    ]))
    e.append(title_row)

    # Profile chart — DARK_HDR for Listening arrow, PURPLE for Reading
    chart = CEFRProfileChart(
        skills=[
            ("Listening", int(listening_scoring.get("scale_score", 120)), DARK_HDR),
            ("Reading",   int(reading_scoring.get("scale_score",   120)), PURPLE),
        ],
        width=USABLE - 20,
        height=285,
    )
    card = Table([[chart]], colWidths=[USABLE])
    card.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    e.append(card)
    e.append(Spacer(1, 10))

    # CEFR blurb
    e.append(Paragraph(
        "The Common European Framework of Reference for Languages (CEFR) is a "
        "standardised grading system aiming to validate language ability.",
        STYLES["blurb"],
    ))

    e.append(_hr())
    e.append(_footer(2))
    return e


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Section Skill Analysis
# ══════════════════════════════════════════════════════════════════════════════
def _skill_section_row(section_num: int, label: str, scoring: dict) -> Table:
    """One skill section row — reused for Reading and Listening."""
    LEFT_W  = 315
    RIGHT_W = 175
    INNER_L = 290

    pct = scoring["performance_pct"]

    left_content = [
        Paragraph(
            f'<font color="#6B7280">Section {section_num}: </font>'
            f'<b><font color="#2D2D6B">{label}</font></b>'
            f'<font color="#2D2D6B">    &nbsp;&nbsp;&nbsp;&nbsp; '
            f'Total Score: <b>{pct}/100</b></font>',
            STYLES["skill_lbl"],
        ),
        Spacer(1, 6),
        Table(
            [[CEFRBadge(scoring["cefr_display"], width=72, height=22),
              Paragraph(scoring["proficiency_label"], STYLES["prof"])]],
            colWidths=[80, INNER_L - 80],
        ),
        Spacer(1, 10),
        Paragraph(scoring["capability_statement"], STYLES["cap"]),
    ]

    right_content = [
        Paragraph(label, STYLES["sb_head"]),
        Spacer(1, 4),
        Paragraph(scoring["skill_definition"], STYLES["sb_body"]),
    ]

    body = Table(
        [[left_content, right_content]],
        colWidths=[LEFT_W, RIGHT_W],
    )
    body.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LINEAFTER",    (0, 0), (0, -1),  0.5, RULE),
        ("RIGHTPADDING", (0, 0), (0, -1),  12),
        ("LEFTPADDING",  (1, 0), (1, -1),  12),
        ("LEFTPADDING",  (0, 0), (0, -1),  6),
    ]))
    return body


def _skill_analysis_page(reading_scoring: dict, listening_scoring: dict) -> list:
    e = []
    e.append(Spacer(1, 10))
    e.append(_section_heading("Section Skill Analysis"))
    e.append(Spacer(1, 6))

    # Column headers
    LEFT_W, RIGHT_W = 315, 175
    hdr = Table(
        [[Paragraph("Capabilities and Skills", STYLES["col_head"]),
          Paragraph("Understanding the skills", STYLES["col_head"])]],
        colWidths=[LEFT_W, RIGHT_W],
    )
    hdr.setStyle(TableStyle([
        ("LINEBELOW",     (0, 0), (-1, -1), 0.5, RULE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    e.append(hdr)
    e.append(Spacer(1, 8))

    # Section 1 — Reading
    e.append(_skill_section_row(1, "Reading", reading_scoring))
    e.append(Spacer(1, 12))

    # Divider between sections
    e.append(HRFlowable(width="100%", thickness=0.3, color=RULE, spaceAfter=8))

    # Section 2 — Listening
    e.append(_skill_section_row(2, "Listening", listening_scoring))

    e.append(Spacer(1, 16))
    e.append(_hr())
    e.append(_footer(3))
    return e


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Test Log
# ══════════════════════════════════════════════════════════════════════════════
def _test_log_page(candidate: dict) -> list:
    e = []
    e.append(Spacer(1, 10))
    e.append(_section_heading("Test Log"))
    e.append(Spacer(1, 10))

    log = [
        [Paragraph("Test Status",    STYLES["log_hdr"]),
         Paragraph("Date & Time",    STYLES["log_hdr"])],
        [Paragraph("Appeared On",    STYLES["log_cell"]),
         Paragraph(candidate.get("appeared_on", "—"),        STYLES["log_cell"])],
        [Paragraph("Report Generated On", STYLES["log_cell"]),
         Paragraph(candidate.get("report_generated_on", "—"), STYLES["log_cell"])],
    ]
    log_t = Table(log, colWidths=[190, USABLE - 190])
    log_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1,  0), DARK_HDR),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [ROW_ALT, colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    e.append(log_t)
    e.append(Spacer(1, 40))
    e.append(_hr())
    e.append(_footer(4))
    return e


# ══════════════════════════════════════════════════════════════════════════════
# Public entry point
# ══════════════════════════════════════════════════════════════════════════════
def generate_reading_report(candidate: dict, reading_scoring: dict, listening_scoring: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=40, rightMargin=40,
        topMargin=30,  bottomMargin=30,
    )

    story = []
    story.extend(_cover_page(candidate))
    story.append(PageBreak())
    story.extend(_score_analysis_page(reading_scoring, listening_scoring))
    story.append(PageBreak())
    story.extend(_skill_analysis_page(reading_scoring, listening_scoring))
    story.append(PageBreak())
    story.extend(_test_log_page(candidate))

    doc.build(story)
    return buf.getvalue()
