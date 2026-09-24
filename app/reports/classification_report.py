from pathlib import Path
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.reports.report_styles import (
    get_biotech_report_styles, NAVY_PRIMARY, TEAL_SECONDARY,
    BORDER_LIGHT, BG_SLATE_LIGHT, WHITE
)
from app.reports.report_components import (
    NumberedCanvas, build_report_header_bar, format_dna_sequence_flowables
)


def generate_dna_classification_report(
    clf_data: Dict[str, Any],
    user_name: str,
    output_path: Path
):
    """
    Generate Report 4: AI-Based DNA Classification Report.
    Includes actual sequence, predicted functional region, and confidence metrics.
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
        title="AI-Based DNA Functional Classification Report",
        module_label="Module 04 &bull; Supervised Genomic Region Classification",
        analysis_id=clf_data.get("id"),
        sequence_name=clf_data.get("sequence_name", "DNA Specimen"),
        user_name=user_name
    ))

    # 2. Classification Result Summary Table
    story.append(Paragraph("1. Machine Learning Classification Outcome", styles['SectionHeading']))
    pred_cls = clf_data.get('predicted_class', 'Unknown Class')
    conf_val = clf_data.get('confidence', 0.0)

    clf_table_data = [
        [Paragraph("Classification Parameter", styles['TableHead']), Paragraph("Inference Result", styles['TableHead'])],
        [Paragraph("Predicted Functional Class", styles['TableCellBold']), Paragraph(f"<font color='#0D9488' size='10'><b>{pred_cls}</b></font>", styles['TableCell'])],
        [Paragraph("Model Prediction Confidence", styles['TableCellBold']), Paragraph(f"<b>{conf_val:.2f}%</b>", styles['TableCell'])],
        [Paragraph("Machine Learning Algorithm", styles['TableCellBold']), Paragraph(str(clf_data.get('model_name', 'RandomForestClassifier (Ensemble)')), styles['TableCell'])],
        [Paragraph("Model Architecture & Input", styles['TableCellBold']), Paragraph("64 Trinucleotide k-mer Frequency Vectors + Compositional Features", styles['TableCell'])],
        [Paragraph("Model Version", styles['TableCellBold']), Paragraph("Version 1.0 (Supervised Random Forest)", styles['TableCell'])],
    ]

    ct = Table(clf_table_data, colWidths=[2.6 * 72, 4.4 * 72])
    ct.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_SLATE_LIGHT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(ct)
    story.append(Spacer(1, 12))

    # 3. ACTUAL DNA Sequence Analyzed
    actual_seq = clf_data.get("sequence") or clf_data.get("cleaned_sequence") or ""
    story.extend(format_dna_sequence_flowables(
        sequence=actual_seq,
        heading_title="2. Actual DNA Sequence Classified",
        chars_per_line=50
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
