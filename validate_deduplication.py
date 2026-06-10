import os
from dotenv import load_dotenv
load_dotenv()

from rag_pipeline import run_rag_query
from pdf_generator import format_citation

def validate():
    queries = [
        "How are transformer models used in healthcare and biomedical research?",
        "Compare cardiovascular risk prediction and sepsis detection using AI.",
        "How is AI transforming drug discovery and target identification?"
    ]
    
    print("=" * 80)
    print("  NOVARAG RAG PIPELINE DEDUPLICATION VALIDATION")
    print("=" * 80)
    
    for idx, query in enumerate(queries, 1):
        print(f"\nQUERY {idx}: {query}")
        print("-" * 80)
        
        # Run query through RAG pipeline (this will perform deduplication and reranking)
        result = run_rag_query(
            query=query,
            api_key=os.getenv("GEMINI_API_KEY"),
            top_k_retrieve=15,
            top_n_rerank=5
        )
        
        retrieved_count = result.get("chunks_retrieved_count", 0)
        unique_count = result.get("unique_papers_count", 0)
        duplicates_removed = result.get("duplicates_removed_count", 0)
        
        print(f"  * Retrieved chunks count:    {retrieved_count}")
        print(f"  * Unique papers count:       {unique_count}")
        print(f"  * Duplicate papers removed:  {duplicates_removed}")
        print(f"  * Final reference list:")
        
        # Output clean list of references
        raw_chunks = result.get("raw_chunks", [])
        seen_citations = set()
        has_duplicates = False
        
        for chunk in raw_chunks:
            title = chunk.get("title", "Unknown")
            citation = format_citation(title)
            
            # Check for duplicate citations
            if citation in seen_citations:
                has_duplicates = True
            seen_citations.add(citation)
            
            print(f"    [{chunk['rank']}] {citation}")
            
        if has_duplicates:
            print("    [WARNING] Duplicate references detected in the final reference list!")
        else:
            print("    [SUCCESS] No duplicate references found.")

if __name__ == "__main__":
    validate()
