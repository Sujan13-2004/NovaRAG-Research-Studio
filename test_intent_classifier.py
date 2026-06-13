"""Smoke test for intent classification."""
from intent_classifier import classify_intent, QueryIntent

# ── Hard overrides (should ALWAYS be FACTUAL_QA) ──
test_cases = [
    # Hard overrides
    ("Answer with ONE LINE ONLY. What exact test accuracy percentage was achieved?", True, QueryIntent.FACTUAL_QA),
    ("SHORT ANSWER: What dataset was used?", True, QueryIntent.FACTUAL_QA),
    ("DO NOT SUMMARIZE. What is the author's email?", True, QueryIntent.FACTUAL_QA),
    ("RETURN ONLY THE ANSWER. How many records are in the dataset?", True, QueryIntent.FACTUAL_QA),
    ("If the exact percentage is not present, reply ONLY: Not stated.", True, QueryIntent.FACTUAL_QA),
    
    # Factual QA (no hard override, detected by patterns)
    ("What accuracy was achieved by the CNN model?", False, QueryIntent.FACTUAL_QA),
    ("Who is the corresponding author?", False, QueryIntent.FACTUAL_QA),
    ("How many patients are in the dataset?", False, QueryIntent.FACTUAL_QA),
    ("What is the F1 score?", False, QueryIntent.FACTUAL_QA),
    ("Does this paper mention transfer learning?", False, QueryIntent.FACTUAL_QA),
    
    # Document Summary
    ("Summarize this paper", False, QueryIntent.DOCUMENT_SUMMARY),
    ("Give me a summary of this document", False, QueryIntent.DOCUMENT_SUMMARY),
    ("Explain this uploaded PDF", False, QueryIntent.DOCUMENT_SUMMARY),
    ("What is this paper about?", False, QueryIntent.DOCUMENT_SUMMARY),
    
    # Research Synthesis
    ("Compare these papers on federated learning", False, QueryIntent.RESEARCH_SYNTHESIS),
    ("Generate a literature review on medical imaging", False, QueryIntent.RESEARCH_SYNTHESIS),
    ("Create a research brief on healthcare AI", False, QueryIntent.RESEARCH_SYNTHESIS),
    ("Identify trends across the papers on drug discovery", False, QueryIntent.RESEARCH_SYNTHESIS),
    
    # Evidence Extraction
    ("List 5 facts from the uploaded paper. For each fact provide: Fact, Page number, Supporting quote", False, QueryIntent.EVIDENCE_EXTRACTION),
    ("Extract facts from this paper with supporting quotes", False, QueryIntent.EVIDENCE_EXTRACTION),
    ("Provide evidence and page citation for the sepsis detection results", False, QueryIntent.EVIDENCE_EXTRACTION),
    ("Show facts explicitly stated in the document", False, QueryIntent.EVIDENCE_EXTRACTION),
    
    # Ambiguous → defaults
    ("Attention Mechanism in Transformers", False, QueryIntent.RESEARCH_SYNTHESIS),  # topic query → synthesis
    ("Deep learning for ECG analysis", False, QueryIntent.RESEARCH_SYNTHESIS),  # topic query → synthesis
]

print("Intent Classification Test Results")
print("=" * 75)

passed = 0
failed = 0

for query, is_hard_override, expected in test_cases:
    result = classify_intent(query)
    status = "PASS" if result == expected else "FAIL"
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    override_tag = "(override) " if is_hard_override else ""
    print(f"  [{status}] [{result.value:20s}] {override_tag}{query[:60]}")
    if result != expected:
        print(f"   EXPECTED: {expected.value}")

print(f"\n{'=' * 75}")
print(f"Passed: {passed}/{len(test_cases)} | Failed: {failed}/{len(test_cases)}")
