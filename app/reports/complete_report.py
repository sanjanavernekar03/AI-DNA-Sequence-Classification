import datetime
from pathlib import Path
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)

from app.reports.report_styles import (
    get_biotech_report_styles, NAVY_PRIMARY, TEAL_SECONDARY, ACCENT_CYAN,
    BORDER_LIGHT, BG_SLATE_LIGHT, BG_HIGHLIGHT, WHITE
)
from app.reports.report_components import (
    NumberedCanvas, build_sequence_summary_table, format_dna_sequence_flowables,
    build_medical_disclaimer_box, generate_nucleotide_composition_chart,
    generate_disease_probabilities_chart
)


def generate_complete_dna_report(
    comp_data: Dict[str, Any],
    user_name: str,
    output_path: Path
):
    """
    Generate Complete DNA Analysis Report.
    Combines all 6 modules + dedicated Cover Page + Executive Summary + ACTUAL sequences.
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

    # Flag for NumberedCanvas to suppress running headers on Page 1
    NumberedCanvas._has_cover = True

    # -------------------------------------------------------------
    # 1. PROFESSIONAL COVER PAGE
    # -------------------------------------------------------------
    story.append(Spacer(1, 40))
    story.append(Paragraph("<font color='#0D9488'>&bull; &bull; &bull; DNAura COMPUTATIONAL PLATFORM &bull; &bull; &bull;</font>", styles['CoverTagline']))
    story.append(Spacer(1, 15))
    story.append(Paragraph("AI-POWERED DNA SEQUENCE<br/>CLASSIFICATION & PREDICTION SYSTEM", styles['CoverTitle']))
    story.append(Paragraph("Comprehensive Multi-Module Genomic Evaluation Report", styles['CoverSubtitle']))
    story.append(HRFlowable(width="60%", thickness=2, color=TEAL_SECONDARY, spaceBefore=10, spaceAfter=25))

    now_str = datetime.datetime.now().strftime("%d %B %Y &bull; %H:%M")
    analysis_id = comp_data.get("id") or "001"
    seq_name = comp_data.get("sequence_name", "Clinical DNA Specimen")

    meta_card = [
        [Paragraph("<b>Analysis Record ID:</b>", styles['TableCellBold']), Paragraph(f"GENO-COMP-{analysis_id}", styles['TableCellMono'])],
        [Paragraph("<b>Primary Specimen:</b>", styles['TableCellBold']), Paragraph(f"<b>{seq_name}</b>", styles['TableCell'])],
        [Paragraph("<b>Investigator / Analyst:</b>", styles['TableCellBold']), Paragraph(user_name, styles['TableCell'])],
        [Paragraph("<b>Publication Date:</b>", styles['TableCellBold']), Paragraph(now_str, styles['TableCell'])],
        [Paragraph("<b>Integrated Modules:</b>", styles['TableCellBold']), Paragraph("All 6 Modules (Sequence, Similarity, Mutation, AI Class, Disease Risk, Visualization)", styles['TableCell'])],
    ]

    mc = Table(meta_card, colWidths=[2.2 * 72, 3.8 * 72])
    mc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_HIGHLIGHT),
        ('BOX', (0, 0), (-1, -1), 1.2, TEAL_SECONDARY),
        ('GRID', (0, 0), (-1, -1), 0.4, BORDER_LIGHT),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(mc)
    story.append(Spacer(1, 40))

    story.append(Paragraph(
        "<i>\"AI-assisted computational bioinformatics, deep sequence-level functional classification, "
        "and multi-class clinical pathogenic risk assessment.\"</i>",
        styles['CoverTagline']
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Academic & Research Exploration Project</b>", styles['CoverMeta']))

    story.append(PageBreak())

    # -------------------------------------------------------------
    # 2. EXECUTIVE GENOMIC SUMMARY (PAGE 2)
    # -------------------------------------------------------------
    story.append(Paragraph("Executive Genomic Analysis Summary", styles['ReportHeader']))
    story.append(Paragraph("Consolidated findings across all 6 computational pipelines.", styles['ReportSubHeader']))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_SECONDARY, spaceBefore=4, spaceAfter=10))

    kpi_data = [
        [Paragraph("Analytical Pipeline", styles['TableHead']), Paragraph("Primary Outcome / Metric", styles['TableHead']),
         Paragraph("Analytical Pipeline", styles['TableHead']), Paragraph("Primary Outcome / Metric", styles['TableHead'])],
        [Paragraph("Sequence Length", styles['TableCellBold']), Paragraph(f"<b>{comp_data.get('length', 0)} bp</b>", styles['TableCellMono']),
         Paragraph("GC / AT Content", styles['TableCellBold']), Paragraph(f"GC: {comp_data.get('gc_content', 0)}% | AT: {comp_data.get('at_content', 0)}%", styles['TableCell'])],
        [Paragraph("Pairwise Similarity", styles['TableCellBold']), Paragraph(f"<b>{comp_data.get('similarity_percentage', 0)}%</b>", styles['TableCell']),
         Paragraph("Total Mutations Detected", styles['TableCellBold']), Paragraph(f"<b>{comp_data.get('total_mutations', 0)}</b> ({comp_data.get('mutation_rate', 0)}% rate)", styles['TableCell'])],
        [Paragraph("AI Functional Class", styles['TableCellBold']), Paragraph(f"<font color='#0D9488'><b>{comp_data.get('predicted_class', 'N/A')}</b></font>", styles['TableCell']),
         Paragraph("Class Confidence", styles['TableCellBold']), Paragraph(f"<b>{comp_data.get('class_confidence', 0)}%</b>", styles['TableCell'])],
        [Paragraph("Disease Risk Category", styles['TableCellBold']), Paragraph(f"<font color='#DC2626'><b>{comp_data.get('predicted_category', 'N/A')}</b></font>", styles['TableCell']),
         Paragraph("Disease Probability", styles['TableCellBold']), Paragraph(f"<b>{comp_data.get('disease_probability', 0)}%</b> ({comp_data.get('risk_category', 'Moderate')} Tier)", styles['TableCell'])],
    ]

    kt = Table(kpi_data, colWidths=[1.8 * 72, 1.7 * 72, 1.8 * 72, 1.7 * 72])
    kt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_SLATE_LIGHT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(kt)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 3. SECTION 1 & 2: Sequence Metrics & Alignment
    # -------------------------------------------------------------
    story.append(Paragraph("Section 1 & 2 &bull; Sequence Processing & Similarity Alignment", styles['SectionHeading']))
    story.append(build_sequence_summary_table(comp_data))
    story.append(Spacer(1, 10))

    sim_table = [
        [Paragraph("Similarity Metric", styles['TableHead']), Paragraph("Value", styles['TableHead']),
         Paragraph("Similarity Metric", styles['TableHead']), Paragraph("Value", styles['TableHead'])],
        [Paragraph("Exact Matches", styles['TableCellBold']), Paragraph(f"{comp_data.get('match_count', 0)} bp", styles['TableCell']),
         Paragraph("Mismatches & Gaps", styles['TableCellBold']), Paragraph(f"{comp_data.get('mismatch_count', 0)} mismatches, {comp_data.get('gap_count', 0)} gaps", styles['TableCell'])],
    ]
    st = Table(sim_table, colWidths=[1.8 * 72, 1.7 * 72, 1.8 * 72, 1.7 * 72])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL_SECONDARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_SLATE_LIGHT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(st)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 4. SECTION 3, 4, 5: Mutation, AI Class & Disease Risk
    # -------------------------------------------------------------
    story.append(Paragraph("Section 3, 4 & 5 &bull; Mutation Calling, AI Classification & Disease Risk", styles['SectionHeading']))

    ai_data = [
        [Paragraph("Module", styles['TableHead']), Paragraph("Model Architecture", styles['TableHead']),
         Paragraph("Predicted Outcome", styles['TableHead']), Paragraph("Score / Confidence", styles['TableHead'])],
        [Paragraph("Mutation Analysis", styles['TableCellBold']), Paragraph("Needleman-Wunsch Coordinate Caller", styles['TableCell']),
         Paragraph(f"{comp_data.get('total_mutations', 0)} mutations ({comp_data.get('substitutions_count', 0)} SNVs, +{comp_data.get('insertions_count', 0)} / -{comp_data.get('deletions_count', 0)})", styles['TableCell']),
         Paragraph(f"{comp_data.get('mutation_rate', 0)}% Rate", styles['TableCellBold'])],
        [Paragraph("AI DNA Classification", styles['TableCellBold']), Paragraph("Random Forest (64-dim k-mers)", styles['TableCell']),
         Paragraph(f"<b>{comp_data.get('predicted_class', 'CDS')}</b>", styles['TableCell']),
         Paragraph(f"{comp_data.get('class_confidence', 0)}% Conf", styles['TableCellBold'])],
        [Paragraph("Genomic Disease Risk", styles['TableCellBold']), Paragraph("Random Forest (5 Classes)", styles['TableCell']),
         Paragraph(f"<font color='#DC2626'><b>{comp_data.get('predicted_category', 'Healthy')}</b></font>", styles['TableCell']),
         Paragraph(f"{comp_data.get('disease_probability', 0)}% ({comp_data.get('risk_category', 'Low')})", styles['TableCellBold'])],
    ]
    at = Table(ai_data, colWidths=[1.6 * 72, 2.0 * 72, 2.2 * 72, 1.2 * 72])
    at.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_SLATE_LIGHT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(at)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 5. SECTION 6: Graphical Analytics Visualizer
    # -------------------------------------------------------------
    story.append(Paragraph("Section 6 &bull; Graphical Composition Analysis", styles['SectionHeading']))
    chart_buf = generate_nucleotide_composition_chart(comp_data)
    story.append(Image(chart_buf, width=6.8 * 72, height=2.0 * 72))
    story.append(Spacer(1, 10))

    # Mandatory Disclaimer
    story.append(build_medical_disclaimer_box())
    story.append(Spacer(1, 12))

    # -------------------------------------------------------------
    # 6. ACTUAL DNA SEQUENCE ANALYZED (Guaranteed Real DNA Content)
    # -------------------------------------------------------------
    target_seq = comp_data.get("sequence") or comp_data.get("cleaned_sequence") or ""
    story.extend(format_dna_sequence_flowables(
        sequence=target_seq,
        heading_title=f"7. Actual Target DNA Sequence Analyzed ({seq_name})",
        chars_per_line=50
    ))

    # Actual Reference Sequence (if provided)
    ref_seq = comp_data.get("reference_sequence") or ""
    if ref_seq:
        ref_title = comp_data.get("reference_name", "Wildtype Reference Sequence")
        story.extend(format_dna_sequence_flowables(
            sequence=ref_seq,
            heading_title=f"8. Actual Reference DNA Sequence ({ref_title})",
            chars_per_line=50
        ))

    doc.build(story, canvasmaker=NumberedCanvas)
