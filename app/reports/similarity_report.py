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


def generate_dna_similarity_report(
    sim_data: Dict[str, Any],
    user_name: str,
    output_path: Path
):
    """
    Generate Report 2: DNA Similarity Analysis Report.
    Displays BOTH actual reference and query sequences + alignment metrics.
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
    ref_name = sim_data.get("reference_name", "Reference Sequence")
    qry_name = sim_data.get("query_name", "Query Sequence")

    story.extend(build_report_header_bar(
        title="DNA Sequence Similarity & Alignment Report",
        module_label="Module 02 &bull; Pairwise Global Alignment",
        analysis_id=sim_data.get("id"),
        sequence_name=f"{ref_name} vs {qry_name}",
        user_name=user_name
    ))

    # 2. Alignment Statistics Table
    story.append(Paragraph("1. Needleman-Wunsch Alignment & Similarity Metrics", styles['SectionHeading']))
    tbl_data = [
        [Paragraph("Alignment Parameter", styles['TableHead']), Paragraph("Calculated Result", styles['TableHead']),
         Paragraph("Alignment Parameter", styles['TableHead']), Paragraph("Calculated Result", styles['TableHead'])],
        [Paragraph("Similarity Index", styles['TableCellBold']), Paragraph(f"<b>{sim_data.get('similarity_percentage', 0)}%</b>", styles['TableCell']),
         Paragraph("Difference Index", styles['TableCellBold']), Paragraph(f"<b>{sim_data.get('difference_percentage', 0)}%</b>", styles['TableCell'])],
        [Paragraph("Exact Base Matches", styles['TableCellBold']), Paragraph(f"{sim_data.get('match_count', 0)} bp", styles['TableCell']),
         Paragraph("Mismatches & Gaps", styles['TableCellBold']), Paragraph(f"Mismatches: {sim_data.get('mismatch_count', 0)}, Gaps: {sim_data.get('gap_count', 0)}", styles['TableCell'])],
        [Paragraph("Alignment Score", styles['TableCellBold']), Paragraph(f"{sim_data.get('alignment_score', 0):.1f}", styles['TableCell']),
         Paragraph("Query / Ref Length", styles['TableCellBold']), Paragraph(f"{sim_data.get('query_length', 0)} bp / {sim_data.get('reference_length', 0)} bp", styles['TableCell'])],
    ]

    t = Table(tbl_data, colWidths=[1.8 * 72, 1.7 * 72, 1.8 * 72, 1.7 * 72])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_SLATE_LIGHT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # 3. ACTUAL REFERENCE Sequence
    ref_seq = sim_data.get("reference_sequence") or ""
    story.extend(format_dna_sequence_flowables(
        sequence=ref_seq,
        heading_title=f"2. Actual Reference DNA Sequence ({ref_name})",
        chars_per_line=50
    ))

    # 4. ACTUAL QUERY Sequence
    qry_seq = sim_data.get("query_sequence") or ""
    story.extend(format_dna_sequence_flowables(
        sequence=qry_seq,
        heading_title=f"3. Actual Query DNA Sequence ({qry_name})",
        chars_per_line=50
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
