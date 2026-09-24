import io
import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, KeepTogether, PageBreak
)

from app.reports.report_styles import (
    get_biotech_report_styles, NAVY_PRIMARY, TEAL_SECONDARY, ACCENT_CYAN,
    DARK_SLATE, MUTED_SLATE, BORDER_LIGHT, BG_SLATE_LIGHT, BG_HIGHLIGHT,
    ALERT_RED, ALERT_BG_RED, WHITE
)


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas for dynamic 'Page X of Y' page numbering and professional
    running headers and footers.
    """
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        # Suppress running header/footer on Cover Page if multi-page report has cover
        is_cover = (self._pageNumber == 1 and page_count > 1 and getattr(self, '_has_cover', False))

        if not is_cover:
            # Header
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(NAVY_PRIMARY)
            self.drawString(36, 758, "DNAura — DNA Sequence Classification & Prediction System")

            self.setFont("Helvetica", 7.5)
            self.setFillColor(MUTED_SLATE)
            self.drawRightString(576, 758, "Research & Academic Bioinformatics")

            self.setStrokeColor(BORDER_LIGHT)
            self.setLineWidth(0.5)
            self.line(36, 752, 576, 752)

            # Footer
            self.line(36, 40, 576, 40)
            now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(MUTED_SLATE)
            self.drawString(36, 28, f"Generated on: {now_str} | Academic Genomic Evaluation Report")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(576, 28, page_text)

        self.restoreState()


def format_dna_sequence_flowables(
    sequence: str,
    heading_title: str = "ACTUAL DNA SEQUENCE",
    chars_per_line: int = 50,
    max_display_bp: Optional[int] = None
) -> List[Any]:
    """
    Format actual DNA sequence into monospaced numbered blocks that page-break cleanly.
    Example:
    00001  ATGCGTACGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA
    00051  GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC
    """
    styles = get_biotech_report_styles()
    elements = []

    seq_clean = sequence.strip().replace(" ", "").replace("\n", "").replace("\r", "").upper()
    total_len = len(seq_clean)

    elements.append(Paragraph(f"<b>{heading_title}</b> (Total Length: {total_len} bp)", styles['SubsectionHeading']))

    if total_len == 0:
        elements.append(Paragraph("<i>No sequence provided.</i>", styles['Body']))
        return elements

    display_seq = seq_clean
    is_truncated = False
    if max_display_bp and total_len > max_display_bp:
        display_seq = seq_clean[:max_display_bp]
        is_truncated = True

    # Build structured table rows of (Line Number, Sequence Block)
    rows = []
    for i in range(0, len(display_seq), chars_per_line):
        line_num = f"{i + 1:05d}"
        chunk = display_seq[i:i + chars_per_line]
        # Divide into sub-groups of 10 for enhanced human readability
        spaced_chunk = " ".join([chunk[j:j+10] for j in range(0, len(chunk), 10)])
        rows.append([
            Paragraph(f"<font color='#0D9488'><b>{line_num}</b></font>", styles['TableCellMono']),
            Paragraph(f"<font color='#0F172A'>{spaced_chunk}</font>", styles['TableCellMono'])
        ])

    seq_table = Table(rows, colWidths=[0.8 * inch, 6.2 * inch])
    seq_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_SLATE_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.3, BORDER_LIGHT),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(seq_table)

    if is_truncated:
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            f"<i>[Note: Display sequence truncated at {max_display_bp} bp for layout. Full sequence of {total_len} bp analyzed in database.]</i>",
            styles['Body']
        ))

    elements.append(Spacer(1, 10))
    return elements


def build_report_header_bar(
    title: str,
    module_label: str,
    analysis_id: Any,
    sequence_name: str,
    user_name: str
) -> List[Any]:
    """Top header metadata card for individual module reports."""
    styles = get_biotech_report_styles()
    now_str = datetime.datetime.now().strftime("%d-%b-%Y %H:%M")

    header_table_data = [
        [
            Paragraph(f"<b>DNAura PLATFORM</b> &bull; <font color='#0D9488'>{module_label}</font>", styles['ReportSubHeader']),
            Paragraph(f"<b>Report ID:</b> GENO-REP-{analysis_id or '001'}", styles['BodyBold'])
        ],
        [
            Paragraph(f"<b>Analysis:</b> {title}", styles['ReportHeader']),
            Paragraph(f"<b>Date:</b> {now_str}", styles['TableCell'])
        ],
        [
            Paragraph(f"<b>Sequence Name:</b> {sequence_name}", styles['TableCellBold']),
            Paragraph(f"<b>Investigator:</b> {user_name}", styles['TableCell'])
        ]
    ]

    ht = Table(header_table_data, colWidths=[4.6 * inch, 2.4 * inch])
    ht.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, TEAL_SECONDARY),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))

    return [ht, Spacer(1, 10)]


def build_sequence_summary_table(metrics: Dict[str, Any]) -> Table:
    """Build standardized 2-column or 4-column sequence summary table."""
    styles = get_biotech_report_styles()
    length = metrics.get('length', 0)
    a_cnt = metrics.get('a_count', 0)
    t_cnt = metrics.get('t_count', 0)
    g_cnt = metrics.get('g_count', 0)
    c_cnt = metrics.get('c_count', 0)
    a_pct = metrics.get('a_percentage', 0.0)
    t_pct = metrics.get('t_percentage', 0.0)
    g_pct = metrics.get('g_percentage', 0.0)
    c_pct = metrics.get('c_percentage', 0.0)
    gc_val = metrics.get('gc_content', 0.0)
    at_val = metrics.get('at_content', 0.0)
    mol_wt = metrics.get('molecular_weight', 0.0)

    data = [
        [Paragraph("Sequence Metric", styles['TableHead']), Paragraph("Calculated Value", styles['TableHead']),
         Paragraph("Nucleotide Composition", styles['TableHead']), Paragraph("Count & Percentage", styles['TableHead'])],
        [Paragraph("Total Length", styles['TableCellBold']), Paragraph(f"{length} bp", styles['TableCellMono']),
         Paragraph("Adenine (A)", styles['TableCellBold']), Paragraph(f"{a_cnt} bp ({a_pct}%)", styles['TableCell'])],
        [Paragraph("GC Content", styles['TableCellBold']), Paragraph(f"<b>{gc_val:.2f}%</b>", styles['TableCell']),
         Paragraph("Thymine (T)", styles['TableCellBold']), Paragraph(f"{t_cnt} bp ({t_pct}%)", styles['TableCell'])],
        [Paragraph("AT Content", styles['TableCellBold']), Paragraph(f"{at_val:.2f}%", styles['TableCell']),
         Paragraph("Guanine (G)", styles['TableCellBold']), Paragraph(f"{g_cnt} bp ({g_pct}%)", styles['TableCell'])],
        [Paragraph("Estimated Mol. Weight", styles['TableCellBold']), Paragraph(f"{mol_wt:.2f} g/mol", styles['TableCell']),
         Paragraph("Cytosine (C)", styles['TableCellBold']), Paragraph(f"{c_cnt} bp ({c_pct}%)", styles['TableCell'])],
    ]

    t = Table(data, colWidths=[1.8 * inch, 1.7 * inch, 1.8 * inch, 1.7 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_SLATE_LIGHT, WHITE]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


def build_medical_disclaimer_box(custom_text: Optional[str] = None) -> Table:
    """Build standardized prominent academic and medical disclaimer callout box."""
    styles = get_biotech_report_styles()
    text = custom_text or (
        "<b>IMPORTANT MEDICAL & RESEARCH DISCLAIMER:</b> This system provides AI-assisted predictions and computational "
        "bioinformatics analysis for academic and research evaluation only. The results are NOT a medical diagnosis, clinical "
        "judgment, or prognosis, and must not be used as a substitute for certified laboratory testing or professional healthcare guidance."
    )
    t = Table([[Paragraph(text, styles['DisclaimerText'])]], colWidths=[7.0 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ALERT_BG_RED),
        ('BOX', (0, 0), (-1, -1), 1.2, ALERT_RED),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


# --- Matplotlib Embedded Chart Generators ---

def generate_nucleotide_composition_chart(metrics: Dict[str, Any]) -> io.BytesIO:
    """Render Matplotlib figure with Nucleotide distribution bar + GC/AT donut."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.2), dpi=220)

    bases = ['A', 'T', 'G', 'C']
    counts = [
        int(metrics.get('a_count') or 0),
        int(metrics.get('t_count') or 0),
        int(metrics.get('g_count') or 0),
        int(metrics.get('c_count') or 0)
    ]
    bar_colors = ['#10B981', '#EF4444', '#F59E0B', '#3B82F6']
    bars = ax1.bar(bases, counts, color=bar_colors, width=0.55, edgecolor='#0F172A', linewidth=0.8)
    ax1.set_title('Nucleotide Distribution (bp)', fontsize=8.5, fontweight='bold', color='#0F172A')
    ax1.set_ylabel('Count', fontsize=7.5)
    ax1.tick_params(labelsize=7.5)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)

    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 2), textcoords="offset points",
                    ha='center', va='bottom', fontsize=7, fontweight='bold')

    gc = float(metrics.get('gc_content') or 50.0)
    at = float(metrics.get('at_content') or 50.0)
    wedges, texts, autotexts = ax2.pie(
        [gc, at],
        labels=[f'GC {gc:.1f}%', f'AT {at:.1f}%'],
        colors=['#0284C7', '#8B5CF6'],
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor='white', linewidth=1.5)
    )
    for t in texts:
        t.set_fontsize(7.5)
        t.set_fontweight('bold')
    for at_text in autotexts:
        at_text.set_fontsize(7)
        at_text.set_color('white')
        at_text.set_fontweight('bold')

    ax2.set_title('GC vs AT Content Ratio', fontsize=8.5, fontweight='bold', color='#0F172A')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=False, facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_disease_probabilities_chart(probabilities: Dict[str, float]) -> io.BytesIO:
    """Horizontal bar chart for 5 disease class probabilities."""
    fig, ax = plt.subplots(figsize=(6.8, 2.0), dpi=220)

    classes = list(probabilities.keys())
    scores = [float(probabilities[k] or 0.0) for k in classes]
    y_pos = range(len(classes))

    colors_list = ['#10B981' if c == 'Healthy' else '#EF4444' for c in classes]
    bars = ax.barh(y_pos, scores, color=colors_list, height=0.55, edgecolor='#0F172A', linewidth=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(classes, fontsize=8, fontweight='medium')
    ax.invert_yaxis()  # top-down
    ax.set_xlabel('Model Probability (%)', fontsize=7.5)
    ax.set_xlim(0, 100)
    ax.tick_params(labelsize=7.5)
    ax.grid(axis='x', linestyle='--', alpha=0.4)
    ax.set_title('5-Class Disease Probability Distribution (Random Forest)', fontsize=8.5, fontweight='bold', color='#0F172A')

    for bar in bars:
        width = bar.get_width()
        ax.annotate(f'{width:.1f}%',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(3, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=7, fontweight='bold')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=False, facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return buf
