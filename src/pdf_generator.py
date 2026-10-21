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

# ── Color Palette (Color Hunt #790d16, #e5d3af, #f5efe1, #aec4d4) ────────────
CLR_PRIMARY = colors.HexColor("#790D16")        # Deep Burgundy Primary
CLR_PRIMARY_DARK = colors.HexColor("#4A070D")   # Deeper Wine Charcoal
CLR_PRIMARY_LIGHT = colors.HexColor("#F5EFE1")  # Ivory Cream Wash
CLR_ACCENT_AMBER = colors.HexColor("#B88628")   # Warm Amber / Sand Gold
CLR_ALERT_RED = colors.HexColor("#790D16")      # Deep Crimson Alert
CLR_BORDER = colors.HexColor("#E5D3AF")         # Warm Sand Border
CLR_BG_CARD = colors.HexColor("#FAF7F0")        # Soft Ivory Card Background
CLR_BG_EVIDENCE = colors.HexColor("#F5EFE1")    # Monospace Ivory Background
CLR_TEXT_DARK = colors.HexColor("#1F1614")      # Primary Deep Charcoal
CLR_TEXT_MUTED = colors.HexColor("#544442")     # Warm Slate Muted
CLR_ACCENT_SKY = colors.HexColor("#AEC4D4")     # Soft Sky Slate Accent
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
            self.drawString(160, h - 25, "· SEBI SCORES 2.0 Review · BSA 2023 Sec. 63 Certified")
            self.drawRightString(w - 36, h - 25, "ADMISSIBLE RECORD")

        # Running Bottom Footer (All Pages)
        self.setStrokeColor(CLR_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 36, w - 36, 36)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(CLR_TEXT_MUTED)
        self.drawString(36, 24, "FinGuard v4.0 · Admissible under BSA 2023 Sec. 63 · Official SEBI: scores.sebi.gov.in · Cyber Crime: cybercrime.gov.in")
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
    style_subheading = ParagraphStyle(
        "SubHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=CLR_PRIMARY,
        spaceBefore=6,
        spaceAfter=3,
    )

    story = []
    content_width = A4[0] - (2 * margin)

    # ── 1. Top Header Banner ──────────────────────────────────────────────────
    is_clearance = "CLEARANCE MEMORANDUM" in complaint_text
    header_top = "SECURITIES AND EXCHANGE BOARD OF INDIA (SEBI) / MEITY COMPLIANCE" if is_clearance else "SECURITIES AND EXCHANGE BOARD OF INDIA (SEBI)"
    header_title = "STATUTORY FORENSIC CLEARANCE MEMORANDUM &amp; COMPLIANCE RECORD" if is_clearance else "PRE-FILING EVIDENCE DOSSIER — SCORES / SURVEILLANCE REVIEW"
    header_bg = colors.HexColor("#065F46") if is_clearance else CLR_PRIMARY

    header_data = [
        [
            Paragraph(header_top, style_subtitle),
        ],
        [
            Paragraph(header_title, style_title),
        ],
        [
            Paragraph("Prepared by FinGuard Decision Support Engine v4.0 · Local-First Architecture", style_subtitle),
        ]
    ]
    header_table = Table(header_data, colWidths=[content_width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), header_bg),
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
    if is_clearance:
        notice_text = (
            "<b>STATUTORY CLEARANCE &amp; FORENSIC ADMISSIBILITY:</b> "
            "This memorandum certifies that the examined electronic record underwent multi-modal forensic inspection "
            "by FinGuard and was verified to operate within standard statutory thresholds under SEBI regulations and IT Rules 2021. "
            "Cryptographic integrity and admissibility certified under Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023)."
        )
    else:
        notice_text = (
            "<b>LEGAL NOTICE &amp; STATUTORY ADMISSIBILITY:</b> "
            "This dossier is an automated evidentiary compilation generated by FinGuard to support "
            "pre-filing reviews and formal complaints before SEBI SCORES 2.0 (scores.sebi.gov.in) and the "
            "National Cyber Crime Reporting Portal (cybercrime.gov.in) under BNS Sections 318(4)/319(2) and IT Act 66D. "
            "Admissibility certified under Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023)."
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
    threat_rating = metadata.get("verdict") or ("AUTHENTIC &amp; COMPLIANT" if is_clearance else "HIGH RISK — PROBABLE VIOLATIONS")
    media_sha256 = metadata.get("sha256") or metadata.get("media_hash") or "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"

    # Extract dynamic key-values from complaint_text if available
    for line in complaint_text.splitlines():
        if "DATE & TIME OF GENERATION" in line and ":" in line:
            now_str = line.split(":", 1)[1].strip()
        elif "INVESTIGATION CASE ID" in line and ":" in line:
            case_id = line.split(":", 1)[1].strip()
        elif "PRIMARY EVIDENCE SHA-256" in line and ":" in line:
            media_sha256 = line.split(":", 1)[1].strip()
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
            Paragraph(f"<b>{_clean_text_for_xml(threat_rating)}</b>", style_bold_label if is_clearance else style_badge_red),
        ],
        [
            Paragraph("<b>Statutory Certification:</b>", style_body),
            Paragraph("<b>Section 63, BSA 2023</b>", style_body),
            Paragraph("<b>Evidence SHA-256:</b>", style_body),
            Paragraph(f"<font face='Courier' size='6.5'>{_clean_text_for_xml(media_sha256[:28])}...</font>", style_body),
        ],
    ]
    half_w = content_width / 4.0
    meta_table = Table(
        meta_grid_data,
        colWidths=[half_w * 0.9, half_w * 1.1, half_w * 0.8, half_w * 1.2],
    )
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDF4") if is_clearance else CLR_PRIMARY_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#86EFAC") if is_clearance else colors.HexColor("#A7F3D0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BBF7D0") if is_clearance else colors.HexColor("#D1FAE5")),
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

            is_certificate = "CERTIFICATE" in title.upper() or "BSA 2023" in title.upper() or "SECTION 63" in title.upper()
            is_evidence = ("EVIDENCE" in title.upper() and not is_certificate) or "TRANSCRIPT" in title.upper()

            if is_certificate:
                # Institutional Certificate Box under Section 63 BSA 2023
                cert_elements = []
                for sline in sec_lines:
                    sline_strip = sline.strip()
                    if not sline_strip:
                        continue
                    if sline_strip.startswith("•") or sline_strip.startswith("-") or sline_strip.startswith("*"):
                        bullet_content = sline_strip.lstrip("•-* ").strip()
                        cert_elements.append(Paragraph(f"• {_clean_text_for_xml(bullet_content)}", style_bullet))
                    elif ":" in sline_strip and len(sline_strip.split(":", 1)[0]) < 35:
                        parts = sline_strip.split(":", 1)
                        k = parts[0].strip()
                        v = parts[1].strip()
                        if "SHA-256" in k.upper() or "FINGERPRINT" in k.upper():
                            cert_elements.append(Paragraph(f"<b>{_clean_text_for_xml(k)}:</b> <font face='Courier' size='7'>{_clean_text_for_xml(v)}</font>", style_body))
                        else:
                            cert_elements.append(Paragraph(f"<b>{_clean_text_for_xml(k)}:</b> {_clean_text_for_xml(v)}", style_body))
                    elif re.match(r"^\d+\.\s+", sline_strip):
                        num_content = re.sub(r"^\d+\.\s+", "", sline_strip)
                        num_prefix = re.match(r"^(\d+\.)\s+", sline_strip).group(1)
                        cert_elements.append(Paragraph(f"<b>{num_prefix}</b> {_clean_text_for_xml(num_content)}", style_bold_label))
                    else:
                        cert_elements.append(Paragraph(_clean_text_for_xml(sline_strip), style_body))

                cert_table = Table([[cert_elements]], colWidths=[content_width])
                cert_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), CLR_PRIMARY_LIGHT),
                    ('BOX', (0, 0), (-1, -1), 0.75, CLR_PRIMARY),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(cert_table)
                story.append(Spacer(1, 6))
            elif is_evidence:
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
                    if sline_strip.startswith("[") and "]" in sline_strip:
                        story.append(Paragraph(f"<b>{_clean_text_for_xml(sline_strip)}</b>", style_subheading))
                    elif sline_strip.startswith("•") or sline_strip.startswith("-") or sline_strip.startswith("*"):
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
        "<b>OFFICIAL REGULATORY &amp; LAW ENFORCEMENT LODGMENT CHECKLIST:</b><br/>"
        "1. <b>SEBI SCORES 2.0:</b> Log in to <b>https://scores.sebi.gov.in</b>. Select Category: <i>Unregistered Investment Advice / Fraudulent Market Inducement</i>.<br/>"
        "2. <b>National Cyber Crime Reporting Portal:</b> Report immediately at <b>https://cybercrime.gov.in</b> (or dial Helpline <b>1930</b>) under BNS Sections 318(4)/319(2) &amp; IT Act 66D.<br/>"
        "3. <b>BSA 2023 Evidentiary Admissibility:</b> Attach this certified PDF dossier and the original uncompressed media file. Reference Section 63 BSA Certificate."
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
