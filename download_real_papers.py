"""
NovaRAG Real Paper Downloader v2.0
===================================
Downloads verified research papers from arXiv using the official API.
Searches by topic keywords to guarantee all papers are real and accessible.

Categories:
  - Healthcare AI (Cardiovascular, Sepsis, Clinical Decision Support, Medical Imaging, Disease Prediction)
  - Drug Discovery (AI Drug Discovery, Target ID, Drug Repurposing, Protein Structure)
  - LLMs in Healthcare (ClinicalGPT, Med-PaLM, BioGPT, GPT-4 Healthcare)
  - Federated Learning (Federated Healthcare, Privacy-Preserving Medical AI)
  - Explainable AI (Explainable Clinical Models, Medical Decision Explainability)
"""

import os
import csv
import sys
import time
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

PAPERS_DIR = "papers"
CSV_PATH = "papers.csv"
TARGET_COUNT = 140

# Namespace for arXiv Atom feed
ATOM_NS = "{http://www.w3.org/2005/Atom}"

# ─────────────────────────────────────────────────────────────────────────────
# Topic search queries: (arXiv_query, max_results, category_label)
# ─────────────────────────────────────────────────────────────────────────────
TOPIC_SEARCHES = [
    # ── Healthcare AI (target ~50 papers) ──
    (
        "all:\"deep learning\" AND all:healthcare AND all:clinical",
        12, "Healthcare AI"
    ),
    (
        "all:\"machine learning\" AND all:\"medical diagnosis\"",
        8, "Healthcare AI"
    ),
    (
        "all:\"medical imaging\" AND all:\"deep learning\" AND (all:classification OR all:segmentation)",
        12, "Medical Imaging"
    ),
    (
        "all:\"cardiovascular\" AND (all:\"risk prediction\" OR all:\"ECG\" OR all:\"electrocardiogram\") AND all:\"deep learning\"",
        10, "Cardiovascular Risk Prediction"
    ),
    (
        "all:\"sepsis\" AND (all:\"prediction\" OR all:\"detection\" OR all:\"early warning\") AND all:\"machine learning\"",
        10, "Sepsis Detection"
    ),
    (
        "all:\"clinical decision support\" AND (all:\"machine learning\" OR all:\"deep learning\")",
        8, "Clinical Decision Support"
    ),

    # ── Drug Discovery (target ~30 papers) ──
    (
        "all:\"drug discovery\" AND (all:\"deep learning\" OR all:\"machine learning\")",
        10, "Drug Discovery"
    ),
    (
        "all:\"drug target\" AND all:\"deep learning\"",
        6, "Drug Discovery"
    ),
    (
        "all:\"drug repurposing\" AND all:\"artificial intelligence\"",
        6, "Drug Discovery"
    ),
    (
        "all:\"protein structure prediction\" AND (all:\"deep learning\" OR all:\"neural network\")",
        8, "Drug Discovery"
    ),

    # ── LLMs in Healthcare (target ~20 papers) ──
    (
        "all:\"large language model\" AND (all:medical OR all:clinical OR all:healthcare)",
        12, "LLMs in Healthcare"
    ),
    (
        "all:\"biomedical\" AND (all:\"language model\" OR all:\"NLP\") AND all:\"transformer\"",
        10, "LLMs in Healthcare"
    ),

    # ── Federated Learning (target ~20 papers) ──
    (
        "all:\"federated learning\" AND (all:healthcare OR all:medical OR all:clinical)",
        12, "Federated Learning"
    ),
    (
        "all:\"privacy preserving\" AND all:\"machine learning\" AND all:medical",
        10, "Federated Learning"
    ),

    # ── Explainable AI (target ~20 papers) ──
    (
        "all:\"explainable\" AND all:\"artificial intelligence\" AND (all:medical OR all:clinical)",
        12, "Explainable AI"
    ),
    (
        "all:\"interpretable\" AND all:\"machine learning\" AND (all:medical OR all:clinical OR all:healthcare)",
        10, "Explainable AI"
    ),
]


def search_arxiv(query, max_results=10):
    """Search arXiv API and return list of paper metadata dicts."""
    encoded_query = urllib.parse.quote(query)
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={encoded_query}"
        f"&start=0&max_results={max_results}"
        f"&sortBy=relevance&sortOrder=descending"
    )

    print(f"  Querying arXiv API: {query[:70]}...")

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'NovaRAG-Downloader/2.0 (academic research project)'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
            break
        except Exception as e:
            print(f"    API attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(5)
            else:
                print(f"    Giving up on this search query.")
                return []

    # Parse Atom XML response
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        print(f"    XML parse error: {e}")
        return []

    papers = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        try:
            # Extract arXiv ID from the id URL
            id_elem = entry.find(f"{ATOM_NS}id")
            if id_elem is None or id_elem.text is None:
                continue
            id_url = id_elem.text
            arxiv_id = id_url.split("/abs/")[-1]
            # Remove version suffix (e.g., v1, v2)
            arxiv_id = re.sub(r'v\d+$', '', arxiv_id)

            # Title
            title_elem = entry.find(f"{ATOM_NS}title")
            if title_elem is None or title_elem.text is None:
                continue
            title = title_elem.text.strip()
            title = re.sub(r'\s+', ' ', title)

            # Authors (take first 5, then "et al.")
            authors = []
            for author in entry.findall(f"{ATOM_NS}author"):
                name_elem = author.find(f"{ATOM_NS}name")
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())
            authors_str = ", ".join(authors[:5])
            if len(authors) > 5:
                authors_str += " et al."

            # Abstract (truncate to ~300 chars for CSV storage)
            abstract_elem = entry.find(f"{ATOM_NS}summary")
            abstract = ""
            if abstract_elem is not None and abstract_elem.text:
                abstract = abstract_elem.text.strip()
                abstract = re.sub(r'\s+', ' ', abstract)
                if len(abstract) > 300:
                    abstract = abstract[:297] + "..."

            # Year from published date
            pub_elem = entry.find(f"{ATOM_NS}published")
            year = "2023"
            if pub_elem is not None and pub_elem.text:
                year = pub_elem.text[:4]

            # PDF link
            pdf_link = None
            for link in entry.findall(f"{ATOM_NS}link"):
                if link.get("title") == "pdf":
                    pdf_link = link.get("href")
                    break
            if not pdf_link:
                pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            papers.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors_str,
                "year": year,
                "abstract": abstract,
                "pdf_url": pdf_link
            })
        except Exception as parse_err:
            print(f"    Skipping entry due to parse error: {parse_err}")
            continue

    print(f"    Found {len(papers)} papers")
    return papers


def clean_filename(title):
    """Cleans a title string to be safe for Windows file paths."""
    clean = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
    return clean.replace(" ", "_").strip("_")[:60]


def download_file(url, filepath):
    """Downloads a file with retries and progress display."""
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

                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            sys.stdout.write(
                                f"\r  Downloading... {percent:.1f}% "
                                f"({downloaded // 1024}KB/{total_size // 1024}KB)"
                            )
                        else:
                            sys.stdout.write(
                                f"\r  Downloading... {downloaded // 1024}KB loaded"
                            )
                        sys.stdout.flush()
                sys.stdout.write("\n")

                # Validate it's a real PDF (not an HTML error page)
                if downloaded < 10240:
                    print(f"  [WARNING] File too small ({downloaded} bytes), likely an error page.")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return False

                return True
        except Exception as e:
            print(f"\n  [ERROR] Attempt {attempt + 1} download failed: {e}")
            if attempt < 2:
                time.sleep(3)
    return False


def main():
    print("=" * 60)
    print("  NovaRAG Real Paper Downloader v2.0")
    print("  Using arXiv API for verified academic papers")
    print("=" * 60)

    os.makedirs(PAPERS_DIR, exist_ok=True)

    # ── Phase 1: Search arXiv API ──
    print("\n--- Phase 1: Searching arXiv API for papers ---")
    all_papers = []
    seen_ids = set()
    category_counts = {}

    for query, max_results, category in TOPIC_SEARCHES:
        time.sleep(3)  # Respect arXiv API rate limits (max 1 req / 3 sec)
        results = search_arxiv(query, max_results)

        for paper in results:
            aid = paper["arxiv_id"]
            if aid not in seen_ids:
                seen_ids.add(aid)
                paper["category"] = category
                all_papers.append(paper)
                category_counts[category] = category_counts.get(category, 0) + 1

    print(f"\nTotal unique papers found via API: {len(all_papers)}")
    print("Category breakdown:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")

    if len(all_papers) < 10:
        print("\n[ERROR] Too few papers found from arXiv API. Check network connection.")
        sys.exit(1)

    # ── Phase 2: Download PDFs ──
    print(f"\n--- Phase 2: Downloading PDFs (target: {TARGET_COUNT}) ---")
    downloaded_papers = []
    success_count = 0
    skip_count = 0
    fail_count = 0

    for idx, paper in enumerate(all_papers):
        if success_count >= TARGET_COUNT:
            print(f"\n[DONE] Target count of {TARGET_COUNT} papers reached!")
            break

        arxiv_id = paper["arxiv_id"]
        clean_name = clean_filename(paper["title"])
        pdf_filename = f"{arxiv_id}_{clean_name}.pdf"
        filepath = os.path.join(PAPERS_DIR, pdf_filename)

        # Check if already downloaded
        if os.path.exists(filepath) and os.path.getsize(filepath) > 10240:
            print(
                f"[{success_count + 1}/{TARGET_COUNT}] "
                f"Already exists: '{paper['title'][:50]}...'"
            )
            paper["pdf_filename"] = pdf_filename
            downloaded_papers.append(paper)
            success_count += 1
            skip_count += 1
            continue

        print(
            f"[{success_count + 1}/{TARGET_COUNT}] "
            f"Fetching: '{paper['title'][:50]}...' "
            f"(arXiv:{arxiv_id})"
        )

        pdf_url = paper.get("pdf_url", f"https://arxiv.org/pdf/{arxiv_id}.pdf")

        time.sleep(3.5)  # Polite delay for arXiv servers
        dl_success = download_file(pdf_url, filepath)

        if dl_success:
            paper["pdf_filename"] = pdf_filename
            downloaded_papers.append(paper)
            success_count += 1
        else:
            print(f"  Failed to download PDF for arXiv:{arxiv_id}")
            fail_count += 1

    # ── Phase 3: Write metadata CSV ──
    print(f"\n--- Phase 3: Writing Metadata to '{CSV_PATH}' ---")
    with open(CSV_PATH, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "title", "authors", "year", "abstract",
            "arxiv_id", "pdf_filename", "category"
        ])
        for paper in downloaded_papers:
            writer.writerow([
                paper["title"],
                paper["authors"],
                paper["year"],
                paper["abstract"],
                paper["arxiv_id"],
                paper["pdf_filename"],
                paper.get("category", "Other")
            ])

    # ── Final Summary ──
    final_cats = {}
    for p in downloaded_papers:
        cat = p.get("category", "Other")
        final_cats[cat] = final_cats.get(cat, 0) + 1

    print(f"\n{'=' * 60}")
    print(f"  DOWNLOAD COMPLETE!")
    print(f"{'=' * 60}")
    print(f"  Total downloaded: {success_count}")
    print(f"  Already existed:  {skip_count}")
    print(f"  Failed:           {fail_count}")
    print(f"  Category breakdown:")
    for cat, count in sorted(final_cats.items()):
        print(f"    {cat}: {count}")
    print(f"  Metadata: {CSV_PATH}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
