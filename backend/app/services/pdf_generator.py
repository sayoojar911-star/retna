"""Professional Clinical PDF Report Generator for GlaucoMap.

Generates ophthalmic structural analysis and longitudinal monitoring reports
using ReportLab with clean medical typography, structured patient data,
AI model estimates, and disclaimers.
"""

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as PlatypusImage,
    KeepTogether,
    HRFlowable,
)
from PIL import Image as PILImage


def _b64_to_temp_img(b64_str: str, max_size: tuple = (200, 200)) -> Optional[io.BytesIO]:
    """Convert base64 image string to PIL Image BytesIO buffer."""
    try:
        if not b64_str:
            return None
        if "base64," in b64_str:
            b64_str = b64_str.split("base64,")[1]
        raw_data = base64.b64decode(b64_str)
        pil_img = PILImage.open(io.BytesIO(raw_data))
        pil_img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception:
        return None


def generate_clinical_report_pdf(
    patient: Dict[str, Any],
    scan: Optional[Dict[str, Any]] = None,
    ai_analysis: Optional[Dict[str, Any]] = None,
    rnflt_summary: Optional[Dict[str, Any]] = None,
    longitudinal: Optional[Dict[str, Any]] = None,
    iop_history: Optional[List[Dict[str, Any]]] = None,
    vf_history: Optional[List[Dict[str, Any]]] = None,
    progression: Optional[Dict[str, Any]] = None,
    images: Optional[Dict[str, str]] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> bytes:
    """Generate a clean, printable clinical PDF report."""
    scan = scan or {}
    ai_analysis = ai_analysis or {}
    rnflt_summary = rnflt_summary or {}
    images = images or {}
    iop_history = iop_history or []
    vf_history = vf_history or []
    longitudinal = longitudinal or {}
    progression = progression or {}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        str(output_path) if output_path else buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0f766e")  # Teal 700
    dark_text = colors.HexColor("#0f172a")     # Slate 900
    muted_text = colors.HexColor("#475569")    # Slate 600
    border_color = colors.HexColor("#cbd5e1")  # Slate 300
    card_bg = colors.HexColor("#f8fafc")       # Slate 50
    alert_bg = colors.HexColor("#f0fdfa")      # Teal 50

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=muted_text,
        spaceAfter=8,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=dark_text,
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=dark_text,
    )
    meta_label = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=muted_text,
    )
    meta_val = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=dark_text,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=muted_text,
    )

    story = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph("GLAUCOMAP", title_style),
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>Confidential Medical Report",
                ParagraphStyle("HRight", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=10, alignment=2, textColor=muted_text),
            ),
        ],
        [
            Paragraph("Ophthalmic Structural Analysis & Longitudinal Monitoring", subtitle_style),
            "",
        ],
    ]
    t_header = Table(header_data, colWidths=[350, 190])
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("SPAN", (0, 1), (1, 1)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=4, spaceAfter=8))

    # 2. Patient & Scan Information Tables (Side by Side)
    p_name = patient.get("name", "Unknown Patient")
    p_id = patient.get("patient_id") or patient.get("id", "N/A")
    p_age = str(patient.get("age", "N/A"))
    p_sex = patient.get("sex", "N/A")
    p_eye = scan.get("eye") or patient.get("eye_laterality", "OD")
    scan_date = scan.get("date", datetime.now().strftime("%Y-%m-%d"))
    scan_type = scan.get("scan_type", "OCT Structural Scan")
    scan_status = scan.get("status", "Analyzed")

    info_data = [
        [
            Paragraph("PATIENT INFORMATION", section_heading),
            Paragraph("SCAN INFORMATION", section_heading),
        ],
        [
            Table([
                [Paragraph("Patient Name:", meta_label), Paragraph(p_name, meta_val)],
                [Paragraph("Patient ID:", meta_label), Paragraph(p_id, meta_val)],
                [Paragraph("Age / Sex:", meta_label), Paragraph(f"{p_age} yrs / {p_sex}", meta_val)],
                [Paragraph("Evaluated Eye:", meta_label), Paragraph(p_eye, meta_val)],
            ], colWidths=[80, 180]),
            Table([
                [Paragraph("Scan Date:", meta_label), Paragraph(scan_date, meta_val)],
                [Paragraph("Scan Type:", meta_label), Paragraph(scan_type, meta_val)],
                [Paragraph("Input Status:", meta_label), Paragraph(scan_status, meta_val)],
                [Paragraph("Model Architecture:", meta_label), Paragraph("Harvard-GD RNFLT CNN", meta_val)],
            ], colWidths=[100, 160]),
        ],
    ]
    t_info = Table(info_data, colWidths=[265, 275])
    t_info.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 8))

    # 3. AI Analysis & RNFLT Summary
    model_score = ai_analysis.get("model_estimated_classification_score")
    model_score_pct = ai_analysis.get("model_estimated_classification_score_pct")
    if model_score_pct is None and model_score is not None:
        model_score_pct = f"{model_score * 100:.1f}%"
    elif model_score_pct is None:
        model_score_pct = "N/A"

    is_glaucoma = ai_analysis.get("is_glaucoma_risk")
    if is_glaucoma is True:
        classification_text = "Glaucoma-associated pattern detected"
        class_color = colors.HexColor("#b91c1c")  # Red
    elif is_glaucoma is False:
        classification_text = "No glaucoma-associated pattern detected"
        class_color = colors.HexColor("#047857")  # Green
    else:
        classification_text = ai_analysis.get("predicted_category", "Classification Unavailable")
        class_color = dark_text

    mean_rnflt = rnflt_summary.get("mean_thickness_um") or scan.get("mean_rnflt_um")
    mean_str = f"{mean_rnflt:.1f} µm" if mean_rnflt is not None else "N/A"
    median_rnflt = rnflt_summary.get("median_thickness_um")
    med_str = f"{median_rnflt:.1f} µm" if median_rnflt is not None else "N/A"
    min_rnflt = rnflt_summary.get("min_thickness_um")
    min_str = f"{min_rnflt:.1f} µm" if min_rnflt is not None else "N/A"
    max_rnflt = rnflt_summary.get("max_thickness_um")
    max_str = f"{max_rnflt:.1f} µm" if max_rnflt is not None else "N/A"

    ai_card_data = [
        [
            Paragraph("AI MODEL ESTIMATE", section_heading),
            Paragraph("RNFLT SUMMARY (MICROMETERS)", section_heading),
        ],
        [
            Table([
                [
                    Paragraph("Classification:", meta_label),
                    Paragraph(f"<font color='{class_color.hexval()}'><b>{classification_text}</b></font>", body_bold),
                ],
                [
                    Paragraph("Model-Estimated Score:", meta_label),
                    Paragraph(f"<b>{model_score_pct}</b> (Clinical correlation required)", body_style),
                ],
                [
                    Paragraph("Disclaimer:", meta_label),
                    Paragraph("Research model estimate — not an autonomous clinical diagnosis.", disclaimer_style),
                ],
            ], colWidths=[110, 155]),
            Table([
                [Paragraph("Mean RNFLT:", meta_label), Paragraph(mean_str, meta_val)],
                [Paragraph("Median RNFLT:", meta_label), Paragraph(med_str, meta_val)],
                [Paragraph("Min / Max RNFLT:", meta_label), Paragraph(f"{min_str} / {max_str}", meta_val)],
                [Paragraph("Physiological Reference:", meta_label), Paragraph("Normal range: 80 - 110 µm", disclaimer_style)],
            ], colWidths=[110, 150]),
        ],
    ]
    t_ai_card = Table(ai_card_data, colWidths=[270, 270])
    t_ai_card.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (0, 1), card_bg),
        ("BACKGROUND", (1, 1), (1, 1), card_bg),
        ("BOX", (0, 1), (0, 1), 0.5, border_color),
        ("BOX", (1, 1), (1, 1), 0.5, border_color),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 1), (-1, -1), 6),
        ("RIGHTPADDING", (0, 1), (-1, -1), 6),
    ]))
    story.append(t_ai_card)
    story.append(Spacer(1, 8))

    # 4. Structural Visualization & Grad-CAM Explainability (Side by Side Images)
    rnflt_b64 = images.get("rnflt_heatmap") or images.get("original_image")
    gradcam_b64 = images.get("gradcam_overlay") or images.get("heatmap_image")

    img_elements = []
    buf1 = _b64_to_temp_img(rnflt_b64) if rnflt_b64 else None
    buf2 = _b64_to_temp_img(gradcam_b64) if gradcam_b64 else None

    if buf1 and buf2:
        img_table_data = [
            [
                Paragraph("<b>STRUCTURAL THICKNESS MAP</b>", section_heading),
                Paragraph("<b>GRAD-CAM EXPLAINABILITY OVERLAY</b>", section_heading),
            ],
            [
                PlatypusImage(buf1, width=150, height=150),
                PlatypusImage(buf2, width=150, height=150),
            ],
            [
                Paragraph("Quantitative RNFL thickness distribution (µm)", meta_label),
                Paragraph("Highlighted regions influenced model prediction. Clinical correlation required.", disclaimer_style),
            ],
        ]
        t_images = Table(img_table_data, colWidths=[270, 270])
        t_images.setStyle(TableStyle([
            ("ALIGN", (0, 1), (-1, 1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
        ]))
        story.append(KeepTogether(t_images))
        story.append(Spacer(1, 8))
    elif buf1:
        img_table_data = [
            [Paragraph("<b>STRUCTURAL THICKNESS MAP</b>", section_heading)],
            [PlatypusImage(buf1, width=150, height=150)],
            [Paragraph("Quantitative RNFL thickness distribution (µm)", meta_label)],
        ]
        t_img = Table(img_table_data, colWidths=[540])
        story.append(KeepTogether(t_img))
        story.append(Spacer(1, 8))

    # 5. Longitudinal Summary & Historical Records
    story.append(Paragraph("LONGITUDINAL MONITORING & SERIAL PROGRESSION", section_heading))

    # Comparison metrics
    prev_rnflt = longitudinal.get("previous_rnflt_um")
    curr_rnflt = longitudinal.get("current_rnflt_um") or mean_rnflt
    rnflt_diff = longitudinal.get("observed_rnflt_change_um")
    if rnflt_diff is None and prev_rnflt is not None and curr_rnflt is not None:
        rnflt_diff = round(curr_rnflt - prev_rnflt, 1)

    diff_str = f"{rnflt_diff:+.1f} µm" if rnflt_diff is not None else "Baseline (First Scan)"
    rnflt_trend_msg = progression.get("observed_trend_message") or (
        f"Observed structural change: {diff_str}" if rnflt_diff is not None else "Awaiting serial follow-up scans."
    )

    long_data = [
        [
            Paragraph("<b>Serial Scan Comparison:</b>", meta_label),
            Paragraph(f"Previous: {prev_rnflt or 'N/A'} µm &nbsp;&nbsp;|&nbsp;&nbsp; Current: {curr_rnflt or 'N/A'} µm &nbsp;&nbsp;|&nbsp;&nbsp; Observed Change: <b>{diff_str}</b>", body_style),
        ],
        [
            Paragraph("<b>Structural Trend:</b>", meta_label),
            Paragraph(rnflt_trend_msg, body_style),
        ],
        [
            Paragraph("<b>24-Month Forecast:</b>", meta_label),
            Paragraph("24-month forecast unavailable — validated progression model not currently connected.", disclaimer_style),
        ],
        [
            Paragraph("<b>Glaucoma Stage:</b>", meta_label),
            Paragraph("Stage assessment unavailable. The current model provides binary classification estimate.", disclaimer_style),
        ],
    ]

    t_long = Table(long_data, colWidths=[120, 420])
    t_long.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), card_bg),
        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_long)
    story.append(Spacer(1, 6))

    # IOP & Visual Field History snippet
    recent_iop = iop_history[-3:] if iop_history else []
    recent_vf = vf_history[-3:] if vf_history else []

    iop_snippets = [f"{i.get('date')}: {i.get('iop_mmhg')} mmHg ({i.get('eye', 'OD')})" for i in recent_iop]
    vf_snippets = [f"{v.get('date')}: MD {v.get('md_db')} dB ({v.get('eye', 'OD')})" for v in recent_vf]

    iop_vf_data = [
        [
            Paragraph("<b>Recent IOP History:</b>", meta_label),
            Paragraph(" &nbsp;&bull;&nbsp; ".join(iop_snippets) if iop_snippets else "No IOP records available.", body_style),
        ],
        [
            Paragraph("<b>Recent Visual Field:</b>", meta_label),
            Paragraph(" &nbsp;&bull;&nbsp; ".join(vf_snippets) if vf_snippets else "Visual-field history unavailable.", body_style),
        ],
    ]
    t_iop_vf = Table(iop_vf_data, colWidths=[120, 420])
    t_iop_vf.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t_iop_vf)
    story.append(Spacer(1, 10))

    # 6. Clinical Disclaimer Box (Mandatory Regulatory Notice)
    disclaimer_box = [
        [
            Paragraph(
                "<b>MANDATORY CLINICAL & RESEARCH NOTICE:</b><br/>"
                "GlaucoMap is an investigational research and clinical decision-support prototype. "
                "AI-generated research estimate — clinical correlation required. "
                "GlaucoMap does not replace clinical diagnosis or treatment decisions. "
                "Highlighted Grad-CAM regions represent areas that influenced the model prediction and do not independently establish a diagnosis.",
                disclaimer_style,
            )
        ]
    ]
    t_disc = Table(disclaimer_box, colWidths=[540])
    t_disc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),  # Amber 50
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fcd34d")),    # Amber 300
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_disc)

    # Build PDF document
    doc.build(story)

    if output_path:
        with open(output_path, "rb") as f:
            return f.read()
    else:
        buffer.seek(0)
        return buffer.getvalue()
