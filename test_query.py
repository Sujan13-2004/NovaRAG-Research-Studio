"""Quick test script to validate structured output from the RAG pipeline."""
import os
import re
from dotenv import load_dotenv
load_dotenv()

from rag_pipeline import run_rag_query

def test_structured_output():
    query = "How is AI transforming drug discovery and target identification?"
    
    print(f"{'='*70}")
    print(f"  TESTING QUERY: '{query}'")
    print(f"{'='*70}\n")
    
    result = run_rag_query(
        query=query,
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
    print(f"Status: {result['status']}")
    print(f"Chunks retrieved: {len(result['raw_chunks'])}")
    
    print(f"\n{'-'*70}")
    print(f"  REASONING FLOW (user-facing)")
    print(f"{'-'*70}")
    print(result["thinking"])
    
    print(f"\n{'-'*70}")
    print(f"  SYNTHESIS SUMMARY (user-facing)")
    print(f"{'-'*70}")
    print(result["summary"])
    
    # ── VALIDATION ──
    summary = result["summary"]
    thinking = result["thinking"]
    
    print(f"\n{'='*70}")
    print(f"  VALIDATION RESULTS")
    print(f"{'='*70}")
    
    all_pass = True
    
    # 1. No <thinking> tags in summary
    has_thinking_tags = "<thinking>" in summary.lower() or "</thinking>" in summary.lower()
    status = "FAIL" if has_thinking_tags else "PASS"
    if has_thinking_tags: all_pass = False
    print(f"  [{status}] No <thinking> tags in summary")
    
    # 2. No CoT leak phrases in summary
    cot_phrases = [
        "the user wants", "i need to", "let me", "my analysis",
        "snippet 1", "snippet 2", "snippet 3",
        "plan:", "step 1:", "step 2:", "internal analysis",
        "i will", "i should", "first, i"
    ]
    leaked = [p for p in cot_phrases if p in summary.lower()]
    status = "FAIL" if leaked else "PASS"
    if leaked: all_pass = False
    print(f"  [{status}] No CoT leak phrases in summary" + (f" (found: {leaked})" if leaked else ""))
    
    # 3. Summary starts with '## Research Overview'
    starts_correct = summary.strip().startswith("## Research Overview")
    status = "PASS" if starts_correct else "WARN"
    if not starts_correct: all_pass = False
    print(f"  [{status}] Summary starts with '## Research Overview'")
    
    # 4. Required academic sections present
    required_sections = [
        "Research Overview", 
        "Methodology", 
        "Key Findings", 
        "Comparative Analysis", 
        "Future Scope", 
        "Conclusion", 
        "References"
    ]
    for section in required_sections:
        found = f"## {section}" in summary
        status = "PASS" if found else "FAIL"
        if not found: all_pass = False
        print(f"  [{status}] Required section '## {section}' present")
        
    # 5. Citation format validation: brackets must be numeric only
    # e.g., no [2406.10064_AI-Driven_Drug_Discovery..., Page 1]
    verbose_citations = re.findall(r'\[\s*[^\]]*?(?:\.pdf|Page|arXiv|_|Drug|Discovery)[^\]]*?\]', summary)
    status = "FAIL" if verbose_citations else "PASS"
    if verbose_citations: 
        all_pass = False
    print(f"  [{status}] In-text citations are clean brackets (found invalid: {verbose_citations})")
    
    # 6. Reasoning flow is a short clean message
    is_short = len(thinking) < 200
    no_cot_in_thinking = not any(p in thinking.lower() for p in ["the user wants", "i need to", "snippet"])
    status = "PASS" if (is_short and no_cot_in_thinking) else "FAIL"
    if not (is_short and no_cot_in_thinking): all_pass = False
    print(f"  [{status}] Reasoning flow is a short, clean message ({len(thinking)} chars)")
    
    # Final verdict
    print(f"\n{'='*70}")
    verdict = "ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED"
    print(f"  VERDICT: {verdict}")
    print(f"{'='*70}")

    # Generate the PDF report for manual inspection
    if all_pass:
        try:
            from pdf_generator import generate_pdf_report
            os.makedirs("reports", exist_ok=True)
            report_path = "reports/drug_discovery_report.pdf"
            
            # Use test guardrail data
            guardrail_data = {
                "input_safe": True,
                "output_safe": True,
                "output_score": 0.95
            }
            
            generate_pdf_report(
                output_path=report_path,
                query=query,
                summary=summary,
                sources=result["raw_chunks"],
                guardrail_results=guardrail_data,
                include_excerpts=False # Compact (4-5 pages max)
            )
            print(f"\n[PASS] Academic PDF report successfully compiled at: {os.path.abspath(report_path)}")
        except Exception as e:
            print(f"\n[FAIL] Academic PDF report compilation failed: {e}")

if __name__ == "__main__":
    test_structured_output()

