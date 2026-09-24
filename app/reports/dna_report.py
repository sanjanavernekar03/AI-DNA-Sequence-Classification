from pathlib import Path
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image

from app.reports.report_styles import get_biotech_report_styles
from app.reports.report_components import (
    NumberedCanvas, build_report_header_bar, build_sequence_summary_table,
    format_dna_sequence_flowables, generate_nucleotide_composition_chart
)


def generate_dna_sequence_report(
    analysis_data: Dict[str, Any],
    user_name: str,
    output_path: Path
):
    """
    Generate Report 1: DNA Sequence Processing & Analysis Report.
    Always includes the ACTUAL DNA sequence formatted in numbered blocks.
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
        title="DNA Sequence Processing & Analysis Report",
        module_label="Module 01 &bull; Physicochemical Analytics",
        analysis_id=analysis_data.get("id"),
        sequence_name=analysis_data.get("sequence_name", "DNA Specimen"),
        user_name=user_name
    ))

    # 2. Sequence Summary Table
    story.append(Paragraph("1. Primary Physicochemical & Compositional Properties", styles['SectionHeading']))
    story.append(build_sequence_summary_table(analysis_data))
    story.append(Spacer(1, 10))

    # 3. Graphical Composition Analysis
    story.append(Paragraph("2. Graphical Nucleotide Distribution & GC/AT Content", styles['SectionHeading']))
    chart_buf = generate_nucleotide_composition_chart(analysis_data)
    story.append(Image(chart_buf, width=6.8 * 72, height=2.2 * 72))
    story.append(Spacer(1, 12))

    # 4. ACTUAL DNA Sequence (Guaranteed Real Sequence Display)
    actual_seq = analysis_data.get("cleaned_sequence") or analysis_data.get("sequence") or ""
    story.extend(format_dna_sequence_flowables(
        sequence=actual_seq,
        heading_title="3. Actual DNA Sequence Analyzed",
        chars_per_line=50
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
