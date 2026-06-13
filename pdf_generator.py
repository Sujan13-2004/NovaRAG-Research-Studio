import os
import re
import datetime
import csv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# ─── Color Palette ───────────────────────────────────────────────────────────
PRIMARY_COLOR   = colors.HexColor("#1E3A8A")   # Deep Blue
SECONDARY_COLOR = colors.HexColor("#0D9488")   # Teal
ACCENT_COLOR    = colors.HexColor("#7C3AED")   # Violet
TEXT_COLOR       = colors.HexColor("#1F2937")   # Slate Gray
BG_LIGHT        = colors.HexColor("#F8FAFC")   # Off-White
BG_COVER        = colors.HexColor("#0F172A")   # Dark Slate (cover page)
BORDER_COLOR    = colors.HexColor("#E2E8F0")   # Light Border
MUTED_TEXT      = colors.HexColor("#64748B")   # Muted

# ─── Page Constants ──────────────────────────────────────────────────────────
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 54  # 0.75 inch
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN  # 504 pt


# Load mapping from papers.csv if available
_papers_mapping = {}

def load_papers_mapping():
    """Loads or reloads papers mapping from papers.csv to handle dynamic downloads."""
    global _papers_mapping
    _papers_mapping = {}
    try:
        _csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papers.csv")
        if os.path.exists(_csv_path):
            with open(_csv_path, mode='r', encoding='utf-8') as _f:
                _reader = csv.DictReader(_f)
                for _row in _reader:
                    _filename = _row.get("pdf_filename", "").strip()
                    _title = _row.get("title", "").strip()
                    _arxiv_id = _row.get("arxiv_id", "").strip()
                    if _filename:
                        _papers_mapping[_filename] = {
                            "title": _title,
                            "arxiv_id": _arxiv_id
                        }
    except Exception as _e:
        print(f"Error loading papers.csv mapping: {_e}")

# Initial load
load_papers_mapping()


# ─── Filename → Citation Helper ─────────────────────────────────────────────
def format_citation(raw_title: str) -> str:
    """
    Converts a raw PDF filename into a readable academic citation.

    Example:
        '2406.10068_Predicting_Cardiovascular_Risk_using_Electrocardiogram_Deep_.pdf'
        → 'Predicting Cardiovascular Risk using Electrocardiogram Deep Analysis (arXiv:2406.10068)'
    """
    if not raw_title:
        return "Unknown Source"

    # Try mapping lookup first
    basename = os.path.basename(raw_title)
    if basename in _papers_mapping:
        mapped = _papers_mapping[basename]
        if mapped["arxiv_id"]:
            return f"{mapped['title']} (arXiv:{mapped['arxiv_id']})"
        return mapped["title"]

    name = basename
    # Strip file extension
    name = re.sub(r'\.pdf$', '', name, flags=re.IGNORECASE)

    # Try to extract arXiv-style ID at the beginning (e.g., 2406.10068_...)
    arxiv_match = re.match(r'^(\d{4}\.\d{4,5})[-_]?(.*)', name)
    arxiv_id = None
    if arxiv_match:
        arxiv_id = arxiv_match.group(1)
        name = arxiv_match.group(2)

    # Replace underscores with spaces and clean up
    name = name.replace('_', ' ').strip()
    # Remove trailing/leading hyphens or dots
    name = re.sub(r'^[\s\-\.]+|[\s\-\.]+$', '', name)
    # Collapse multiple spaces
    name = re.sub(r'\s{2,}', ' ', name)

    if not name:
        name = "Untitled Paper"

    # Append arXiv ID if found
    if arxiv_id:
        return f"{name} (arXiv:{arxiv_id})"
    return name


# ─── CoT Sanitization ───────────────────────────────────────────────────────
def sanitize_summary(summary: str) -> str:
    """Strips any chain-of-thought leakage from the summary text."""
    text = summary
    # Remove <thinking> blocks
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL).strip()
    text = re.sub(r'</?thinking>', '', text).strip()
    # Strip everything before '## Research Overview'
    overview_pos = re.search(r'## Research Overview', text)
    if overview_pos:
        text = text[overview_pos.start():]
    # Remove common leaked CoT lines
    cot_patterns = [
        r'(?i)^\s*(?:the user wants|I need to|let me|my analysis|I will|I should|first,? I)',
        r'(?i)^\s*(?:snippet|source|passage)\s*\d+[:\.]',
        r'(?i)^\s*(?:plan|step \d+|analysis|internal|reasoning)[:.]',
        r'(?i)^\s*(?:here is|below is|the following|I\'ve|I have).*(?:summary|synthesis|report)',
    ]
    cleaned = []
    for line in text.split('\n'):
        if not any(re.match(p, line.strip()) for p in cot_patterns):
            cleaned.append(line)
    text = '\n'.join(cleaned).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


# ─── Two-Pass Canvas (Headers / Footers) ────────────────────────────────────
class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that renders consistent headers and footers
    with accurate total page counts across all pages.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_decorations(self, page_count):
        self.saveState()

        # ── Header (skip on cover page) ──
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(PRIMARY_COLOR)
            self.drawString(MARGIN, PAGE_HEIGHT - 38, "NOVARAG RESEARCH REPORT")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(MUTED_TEXT)
            self.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 38,
                                 "AI Research Paper Summarizer & Report Generator")
            # Header rule
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(MARGIN, PAGE_HEIGHT - 44, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 44)

        # ── Footer (all pages) ──
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(MARGIN, 46, PAGE_WIDTH - MARGIN, 46)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(MUTED_TEXT)
        self.drawString(MARGIN, 34,
                        "NovaRAG Research Studio | AI Research Paper Summarizer & Report Generator")
        self.drawRightString(PAGE_WIDTH - MARGIN, 34,
                             f"Page {self._pageNumber} of {page_count}")

        self.restoreState()


# ─── Markdown → ReportLab Helpers ────────────────────────────────────────────
def escape_md(text: str) -> str:
    """Converts markdown inline formatting to ReportLab-compatible HTML tags."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.*?)`', r'<font face="Courier" size="8" color="#85144b">\1</font>', text)
    return text


def parse_markdown_to_story(md_text: str, styles: dict, story: list):
    """Parses markdown text line-by-line and appends ReportLab flowables to the story."""
    for line in md_text.split('\n'):
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith('### '):
            story.append(Paragraph(escape_md(stripped[4:]), styles['H3']))
            story.append(Spacer(1, 4))
        elif stripped.startswith('## '):
            story.append(Paragraph(escape_md(stripped[3:]), styles['H2']))
            story.append(Spacer(1, 6))
        elif stripped.startswith('# '):
            story.append(Paragraph(escape_md(stripped[2:]), styles['H1']))
            story.append(Spacer(1, 8))
        elif stripped.startswith('- ') or stripped.startswith('* '):
            story.append(Paragraph(f"&bull; {escape_md(stripped[2:])}", styles['Bullet']))
            story.append(Spacer(1, 3))
        elif re.match(r'^\d+\.\s', stripped):
            m = re.match(r'^(\d+)\.\s(.*)', stripped)
            story.append(Paragraph(f"{m.group(1)}. {escape_md(m.group(2))}", styles['Bullet']))
            story.append(Spacer(1, 3))
        else:
            story.append(Paragraph(escape_md(stripped), styles['Body']))
            story.append(Spacer(1, 4))


# ─── Style Factory ───────────────────────────────────────────────────────────
def _build_styles() -> dict:
    """Creates all ParagraphStyles used in the report."""
    base = getSampleStyleSheet()
    return {
        # ── Cover Page ──
        'CoverTitle': ParagraphStyle(
            'CoverTitle', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=28, leading=34,
            textColor=PRIMARY_COLOR, alignment=TA_CENTER, spaceAfter=12,
        ),
        'CoverSubtitle': ParagraphStyle(
            'CoverSubtitle', parent=base['Normal'],
            fontName='Helvetica', fontSize=13, leading=18,
            textColor=MUTED_TEXT, alignment=TA_CENTER, spaceAfter=6,
        ),
        'CoverMeta': ParagraphStyle(
            'CoverMeta', parent=base['Normal'],
            fontName='Helvetica', fontSize=10, leading=14,
            textColor=TEXT_COLOR, alignment=TA_CENTER, spaceAfter=4,
        ),

        # ── Section Headers ──
        'SectionHeader': ParagraphStyle(
            'SectionHeader', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=16, leading=20,
            textColor=PRIMARY_COLOR, spaceBefore=18, spaceAfter=10,
            keepWithNext=True,
        ),

        # ── Markdown Headings ──
        'H1': ParagraphStyle(
            'H1', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=15, leading=19,
            textColor=PRIMARY_COLOR, spaceBefore=14, spaceAfter=7,
            keepWithNext=True,
        ),
        'H2': ParagraphStyle(
            'H2', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=13, leading=17,
            textColor=SECONDARY_COLOR, spaceBefore=12, spaceAfter=6,
            keepWithNext=True,
        ),
        'H3': ParagraphStyle(
            'H3', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=11, leading=14,
            textColor=TEXT_COLOR, spaceBefore=10, spaceAfter=5,
            keepWithNext=True,
        ),


        # ── Body Text ──
        'Body': ParagraphStyle(
            'Body', parent=base['Normal'],
            fontName='Helvetica', fontSize=10, leading=14.5,
            textColor=TEXT_COLOR, alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        'Bullet': ParagraphStyle(
            'Bullet', parent=base['Normal'],
            fontName='Helvetica', fontSize=10, leading=14,
            textColor=TEXT_COLOR, leftIndent=18, firstLineIndent=-12,
            spaceAfter=4,
        ),
        'ReferenceItem': ParagraphStyle(
            'ReferenceItem', parent=base['Normal'],
            fontName='Helvetica', fontSize=9.5, leading=14,
            textColor=TEXT_COLOR, leftIndent=24, firstLineIndent=-24,
            spaceBefore=4, spaceAfter=4,
        ),

        'TableHeader': ParagraphStyle(
            'TableHeader', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=9, leading=12,
            textColor=colors.white,
        ),
        'TableCell': ParagraphStyle(
            'TableCell', parent=base['Normal'],
            fontName='Helvetica', fontSize=9, leading=12,
            textColor=TEXT_COLOR,
        ),
        'TableCellBold': ParagraphStyle(
            'TableCellBold', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=9, leading=12,
            textColor=TEXT_COLOR,
        ),

        # ── Source Excerpt (Appendix) ──
        'SourceTitle': ParagraphStyle(
            'SourceTitle', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=9, leading=12,
            textColor=PRIMARY_COLOR,
        ),
        'SourceText': ParagraphStyle(
            'SourceText', parent=base['Normal'],
            fontName='Helvetica-Oblique', fontSize=8.5, leading=12,
            textColor=MUTED_TEXT,
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def generate_pdf_report(
    output_path: str,
    query: str,
    summary: str,
    sources: list,
    guardrail_results: dict = None,
    include_excerpts: bool = False,
) -> str:
    """
    Generates a professional academic research report PDF.

    Args:
        output_path:      File path to write the PDF.
        query:            The user's research query.
        summary:          LLM-generated markdown summary.
        sources:          List of source chunk dicts from the RAG pipeline.
        guardrail_results: Dict with input_safe, output_safe, output_score.
        include_excerpts: If True, appends an Appendix with full source excerpts.

    Returns:
        The output_path after writing the PDF.
    """
    load_papers_mapping()
    
    # Defensive deduplication of sources to ensure unique papers in report
    seen_ref_titles = set()
    seen_ref_arxivs = set()
    deduplicated_sources = []
    
    for idx, src in enumerate(sources):
        raw_title = src.get("title", "Unknown")
        citation = format_citation(raw_title)
        
        # Extract title and arXiv ID for deduplication
        arxiv_match = re.search(r'\(arXiv:(.*?)\)', citation)
        clean_ref_title = re.sub(r'\(arXiv:.*?\)', '', citation).strip().lower()
        clean_ref_title = re.sub(r'[^a-z0-9]', '', clean_ref_title)
        
        is_dup = False
        if clean_ref_title in seen_ref_titles:
            is_dup = True
        if arxiv_match:
            arxiv_id = arxiv_match.group(1).strip()
            if arxiv_id in seen_ref_arxivs:
                is_dup = True
                
        if is_dup:
            continue
            
        seen_ref_titles.add(clean_ref_title)
        if arxiv_match:
            seen_ref_arxivs.add(arxiv_id)
            
        new_src = src.copy()
        new_src["rank"] = len(deduplicated_sources) + 1
        deduplicated_sources.append(new_src)
        
    sources = deduplicated_sources

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    styles = _build_styles()
    story = []

    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    num_sources = len(sources)
    groundedness = guardrail_results.get("output_score", 0.0) if guardrail_results else 0.0

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1: COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 120))

    # Top accent rule
    story.append(HRFlowable(
        width="60%", thickness=3, color=PRIMARY_COLOR,
        spaceBefore=0, spaceAfter=20, hAlign='CENTER',
    ))

    story.append(Paragraph("NovaRAG Research Studio", styles['CoverTitle']))
    story.append(Paragraph(
        "AI-Assisted Research Synthesis Report",
        styles['CoverSubtitle'],
    ))
    story.append(Spacer(1, 30))

    # Cover metadata table
    cover_data = [
        [Paragraph("<b>Project Title</b>", styles['TableCell']),
         Paragraph("NovaRAG: Enterprise-Grade Retrieval-Augmented Generation "
                    "& Academic Report Builder", styles['TableCell'])],
        [Paragraph("<b>Generated Date</b>", styles['TableCell']),
         Paragraph(current_date, styles['TableCell'])],
        [Paragraph("<b>Research Query</b>", styles['TableCell']),
         Paragraph(query, styles['TableCell'])],
        [Paragraph("<b>Sources Retrieved</b>", styles['TableCell']),
         Paragraph(f"{num_sources} documents reranked by relevance", styles['TableCell'])],
        [Paragraph("<b>Groundedness Score</b>", styles['TableCell']),
         Paragraph(f"{groundedness:.1%}", styles['TableCell'])],
    ]

    cover_table = Table(cover_data, colWidths=[140, CONTENT_WIDTH - 140])
    cover_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0, 0), (0, -1), BG_LIGHT),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(cover_table)

    story.append(Spacer(1, 30))

    # Bottom accent rule
    story.append(HRFlowable(
        width="60%", thickness=1, color=SECONDARY_COLOR,
        spaceBefore=10, spaceAfter=0, hAlign='CENTER',
    ))



    story.append(Spacer(1, 40))
    story.append(Paragraph(
        "NovaRAG Research Studio | AI Research Paper Summarizer & Report Generator",
        ParagraphStyle('FootNote', fontName='Helvetica-Oblique', fontSize=9,
                       leading=12, textColor=MUTED_TEXT, alignment=TA_CENTER),
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2+: GUARDRAIL AUDIT TABLE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    story.append(Paragraph("Security & Groundedness Audit", styles['SectionHeader']))
    story.append(Spacer(1, 4))

    audit_rows = [
        [Paragraph("Attribute", styles['TableHeader']),
         Paragraph("Status", styles['TableHeader'])],
        [Paragraph("Research Query", styles['TableCell']),
         Paragraph(query, styles['TableCell'])],
    ]

    if guardrail_results:
        input_safe = guardrail_results.get("input_safe", True)
        input_label = ("<font color='green'><b>PASSED</b></font> - No prompt injection detected"
                       if input_safe else
                       "<font color='red'><b>FAILED</b></font> - Prompt injection flagged")
        audit_rows.append([
            Paragraph("Input Guardrail", styles['TableCell']),
            Paragraph(input_label, styles['TableCell']),
        ])

        output_safe = guardrail_results.get("output_safe", True)
        output_label = (
            f"<font color='green'><b>PASSED</b></font> - Groundedness: {groundedness:.1%}"
            if output_safe else
            f"<font color='orange'><b>WARNING</b></font> - Groundedness: {groundedness:.1%} (hallucination risk)"
        )
        audit_rows.append([
            Paragraph("Output Guardrail", styles['TableCell']),
            Paragraph(output_label, styles['TableCell']),
        ])

        # Citation coverage metrics (from the new 3-tier scoring system)
        citation_info = guardrail_results.get("citation_info")
        if citation_info:
            cov = citation_info.get("citation_coverage", 0.0)
            cited = citation_info.get("total_citations", 0)
            uncited = citation_info.get("uncited_sentences", 0)
            total_sent = citation_info.get("total_sentences", 0)
            invalid = citation_info.get("invalid_citations", [])
            is_refusal = citation_info.get("is_refusal", False)

            if is_refusal:
                cov_label = "<font color='green'><b>N/A (Refusal)</b></font> (No factual claims requiring citations)"
            else:
                cov_color = "green" if cov >= 0.6 else "orange"
                cov_label = (
                    f"<font color='{cov_color}'><b>{cov:.1%}</b></font> "
                    f"({total_sent - uncited}/{total_sent} sentences cited, "
                    f"{cited} total citations)"
                )
                if invalid:
                    cov_label += f" | <font color='red'>Invalid: {invalid}</font>"

            audit_rows.append([
                Paragraph("Citation Coverage", styles['TableCell']),
                Paragraph(cov_label, styles['TableCell']),
            ])

    audit_rows.append([
        Paragraph("Sources Consulted", styles['TableCell']),
        Paragraph(f"{num_sources} passages reranked", styles['TableCell']),
    ])

    audit_table = Table(audit_rows, colWidths=[150, CONTENT_WIDTH - 150])
    audit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(audit_table)
    story.append(Spacer(1, 20))

    # ══════════════════════════════════════════════════════════════════════════
    # RESEARCH SYNTHESIS (main body)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(HRFlowable(
        width="100%", thickness=1, color=BORDER_COLOR,
        spaceBefore=5, spaceAfter=12,
    ))
    story.append(Paragraph("Research Synthesis", styles['SectionHeader']))
    story.append(Spacer(1, 4))

    # Import cleaning helper
    from rag_pipeline import clean_inline_citations
    
    # Strip any markdown-generated references section to prevent duplicates
    summary_parts = re.split(r'##\s+References', summary, flags=re.IGNORECASE)
    clean_summary = sanitize_summary(summary_parts[0])
    clean_summary = clean_inline_citations(clean_summary, sources)
    parse_markdown_to_story(clean_summary, styles, story)

    story.append(Spacer(1, 15))

    # ══════════════════════════════════════════════════════════════════════════
    # REFERENCES SECTION (academic style)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("References", styles['SectionHeader']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "The following sources were retrieved from the ChromaDB vector store, "
        "reranked by FlashRank, and referenced during the synthesis process.",
        styles['Body'],
    ))
    story.append(Spacer(1, 10))

    for idx, src in enumerate(sources):
        raw_title = src.get("title", "Unknown")
        citation = format_citation(raw_title)
        rank = src.get("rank", idx + 1)
        
        # Render as hanging indent academic reference
        ref_text = f"<b>[{rank}]</b> &nbsp;&nbsp; {citation}"
        story.append(Paragraph(ref_text, styles['ReferenceItem']))

    # ══════════════════════════════════════════════════════════════════════════
    # APPENDIX: FULL SOURCE EXCERPTS (optional)
    # ══════════════════════════════════════════════════════════════════════════
    if include_excerpts:
        story.append(PageBreak())
        story.append(Paragraph("Appendix: Source Excerpts", styles['SectionHeader']))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "Full text excerpts from each retrieved passage are reproduced below "
            "for transparency and verification purposes.",
            styles['Body'],
        ))
        story.append(Spacer(1, 10))

        for idx, src in enumerate(sources):
            raw_title = src.get("title", "Unknown")
            citation = format_citation(raw_title)
            page = src.get("page", "?")
            rank = src.get("rank", idx + 1)
            text = src.get("text", "")

            title_p = Paragraph(
                f"<b>[{rank}] {citation} - Page {page}</b>",
                styles['SourceTitle'],
            )
            text_p = Paragraph(f'"{text}"', styles['SourceText'])

            box_data = [[title_p], [Spacer(1, 3)], [text_p]]
            box_table = Table(box_data, colWidths=[CONTENT_WIDTH])
            box_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('LINELEFT', (0, 0), (0, -1), 3, SECONDARY_COLOR),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(KeepTogether([box_table, Spacer(1, 10)]))

    # ── Build ──
    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path
