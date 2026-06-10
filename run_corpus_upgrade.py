import os
import csv
import shutil
import subprocess
import sys

from ingest import get_chroma_client, get_collection, clear_collection, add_pdf_to_vector_store, list_documents

PAPERS_DIR = "papers"
CSV_PATH = "papers.csv"

def clean_local_data():
    """Deletes all existing synthetic PDF files and clears the CSV metadata file."""
    print("--- Cleaning Local Data ---")
    if os.path.exists(PAPERS_DIR):
        print(f"Purging contents of directory '{PAPERS_DIR}'...")
        for filename in os.listdir(PAPERS_DIR):
            file_path = os.path.join(PAPERS_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        os.makedirs(PAPERS_DIR, exist_ok=True)
        
    if os.path.exists(CSV_PATH):
        print(f"Removing metadata index file '{CSV_PATH}'...")
        try:
            os.remove(CSV_PATH)
        except Exception as e:
            print(f"Failed to remove {CSV_PATH}. Reason: {e}")

def run_download_papers():
    """Executes the download_real_papers.py script to fetch real academic papers."""
    print("\n--- Running download_real_papers.py ---")
    cmd = [sys.executable, "download_real_papers.py"]
    try:
        # Run process and print output in real-time
        result = subprocess.run(cmd, check=True)
        print("Papers downloaded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing downloader: {e}")
        sys.exit(1)

def ingest_all_papers():
    """Reads papers.csv, clears ChromaDB, and indexes all downloaded papers."""
    print("\n--- Initializing Vector Store Ingestion ---")
    if not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
        print("[ERROR] papers.csv not found or empty. Ingestion aborted.")
        sys.exit(1)
        
    client = get_chroma_client()
    # Reset/clear collection to purge old synthetic entries
    collection = clear_collection(client)
    
    # Read metadata from CSV
    print(f"Reading metadata from '{CSV_PATH}'...")
    papers_metadata = []
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            papers_metadata.append(row)
            
    print(f"Found {len(papers_metadata)} papers in metadata index. Starting ingestion...")
    
    success_count = 0
    total_chunks = 0
    
    for idx, paper in enumerate(papers_metadata):
        pdf_filename = paper.get("pdf_filename")
        if not pdf_filename:
            print(f"[{idx+1}/{len(papers_metadata)}] Skipping '{paper['title'][:40]}': no PDF filename.")
            continue
            
        pdf_path = os.path.join(PAPERS_DIR, pdf_filename)
        if not os.path.exists(pdf_path):
            print(f"[{idx+1}/{len(papers_metadata)}] Skipping '{paper['title'][:40]}': PDF file not found at {pdf_path}.")
            continue
            
        print(f"[{idx+1}/{len(papers_metadata)}] Indexing '{paper['title'][:40]}...'")
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
                
            metadata = {
                "authors": paper.get("authors"),
                "year": paper.get("year"),
                "abstract": paper.get("abstract"),
                "arxiv_id": paper.get("arxiv_id")
            }
            
            doc_id, chunks_count = add_pdf_to_vector_store(
                collection=collection,
                file_bytes=pdf_bytes,
                file_name=pdf_filename,
                metadata=metadata
            )
            
            if chunks_count > 0:
                success_count += 1
                total_chunks += chunks_count
                print(f"  Successfully indexed. Chunks: {chunks_count}")
            else:
                print(f"  [WARNING] No chunks generated for: {pdf_filename}")
                
        except Exception as ingest_err:
            print(f"  [ERROR] Ingestion failed for {pdf_filename}: {ingest_err}")
            
    print("\n--- Ingestion Summary ---")
    print(f"Successfully indexed {success_count}/{len(papers_metadata)} papers.")
    print(f"Total vector database chunks created: {total_chunks}")
    
    # Print database inventory to verify
    docs_inventory = list_documents(collection)
    print(f"Unique documents currently in ChromaDB: {len(docs_inventory)}")

def main():
    print("==================================================")
    print("   NovaRAG Research Corpus Upgrade Orchestrator  ")
    print("==================================================")
    
    # Step 1: Clean local synthetic corpus
    clean_local_data()
    
    # Step 2: Download real research papers
    run_download_papers()
    
    # Step 3: Clear and re-ingest database
    ingest_all_papers()
    
    print("\n==================================================")
    print("         CORPUS UPGRADE RUN COMPLETED!            ")
    print("==================================================")

if __name__ == "__main__":
    main()
