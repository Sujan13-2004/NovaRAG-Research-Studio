import os
import csv
import time
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import sys

PAPERS_DIR = "papers"
CSV_PATH = "papers.csv"
ATOM_NS = "{http://www.w3.org/2005/Atom}"

# We target 20-30 papers. Let's target exactly 25 papers per category.
TARGET_PER_CAT = 25

WEAK_CATEGORIES = {
    "Drug Discovery": [
        ("all:\"drug discovery\" AND (all:\"deep learning\" OR all:\"machine learning\")", 25),
        ("all:\"protein structure prediction\" AND (all:\"deep learning\" OR all:\"neural network\")", 15),
        ("all:\"molecular property prediction\" AND all:\"machine learning\"", 15)
    ],
    "Sepsis Detection": [
        ("all:\"sepsis\" AND (all:\"prediction\" OR all:\"detection\") AND all:\"machine learning\"", 25),
        ("all:\"sepsis\" AND all:\"intensive care\" AND all:\"deep learning\"", 20)
    ],
    "Federated Learning": [
        ("all:\"federated learning\" AND (all:healthcare OR all:medical)", 25),
        ("all:\"privacy preserving\" AND all:\"machine learning\" AND all:medical", 20)
    ],
    "Explainable AI": [
        ("all:\"explainable\" AND all:\"artificial intelligence\" AND (all:medical OR all:clinical)", 25),
        ("all:\"interpretable\" AND all:\"machine learning\" AND (all:medical OR all:clinical)", 20)
    ]
}

def categorize_paper(title: str) -> str:
    """Categorizes a paper by title keywords into one of the research domains."""
    t = title.lower()
    if any(k in t for k in ["llm", "gpt", "language model", "llama", "clinicalgpt",
                             "med-palm", "instruction-tuned", "instruction tuning",
                             "multi-modal medical", "med-halt", "preference optimization",
                             "scaling instruction"]):
        return "LLMs in Healthcare"
    if "federated" in t:
        return "Federated Learning"
    if any(k in t for k in ["explainable", "xai", "interpretab", "shap", "lime",
                             "trustworthy"]):
        return "Explainable AI"
    if any(k in t for k in ["drug discovery", "drug design", "drug-target",
                             "molecular property", "drug screening",
                             "pharmacogenomics", "de novo drug", "drug response",
                             "high-throughput drug"]):
        return "Drug Discovery"
    if "sepsis" in t:
        return "Sepsis Detection"
    if any(k in t for k in ["cardiovascular", "ecg", "cardiology",
                             "electrocardiogram"]):
        return "Cardiovascular"
    if any(k in t for k in ["medical imag", "x-ray", "mri", "radiology",
                             "segmentation", "u-net", "vision transformer",
                             "chest", "diffusion model"]):
        return "Medical Imaging"
    if any(k in t for k in ["cdss", "decision support", "clinical workflow",
                             "medication recommendation", "treatment selection",
                             "treatment plan"]):
        return "Clinical Decision Support"
    if any(k in t for k in ["precision", "personalized", "genomic", "multi-omics",
                             "patient stratification", "oncology"]):
        return "Personalized Medicine"
    if any(k in t for k in ["healthcare", "clinical application", "digital health",
                             "patient care", "health informatics",
                             "health automation", "attention-based model"]):
        return "Healthcare AI"
    return "Other"

def search_arxiv(query, max_results=10):
    encoded_query = urllib.parse.quote(query)
    url = f"http://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
    print(f"  Querying arXiv API: {query[:70]}...", flush=True)
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'NovaRAG-Downloader/2.0 (academic research project)'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
            break
        except Exception as e:
            print(f"    API attempt {attempt + 1} failed: {e}", flush=True)
            if attempt < 2:
                time.sleep(5)
            else:
                return []
                
    try:
        root = ET.fromstring(data)
    except Exception as e:
        print(f"    XML parse error: {e}", flush=True)
        return []
        
    papers = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        try:
            id_elem = entry.find(f"{ATOM_NS}id")
            if id_elem is None or not id_elem.text:
                continue
            arxiv_id = id_elem.text.split("/abs/")[-1]
            arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
            
            title_elem = entry.find(f"{ATOM_NS}title")
            if title_elem is None or not title_elem.text:
                continue
            title = re.sub(r'\s+', ' ', title_elem.text.strip())
            
            authors = []
            for author in entry.findall(f"{ATOM_NS}author"):
                name_elem = author.find(f"{ATOM_NS}name")
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())
            authors_str = ", ".join(authors[:5])
            if len(authors) > 5:
                authors_str += " et al."
                
            abstract_elem = entry.find(f"{ATOM_NS}summary")
            abstract = ""
            if abstract_elem is not None and abstract_elem.text:
                abstract = re.sub(r'\s+', ' ', abstract_elem.text.strip())
                if len(abstract) > 300:
                    abstract = abstract[:297] + "..."
                    
            pub_elem = entry.find(f"{ATOM_NS}published")
            year = pub_elem.text[:4] if (pub_elem is not None and pub_elem.text) else "2023"
            
            pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            papers.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors_str,
                "year": year,
                "abstract": abstract,
                "pdf_url": pdf_link
            })
        except Exception:
            continue
    return papers

def clean_filename(title):
    clean = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
    return clean.replace(" ", "_").strip("_")[:60]

def download_file(url, filepath):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.info().get('Content-Length', 0))
                block_size = 8192
                downloaded = 0
                
                with open(filepath, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        f.write(buffer)
                        downloaded += len(buffer)
                
                if downloaded < 10240:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return False
                return True
        except Exception:
            time.sleep(3)
    return False

def main():
    print("=" * 60, flush=True)
    print("      NovaRAG Weak Category Downloader      ", flush=True)
    print("=" * 60, flush=True)
    
    # 1. Load existing papers.csv
    existing_arxiv_ids = set()
    existing_titles = set()
    existing_papers = []
    
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_papers.append(row)
                aid = row.get("arxiv_id", "").strip()
                if aid:
                    existing_arxiv_ids.add(aid)
                title = row.get("title", "").strip().lower()
                title_norm = re.sub(r'[^a-z0-9]', '', title)
                if title_norm:
                    existing_titles.add(title_norm)
    
    print(f"Loaded {len(existing_papers)} existing papers.", flush=True)
    
    # Calculate counts per category
    cat_counts = {}
    for p in existing_papers:
        cat = categorize_paper(p.get("title", ""))
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        
    print("Current counts in weak categories:", flush=True)
    for cat in WEAK_CATEGORIES:
        print(f"  {cat}: {cat_counts.get(cat, 0)}", flush=True)
        
    # Search and download loop
    new_papers_to_append = []
    
    for cat, queries in WEAK_CATEGORIES.items():
        current_count = cat_counts.get(cat, 0)
        needed = TARGET_PER_CAT - current_count
        if needed <= 0:
            print(f"\nCategory '{cat}' already has {current_count} papers (Target: {TARGET_PER_CAT}). Skipping.", flush=True)
            continue
            
        print(f"\n--- Gathering papers for '{cat}' (Need {needed} more) ---", flush=True)
        candidates = []
        seen_candidates_ids = set()
        
        for query, max_res in queries:
            if len(candidates) >= needed * 2:  # get plenty of candidates
                break
            time.sleep(3)
            results = search_arxiv(query, max_res)
            for p in results:
                aid = p["arxiv_id"]
                title_norm = re.sub(r'[^a-z0-9]', '', p["title"].lower())
                
                # Deduplication checks
                if aid in existing_arxiv_ids or aid in seen_candidates_ids:
                    continue
                if title_norm in existing_titles:
                    continue
                
                # Verify that categorize_paper actually categorizes this paper as the target category
                detected_cat = categorize_paper(p["title"])
                if detected_cat != cat:
                    continue
                    
                seen_candidates_ids.add(aid)
                candidates.append(p)
                
        print(f"Found {len(candidates)} unique new candidate papers for '{cat}'.", flush=True)
        
        # Download PDFs
        downloaded_for_cat = 0
        for p in candidates:
            if downloaded_for_cat >= needed:
                break
                
            arxiv_id = p["arxiv_id"]
            clean_name = clean_filename(p["title"])
            pdf_filename = f"{arxiv_id}_{clean_name}.pdf"
            filepath = os.path.join(PAPERS_DIR, pdf_filename)
            
            print(f"  [{downloaded_for_cat + 1}/{needed}] Downloading: {p['title'][:50]}...", flush=True)
            time.sleep(3.5)
            success = download_file(p["pdf_url"], filepath)
            if success:
                p["pdf_filename"] = pdf_filename
                new_papers_to_append.append(p)
                # Update sets
                existing_arxiv_ids.add(arxiv_id)
                title_norm = re.sub(r'[^a-z0-9]', '', p["title"].lower())
                existing_titles.add(title_norm)
                downloaded_for_cat += 1
            else:
                print(f"    Failed download.", flush=True)
                
        print(f"Successfully downloaded {downloaded_for_cat} new papers for '{cat}'.", flush=True)
        
    if new_papers_to_append:
        print(f"\nAppending {len(new_papers_to_append)} new records to '{CSV_PATH}'...", flush=True)
        with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for p in new_papers_to_append:
                writer.writerow([
                    p["title"],
                    p["authors"],
                    p["year"],
                    p["abstract"],
                    p["arxiv_id"],
                    p["pdf_filename"]
                ])
        print("CSV updated successfully.", flush=True)
    else:
        print("\nNo new papers were downloaded.", flush=True)

if __name__ == "__main__":
    main()
