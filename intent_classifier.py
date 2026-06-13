"""
Intent Classification for NovaRAG Research Studio.

Classifies user queries into one of three intents:
    - FACTUAL_QA:          Short factual questions expecting a direct answer
    - DOCUMENT_SUMMARY:    Requests to summarize a specific document
    - RESEARCH_SYNTHESIS:  Multi-paper analysis, literature reviews, research briefs

Uses a two-stage approach:
    1. Hard-override detection (explicit user instructions always win)
    2. Rule-based keyword/pattern classification
"""

import re
from enum import Enum


class QueryIntent(str, Enum):
    FACTUAL_QA = "FACTUAL_QA"
    DOCUMENT_SUMMARY = "DOCUMENT_SUMMARY"
    RESEARCH_SYNTHESIS = "RESEARCH_SYNTHESIS"
    EVIDENCE_EXTRACTION = "EVIDENCE_EXTRACTION"


# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 1: HARD OVERRIDES
# If the user explicitly requests a specific response format, honour it.
# ═══════════════════════════════════════════════════════════════════════════════

_HARD_OVERRIDE_PATTERNS = [
    # Explicit short-answer instructions
    r"one\s*line\s*only",
    r"short\s*answer",
    r"do\s*not\s*summarize",
    r"do\s*not\s*summarise",
    r"return\s*only\s*the\s*answer",
    r"answer\s*only",
    r"just\s*answer",
    r"brief\s*answer",
    r"direct\s*answer",
    r"no\s*report",
    r"no\s*synthesis",
    r"no\s*summary",
    r"one\s*sentence\s*only",
    r"single\s*line",
    r"reply\s*only",
    r"respond\s*only",
    r"answer\s*in\s*one\s*(line|sentence|word)",
    r"answer\s*with\s*one\s*(line|sentence|word)",
    r"do\s*not\s*explain",
    r"if\s*.+not\s*(present|found|stated|available|mentioned).+reply\s*only",
]

_HARD_OVERRIDE_COMPILED = [
    re.compile(p, re.IGNORECASE) for p in _HARD_OVERRIDE_PATTERNS
]


def _check_hard_override(query: str) -> bool:
    """Returns True if the query contains an explicit short-answer instruction."""
    for pattern in _HARD_OVERRIDE_COMPILED:
        if pattern.search(query):
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 2: RULE-BASED INTENT CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

# ── Factual QA signals ──
# Questions asking for a specific data point, number, name, or fact
_FACTUAL_QA_PATTERNS = [
    # Wh-questions asking for specific facts
    r"^what\s+(is|was|are|were)\s+the\s+(exact|specific|reported|test|training|validation)?\s*(accuracy|precision|recall|f1|auc|score|percentage|result|value|number|count|size|name|email|author|title|year|date|doi|volume|journal|dataset|metric)",
    r"^what\s+(accuracy|precision|recall|f1|auc|score|percentage|result|value|number|count)",
    r"^what\s+exact\s+",
    r"^what\s+is\s+the\s+(name|email|affiliation|address|doi|isbn|issn)\s+",
    r"^who\s+(is|are|was|were)\s+the\s+(author|researcher|principal|corresponding|first|lead)",
    r"^how\s+many\s+(records|samples|patients|participants|subjects|images|epochs|layers|parameters|features|classes|categories|rows|entries|data\s*points)",
    r"^how\s+much\s+(data|accuracy|improvement|gain)",
    r"^when\s+was\s+(this|the)\s+(paper|study|research|article)\s+(published|written|submitted)",
    r"^where\s+was\s+(this|the)\s+(paper|study|research)\s+(published|presented|submitted)",
    r"^which\s+(model|algorithm|method|approach|technique|dataset|tool|framework)\s+(achieved|had|got|reported|produced|showed|was\s+used)",
    r"^(list|name|identify|state|give)\s+the\s+",
    r"^is\s+there\s+(a|any)\s+(mention|reference|discussion|section)\s+(of|about|on)\s+",
    r"^does\s+(this|the)\s+(paper|study|article|document)\s+(mention|discuss|address|include|contain|report|state)",
    # Direct value extraction patterns
    r"what\s+percentage",
    r"what\s+(?:was|is)\s+the\s+.*\s+(score|accuracy|rate|ratio|loss)",
    r"how\s+large\s+(?:is|was)\s+the\s+dataset",
    r"extract\s+the\s+",
    r"find\s+the\s+(exact|specific)?\s*(value|number|percentage|accuracy|name|author)",
]

_FACTUAL_QA_COMPILED = [
    re.compile(p, re.IGNORECASE) for p in _FACTUAL_QA_PATTERNS
]

# ── Document Summary signals ──
_SUMMARY_PATTERNS = [
    r"^summarize\s+(this|the|my)\s+(paper|document|pdf|article|upload|file)",
    r"^(give|provide|create|generate|write)\s+(me\s+)?(a|the)?\s*(brief|short|concise|comprehensive|detailed|full)?\s*summary",
    r"^explain\s+(this|the|my)\s+(paper|document|pdf|article|upload|file)",
    r"^overview\s+of\s+(this|the|my)\s+",
    r"^what\s+is\s+(this|the)\s+(paper|document|article|study)\s+about",
    r"^describe\s+(this|the|my)\s+(paper|document|pdf)",
    r"^break\s*down\s+(this|the)\s+(paper|document)",
    r"summarize\s+the\s+key\s+(findings|points|contributions|results|methodology)",
    r"^tldr",
    r"^tl;dr",
    r"^abstract\s+of\s+",
    r"^main\s+(points|ideas|contributions|arguments)\s+(of|in|from)\s+",
]

_SUMMARY_COMPILED = [
    re.compile(p, re.IGNORECASE) for p in _SUMMARY_PATTERNS
]

# ── Research Synthesis signals ──
_SYNTHESIS_PATTERNS = [
    r"^compare\s+(the|these|multiple|different|various)\s+(papers|studies|articles|methods|approaches|models)",
    r"^(generate|create|write|produce|compile)\s+(a|the)?\s*(research|literature|comparative|systematic)?\s*(review|brief|report|synthesis|analysis)",
    r"literature\s+review",
    r"research\s+(synthesis|brief|report|overview|survey)",
    r"^(analyze|analyse)\s+(?:the\s+)?(literature|research|studies|papers)",
    r"^cross[\-\s]paper\s+(analysis|comparison|synthesis)",
    r"^multi[\-\s]paper\s+(analysis|comparison|synthesis|review)",
    r"^(identify|find)\s+(common\s+)?(trends|patterns|themes|gaps)\s+(in|across|among)\s+(the\s+)?(literature|papers|studies|research)",
    r"^state\s+of\s+the\s+art\s+(in|for|on)\s+",
    r"^how\s+do\s+(the|these|different|various)\s+(papers|studies|methods|approaches)\s+compare",
]

_SYNTHESIS_COMPILED = [
    re.compile(p, re.IGNORECASE) for p in _SYNTHESIS_PATTERNS
]

# ── Evidence Extraction signals ──
_EVIDENCE_PATTERNS = [
    r"\bfact",
    r"page\s*number",
    r"supporting\s*quote",
    r"\bevidence",
    r"\bcitation",
    r"\bsource",
    r"explicitly\s*stated",
    r"extract\s*facts"
]

_EVIDENCE_COMPILED = [
    re.compile(p, re.IGNORECASE) for p in _EVIDENCE_PATTERNS
]


# ── Short-question heuristics (additional factual QA signals) ──
_QUESTION_WORD_STARTS = {"what", "who", "where", "when", "which", "how", "does", "did", "is", "are", "was", "were", "can", "has", "have"}


def classify_intent(query: str, is_single_doc_mode: bool = False) -> QueryIntent:
    """
    Classifies a user query into one of three intents.
    
    Args:
        query: The raw user query string.
        is_single_doc_mode: Whether a specific document is selected in the scope dropdown.
    
    Returns:
        QueryIntent enum value.
    """
    q = query.strip()
    q_lower = q.lower()
    
    # ── Stage 1: Hard overrides (always win) ──
    if _check_hard_override(q):
        return QueryIntent.FACTUAL_QA
    
    # ── Stage 2: Rule-based classification ──
    
    # Check for explicit evidence extraction patterns (takes precedence over summary/synthesis)
    for pattern in _EVIDENCE_COMPILED:
        if pattern.search(q_lower):
            return QueryIntent.EVIDENCE_EXTRACTION
            
    # Check for explicit synthesis patterns first (highest priority for multi-doc)
    for pattern in _SYNTHESIS_COMPILED:
        if pattern.search(q_lower):
            return QueryIntent.RESEARCH_SYNTHESIS
    
    # Check for explicit summary patterns
    for pattern in _SUMMARY_COMPILED:
        if pattern.search(q_lower):
            return QueryIntent.DOCUMENT_SUMMARY
    
    # Check for factual QA patterns
    for pattern in _FACTUAL_QA_COMPILED:
        if pattern.search(q_lower):
            return QueryIntent.FACTUAL_QA
    
    # ── Stage 3: Heuristic fallbacks ──
    
    # Short question heuristic: if query is short, starts with a question word,
    # and ends with "?" → likely factual QA
    first_word = q_lower.split()[0] if q_lower.split() else ""
    is_question = q.rstrip().endswith("?") or first_word in _QUESTION_WORD_STARTS
    is_short = len(q.split()) <= 15
    
    if is_question and is_short:
        return QueryIntent.FACTUAL_QA
    
    # If a single document is scoped and the query doesn't match synthesis patterns,
    # default to document summary
    if is_single_doc_mode:
        return QueryIntent.DOCUMENT_SUMMARY
    
    # Default: full research synthesis
    return QueryIntent.RESEARCH_SYNTHESIS


def get_intent_display_info(intent: QueryIntent) -> dict:
    """
    Returns display metadata for a given intent (icon, label, description).
    Used by the UI layer to style the response appropriately.
    """
    return {
        QueryIntent.FACTUAL_QA: {
            "icon": "🎯",
            "label": "Direct Answer",
            "description": "Returning a concise factual answer from the retrieved sources.",
            "badge_class": "badge-info",
            "show_pdf": False,
            "show_sections": False,
        },
        QueryIntent.DOCUMENT_SUMMARY: {
            "icon": "📄",
            "label": "Document Summary",
            "description": "Generating a structured summary of the selected document.",
            "badge_class": "badge-pass",
            "show_pdf": True,
            "show_sections": True,
        },
        QueryIntent.RESEARCH_SYNTHESIS: {
            "icon": "🔬",
            "label": "Research Synthesis",
            "description": "Synthesizing a comprehensive research report across multiple sources.",
            "badge_class": "badge-pass",
            "show_pdf": True,
            "show_sections": True,
        },
        QueryIntent.EVIDENCE_EXTRACTION: {
            "icon": "🔍",
            "label": "Evidence Extraction",
            "description": "Extracting evidence-backed facts, page numbers, and supporting quotes.",
            "badge_class": "badge-info",
            "show_pdf": False,
            "show_sections": False,
        },
    }[intent]
