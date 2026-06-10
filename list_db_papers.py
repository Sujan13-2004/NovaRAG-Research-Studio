from ingest import get_chroma_client, get_collection, list_documents
from app import categorize_paper
from collections import defaultdict

client = get_chroma_client()
collection = get_collection(client)
docs = list_documents(collection)

cats = defaultdict(list)
for d in docs:
    title = d["title"]
    cat = categorize_paper(title)
    cats[cat].append(title)

for cat, titles in cats.items():
    print(f"\nCategory: {cat} ({len(titles)} papers)")
    for t in titles[:5]:
        print(f"  - {t}")
    if len(titles) > 5:
        print(f"  - ... and {len(titles)-5} more")
