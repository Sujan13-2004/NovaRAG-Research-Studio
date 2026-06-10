import os
import re
import csv
from ingest import get_chroma_client, get_collection
from app import categorize_paper
from rag_pipeline import get_ranker, clean_text, get_paper_identifiers, load_papers_mapping, clean_inline_citations
from guardrails import check_output_guardrail
from pdf_generator import generate_pdf_report
import google.generativeai as genai

def generate_review():
    print("==================================================")
    print("      Generating Healthcare AI Review Paper       ")
    print("==================================================")
    
    load_papers_mapping()
    client = get_chroma_client()
    collection = get_collection(client)
    
    # 1. Retrieve papers from each of the 3 domains specifically to ensure 3+ unique papers each
    domains_queries = {
        "Federated Learning": "Federated Learning in healthcare privacy preserving collaborative training Fed-BioMed secure",
        "Explainable AI": "Explainable AI clinical models interpretability SHAP LIME trustworthy Grad-CAM XAI",
        "LLMs in Healthcare": "Large Language Models clinical knowledge medicine ClinicalGPT Med-PaLM Med-HALT"
    }
    
    combined_sources = []
    seen_arxiv_ids = set()
    seen_titles = set()
    global_rank = 1
    
    for category, query in domains_queries.items():
        print(f"Retrieving candidate papers for '{category}'...")
        results = collection.query(query_texts=[query], n_results=150)
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        ids = results["ids"][0]
        
        unique_passages = []
        for doc, meta, id_ in zip(documents, metadatas, ids):
            fn = meta.get("title", "Unknown")
            norm_title, arxiv_id = get_paper_identifiers(fn)
            detected_cat = categorize_paper(fn)
            
            # Restrict to matches of target category
            if detected_cat != category:
                continue
                
            is_dup = False
            if arxiv_id and arxiv_id in seen_arxiv_ids:
                is_dup = True
            if norm_title and norm_title in seen_titles:
                is_dup = True
                
            if is_dup:
                continue
                
            if arxiv_id:
                seen_arxiv_ids.add(arxiv_id)
            if norm_title:
                seen_titles.add(norm_title)
                
            unique_passages.append({
                "id": id_,
                "text": clean_text(doc),
                "meta": meta
            })
            if len(unique_passages) >= 4:  # take top 4 unique papers from each domain
                break
                
        # Rerank this domain
        from flashrank import RerankRequest
        ranker = get_ranker()
        rerank_request = RerankRequest(query=query, passages=unique_passages)
        reranked = ranker.rerank(rerank_request)
        
        # Append to combined list
        for p in reranked:
            combined_sources.append({
                "rank": global_rank,
                "id": p["id"],
                "text": p["text"],
                "title": p["meta"].get("title", "Unknown Document"),
                "page": p["meta"].get("page_number", "Unknown"),
                "doc_id": p["meta"].get("document_id", "Unknown"),
                "category": category
            })
            global_rank += 1

    print(f"Total unique papers selected across 3 domains: {len(combined_sources)}")
    for src in combined_sources:
        print(f"  [{src['rank']}] Category: {src['category']} | Title: {src['title']}")

    # 2. Build LLM prompt with strict grounding rules
    context_str = ""
    for src in combined_sources:
        context_str += f"\n--- SOURCE [{src['rank']}]: {src['title']} (Page {src['page']}) ---\n"
        context_str += f"Category Domain: {src['category']}\n"
        context_str += f"Excerpt: {src['text']}\n"
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is not configured.")
        return
        
    genai.configure(api_key=api_key)
    
    system_instruction = (
        "You are an elite academic AI research assistant. Your task is to produce a "
        "professional, balanced research synthesis comparing Federated Learning, "
        "Explainable AI, and Large Language Models in Healthcare using ONLY the provided sources.\n\n"
        "CRITICAL OUTPUT RULES:\n"
        "1. Do ALL of your internal reasoning silently. Do NOT write any reasoning, planning, or chain-of-thought in your output.\n"
        "2. Start your response IMMEDIATELY with the first section header: '## Research Overview'. No introduction/meta-commentary.\n"
        "3. Your output MUST follow this exact structure:\n"
        "   ## Research Overview\n"
        "   ## Methodology\n"
        "   ## Federated Learning\n"
        "   - Definition: (Definition using references)\n"
        "   - Methodology: (Methodology using references)\n"
        "   - Applications: (Applications using references)\n"
        "   - Advantages: (Advantages using references)\n"
        "   - Limitations: (Limitations using references)\n"
        "   ## Explainable AI\n"
        "   - Definition: ...\n"
        "   - Methodology: ...\n"
        "   - Applications: ...\n"
        "   - Advantages: ...\n"
        "   - Limitations: ...\n"
        "   ## Large Language Models\n"
        "   - Definition: ...\n"
        "   - Methodology: ...\n"
        "   - Applications: ...\n"
        "   - Advantages: ...\n"
        "   - Limitations: ...\n"
        "   ## Comparative Analysis\n"
        "   Provide a comprehensive comparative analysis of FL, XAI, and LLMs in Healthcare covering exactly: Privacy, Interpretability, Scalability, Data Requirements, Clinical Adoption, Regulatory Challenges, and Future Potential.\n"
        "   (Include a comparison table in standard HTML format using <table>, <tr>, <th>, <td> tags summarizing these points. Do NOT use markdown pipe/dash syntax, and do NOT use empty spacing or indentation inside the table HTML to avoid repetition bugs).\n"
        "   ## Future Scope\n"
        "   Discuss: Federated Learning, Explainable AI, Multi-modal AI, Privacy-Preserving Healthcare Systems, and Large Biomedical Foundation Models.\n"
        "   ## Conclusion\n"
        "   ## References\n\n"
        "4. Every major claim must be supported by retrieved papers. Cite using bracketed numbers matching the source rank, e.g., [1]. No filename or page in citations.\n"
        "5. If evidence is insufficient, explicitly state it."
    )
    
    prompt = (
        f"Generate a balanced academic review paper based on the following source materials.\n\n"
        f"SOURCE MATERIAL:\n{context_str}\n\n"
        f"Begin your response IMMEDIATELY with '## Research Overview'. "
        f"Ensure equal, detailed coverage of Federated Learning, Explainable AI, and Large Language Models."
    )
    
    MODEL_CANDIDATES = ['gemini-2.0-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-flash']
    summary_text = None
    
    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(
                max_output_tokens=8192,
                temperature=0.2
            ))
            summary_text = response.text
            print(f"Gemini call succeeded with model: {model_name}")
            break
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue
            
    if not summary_text:
        print("[ERROR] Failed to generate summary.")
        return
        
    # Post-process
    overview_match = re.search(r'## Research Overview', summary_text)
    if overview_match:
        summary_text = summary_text[overview_match.start():]
        
    summary_text = clean_inline_citations(summary_text, combined_sources)
    
    # Save the raw markdown summary
    with open("reports/report_academic_comparison.md", "w", encoding="utf-8") as f:
        f.write(summary_text)
        
    # Groundedness Check
    contexts = [s["text"] for s in combined_sources]
    is_grounded, msg, score = check_output_guardrail(summary_text, contexts)
    print(f"\nGroundedness Check:")
    print(f"  Is Grounded: {is_grounded}")
    print(f"  Score: {score:.1%}")
    print(f"  Message: {msg}")
    
    # Generate PDF Report
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, "report_academic_comparison.pdf")
    
    guardrail_results = {
        "input_safe": True,
        "output_safe": is_grounded,
        "output_score": score
    }
    
    try:
        generate_pdf_report(
            output_path=report_path,
            query="Comparison of Federated Learning, Explainable AI, and LLMs in Healthcare",
            summary=summary_text,
            sources=combined_sources,
            guardrail_results=guardrail_results,
            include_excerpts=True
        )
        print(f"\nPDF Report generated successfully at: {report_path} (Size: {os.path.getsize(report_path)/1024:.1f} KB)")
    except Exception as pdf_err:
        print(f"PDF generation crashed: {pdf_err}")
        
    # Print summary to console
    print("\n" + "="*50 + "\nGENERATED REVIEW SUMMARY:\n" + "="*50)
    print(summary_text)

if __name__ == "__main__":
    generate_review()
