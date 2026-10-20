"""
FinGuard Institutional PDF Report Generator
Generates publication-quality, court/regulatory-ready PDF dossiers for SEBI SCORES pre-filing.
Uses ReportLab with custom page layouts, institutional typography, and two-pass NumberedCanvas.
"""

import io
import re
import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# ── Color Palette ─────────────────────────────────────────────────────────────
CLR_PRIMARY = colors.HexColor("#0E4D34")      # Institutional Deep Green
CLR_PRIMARY_DARK = colors.HexColor("#093322") # Deeper Emerald
CLR_PRIMARY_LIGHT = colors.HexColor("#EAF5EF")# Soft Green Wash
CLR_ACCENT_AMBER = colors.HexColor("#B45309") # Regulatory Warning Amber
CLR_ALERT_RED = colors.HexColor("#B91C1C")    # Deepfake Alert Red
CLR_BORDER = colors.HexColor("#CBD5E1")       # Neutral Border Slate
CLR_BG_CARD = colors.HexColor("#F8FAFC")      # Slate Card Background
CLR_BG_EVIDENCE = colors.HexColor("#F1F5F9")  # Monospace Quote Background
CLR_TEXT_DARK = colors.HexColor("#0F172A")    # Primary Charcoal
CLR_TEXT_MUTED = colors.HexColor("#475569")   # Muted Slate
CLR_WHITE = colors.HexColor("#FFFFFF")


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that dynamically calculates total page count
    and renders institutional running headers and footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_and_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_and_footer(self, page_count):
        self.saveState()
        w, h = A4

        # Running Top Header (Pages 2+)
        if self._pageNumber > 1:
            self.setStrokeColor(CLR_BORDER)
            self.setLineWidth(0.5)
            self.line(36, h - 30, w - 36, h - 30)
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(CLR_PRIMARY)
            self.drawString(36, h - 25, "FINGUARD FORENSIC DOSSIER")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(CLR_TEXT_MUTED)
            self.drawString(160, h - 25, "· SEBI SCORES Pre-Filing Review · Strictly Confidential")
            self.drawRightString(w - 36, h - 25, "EVIDENTIARY SUBMISSION")

        # Running Bottom Footer (All Pages)
        self.setStrokeColor(CLR_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 36, w - 36, 36)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(CLR_TEXT_MUTED)
        self.drawString(36, 24, "FinGuard Forensic Platform v4.0 · Decision Support System · Verify through official portal: scores.sebi.gov.in")
        self.drawRightString(w - 36, 24, f"Page {self._pageNumber} of {page_count}")

        self.restoreState()


def _clean_text_for_xml(text: str) -> str:
    """Escapes XML entities so reportlab Paragraph can safely parse strings."""
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text


def generate_complaint_pdf(
    complaint_text: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Parses a SEBI SCORES complaint draft and creates an institutional PDF document.
    Returns the binary content (bytes) of the PDF.
    """
    metadata = metadata or {}
    pdf_buffer = io.BytesIO()

    margin = 36 # 0.5 in
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=36,
        bottomMargin=46,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=CLR_WHITE,
        alignment=1, # Center
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#D1FAE5"),
        alignment=1, # Center
    )
    style_notice = ParagraphStyle(
        "DocNotice",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=11,
        textColor=CLR_TEXT_MUTED,
    )
    style_section_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=CLR_PRIMARY,
        spaceBefore=8,
        spaceAfter=4,
    )
    style_body = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=CLR_TEXT_DARK,
    )
    style_bold_label = ParagraphStyle(
        "BoldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11.5,
        textColor=CLR_TEXT_DARK,
    )
    style_bullet = ParagraphStyle(
        "BulletItem",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=CLR_TEXT_DARK,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2,
    )
    style_mono = ParagraphStyle(
        "MonoQuote",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#1E293B"),
    )
    style_badge_red = ParagraphStyle(
        "BadgeRed",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=CLR_ALERT_RED,
    )

    story = []
    content_width = A4[0] - (2 * margin)

    # ── 1. Top Header Banner ──────────────────────────────────────────────────
    header_data = [
        [
            Paragraph("SECURITIES AND EXCHANGE BOARD OF INDIA (SEBI)", style_subtitle),
        ],
        [
            Paragraph("PRE-FILING EVIDENCE DOSSIER — SCORES / SURVEILLANCE REVIEW", style_title),
        ],
        [
            Paragraph("Prepared by FinGuard Decision Support Engine v4.0 · Local-First Architecture", style_subtitle),
        ]
    ]
    header_table = Table(header_data, colWidths=[content_width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CLR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # ── 2. Regulatory Notice & Disclaimer Callout ─────────────────────────────
    notice_text = (
        "<b>LEGAL NOTICE &amp; COMPLIANCE DISCLAIMER:</b> "
        "This document is an automated evidentiary compilation generated by FinGuard to support "
        "pre-filing reviews by compliance officers, legal counsel, and retail victims. It provides structured "
        "indicators and evidence citations for official lodgment via SEBI SCORES 2.0 (scores.sebi.gov.in) "
        "or the National Cyber Crime Reporting Portal (cybercrime.gov.in). It does not constitute a judicial ruling."
    )
    notice_table = Table([[Paragraph(notice_text, style_notice)]], colWidths=[content_width])
    notice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CLR_BG_CARD),
        ('BOX', (0, 0), (-1, -1), 0.75, CLR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(notice_table)
    story.append(Spacer(1, 8))

    # ── 3. Parse Metadata & Summary Fields ────────────────────────────────────
    now_str = datetime.datetime.now().strftime("%d-%B-%Y %H:%M:%S IST")
    case_id = metadata.get("job_id") or f"FG-SCORES-{datetime.datetime.now().strftime('%Y%m%d')}-AUDIT"
    mode_str = (metadata.get("mode") or "Multi-Modal Scan").upper()
    threat_rating = metadata.get("verdict") or "HIGH RISK — PROBABLE VIOLATIONS"

    # Extract dynamic key-values from complaint_text if available
    for line in complaint_text.splitlines():
        if "DATE & TIME OF GENERATION" in line and ":" in line:
            now_str = line.split(":", 1)[1].strip()
        elif "INVESTIGATION CASE ID" in line and ":" in line:
            case_id = line.split(":", 1)[1].strip()
        elif "RISK ASSESSMENT RATING" in line and ":" in line:
            threat_rating = line.split(":", 1)[1].strip()

    meta_grid_data = [
        [
            Paragraph("<b>Investigation Case ID:</b>", style_body),
            Paragraph(_clean_text_for_xml(case_id), style_bold_label),
            Paragraph("<b>Date &amp; Time:</b>", style_body),
            Paragraph(_clean_text_for_xml(now_str), style_body),
        ],
        [
            Paragraph("<b>Inspection Mode:</b>", style_body),
            Paragraph(_clean_text_for_xml(mode_str), style_bold_label),
            Paragraph("<b>Threat Assessment:</b>", style_body),
            Paragraph(f"<b>{_clean_text_for_xml(threat_rating)}</b>", style_badge_red),
        ],
    ]
    half_w = content_width / 4.0
    meta_table = Table(
        meta_grid_data,
        colWidths=[half_w * 0.9, half_w * 1.1, half_w * 0.8, half_w * 1.2],
    )
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CLR_PRIMARY_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#A7F3D0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1FAE5")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ── 4. Parse Sections from Complaint Text ─────────────────────────────────
    # Split text by standard dashed or numbered section dividers
    raw_lines = complaint_text.splitlines()
    in_section = False
    current_section_title = ""
    current_section_lines = []

    sections = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i].strip()
        # Look for section headings like "1. RESPONDENT / SUSPECT DETAILS"
        match = re.match(r"^(\d\.\s+[A-Z0-9\s/&—\(\)\-]+)$", line)
        if match:
            if current_section_title or current_section_lines:
                sections.append((current_section_title, current_section_lines))
            current_section_title = match.group(1).strip()
            current_section_lines = []
            i += 1
            # Skip subsequent dashed lines like "--------"
            while i < len(raw_lines) and raw_lines[i].strip().startswith("-"):
                i += 1
            continue
        elif not current_section_title and line.startswith("1. RESPONDENT"):
            current_section_title = line
            current_section_lines = []
            i += 1
            continue

        if current_section_title:
            # Check if line is a divider
            if not line.startswith("----") and not line.startswith("===="):
                current_section_lines.append(raw_lines[i])
        i += 1

    if current_section_title or current_section_lines:
        sections.append((current_section_title, current_section_lines))

    # If parsing found sections, format them nicely
    if sections:
        for title, sec_lines in sections:
            story.append(HRFlowable(width="100%", thickness=0.75, color=CLR_PRIMARY, spaceBefore=4, spaceAfter=4))
            story.append(Paragraph(_clean_text_for_xml(title), style_section_h1))

            # Detect whether this is evidence transcript section (monospaced)
            is_evidence = "EVIDENCE" in title.upper() or "TRANSCRIPT" in title.upper()

            if is_evidence:
                # Group text into a shaded box
                quote_text = "\n".join(sec_lines).strip()
                if quote_text:
                    clean_quotes = _clean_text_for_xml(quote_text).replace("\n", "<br/>&nbsp;&nbsp;")
                    quote_p = Paragraph(f"&nbsp;&nbsp;{clean_quotes}", style_mono)
                    quote_box = Table([[quote_p]], colWidths=[content_width])
                    quote_box.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), CLR_BG_EVIDENCE),
                        ('BOX', (0, 0), (-1, -1), 0.5, CLR_BORDER),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ]))
                    story.append(quote_box)
                    story.append(Spacer(1, 6))
            else:
                for sline in sec_lines:
                    sline_strip = sline.strip()
                    if not sline_strip:
                        continue
                    if sline_strip.startswith("•") or sline_strip.startswith("-") or sline_strip.startswith("*"):
                        bullet_content = sline_strip.lstrip("•-* ").strip()
                        story.append(Paragraph(f"• {_clean_text_for_xml(bullet_content)}", style_bullet))
                    elif ":" in sline_strip and len(sline_strip.split(":", 1)[0]) < 35:
                        parts = sline_strip.split(":", 1)
                        k = parts[0].strip()
                        v = parts[1].strip()
                        story.append(Paragraph(f"<b>{_clean_text_for_xml(k)}:</b> {_clean_text_for_xml(v)}", style_body))
                    elif re.match(r"^\d+\.\s+", sline_strip):
                        num_content = re.sub(r"^\d+\.\s+", "", sline_strip)
                        num_prefix = re.match(r"^(\d+\.)\s+", sline_strip).group(1)
                        story.append(Paragraph(f"<b>{num_prefix}</b> {_clean_text_for_xml(num_content)}", style_bullet))
                    else:
                        story.append(Paragraph(_clean_text_for_xml(sline_strip), style_body))

            story.append(Spacer(1, 4))
    else:
        # Fallback if structure was arbitrary: Render clean paragraphs
        for line in raw_lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("====") or line_str.startswith("----"):
                continue
            story.append(Paragraph(_clean_text_for_xml(line_str), style_body))

    # ── 5. Official Verification Stamp & Signature Callout ───────────────────
    story.append(Spacer(1, 8))
    stamp_text = (
        "<b>OFFICIAL REGULATORY SUBMISSION CHECKLIST:</b><br/>"
        "1. Log in to SEBI SCORES portal at <b>https://scores.sebi.gov.in</b> using PAN or Investor registration.<br/>"
        "2. Select Complaint Category: <i>Unregistered Investment Advisory / Fraudulent Media &amp; Deceptive Claims</i>.<br/>"
        "3. Attach this PDF dossier and original multimedia recordings as corroborative forensic evidence.<br/>"
        "4. File simultaneous cyber reporting at <b>https://cybercrime.gov.in</b> for unauthorized fund funnels."
    )
    stamp_table = Table([[Paragraph(stamp_text, style_notice)]], colWidths=[content_width])
    stamp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")), # Soft amber
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#F59E0B")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(stamp_table)

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    return pdf_bytes
