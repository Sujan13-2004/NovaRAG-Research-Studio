import os
import shutil
from ingest import get_chroma_client, get_collection
from app import categorize_paper
from rag_pipeline import get_ranker, clean_text, get_paper_identifiers, load_papers_mapping
from guardrails import check_output_guardrail
from pdf_generator import generate_pdf_report

shutil.copy("reports/test_raw.md", "reports/report_academic_comparison.md")
print("Copied test_raw.md to report_academic_comparison.md")

with open("reports/report_academic_comparison.md", "r", encoding="utf-8") as f:
    summary_text = f.read()

load_papers_mapping()
client = get_chroma_client()
collection = get_collection(client)

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
    results = collection.query(query_texts=[query], n_results=150)
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    ids = results["ids"][0]
    
    unique_passages = []
    for doc, meta, id_ in zip(documents, metadatas, ids):
        fn = meta.get("title", "Unknown")
        norm_title, arxiv_id = get_paper_identifiers(fn)
        detected_cat = categorize_paper(fn)
        
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
        if len(unique_passages) >= 4:
            break
            
    from flashrank import RerankRequest
    ranker = get_ranker()
    rerank_request = RerankRequest(query=query, passages=unique_passages)
    reranked = ranker.rerank(rerank_request)
    
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

# Groundedness check
contexts = [s["text"] for s in combined_sources]
is_grounded, msg, score = check_output_guardrail(summary_text, contexts)
print(f"Groundedness: {is_grounded} ({score:.1%}) - {msg}")

guardrail_results = {
    "input_safe": True,
    "output_safe": is_grounded,
    "output_score": score
}

pdf_path = "reports/report_academic_comparison.pdf"
generate_pdf_report(
    output_path=pdf_path,
    query="Comparison of Federated Learning, Explainable AI, and LLMs in Healthcare",
    summary=summary_text,
    sources=combined_sources,
    guardrail_results=guardrail_results,
    include_excerpts=True
)
print(f"PDF generated successfully at: {pdf_path} (Size: {os.path.getsize(pdf_path)/1024:.1f} KB)")
