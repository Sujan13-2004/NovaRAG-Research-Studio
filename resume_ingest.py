"""Indexes only the papers from papers.csv that are NOT already in ChromaDB."""
import os
import csv
from ingest import get_chroma_client, get_collection, add_pdf_to_vector_store, list_documents

PAPERS_DIR = "papers"
CSV_PATH = "papers.csv"

def main():
    print("=== Resuming Ingestion for Missing Papers ===")
    
    client = get_chroma_client()
    collection = get_collection(client)
    
    # Get already-indexed document IDs
    existing_docs = list_documents(collection)
    existing_titles = set(d["title"] for d in existing_docs)
    print(f"Already indexed: {len(existing_docs)} documents")
    
    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        papers = list(csv.DictReader(f))
    print(f"Total papers in CSV: {len(papers)}")
    
    # Filter to only missing papers
    missing = [p for p in papers if p.get("pdf_filename", "") not in existing_titles]
    print(f"Papers to index: {len(missing)}")
    
    success = 0
    total_chunks = 0
    
    for idx, paper in enumerate(missing):
        pdf_filename = paper.get("pdf_filename", "")
        if not pdf_filename:
            continue
        pdf_path = os.path.join(PAPERS_DIR, pdf_filename)
        if not os.path.exists(pdf_path):
            print(f"[{idx+1}/{len(missing)}] SKIP - file not found: {pdf_filename}")
            continue
            
        print(f"[{idx+1}/{len(missing)}] Indexing: {paper['title'][:50]}...")
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            metadata = {
                "authors": paper.get("authors"),
                "year": paper.get("year"),
                "abstract": paper.get("abstract"),
                "arxiv_id": paper.get("arxiv_id")
            }
            
            doc_id, chunks = add_pdf_to_vector_store(
                collection=collection,
                file_bytes=pdf_bytes,
                file_name=pdf_filename,
                metadata=metadata
            )
            
            if chunks > 0:
                success += 1
                total_chunks += chunks
                print(f"  OK: {chunks} chunks")
            else:
                print(f"  WARNING: 0 chunks generated")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print(f"\n=== Resume Complete ===")
    print(f"Newly indexed: {success} papers, {total_chunks} chunks")
    
    # Final stats
    final_docs = list_documents(collection)
    final_all = collection.get(include=["metadatas"])
    print(f"Total in ChromaDB: {len(final_docs)} documents, {len(final_all['ids'])} chunks")

if __name__ == "__main__":
    main()
