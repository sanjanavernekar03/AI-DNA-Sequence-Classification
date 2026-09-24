from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Curated Biotechnology + AI Color Palette
NAVY_PRIMARY = colors.HexColor("#0F172A")       # Deep Bio-Navy
TEAL_SECONDARY = colors.HexColor("#0D9488")     # Bio-Emerald / Teal
ACCENT_CYAN = colors.HexColor("#0284C7")        # Biotech Cyan
ACCENT_PURPLE = colors.HexColor("#7C3AED")      # Deep Violet
DARK_SLATE = colors.HexColor("#1E293B")         # Charcoal Body Text
MUTED_SLATE = colors.HexColor("#64748B")        # Subtitle / Muted Text
BORDER_LIGHT = colors.HexColor("#CBD5E1")       # Clean Grid Border
BG_SLATE_LIGHT = colors.HexColor("#F8FAFC")     # Alternating Row BG
BG_HIGHLIGHT = colors.HexColor("#F0FDFA")       # Emerald Card BG
ALERT_RED = colors.HexColor("#DC2626")          # Warning / Pathogenic Red
ALERT_BG_RED = colors.HexColor("#FEF2F2")       # Warning Callout BG
WHITE = colors.HexColor("#FFFFFF")

# Nucleotide Colors for Styling
COLOR_A = colors.HexColor("#10B981")
COLOR_T = colors.HexColor("#EF4444")
COLOR_G = colors.HexColor("#F59E0B")
COLOR_C = colors.HexColor("#3B82F6")


def get_biotech_report_styles():
    """Build and return a unified suite of professional ReportLab ParagraphStyles."""
    base_styles = getSampleStyleSheet()

    styles = {
        'CoverTitle': ParagraphStyle(
            'CoverTitle',
            parent=base_styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=26,
            leading=32,
            textColor=NAVY_PRIMARY,
            alignment=1, # Center
            spaceAfter=12
        ),
        'CoverSubtitle': ParagraphStyle(
            'CoverSubtitle',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=13,
            leading=18,
            textColor=TEAL_SECONDARY,
            alignment=1,
            spaceAfter=24
        ),
        'CoverMeta': ParagraphStyle(
            'CoverMeta',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=15,
            textColor=DARK_SLATE,
            alignment=1
        ),
        'CoverTagline': ParagraphStyle(
            'CoverTagline',
            parent=base_styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            leading=14,
            textColor=MUTED_SLATE,
            alignment=1
        ),
        'ReportHeader': ParagraphStyle(
            'ReportHeader',
            parent=base_styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=NAVY_PRIMARY,
            spaceAfter=4
        ),
        'ReportSubHeader': ParagraphStyle(
            'ReportSubHeader',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=TEAL_SECONDARY,
            spaceAfter=10
        ),
        'SectionHeading': ParagraphStyle(
            'SectionHeading',
            parent=base_styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=NAVY_PRIMARY,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        ),
        'SubsectionHeading': ParagraphStyle(
            'SubsectionHeading',
            parent=base_styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=ACCENT_CYAN,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'Body',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=DARK_SLATE
        ),
        'BodyBold': ParagraphStyle(
            'BodyBold',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=12,
            textColor=NAVY_PRIMARY
        ),
        'TableHead': ParagraphStyle(
            'TableHead',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=WHITE,
            alignment=0
        ),
        'TableCell': ParagraphStyle(
            'TableCell',
            parent=base_styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=DARK_SLATE
        ),
        'TableCellBold': ParagraphStyle(
            'TableCellBold',
            parent=base_styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=NAVY_PRIMARY
        ),
        'TableCellMono': ParagraphStyle(
            'TableCellMono',
            parent=base_styles['Normal'],
            fontName='Courier',
            fontSize=7.5,
            leading=10,
            textColor=NAVY_PRIMARY
        ),
        'SequenceBlock': ParagraphStyle(
            'SequenceBlock',
            parent=base_styles['Normal'],
            fontName='Courier',
            fontSize=7.5,
            leading=10,
            textColor=NAVY_PRIMARY
        ),
        'DisclaimerText': ParagraphStyle(
            'DisclaimerText',
            parent=base_styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=ALERT_RED
        )
    }

    return styles
