from pathlib import Path
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image

from app.reports.report_styles import get_biotech_report_styles
from app.reports.report_components import (
    NumberedCanvas, build_report_header_bar, build_sequence_summary_table,
    format_dna_sequence_flowables, generate_nucleotide_composition_chart
)


def generate_dna_visualization_report(
    vis_data: Dict[str, Any],
    user_name: str,
    output_path: Path
):
    """
    Generate Report 6: DNA Sequence Visualization Report.
    Includes actual sequence, graphical charts, and composition analytics.
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
        title="DNA Sequence Graphical Visualization Report",
        module_label="Module 06 &bull; Graphical Analytics & Distributions",
        analysis_id=vis_data.get("id"),
        sequence_name=vis_data.get("sequence_name", "DNA Specimen"),
        user_name=user_name
    ))

    # 2. Summary Table
    metrics = vis_data.get("metrics") or vis_data
    story.append(Paragraph("1. Physicochemical Composition Summary", styles['SectionHeading']))
    story.append(build_sequence_summary_table(metrics))
    story.append(Spacer(1, 10))

    # 3. Graphical Distributions
    story.append(Paragraph("2. Nucleotide Distribution & Composition Graphics", styles['SectionHeading']))
    chart_buf = generate_nucleotide_composition_chart(metrics)
    story.append(Image(chart_buf, width=6.8 * 72, height=2.2 * 72))
    story.append(Spacer(1, 12))

    # 4. ACTUAL DNA Sequence Analyzed
    actual_seq = vis_data.get("sequence") or vis_data.get("cleaned_sequence") or ""
    story.extend(format_dna_sequence_flowables(
        sequence=actual_seq,
        heading_title="3. Actual DNA Sequence Visualized",
        chars_per_line=50
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
