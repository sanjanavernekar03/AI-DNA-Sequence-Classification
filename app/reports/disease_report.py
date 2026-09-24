from pathlib import Path
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from app.reports.report_styles import (
    get_biotech_report_styles, NAVY_PRIMARY, TEAL_SECONDARY,
    BORDER_LIGHT, BG_SLATE_LIGHT, WHITE
)
from app.reports.report_components import (
    NumberedCanvas, build_report_header_bar, format_dna_sequence_flowables,
    build_medical_disclaimer_box, generate_disease_probabilities_chart
)


def generate_dna_disease_report(
    dis_data: Dict[str, Any],
    user_name: str,
    output_path: Path
):
    """
    Generate Report 5: AI-Based DNA Disease Prediction Report.
    Includes actual sequence, 5-class probability spectrum, and performance metrics.
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=46
    )

    styles = get_biotech_report_styles()
    story = []

    # 1. Header Bar
    story.extend(build_report_header_bar(
        title="AI-Based DNA Disease Prediction Report",
        module_label="Module 05 &bull; 5-Class Random Forest Disease Risk Predictor",
        analysis_id=dis_data.get("id"),
        sequence_name=dis_data.get("sequence_name", "DNA Specimen"),
        user_name=user_name
    ))

    # 2. Prediction Assessment Table
    story.append(Paragraph("1. Disease Prediction & Pathogenic Assessment", styles['SectionHeading']))
    pred_cat = dis_data.get('predicted_category', 'Unknown Category')
    prob_val = dis_data.get('probability', 0.0)
    risk_tier = dis_data.get('risk_category', 'Moderate')

    pred_table_data = [
        [Paragraph("Prediction Parameter", styles['TableHead']), Paragraph("Assessment Output", styles['TableHead']),
         Paragraph("Prediction Parameter", styles['TableHead']), Paragraph("Assessment Output", styles['TableHead'])],
        [Paragraph("Predicted Disease Category", styles['TableCellBold']), Paragraph(f"<font color='#DC2626' size='9.5'><b>{pred_cat}</b></font>", styles['TableCell']),
         Paragraph("Model Probability", styles['TableCellBold']), Paragraph(f"<b>{prob_val:.2f}%</b>", styles['TableCell'])],
        [Paragraph("Risk Stratification Tier", styles['TableCellBold']), Paragraph(f"<b>{risk_tier} Risk</b>", styles['TableCell']),
         Paragraph("ML Algorithm", styles['TableCellBold']), Paragraph("RandomForestClassifier", styles['TableCell'])],
        [Paragraph("Target Classes", styles['TableCellBold']), Paragraph("5 (Healthy, Cancer, Sickle Cell, CF, Huntington's)", styles['TableCell']),
         Paragraph("Dataset Source", styles['TableCellBold']), Paragraph("NCBI Curated Multi-Class Dataset", styles['TableCell'])],
    ]

    pt = Table(pred_table_data, colWidths=[1.8 * 72, 1.7 * 72, 1.8 * 72, 1.7 * 72])
    pt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_SLATE_LIGHT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(pt)
    story.append(Spacer(1, 10))

    # 3. 5-Class Probability Spectrum Chart
    probs = dis_data.get("probabilities") or {
        "Healthy": 0.0, "Cancer": 0.0, "Sickle Cell Disease": 0.0,
        "Cystic Fibrosis": 0.0, "Huntington's Disease": 0.0
    }
    story.append(Paragraph("2. 5-Class Probability Spectrum", styles['SectionHeading']))
    chart_buf = generate_disease_probabilities_chart(probs)
    story.append(Image(chart_buf, width=6.8 * 72, height=2.0 * 72))
    story.append(Spacer(1, 10))

    # 4. Mandatory Medical Disclaimer Box
    story.append(Paragraph("3. Academic & Clinical Evaluation Notice", styles['SectionHeading']))
    story.append(build_medical_disclaimer_box())
    story.append(Spacer(1, 12))

    # 5. ACTUAL DNA Sequence Analyzed
    actual_seq = dis_data.get("sequence") or dis_data.get("cleaned_sequence") or ""
    story.extend(format_dna_sequence_flowables(
        sequence=actual_seq,
        heading_title="4. Actual DNA Sequence Analyzed",
        chars_per_line=50
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
