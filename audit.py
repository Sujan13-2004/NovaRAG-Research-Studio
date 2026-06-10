import os
import csv
from ingest import get_chroma_client, get_collection, list_documents
from app import categorize_paper

def audit_database():
    print("==================================================")
    print("            NovaRAG Database Auditor              ")
    print("==================================================")

    # 1. Load papers.csv
    csv_path = "papers.csv"
    csv_papers = []
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_papers = list(reader)
    print(f"Loaded {len(csv_papers)} papers from metadata CSV ({csv_path}).")

    # 2. Load ChromaDB
    client = get_chroma_client()
    collection = get_collection(client)
    chroma_docs = list_documents(collection)
    print(f"Loaded {len(chroma_docs)} unique documents from ChromaDB.")

    # 3. Category distribution (papers & pages)
    category_papers = {}
    category_pages = {}
    
    # We will build a lookup of ChromaDB documents by their filename/source to get page count
    chroma_lookup = {d["title"]: d for d in chroma_docs}

    duplicates_by_title = {}
    duplicates_by_arxiv = {}
    incorrect_metadata = []
    missing_files = []

    for idx, row in enumerate(csv_papers):
        title = row.get("title", "").strip()
        arxiv_id = row.get("arxiv_id", "").strip()
        pdf_filename = row.get("pdf_filename", "").strip()
        authors = row.get("authors", "").strip()
        year = row.get("year", "").strip()
        abstract = row.get("abstract", "").strip()

        # Categorize
        category = categorize_paper(title)
        category_papers[category] = category_papers.get(category, 0) + 1

        # Page count
        page_count = 0
        if pdf_filename in chroma_lookup:
            page_count = chroma_lookup[pdf_filename]["total_pages"]
        category_pages[category] = category_pages.get(category, 0) + page_count

        # Check duplicates
        if title:
            duplicates_by_title.setdefault(title.lower(), []).append(pdf_filename)
        if arxiv_id:
            duplicates_by_arxiv.setdefault(arxiv_id, []).append(pdf_filename)

        # Check incorrect metadata
        errors = []
        if not title:
            errors.append("Missing Title")
        if not authors or authors == "Unknown":
            errors.append("Missing/Unknown Authors")
        if not year or not year.isdigit() or not (2000 <= int(year) <= 2030):
            errors.append(f"Invalid Year ('{year}')")
        if not abstract:
            errors.append("Missing Abstract")
        if not arxiv_id:
            errors.append("Missing arXiv ID")
        if not pdf_filename:
            errors.append("Missing PDF Filename")
        else:
            pdf_path = os.path.join("papers", pdf_filename)
            if not os.path.exists(pdf_path):
                missing_files.append(pdf_filename)
                errors.append("PDF file not found in /papers")

        if errors:
            incorrect_metadata.append({
                "row": idx + 2,
                "title": title[:50],
                "errors": errors
            })

    # Show category stats
    print("\n--- 1. Number of Papers & Pages per Category ---")
    all_categories = set(category_papers.keys()) | {"Drug Discovery", "Sepsis Detection", "Federated Learning", "Explainable AI"}
    weak_categories = []
    
    print(f"{'Category':<30} | {'Papers':<8} | {'Pages':<8}")
    print("-" * 52)
    for cat in sorted(all_categories):
        p_count = category_papers.get(cat, 0)
        pg_count = category_pages.get(cat, 0)
        print(f"{cat:<30} | {p_count:<8} | {pg_count:<8}")
        if p_count < 20:
            weak_categories.append((cat, p_count))

    # Show duplicates
    print("\n--- 2. Duplicate Papers ---")
    dup_titles = {t: filenames for t, filenames in duplicates_by_title.items() if len(filenames) > 1}
    dup_arxivs = {a: filenames for a, filenames in duplicates_by_arxiv.items() if len(filenames) > 1}
    
    print(f"Duplicates by Title: {len(dup_titles)}")
    for t, filenames in dup_titles.items():
        print(f"  - Title: '{t}' -> Files: {filenames}")
        
    print(f"Duplicates by arXiv ID: {len(dup_arxivs)}")
    for a, filenames in dup_arxivs.items():
        print(f"  - arXiv ID: {a} -> Files: {filenames}")

    # Show incorrect metadata
    print("\n--- 3. Incorrect Metadata ---")
    print(f"Found {len(incorrect_metadata)} rows with metadata issues:")
    for item in incorrect_metadata[:15]:
        print(f"  - Row {item['row']} | Title: '{item['title']}...' | Issues: {', '.join(item['errors'])}")
    if len(incorrect_metadata) > 15:
        print(f"  ... and {len(incorrect_metadata) - 15} more.")

    # Show categories with fewer than 20 papers
    print("\n--- 4. Categories with Fewer than 20 Papers (Weak Categories) ---")
    for cat, p_count in weak_categories:
        print(f"  - {cat}: {p_count} papers (Needs at least {20 - p_count} more to hit 20)")

if __name__ == "__main__":
    audit_database()
