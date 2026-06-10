from ingest import get_chroma_client, get_collection
from app import categorize_paper
from rag_pipeline import get_paper_identifiers, load_papers_mapping

load_papers_mapping()
client = get_chroma_client()
collection = get_collection(client)

query = "Large Language Models clinical knowledge medicine ClinicalGPT Med-PaLM Med-HALT"
results = collection.query(query_texts=[query], n_results=150)

documents = results["documents"][0]
metadatas = results["metadatas"][0]
ids = results["ids"][0]

seen = set()
for doc, meta, id_ in zip(documents, metadatas, ids):
    fn = meta.get("title", "Unknown")
    detected_cat = categorize_paper(fn)
    norm_title, arxiv_id = get_paper_identifiers(fn)
    if detected_cat == "LLMs in Healthcare":
        if norm_title not in seen:
            seen.add(norm_title)
            print(f"Paper: {fn} | Arxiv ID: {arxiv_id}")
