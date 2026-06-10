import os
import csv

# Check papers directory
papers_dir = "papers"
files = [f for f in os.listdir(papers_dir) if f.endswith('.pdf')]
sizes = [os.path.getsize(os.path.join(papers_dir, f)) for f in files]
print(f"Papers directory: {len(files)} PDFs, total {sum(sizes)//1024//1024}MB")

# Check CSV
csv_path = "papers.csv"
if os.path.exists(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print(f"papers.csv: {len(rows)} rows")
else:
    print("papers.csv: NOT FOUND")

# Check ChromaDB state
from ingest import get_chroma_client, get_collection, list_documents
client = get_chroma_client()
collection = get_collection(client)
all_items = collection.get(include=["metadatas"])
total_chunks = len(all_items.get("ids", []))
docs = list_documents(collection)
print(f"ChromaDB: {len(docs)} unique documents, {total_chunks} total chunks")
