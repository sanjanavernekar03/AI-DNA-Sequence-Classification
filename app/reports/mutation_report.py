from pathlib import Path
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.reports.report_styles import (
    get_biotech_report_styles, NAVY_PRIMARY, TEAL_SECONDARY,
    BORDER_LIGHT, BG_SLATE_LIGHT, WHITE
)
from app.reports.report_components import (
    NumberedCanvas, build_report_header_bar, format_dna_sequence_flowables
)


def generate_dna_mutation_report(
    mut_data: Dict[str, Any],
    mutations_list: List[Dict[str, Any]],
    user_name: str,
    output_path: Path
):
    """
    Generate Report 3: Mutation Detection & Analysis Report.
    Includes actual sequence, mutation summary metrics, and coordinate catalog.
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
        title="DNA Mutation Detection & Coordinate Mapping Report",
        module_label="Module 03 &bull; SNV & Indel Variant Calling",
        analysis_id=mut_data.get("id"),
        sequence_name=mut_data.get("sample_name", "Clinical DNA Sample"),
        user_name=user_name
    ))

    # 2. Mutation Summary Table
    story.append(Paragraph("1. Mutation & Variant Overview", styles['SectionHeading']))
    summary_rows = [
        [Paragraph("Metric", styles['TableHead']), Paragraph("Value", styles['TableHead']),
         Paragraph("Metric", styles['TableHead']), Paragraph("Value", styles['TableHead'])],
        [Paragraph("Total Mutations Detected", styles['TableCellBold']), Paragraph(f"<b>{mut_data.get('total_mutations', len(mutations_list))}</b>", styles['TableCell']),
         Paragraph("Overall Mutation Rate", styles['TableCellBold']), Paragraph(f"<b>{mut_data.get('mutation_rate', 0)}%</b>", styles['TableCell'])],
        [Paragraph("Point Substitutions (SNVs)", styles['TableCellBold']), Paragraph(str(mut_data.get('substitutions_count', 0)), styles['TableCell']),
         Paragraph("Insertions / Deletions", styles['TableCellBold']), Paragraph(f"+{mut_data.get('insertions_count', 0)} / -{mut_data.get('deletions_count', 0)}", styles['TableCell'])],
    ]

    st = Table(summary_rows, colWidths=[1.8 * 72, 1.7 * 72, 1.8 * 72, 1.7 * 72])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_SLATE_LIGHT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(st)
    story.append(Spacer(1, 10))

    # 3. Mutation Coordinate Catalog Table
    story.append(Paragraph("2. Detailed Mutation Coordinate Catalog", styles['SectionHeading']))
    cat_rows = [
        [Paragraph("Pos (bp)", styles['TableHead']), Paragraph("Mutation Type", styles['TableHead']),
         Paragraph("Ref", styles['TableHead']), Paragraph("Obs", styles['TableHead']),
         Paragraph("Biological Consequence / Coordinate Note", styles['TableHead'])]
    ]

    if mutations_list:
        for m in mutations_list[:40]: # up to 40 mutations in detailed catalog
            pos = m.get("position", "-")
            m_type = m.get("mutation_type") or m.get("type", "-")
            ref_b = m.get("reference_base") or m.get("ref_base", "-")
            obs_b = m.get("observed_base") or m.get("obs_base", "-")
            note = m.get("consequence_note") or m.get("note", "Point variant detected")
            cat_rows.append([
                Paragraph(str(pos), styles['TableCellMono']),
                Paragraph(m_type, styles['TableCellBold']),
                Paragraph(f"<font color='#0D9488'><b>{ref_b}</b></font>", styles['TableCellMono']),
                Paragraph(f"<font color='#DC2626'><b>{obs_b}</b></font>", styles['TableCellMono']),
                Paragraph(note, styles['TableCell'])
            ])
    else:
        cat_rows.append([
            Paragraph("-", styles['TableCell']),
            Paragraph("No Mutations Detected", styles['TableCellBold']),
            Paragraph("-", styles['TableCell']),
            Paragraph("-", styles['TableCell']),
            Paragraph("Sequence is 100% homologous to reference sequence.", styles['TableCell'])
        ])

    ct = Table(cat_rows, colWidths=[0.8 * 72, 1.3 * 72, 0.6 * 72, 0.6 * 72, 3.7 * 72])
    ct.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL_SECONDARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_SLATE_LIGHT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(ct)
    story.append(Spacer(1, 12))

    # 4. ACTUAL Sample DNA Sequence Analyzed
    sample_seq = mut_data.get("sample_sequence") or ""
    story.extend(format_dna_sequence_flowables(
        sequence=sample_seq,
        heading_title="3. Actual Sample DNA Sequence Analyzed",
        chars_per_line=50
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
