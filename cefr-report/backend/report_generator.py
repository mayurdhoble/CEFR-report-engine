"""
PDF report generator for CEFR Reading report.
Design mirrors the iMocha AI-English Pro sample report.

Width budget (A4):
  Page width W = 595 pt
  Left/Right margins = 40 pt each  →  usable = 515 pt
"""
import io
import math
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.platypus.flowables import Flowable

_HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_FULL = os.path.join(_HERE, "logoimocha.png")   # full logo (icon + text)
LOGO_ICON = os.path.join(_HERE, "logo.png")          # icon only

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
    "A1":      colors.HexColor("#AECEF0"),
    "A2":      colors.HexColor("#7DB8E8"),
    "B1":      colors.HexColor("#4A90D9"),
    "B2":      colors.HexColor("#1C5FAA"),
    "B2+":     colors.HexColor("#1C5FAA"),
    "C1":      colors.HexColor("#1A3A6B"),
    "C2":      colors.HexColor("#0D1B4E"),
}


# ── Reusable styles ────────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

SOFT_PURPLE = colors.HexColor("#8B7EC8")   # cover info labels
INFO_GREY   = colors.HexColor("#9CA3AF")   # cover info values

STYLES = {
    "logo":       S("logo",   fontName="Helvetica-Bold", fontSize=16, textColor=ORANGE),
    "title":      S("title",  fontName="Helvetica-Bold", fontSize=26, textColor=PURPLE, spaceAfter=6),
    "lbl":        S("lbl",    fontName="Helvetica-Bold", fontSize=17, textColor=SOFT_PURPLE, spaceBefore=18),
    "val":        S("val",    fontName="Helvetica",      fontSize=15, textColor=INFO_GREY),
    "sec_head":   S("sh",     fontName="Helvetica-Bold", fontSize=14, textColor=HEADING, spaceBefore=2, spaceAfter=2),
    "col_head":   S("ch",     fontName="Helvetica-Bold", fontSize=13, textColor=HEADING),
    "col_head_r": S("chr",    fontName="Helvetica-Bold", fontSize=13, textColor=HEADING, alignment=TA_RIGHT),
    "skill_lbl":  S("sl",     fontName="Helvetica",      fontSize=12, textColor=SUBTEXT),
    "skill_bold": S("sb",     fontName="Helvetica-Bold", fontSize=13, textColor=HEADING),
    "score_r":    S("scr",    fontName="Helvetica-Bold", fontSize=12, textColor=HEADING, alignment=TA_RIGHT),
    "score":      S("sc",     fontName="Helvetica-Bold", fontSize=13, textColor=HEADING),
    "prof":       S("pr",     fontName="Helvetica-Bold", fontSize=12, textColor=SUBTEXT),
    "cap":        S("ca",     fontName="Helvetica",      fontSize=11, textColor=colors.HexColor("#374151"), leading=16),
    "sb_head":    S("sbh",    fontName="Helvetica-Bold", fontSize=13, textColor=HEADING, spaceAfter=4),
    "sb_body":    S("sbb",    fontName="Helvetica",      fontSize=11, textColor=SUBTEXT, leading=16),
    "blurb":      S("bl",     fontName="Helvetica",      fontSize=9,  textColor=SUBTEXT, leading=13, spaceAfter=8),
    "pg_num":     S("pn",     fontName="Helvetica",      fontSize=8,  textColor=SUBTEXT, alignment=TA_RIGHT),
    "log_hdr":    S("lh",     fontName="Helvetica-Bold", fontSize=9,  textColor=colors.white),
    "log_cell":   S("lc",     fontName="Helvetica",      fontSize=9,  textColor=colors.HexColor("#374151")),
    "badge_lbl":  S("bgl",    fontName="Helvetica-Bold", fontSize=8,  textColor=colors.white, alignment=TA_CENTER),
    "badge_sub":  S("bgs",    fontName="Helvetica",      fontSize=8,  textColor=SUBTEXT,       alignment=TA_CENTER),
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=4)


def _logo_img(height=22):
    """Returns iMocha logo image at correct aspect ratio (759×354)."""
    if os.path.exists(LOGO_FULL):
        w = round(height * 759 / 354)
        img = Image(LOGO_FULL, width=w, height=height)
        img.hAlign = "LEFT"
        return img
    return Paragraph("iMocha", STYLES["logo"])


TOTAL_PAGES = 4

def _on_page(canvas, doc):
    """Fixed footer drawn at bottom of every page via onPage callback."""
    canvas.saveState()
    page_num = doc.page
    logo_h = 28
    logo_w = round(logo_h * 759 / 354)
    y = 24   # bottom position for logo

    # Separator line above footer
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(40, y + logo_h + 8, W - 40, y + logo_h + 8)

    # Centred iMocha logo (larger)
    if os.path.exists(LOGO_FULL):
        canvas.drawImage(LOGO_FULL, (W - logo_w) / 2, y,
                         width=logo_w, height=logo_h, mask='auto')

    # Page number right-aligned, vertically centred with logo
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(SUBTEXT)
    canvas.drawRightString(W - 40, y + logo_h / 2 - 3, f"Page {page_num}/{TOTAL_PAGES}")
    canvas.restoreState()


def _section_heading(text: str):
    """Grey-background heading with orange left bar — matches iMocha HTML reference."""
    t = Table(
        [[Paragraph(text, STYLES["sec_head"])]],
        colWidths=[USABLE],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
        ("LINEBEFORE",    (0, 0), (0, -1), 4, ORANGE),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


# CEFR legend row (Pre A1 → C2) — colors match the chart band strip
_CEFR_LEGEND = [
    ("Pre A1", "#D6E4F7", "#1F2937", "Beginner"),
    ("A1",     "#AECEF0", "#1F2937", "Beginner"),
    ("A2",     "#7DB8E8", "#FFFFFF", "Elementary"),
    ("B1",     "#4A90D9", "#FFFFFF", "Intermediate"),
    ("B2",     "#1C5FAA", "#FFFFFF", "Upper-Int"),
    ("C1",     "#1A3A6B", "#FFFFFF", "Advanced"),
    ("C2",     "#0D1B4E", "#FFFFFF", "Mastery"),
]

# 9-point star polygon (HTML % coords, y-axis flipped in draw())
_STAR_PTS = [
    (50, 0), (61, 19), (82, 12), (79, 35), (98, 45),
    (82, 61), (92, 82), (69, 80), (61, 100), (50, 83),
    (39, 100), (31, 80), (8, 82), (18, 61), (2, 45),
    (21, 35), (18, 12), (39, 19),
]


class StarBadge(Flowable):
    """CEFR star badge: 9-point star with level text + subtitle below."""
    STAR_SIZE = 56
    LABEL_GAP = 6
    LABEL_H   = 12

    def __init__(self, level, label, bg_color, fg_color):
        super().__init__()
        self.level    = level
        self.label    = label
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.width    = self.STAR_SIZE
        self.height   = self.STAR_SIZE + self.LABEL_GAP + self.LABEL_H

    def draw(self):
        c = self.canv
        size = self.STAR_SIZE
        star_bottom = self.LABEL_GAP + self.LABEL_H

        # Star shape
        c.setFillColor(self.bg_color)
        p = c.beginPath()
        for i, (px, py) in enumerate(_STAR_PTS):
            x = size * px / 100
            y = star_bottom + size * (100 - py) / 100
            (p.moveTo if i == 0 else p.lineTo)(x, y)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # Level text in center of star
        cx = size / 2
        cy = star_bottom + size / 2
        c.setFillColor(self.fg_color)
        if " " in self.level:
            parts = self.level.split(" ", 1)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(cx, cy + 2,  parts[0])
            c.drawCentredString(cx, cy - 8,  parts[1])
        else:
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(cx, cy - 5, self.level)

        # Subtitle label below star
        c.setFillColor(HEADING)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(cx, 1, self.label)


def _cefr_legend():
    """Row of 7 star-shaped CEFR level badges."""
    badges = [
        StarBadge(lvl, sub, colors.HexColor(bg), colors.HexColor(fg))
        for lvl, bg, fg, sub in _CEFR_LEGEND
    ]
    bw = USABLE / 7
    t = Table([badges], colWidths=[bw] * 7)
    t.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("BOX",           (0, 0), (-1, -1), 0.5, RULE),
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
        (100, 140, "Basic"),        # A1–A2
        (140, 180, "Independent"),  # B1–B2
        (180, 230, "Proficient"),   # C1–C2
    ]

    _DEFAULT_SKILLS = ["Speaking", "Listening", "Reading", "Writing"]

    def __init__(self, skills, width=490, height=310, skills_order=None):
        """
        skills:       list of (skill_name, scale_score, fill_color)
        skills_order: list of column names to display (controls which columns appear)
        """
        super().__init__()
        self.skills_map = {s[0]: s for s in skills}
        self._SKILLS    = skills_order if skills_order else self._DEFAULT_SKILLS
        self.width  = width
        self.height = height

        self._prof_w  = 40     # rotated proficiency label column
        self._band_w  = 54     # coloured CEFR band strip
        self._scale_w = 36     # Cambridge scale numbers
        self._hdr_h   = 32     # column header area at top
        self._grid_x  = self._prof_w + self._band_w + self._scale_w
        self._grid_w  = width - self._grid_x
        self._ch_bot  = 8
        self._ch_top  = height - self._hdr_h - 8
        self._ch_h    = self._ch_top - self._ch_bot

    def _y(self, val):
        """Map Cambridge scale value (80-230) to canvas y-coordinate."""
        return self._ch_bot + (val - 80) / (230 - 80) * self._ch_h

    def draw(self):
        c     = self.canv
        col_w = self._grid_w / len(self._SKILLS)

        # ── Proficiency strip: grey background only for A1–C2, white for Pre A1 ─
        c.setFillColor(colors.white)
        c.rect(0, self._ch_bot, self._prof_w, self._ch_h, fill=1, stroke=0)
        y_a1 = self._y(100)   # start of A1 band
        c.setFillColor(colors.HexColor("#F3F4F6"))
        c.rect(0, y_a1, self._prof_w, self._ch_top - y_a1, fill=1, stroke=0)

        # ── Left panel: coloured CEFR band stripes ────────────────────────────
        for i in range(len(self._BANDS) - 1):
            bot, lbl, bg = self._BANDS[i]
            top = self._BANDS[i + 1][0]
            yb  = self._y(bot)
            bh  = self._y(top) - yb

            c.setFillColor(bg)
            c.rect(self._prof_w, yb, self._band_w, bh, fill=1, stroke=0)

            txt_col = colors.white if i >= 2 else colors.HexColor("#1F2937")
            c.setFillColor(txt_col)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(self._prof_w + self._band_w / 2, yb + bh / 2 - 4, lbl)

        # ── Proficiency group dividers (dashed lines at B1=140 and C1=180) ────
        for boundary in (140, 180):
            yb = self._y(boundary)
            c.setStrokeColor(colors.HexColor("#9CA3AF"))
            c.setLineWidth(0.6)
            c.setDash(3, 3)
            c.line(0, yb, self._prof_w + self._band_w, yb)
        c.setDash()

        # ── Left panel: rotated proficiency group labels ───────────────────────
        for bot, top, lbl in self._PROFICIENCY:
            mid = (self._y(bot) + self._y(top)) / 2
            c.saveState()
            c.setFillColor(HEADING)
            c.setFont("Helvetica-Bold", 9)
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
            c.setFont("Helvetica", 7)
            c.drawRightString(self._grid_x - 4, y - 3, str(val))
            c.setStrokeColor(colors.HexColor("#D1D5DB"))
            c.setLineWidth(0.3)
            c.setDash(2, 3)
            c.line(self._grid_x, y, self.width, y)
        c.setDash()

        # ── Outer border around the full chart ────────────────────────────────
        c.setStrokeColor(colors.HexColor("#E5E7EB"))
        c.setLineWidth(0.5)
        c.rect(0, self._ch_bot, self.width, self._ch_h, fill=0, stroke=1)

        # ── Vertical column dividers ──────────────────────────────────────────
        for i in range(1, len(self._SKILLS)):
            x = self._grid_x + i * col_w
            c.setStrokeColor(colors.HexColor("#E5E7EB"))
            c.setLineWidth(0.5)
            c.line(x, self._ch_bot, x, self._ch_top)

        # ── Column headers ────────────────────────────────────────────────────
        hdr_y = self._ch_top + 8

        # CEFR panel header (spans proficiency + band strip)
        cefr_mid = (self._prof_w + self._band_w) / 2
        c.setFillColor(HEADING)
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(cefr_mid, hdr_y + 10, "Common European")
        c.drawCentredString(cefr_mid, hdr_y + 3,  "Framework (CEFR)")

        # Cambridge English Scale header
        scale_mid = self._prof_w + self._band_w + self._scale_w / 2
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(scale_mid, hdr_y + 10, "Cambridge")
        c.drawCentredString(scale_mid, hdr_y + 3,  "English Scale")

        # Skill column headers
        for i, name in enumerate(self._SKILLS):
            cx = self._grid_x + i * col_w + col_w / 2
            c.setFillColor(HEADING)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(cx, hdr_y + 5, name)

        # ── Left-pointing arrow markers for each scored skill ─────────────────
        col_idx = {n: i for i, n in enumerate(self._SKILLS)}
        aw  = col_w * 0.78   # arrow body width
        ah  = 18             # arrow total height
        tip = ah * 0.45      # how far the tip protrudes left of body

        for name, (_, scale_score, fill) in self.skills_map.items():
            idx = col_idx.get(name)
            if idx is None:
                continue
            col_cx   = self._grid_x + idx * col_w + col_w / 2
            plot_val = max(scale_score, 80)   # clamp Pre A1 scores to chart floor
            y        = self._y(plot_val)

            lx = col_cx - aw / 2
            rx = col_cx + aw / 2
            tx = lx - tip

            c.setFillColor(fill)
            c.setStrokeColor(fill)
            p = c.beginPath()
            p.moveTo(tx, y)
            p.lineTo(lx, y + ah / 2)
            p.lineTo(rx, y + ah / 2)
            p.lineTo(rx, y - ah / 2)
            p.lineTo(lx, y - ah / 2)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(col_cx + tip / 2, y - 4, str(scale_score))


# ── CEFR badge flowable ────────────────────────────────────────────────────────
class CEFRBadge(Flowable):
    def __init__(self, level, width=82, height=24):
        super().__init__()
        self.level  = level
        self.width  = width
        self.height = height

    def draw(self):
        bg = BADGE_COLORS.get(self.level, PURPLE)
        fg = colors.HexColor("#1F2937") if self.level in ("A1", "A2", "Pre A1", "BelowA2") else colors.white
        self.canv.setFillColor(bg)
        self.canv.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=0)
        self.canv.setFillColor(fg)
        self.canv.setFont("Helvetica-Bold", 10)
        self.canv.drawCentredString(self.width / 2, 7, f"CEFR: {self.level}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Cover
# ══════════════════════════════════════════════════════════════════════════════
LAVENDER     = colors.HexColor("#EEEFFE")
L_MARGIN     = 40   # must match SimpleDocTemplate leftMargin


class CoverPanel(Flowable):
    """Full-bleed lavender hero: iMocha logo top-left, illustration, AI-English Pro title.
    Lavender extends ABOVE the flowable bounds to cover the page's topMargin area."""
    PANEL_H = 500
    TOP_EXT = 30   # matches SimpleDocTemplate topMargin — extends lavender to page top edge

    def __init__(self, illus_path=None):
        super().__init__()
        self.illus_path = illus_path
        self.width  = USABLE
        self.height = self.PANEL_H

    def draw(self):
        c = self.canv
        W_ = self.width
        H_ = self.PANEL_H
        EXT = self.TOP_EXT

        # Full-bleed lavender — over-extend by 10pt to guarantee no white slivers
        c.setFillColor(LAVENDER)
        c.rect(-L_MARGIN - 10, -10, W + 20, H_ + EXT + 20, fill=1, stroke=0)

        # iMocha logo — top-left of lavender, larger and closer to page top
        logo_h = 40
        logo_w = round(logo_h * 759 / 354)
        if os.path.exists(LOGO_FULL):
            c.drawImage(LOGO_FULL, 0, H_ + EXT - logo_h - 18,
                        width=logo_w, height=logo_h, mask='auto')

        # Illustration image — below the logo, aspect-preserved
        if self.illus_path and os.path.exists(self.illus_path):
            box_x = 20
            box_y = 120
            box_w = W_ - 40
            box_h = (H_ + EXT) - logo_h - 50 - box_y   # leave space for logo and title
            c.drawImage(
                self.illus_path, box_x, box_y,
                width=box_w, height=box_h,
                mask='auto', preserveAspectRatio=True, anchor='c',
            )

        # "AI-English Pro" title — bottom-left of hero
        c.setFillColor(SOFT_PURPLE)
        c.setFont("Helvetica-Bold", 42)
        c.drawString(0, 42, "AI-English Pro")


def _cover_page(candidate: dict) -> list:
    e = []

    # Full-bleed lavender hero (logo + illustration + title)
    illus = os.path.join(_HERE, "cover_illustration.png")
    e.append(CoverPanel(illus_path=illus if os.path.exists(illus) else None))
    e.append(Spacer(1, 26))

    COL = 240
    info = [
        [Paragraph("Company",         STYLES["lbl"]), Paragraph("Candidate Name", STYLES["lbl"])],
        [Paragraph(candidate.get("company", "—"),   STYLES["val"]),
         Paragraph(candidate.get("name",    "—"),   STYLES["val"])],
        [Paragraph("Date of Attempt",  STYLES["lbl"]), Paragraph("Candidate ID",  STYLES["lbl"])],
        [Paragraph(candidate.get("appeared_on", "—"), STYLES["val"]),
         Paragraph(str(candidate.get("id", "—")),   STYLES["val"])],
    ]
    t = Table(info, colWidths=[COL, COL])
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        # Extra gap after first value row (separates the two label groups)
        ("BOTTOMPADDING", (0, 1), (-1, 1), 28),
    ]))
    e.append(t)
    e.append(Spacer(1, 60))
    return e


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Score Analysis
# ══════════════════════════════════════════════════════════════════════════════
def _score_analysis_page(reading_scoring: dict, listening_scoring: dict, writing_scoring: dict) -> list:
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

    # Profile chart — DARK_HDR for Listening, PURPLE for Reading, ORANGE for Writing
    chart = CEFRProfileChart(
        skills=[
            ("Listening", int(listening_scoring.get("scale_score", 120)), HEADING),
            ("Reading",   int(reading_scoring.get("scale_score",   120)), HEADING),
            ("Writing",   int(writing_scoring.get("scale_score",   120)), HEADING),
        ],
        width=USABLE - 20,
        height=310,
        skills_order=["Listening", "Reading", "Writing"],
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

    # CEFR level legend badges
    e.append(_cefr_legend())

    return e


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Section Skill Analysis
# ══════════════════════════════════════════════════════════════════════════════
def _skill_section_row(section_num: int, label: str, scoring: dict) -> Table:
    """One skill section row — reused for Reading, Listening, Writing."""
    LEFT_W  = 315
    RIGHT_W = 175
    INNER_L = 290

    scale = scoring["scale_score"]

    # Title line: section label left, Cambridge scale score right-aligned
    title_tbl = Table([[
        Paragraph(
            f'<font color="#6B7280">Section {section_num}: </font>'
            f'<b><font color="#2D2D6B">{label}</font></b>',
            STYLES["skill_lbl"],
        ),
        Paragraph(f'Score : <b>{scale}</b>', STYLES["score_r"]),
    ]], colWidths=[LEFT_W - 130, 120])
    title_tbl.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",(0, 0), (-1, -1), 0),
    ]))

    left_content = [
        title_tbl,
        Spacer(1, 6),
        Table(
            [[CEFRBadge(scoring["cefr_display"], width=82, height=24),
              Paragraph(scoring["proficiency_label"], STYLES["prof"])]],
            colWidths=[90, INNER_L - 90],
            style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ("LEFTPADDING", (0, 0), (-1, -1), 0),
                   ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                   ("TOPPADDING", (0, 0), (-1, -1), 0),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 0)],
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


def _skill_analysis_page(reading_scoring: dict, listening_scoring: dict, writing_scoring: dict) -> list:
    e = []
    e.append(Spacer(1, 10))
    e.append(_section_heading("Section Skill Analysis"))
    e.append(Spacer(1, 6))

    # Column headers
    LEFT_W, RIGHT_W = 315, 175
    hdr = Table(
        [[Paragraph("Capabilities and Skills", STYLES["col_head"]),
          Paragraph("Understanding the skills", STYLES["col_head_r"])]],
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
    e.append(Spacer(1, 12))

    e.append(HRFlowable(width="100%", thickness=0.3, color=RULE, spaceAfter=8))

    # Section 3 — Writing
    e.append(_skill_section_row(3, "Writing", writing_scoring))

    e.append(Spacer(1, 16))
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
    return e


# ══════════════════════════════════════════════════════════════════════════════
# Speaking-only pages
# ══════════════════════════════════════════════════════════════════════════════
def _speaking_score_analysis_page(speaking_scoring: dict) -> list:
    e = []
    e.append(Spacer(1, 10))
    e.append(_section_heading("Score Analysis"))
    e.append(Spacer(1, 8))

    title_row = Table([[
        Paragraph("<b>CEFR Assessment Profile</b>", STYLES["col_head"]),
        Paragraph("Cambridge English Scale &middot; Speaking breakdown", STYLES["blurb"]),
    ]], colWidths=[180, USABLE - 180])
    title_row.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    e.append(title_row)

    chart = CEFRProfileChart(
        skills=[("Speaking", int(speaking_scoring.get("scale_score", 120)), HEADING)],
        width=USABLE - 20,
        height=310,
        skills_order=["Speaking"],
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
    e.append(Paragraph(
        "The Common European Framework of Reference for Languages (CEFR) is a "
        "standardised grading system aiming to validate language ability.",
        STYLES["blurb"],
    ))
    e.append(_cefr_legend())
    return e


def _speaking_skill_analysis_page(speaking_scoring: dict) -> list:
    e = []
    e.append(Spacer(1, 10))
    e.append(_section_heading("Section Skill Analysis"))
    e.append(Spacer(1, 6))

    LEFT_W, RIGHT_W = 315, 175
    hdr = Table(
        [[Paragraph("Capabilities and Skills", STYLES["col_head"]),
          Paragraph("Understanding the skills", STYLES["col_head_r"])]],
        colWidths=[LEFT_W, RIGHT_W],
    )
    hdr.setStyle(TableStyle([
        ("LINEBELOW",     (0, 0), (-1, -1), 0.5, RULE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    e.append(hdr)
    e.append(Spacer(1, 8))
    e.append(_skill_section_row(1, "Speaking", speaking_scoring))
    e.append(Spacer(1, 16))
    return e


# ══════════════════════════════════════════════════════════════════════════════
# Public entry points
# ══════════════════════════════════════════════════════════════════════════════
def generate_speaking_report(candidate: dict, speaking_scoring: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=40, rightMargin=40,
        topMargin=30,  bottomMargin=30,
    )
    story = []
    story.extend(_cover_page(candidate))
    story.append(PageBreak())
    story.extend(_speaking_score_analysis_page(speaking_scoring))
    story.append(PageBreak())
    story.extend(_speaking_skill_analysis_page(speaking_scoring))
    story.append(PageBreak())
    story.extend(_test_log_page(candidate))
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


def generate_reading_report(candidate: dict, reading_scoring: dict, listening_scoring: dict, writing_scoring: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=40, rightMargin=40,
        topMargin=30,  bottomMargin=30,
    )

    story = []
    story.extend(_cover_page(candidate))
    story.append(PageBreak())
    story.extend(_score_analysis_page(reading_scoring, listening_scoring, writing_scoring))
    story.append(PageBreak())
    story.extend(_skill_analysis_page(reading_scoring, listening_scoring, writing_scoring))
    story.append(PageBreak())
    story.extend(_test_log_page(candidate))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()
