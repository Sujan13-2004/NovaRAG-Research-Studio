"""
NovaRAG Research Studio — Shared Helper Functions.

Extracted from the original monolithic app.py. These utility functions
are used across multiple page modules.
"""

import os
import csv


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════
CATEGORY_COLORS = {
    "Healthcare AI":              "#3B82F6",
    "Cardiovascular":             "#EF4444",
    "Sepsis Detection":           "#F59E0B",
    "Drug Discovery":             "#10B981",
    "Explainable AI":             "#8B5CF6",
    "Federated Learning":         "#EC4899",
    "Medical Imaging":            "#0EA5E9",
    "LLMs in Healthcare":         "#6366F1",
    "Clinical Decision Support":  "#F97316",
    "Personalized Medicine":      "#14B8A6",
    "Other":                      "#64748B",
}


def load_papers_csv():
    """Loads papers.csv and returns a list of paper dicts."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "papers.csv")
    papers = []
    if os.path.exists(csv_path):
        try:
            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    papers.append(row)
        except Exception:
            pass
    return papers


def categorize_paper(title: str) -> str:
    """Categorizes a paper by title keywords into one of the 10 research domains."""
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


def get_year_distribution(papers):
    """Returns {year_int: count} sorted by year."""
    years = {}
    for p in papers:
        try:
            yr = int(p.get("year", 0))
            if 2000 <= yr <= 2030:
                years[yr] = years.get(yr, 0) + 1
        except (ValueError, TypeError):
            pass
    return dict(sorted(years.items()))


def get_category_distribution(papers):
    """Returns {category_str: count} sorted descending."""
    cats = {}
    for p in papers:
        cat = categorize_paper(p.get("title", ""))
        cats[cat] = cats.get(cat, 0) + 1
    return dict(sorted(cats.items(), key=lambda x: x[1], reverse=True))


def enrich_docs_with_csv(docs, csv_papers):
    """Cross-references ChromaDB docs with papers.csv for richer metadata."""
    lookup = {}
    for p in csv_papers:
        fn = p.get("pdf_filename", "").strip()
        if fn:
            lookup[fn] = p

    enriched = []
    for doc in docs:
        title = doc.get("title", "")
        info = lookup.get(title, {})
        enriched.append({
            **doc,
            "paper_title": info.get("title", title.replace(".pdf", "").replace("_", " ")),
            "authors": info.get("authors", "Unknown"),
            "year": info.get("year", "—"),
            "category": categorize_paper(info.get("title", title)),
        })
    return enriched
