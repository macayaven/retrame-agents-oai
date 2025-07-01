"""PDF tool for the agents."""

from datetime import UTC, datetime
from io import BytesIO
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf_bytes(intake_data: dict, analysis_output: str) -> bytes:
    """Return the generated PDF as raw bytes without interacting with ADK context.

    This is a pure helper so other agents can create the same PDF deterministically
    without calling the LongRunningFunctionTool wrapper.
    """

    # -----------------  BEGIN: copy of original PDF building logic  -----------------
    # Parse analysis JSON if it contains JSON
    analysis_data = {}
    if "```json" in analysis_output:
        try:
            json_start = analysis_output.find("```json") + 7
            json_end = analysis_output.find("```", json_start)
            json_str = analysis_output[json_start:json_end].strip()
            analysis_data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=30,
    )
    story.append(Paragraph("CBT Micro-Session Report", title_style))
    story.append(Spacer(1, 0.2 * inch))

    # Date
    story.append(
        Paragraph(f"<b>Date:</b> {datetime.now(UTC).strftime('%Y-%m-%d')}", styles["Normal"])
    )
    story.append(Spacer(1, 0.3 * inch))

    # Section 1: Situation Snapshot
    story.append(Paragraph("<b>1. Your Situation Snapshot</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))

    situation_data = [
        ["Field", "Your Entry"],
        ["Situation", intake_data.get("trigger_situation", "Not provided")],
        ["Automatic Thought", f'"{intake_data.get("automatic_thought", "Not provided")}"'],
        [
            "Initial Emotion",
            f'{intake_data.get("emotion_data", {}).get("emotion", "Unknown")} ({intake_data.get("emotion_data", {}).get("intensity", 0)}/10)',
        ],
    ]

    situation_table = Table(situation_data, colWidths=[2 * inch, 4 * inch])
    situation_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(situation_table)
    story.append(Spacer(1, 0.3 * inch))

    # Section 2: Analysis (same as in _generate_pdf_report)
    if analysis_data:
        story.append(Paragraph("<b>2. Analysis: Looking at the Evidence</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        distortions = analysis_data.get("distortions", [])
        distortion_map = {
            "MW": "Mind Reading",
            "FT": "Fortune Telling",
            "CT": "Catastrophizing",
            "AO": "All-or-Nothing",
            "MF": "Mental Filter",
            "PR": "Personalization",
            "LB": "Labeling",
            "SH": "Should Statements",
            "ER": "Emotional Reasoning",
            "DP": "Discounting Positive",
        }
        distortion_names = [distortion_map.get(d, d) for d in distortions]
        if distortion_names:
            story.append(
                Paragraph(
                    f"<b>Cognitive Distortions Identified:</b> {', '.join(map(str, distortion_names))}",
                    styles["Normal"],
                )
            )
        else:
            story.append(Paragraph("<b>No Cognitive Distortions Identified:</b>", styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        if analysis_data.get("balanced_thought"):
            story.append(Paragraph("<b>A More Balanced Perspective:</b>", styles["Normal"]))
            story.append(Paragraph(f'<i>{analysis_data["balanced_thought"]}</i>', styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

        if analysis_data.get("micro_action"):
            story.append(Paragraph("<b>Your Micro-Action Plan:</b>", styles["Normal"]))
            story.append(Paragraph(f'<i>{analysis_data["micro_action"]}</i>', styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

        if "certainty_before" in analysis_data and "certainty_after" in analysis_data:
            story.append(
                Paragraph(
                    f"<b>Confidence Shift:</b> {analysis_data['certainty_before']}% → {analysis_data['certainty_after']}%",
                    styles["Normal"],
                )
            )

    story.append(Spacer(1, 0.3 * inch))

    disclaimer_style = ParagraphStyle(
        "Disclaimer", parent=styles["Normal"], fontSize=9, textColor=colors.grey
    )
    story.append(
        Paragraph(
            "This is an educational tool, not a substitute for clinical diagnosis or therapy.",
            disclaimer_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    # -----------------  END  -----------------
    return buffer.read()
