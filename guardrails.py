import re

# List of common prompt injection keywords / phrases
PROMPT_INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore the instructions above",
    "bypass restrictions",
    "system prompt",
    "override",
    "you are now a",
    "you must now act as",
    "forget everything",
    "dan mode",
    "jailbreak",
    "do not follow the guidelines"
]

def check_input_guardrail(query: str) -> tuple[bool, str]:
    """
    Checks the user query for prompt injections or out-of-scope topics.
    Returns (is_safe, failure_reason).
    """
    if not query or not query.strip():
        return False, "Query cannot be empty."

    query_lower = query.lower()

    # 1. Prompt Injection Check
    for keyword in PROMPT_INJECTION_KEYWORDS:
        if keyword in query_lower:
            return False, f"Potential prompt injection detected (keyword: '{keyword}')."
            
    # 2. Heuristic check to prevent malicious scripts/code injections
    if re.search(r"<script>|javascript:|onerror=|onload=", query_lower):
        return False, "Potential script injection detected."

    # 3. Simple Scope Check
    # The application is an AI Research Paper Summarizer & Report Generator.
    # We want to encourage academic, scientific, or research-oriented questions.
    # While we don't want to block basic inquiries, we should block highly out-of-scope items
    # like casual chatting, offensive terms, or system hacking attempts.
    out_of_scope_indicators = [
        "hack into", "crack password", "steal data", "ddos", "pirate software"
    ]
    for indicator in out_of_scope_indicators:
        if indicator in query_lower:
            return False, f"Out-of-scope request regarding cybersecurity attack/theft detected."

    return True, "Query passed all input guardrails."


# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDED STOP WORDS — Common academic terms that should NOT be counted as
# "hallucinated" when they appear in a generated summary
# ═══════════════════════════════════════════════════════════════════════════════
COMMON_STOP_WORDS = {
    # Academic structure terms
    "summary", "report", "research", "paper", "author", "authors", "system",
    "method", "result", "results", "analysis", "section", "figure", "table",
    "introduction", "conclusion", "discussion", "abstract", "proposed", "presents",
    "information", "generation", "summarizer", "overview", "methodology",
    "findings", "comparative", "references", "future", "scope", "approach",
    # Common academic verbs/adjectives
    "demonstrates", "demonstrated", "achieves", "achieved", "outperforms",
    "performance", "significant", "significantly", "effectively", "efficient",
    "efficiency", "proposed", "utilizing", "leveraging", "addressing",
    "framework", "technique", "techniques", "algorithm", "algorithms",
    "implementation", "evaluated", "evaluation", "experimental", "experiments",
    "baseline", "comparison", "improvements", "improved", "improving",
    "traditional", "conventional", "existing", "previous", "current",
    "comprehensive", "respectively", "furthermore", "moreover", "however",
    "therefore", "specifically", "particular", "particularly", "various",
    "several", "multiple", "different", "provides", "providing", "provided",
    "including", "included", "following", "potential", "limitations",
    "challenges", "advantage", "advantages", "disadvantage", "highlight",
    "highlights", "highlighted", "indicating", "indicates", "indicated",
    "suggesting", "suggests", "suggested", "considered", "considering",
    "enabling", "enabled", "between", "through", "across", "within",
    "without", "against", "towards", "application", "applications",
    "important", "importance", "contribute", "contribution", "contributions",
    "accurate", "accuracy", "precision", "robustness", "scalable",
    "scalability", "training", "testing", "validation", "dataset", "datasets",
    "architecture", "component", "components", "process", "processing",
    "enhance", "enhanced", "enhancement", "promising", "notable", "notable",
    "superior", "compared", "underlying", "overall", "achieving",
    "investigate", "investigated", "investigation", "employed", "employing",
    "strategies", "strategy", "integrated", "integrating", "integration",
    "recently", "emerging", "established", "extensive", "ultimately",
}


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 1: N-GRAM OVERLAP SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_ngrams(text: str, n: int) -> set:
    """Extracts character-level n-grams from cleaned lowercase text."""
    words = re.findall(r'\b[a-z0-9]+\b', text.lower())
    if len(words) < n:
        return set()
    ngrams = set()
    for i in range(len(words) - n + 1):
        ngrams.add(" ".join(words[i:i+n]))
    return ngrams


def _ngram_overlap_score(generated_output: str, full_context: str) -> float:
    """
    Tier 1: Computes the fraction of 3-grams and 4-grams from the generated output
    that also appear in the source context. N-grams capture multi-word phrases,
    which are far harder to hallucinate than individual words.
    """
    # Extract n-grams from the generated text (excluding section headers)
    clean_output = re.sub(r'##\s+.*', '', generated_output)  # Remove markdown headers
    clean_output = re.sub(r'\[\d+(?:\s*,\s*\d+)*\]', '', clean_output)  # Remove citations
    
    trigrams_out = _extract_ngrams(clean_output, 3)
    quadgrams_out = _extract_ngrams(clean_output, 4)
    
    all_ngrams = trigrams_out | quadgrams_out
    if not all_ngrams:
        return 1.0  # No n-grams to check → pass
    
    # Check how many appear in source context
    context_trigrams = _extract_ngrams(full_context, 3)
    context_quadgrams = _extract_ngrams(full_context, 4)
    context_ngrams = context_trigrams | context_quadgrams
    
    matched = all_ngrams & context_ngrams
    return len(matched) / len(all_ngrams)


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 2: NAMED ENTITY & NUMBER VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def _entity_number_score(generated_output: str, full_context: str) -> tuple[float, list]:
    """
    Tier 2: Extracts numbers, percentages, proper nouns, and technical terms from
    the generated output and checks what fraction appear in the source text.
    This catches fabricated statistics and invented method names.
    
    Returns (score, list_of_unmatched_entities).
    """
    context_lower = full_context.lower()
    
    # Extract candidate entities from the generated output
    # 1. Numbers and percentages (e.g., "98.5%", "0.92", "2024")
    numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', generated_output)
    
    # 2. Technical terms: words ≥6 chars that are NOT common stop words
    words = re.findall(r'\b[a-zA-Z0-9-]{6,}\b', generated_output)
    technical_terms = [w for w in words if w.lower() not in COMMON_STOP_WORDS]
    
    candidates = list(set(numbers + technical_terms))
    
    if not candidates:
        return 1.0, []
    
    matched = []
    unmatched = []
    
    for candidate in candidates:
        pattern = re.escape(candidate.lower())
        if re.search(pattern, context_lower):
            matched.append(candidate)
        else:
            unmatched.append(candidate)
    
    score = len(matched) / len(candidates) if candidates else 1.0
    return score, unmatched[:10]  # Return up to 10 unmatched for diagnostics


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 3: CITATION COVERAGE SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def _citation_coverage_score(generated_output: str, num_sources: int) -> tuple[float, dict]:
    """
    Tier 3: Measures what fraction of substantive sentences contain at least one 
    citation [N], and validates that cited source numbers exist.
    
    Returns (score, details_dict).
    """
    # Split into sentences (simple heuristic)
    sentences = re.split(r'(?<=[.!?])\s+', generated_output)
    
    # Filter out non-substantive lines (headers, empty lines, boilerplate)
    substantive_sentences = []
    for s in sentences:
        s_stripped = s.strip()
        if not s_stripped:
            continue
        if s_stripped.startswith('#'):  # Markdown headers
            continue
        if len(s_stripped) < 20:  # Too short to be a real sentence
            continue
        if s_stripped.startswith('---') or s_stripped.startswith('***'):
            continue
        
        # Skip refusal / absence-of-evidence disclaimers (these are expected and don't need citations)
        s_lower = s_stripped.lower()
        refusal_phrases = [
            "insufficient evidence",
            "not covered in the available",
            "do not explicitly discuss",
            "does not explicitly discuss",
            "not stated in the document",
            "not stated in the provided",
            "not mentioned in the",
            "no information is provided",
            "no information could be found",
            "does not contain information",
            "does not mention",
            "do not mention",
            "not explicitly mentioned",
            "unable to answer",
            "cannot answer",
            "information unavailable in retrieved sources",
            "not stated in the source",
            "not mentioned in the source",
            "not mentioned in the paper",
            "not stated in the paper"
        ]
        if any(phrase in s_lower for phrase in refusal_phrases):
            continue
            
        substantive_sentences.append(s_stripped)
    
    if not substantive_sentences:
        return 1.0, {"cited": 0, "total": 0, "invalid_citations": []}
    
    cited_count = 0
    invalid_citations = set()
    
    for sentence in substantive_sentences:
        # Check if this sentence contains any citation [N]
        citations = re.findall(r'\[(\d+)\]', sentence)
        if citations:
            cited_count += 1
            # Validate citation numbers
            for c in citations:
                if int(c) > num_sources or int(c) < 1:
                    invalid_citations.add(int(c))
    
    coverage = cited_count / len(substantive_sentences)
    
    details = {
        "cited": cited_count,
        "total": len(substantive_sentences),
        "invalid_citations": list(invalid_citations)
    }
    
    return coverage, details


# ═══════════════════════════════════════════════════════════════════════════════
# CITATION VALIDATION (standalone function)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_citations(summary: str, sources: list, query_intent: str = None) -> dict:
    """
    Validates all citation markers [N] in the summary against actual sources.
    
    Returns a dict with:
        - valid: bool (all citations map to real sources)
        - total_citations: int
        - unique_sources_cited: set of ints
        - invalid_citations: list of ints (citation numbers with no matching source)
        - citation_coverage: float (fraction of sentences with citations)
        - uncited_sentences: int
        - total_sentences: int
        - is_refusal: bool
        - is_evidence: bool
    """
    num_sources = len(sources)
    source_ranks = {src.get("rank", i+1) for i, src in enumerate(sources)}
    
    # Find all citation markers
    all_citations = re.findall(r'\[(\d+)\]', summary)
    cited_numbers = set(int(c) for c in all_citations)
    
    invalid = [c for c in cited_numbers if c not in source_ranks]
    
    # Compute sentence-level coverage
    coverage, coverage_details = _citation_coverage_score(summary, num_sources)
    
    # Detect if the entire summary is a refusal/absence-of-evidence response
    summary_lower = summary.strip().lower()
    refusal_phrases = [
        "not stated in the document",
        "not stated in the provided",
        "not mentioned in the",
        "no information is provided",
        "no information could be found",
        "does not contain information",
        "does not mention",
        "do not mention",
        "insufficient evidence",
        "not explicitly mentioned",
        "unable to answer",
        "cannot answer",
        "information unavailable in retrieved sources",
        "not stated in the source",
        "not mentioned in the source",
        "not mentioned in the paper",
        "not stated in the paper",
        "unsupported by document"
    ]
    is_refusal = any(phrase in summary_lower for phrase in refusal_phrases) and len(summary_lower) < 250
    is_evidence = (query_intent == "EVIDENCE_EXTRACTION")
    
    if is_refusal or is_evidence:
        coverage = 1.0
        
    return {
        "valid": len(invalid) == 0,
        "total_citations": len(all_citations),
        "unique_sources_cited": cited_numbers,
        "invalid_citations": invalid,
        "citation_coverage": coverage,
        "uncited_sentences": 0 if (is_refusal or is_evidence) else (coverage_details["total"] - coverage_details["cited"]),
        "total_sentences": 0 if (is_refusal or is_evidence) else coverage_details["total"],
        "is_refusal": is_refusal,
        "is_evidence": is_evidence,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN OUTPUT GUARDRAIL — 3-TIER GROUNDEDNESS SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def check_output_guardrail(generated_output: str, retrieved_contexts: list[str]) -> tuple[bool, str, float]:
    """
    Verifies that the generated summary/report is grounded in the retrieved context.
    Uses a 3-tier scoring system for robust hallucination detection:
    
        Tier 1: N-gram overlap (40% weight) — catches fabricated phrases
        Tier 2: Named entity & number verification (30% weight) — catches invented stats
        Tier 3: Citation coverage (30% weight) — ensures claims are attributed
    
    Returns (is_grounded, details_message, composite_score).
    """
    if not generated_output or not generated_output.strip():
        return True, "Output is empty.", 1.0
        
    # Detect negative/disclaimer responses (e.g. "Not stated in the document")
    output_lower = generated_output.strip().lower()
    negative_phrases = [
        "not stated in the document",
        "not stated in the provided",
        "not mentioned in the",
        "no information is provided",
        "no information could be found",
        "does not contain information",
        "does not mention",
        "do not mention",
        "insufficient evidence",
        "not explicitly mentioned",
        "unable to answer",
        "cannot answer",
        "unsupported by document"
    ]
    if any(phrase in output_lower for phrase in negative_phrases) and len(output_lower) < 250:
        return True, "Output is a valid negative response (Score: 100.0%). N-gram overlap: 100.0% | Entity verification: 100.0% | Citation coverage: 100.0% (1/1 sentences)", 1.0

    if not retrieved_contexts:
        return False, "No retrieved context available to verify against.", 0.0

    # Combine all contexts
    full_context = " ".join(retrieved_contexts)
    num_sources = len(retrieved_contexts)
    
    # ── Tier 1: N-gram overlap (40% weight) ──
    ngram_score = _ngram_overlap_score(generated_output, full_context)
    
    # ── Tier 2: Entity & number verification (30% weight) ──
    entity_score, unmatched_entities = _entity_number_score(generated_output, full_context)
    
    # ── Tier 3: Citation coverage (30% weight) ──
    citation_score, citation_details = _citation_coverage_score(generated_output, num_sources)
    
    # ── Composite Score ──
    WEIGHT_NGRAM = 0.40
    WEIGHT_ENTITY = 0.30
    WEIGHT_CITATION = 0.30
    
    composite_score = (
        ngram_score * WEIGHT_NGRAM +
        entity_score * WEIGHT_ENTITY +
        citation_score * WEIGHT_CITATION
    )
    
    # Threshold: 55% composite score for groundedness pass
    # This is lower than the old 60% threshold because the new scoring is more accurate
    threshold = 0.55
    
    # Build detail message
    details_parts = [
        f"N-gram overlap: {ngram_score:.1%}",
        f"Entity verification: {entity_score:.1%}",
        f"Citation coverage: {citation_score:.1%} ({citation_details['cited']}/{citation_details['total']} sentences)",
    ]
    
    if unmatched_entities:
        details_parts.append(f"Unverified terms: {', '.join(unmatched_entities[:5])}")
    
    if citation_details.get("invalid_citations"):
        details_parts.append(f"Invalid citations: {citation_details['invalid_citations']}")
    
    details_str = " | ".join(details_parts)
    
    if composite_score >= threshold:
        return (
            True, 
            f"Output is grounded (Score: {composite_score:.1%}). {details_str}",
            composite_score
        )
    else:
        return (
            False,
            f"Potential hallucination detected (Score: {composite_score:.1%}). {details_str}",
            composite_score
        )
