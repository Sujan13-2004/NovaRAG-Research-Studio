import os
import csv
import datetime
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from ingest import (
    get_chroma_client,
    get_collection,
    add_pdf_to_vector_store,
    delete_document,
    list_documents
)
from rag_pipeline import run_rag_query
from guardrails import check_input_guardrail, check_output_guardrail
from pdf_generator import generate_pdf_report


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="NovaRAG | Research Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)


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


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def load_papers_csv():
    """Loads papers.csv and returns a list of paper dicts."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papers.csv")
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


def create_donut_chart(categories):
    """Creates a Plotly donut chart for paper categories."""
    labels = list(categories.keys())
    values = list(categories.values())
    colors = [CATEGORY_COLORS.get(c, "#64748B") for c in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.58,
        marker=dict(colors=colors, line=dict(color="#0F172A", width=2)),
        textinfo="percent",
        textfont=dict(size=11, color="#CBD5E1", family="Inter"),
        hovertemplate="<b>%{label}</b><br>Papers: %{value}<br>Share: %{percent}<extra></extra>",
        direction="clockwise",
        sort=False,
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", family="Inter"),
        showlegend=True,
        legend=dict(
            font=dict(size=10, color="#94A3B8"),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom", y=-0.35,
            xanchor="center", x=0.5,
        ),
        margin=dict(l=10, r=10, t=10, b=70),
        height=340,
    )
    return fig


def create_area_chart(year_dist):
    """Creates a Plotly area chart for papers published per year."""
    years = list(year_dist.keys())
    counts = list(year_dist.values())

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=counts,
        fill="tozeroy",
        line=dict(color="#8B5CF6", width=2.5),
        fillcolor="rgba(139,92,246,0.12)",
        mode="lines+markers",
        marker=dict(size=7, color="#A78BFA",
                    line=dict(color="#0F172A", width=1.5)),
        hovertemplate="<b>%{x}</b><br>Papers: %{y}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#64748B",
                   gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=11), dtick=1),
        yaxis=dict(color="#64748B",
                   gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=11)),
        font=dict(color="#CBD5E1", family="Inter"),
        margin=dict(l=40, r=20, t=10, b=40),
        height=340,
        hovermode="x unified",
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS — DARK DASHBOARD THEME
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Orbitron:wght@700;900&family=Space+Grotesk:wght@700&display=swap');

/* ── Global ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp, 
[data-testid="stAppViewContainer"], 
.main, 
.reportview-container,
[data-testid="stMain"],
[data-testid="stApp"] {
    background-color: #05070f !important;
    background-image: 
        radial-gradient(circle at 20% 30%, rgba(0, 255, 255, 0.05) 0%, transparent 60%),
        radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.04) 0%, transparent 60%),
        linear-gradient(rgba(56, 189, 248, 0.015) 1.5px, transparent 1.5px),
        linear-gradient(90deg, rgba(56, 189, 248, 0.015) 1.5px, transparent 1.5px),
        url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1000' height='1000' viewBox='0 0 1000 1000'%3E%3Cdefs%3E%3ClinearGradient id='g1' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%2300ffff' stop-opacity='0.15'/%3E%3Cstop offset='50%25' stop-color='%233b82f6' stop-opacity='0.15'/%3E%3Cstop offset='100%25' stop-color='%238b5cf6' stop-opacity='0.15'/%3E%3C/linearGradient%3E%3Cfilter id='glow'%3E%3CfeGaussianBlur stdDeviation='4' result='blur'/%3E%3CfeMerge%3E%3CfeMergeNode in='blur'/%3E%3CfeMergeNode in='SourceGraphic'/%3E%3C/feMerge%3E%3C/filter%3E%3C/defs%3E%3Cg stroke='url(%23g1)' stroke-width='1.5' fill='none'%3E%3Cpath d='M150 150 L350 250 L300 450 L100 350 Z'/%3E%3Cpath d='M350 250 L650 150 L800 350 L500 400 Z'/%3E%3Cpath d='M300 450 L500 400 L600 700 L250 800 Z'/%3E%3Cpath d='M800 350 L850 650 L600 700 Z'/%3E%3C/g%3E%3Cg filter='url(%23glow)' fill='%2300ffff' opacity='0.35'%3E%3Ccircle cx='150' cy='150' r='5.5'/%3E%3Ccircle cx='300' cy='450' r='5.5'/%3E%3Ccircle cx='600' cy='700' r='5.5'/%3E%3C/g%3E%3Cg filter='url(%23glow)' fill='%233b82f6' opacity='0.35'%3E%3Ccircle cx='350' cy='250' r='6.5'/%3E%3Ccircle cx='500' cy='400' r='6.5'/%3E%3Ccircle cx='250' cy='800' r='6.5'/%3E%3C/g%3E%3C/svg%3E"),
        url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='800' viewBox='0 0 800 800'%3E%3Cg fill='none' stroke-width='1'%3E%3Ccircle cx='200' cy='150' r='4' fill='%2300ffff' opacity='0.3'/%3E%3Ccircle cx='600' cy='250' r='4.5' fill='%238b5cf6' opacity='0.35'/%3E%3Ccircle cx='400' cy='550' r='4' fill='%233b82f6' opacity='0.3'/%3E%3Ccircle cx='150' cy='700' r='5' fill='%2300ffff' opacity='0.35'/%3E%3Ccircle cx='700' cy='650' r='3.5' fill='%238b5cf6' opacity='0.3'/%3E%3C/g%3E%3C/svg%3E") !important;
    background-size: 100% 100%, 100% 100%, 100px 100px, 100px 100px, 1000px 1000px, 800px 800px !important;
    background-repeat: no-repeat, no-repeat, repeat, repeat, repeat, repeat !important;
    animation: dynamicBackground 120s linear infinite !important;
}

@keyframes dynamicBackground {
    0% {
        background-position: 0% 0%, 0% 0%, 0px 0px, 0px 0px, 0px 0px, 0px 0px;
    }
    100% {
        background-position: 15% 15%, -15% -15%, 0px 0px, 0px 0px, 1000px -1000px, -800px 800px;
    }
}





/* ── Header Styling ── */
header[data-testid="stHeader"], 
.stHeader,
.stAppHeader,
[data-testid="stHeader"] {
    background: linear-gradient(270deg, #0f172a, #1e3a8a, #3b82f6, #1d4ed8) !important;
    background-size: 400% 400% !important;
    animation: headerGradient 8s ease infinite !important;
    color: white !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
    overflow: hidden !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}

@keyframes headerGradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

header[data-testid="stHeader"]::before, 
.stHeader::before,
.stAppHeader::before,
[data-testid="stHeader"]::before {
    content: "NovaRAG Research Studio";
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    white-space: nowrap;
    font-family: 'Orbitron', 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 900;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    background: linear-gradient(90deg, #00ffff, #3b82f6, #00ffff);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 8px rgba(0, 255, 255, 0.4));
    animation: textShine 4s linear infinite, textGlow 3s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 1;
}

@keyframes textShine {
    0% { background-position: 0% center; }
    100% { background-position: 200% center; }
}

@keyframes textGlow {
    0% {
        filter: drop-shadow(0 0 4px rgba(0, 255, 255, 0.3)) drop-shadow(0 0 8px rgba(59, 130, 246, 0.2));
    }
    100% {
        filter: drop-shadow(0 0 10px rgba(0, 255, 255, 0.6)) drop-shadow(0 0 16px rgba(59, 130, 246, 0.5));
    }
}

@media (max-width: 768px) {
    header[data-testid="stHeader"]::before, 
    .stHeader::before,
    .stAppHeader::before,
    [data-testid="stHeader"]::before {
        font-size: 1.1rem;
        letter-spacing: 0.08em;
    }
}

/* Header interactive elements readability */
header[data-testid="stHeader"] *, 
.stHeader *,
.stAppHeader *,
[data-testid="stHeader"] * {
    color: white !important;
    fill: white !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] { color: #CBD5E1; }

/* ── Dashboard Title ── */
.dashboard-title {
    font-size: 1.85rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818CF8 0%, #A78BFA 40%, #C084FC 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
    margin-bottom: 2px;
}
.dashboard-subtitle {
    font-size: 0.88rem;
    color: #64748B;
    font-weight: 400;
    margin-bottom: 1.2rem;
}

/* ── Metric Cards ── */
.metric-card {
    background: rgba(30,41,59,0.65);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 20px 22px;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    transition: border-color 0.3s, box-shadow 0.3s;
}
.metric-card:hover {
    border-color: rgba(139,92,246,0.3);
    box-shadow: 0 4px 24px rgba(139,92,246,0.08);
}
.metric-label {
    font-size: 0.7rem; font-weight: 600; color: #64748B;
    text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 6px;
}
.metric-value {
    font-size: 1.95rem; font-weight: 800; color: #F1F5F9; line-height: 1;
}
.metric-unit {
    font-size: 0.85rem; font-weight: 400; color: #94A3B8; margin-left: 4px;
}

/* ── Glass Card ── */
.glass-card {
    background: rgba(30,41,59,0.45);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 14px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}
.card-title {
    font-size: 0.95rem; font-weight: 700; color: #E2E8F0;
    margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
}

/* ── Thinking Card ── */
.thinking-card {
    background: rgba(17,24,39,0.6);
    border-left: 4px solid #8B5CF6;
    border-radius: 4px 12px 12px 4px;
    padding: 16px; margin-bottom: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem; color: #C084FC;
}

/* ── Source Card ── */
.source-card {
    background: rgba(15,23,42,0.5);
    border: 1px solid rgba(255,255,255,0.04);
    border-left: 3px solid #0D9488;
    border-radius: 8px;
    padding: 14px 18px; margin-bottom: 10px;
    transition: border-left-color 0.2s, background 0.2s;
}
.source-card:hover {
    border-left-color: #8B5CF6;
    background: rgba(15,23,42,0.7);
}

/* ── Badges ── */
.badge {
    display: inline-block; padding: 4px 10px; border-radius: 9999px;
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; margin-right: 8px;
}
.badge-pass  { background: rgba(16,185,129,0.12); color: #10B981; border: 1px solid rgba(16,185,129,0.2); }
.badge-warning { background: rgba(245,158,11,0.12); color: #F59E0B; border: 1px solid rgba(245,158,11,0.2); }
.badge-fail  { background: rgba(239,68,68,0.12); color: #EF4444; border: 1px solid rgba(239,68,68,0.2); }
.badge-info  { background: rgba(59,130,246,0.12); color: #3B82F6; border: 1px solid rgba(59,130,246,0.2); }

/* ── Category Badge ── */
.cat-badge {
    display: inline-block; padding: 3px 8px; border-radius: 6px;
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.03em;
}

/* ── Data Table ── */
.doc-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    transition: background 0.15s;
}
.doc-row:hover { background: rgba(139,92,246,0.05); }
.doc-row:nth-child(even) { background: rgba(15,23,42,0.25); }
.doc-row:nth-child(even):hover { background: rgba(139,92,246,0.07); }

.doc-rank {
    font-size: 0.8rem; font-weight: 700; color: #64748B;
    min-width: 28px; text-align: center;
}
.doc-title-cell {
    flex: 1; font-size: 0.85rem; color: #CBD5E1; font-weight: 500;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.doc-meta {
    font-size: 0.75rem; color: #64748B; min-width: 70px; text-align: center;
}

.table-header {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 16px;
    background: rgba(30,41,59,0.8);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px 10px 0 0;
}
.th { font-size: 0.7rem; font-weight: 700; color: #64748B;
      text-transform: uppercase; letter-spacing: 0.06em; }
.th-rank { min-width: 28px; text-align: center; }
.th-title { flex: 1; }
.th-meta  { min-width: 70px; text-align: center; }

/* ── Streamlit Widget Overrides ── */
.stTextInput > div > div > input {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(139,92,246,0.5) !important;
    box-shadow: 0 0 0 2px rgba(139,92,246,0.15) !important;
}

.stSelectbox > div > div {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 8px 20px !important;
    transition: box-shadow 0.2s, transform 0.2s !important;
}
.stButton > button:hover {
    box-shadow: 0 4px 18px rgba(139,92,246,0.35) !important;
    transform: translateY(-1px) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(15,23,42,0.35);
    border: 1px dashed rgba(139,92,246,0.25);
    border-radius: 10px; padding: 10px;
}

/* Download button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #0D9488 0%, #14B8A6 100%) !important;
    border: none !important; border-radius: 8px !important;
    color: white !important; font-weight: 600 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(30,41,59,0.5);
    border-radius: 10px; padding: 4px; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; color: #94A3B8; font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(139,92,246,0.15) !important;
    color: #C084FC !important;
}

/* Plotly container */
[data-testid="stPlotlyChart"] { background: transparent !important; }

/* Expander */
.streamlit-expanderHeader {
    background: rgba(30,41,59,0.5) !important;
    border-radius: 8px !important;
    color: #CBD5E1 !important;
}

/* Progress bar */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #7C3AED, #8B5CF6) !important;
}

/* General text */
.stMarkdown { color: #CBD5E1; }
h1, h2, h3, h4 { color: #E2E8F0 !important; }
p, li { color: #CBD5E1; }
hr { border-color: rgba(255,255,255,0.06) !important; }

/* Checkbox */
.stCheckbox label { color: #CBD5E1 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0F172A; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

/* Success / Warning / Error boxes */
.stAlert { border-radius: 10px !important; }

/* ── Sidebar Logo & Title Animations ── */
.sidebar-logo {
    display: inline-block;
    animation: floatLogo 4s ease-in-out infinite;
}
@keyframes floatLogo {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-5px) rotate(8deg); }
}

.sidebar-title {
    font-family: 'Orbitron', 'Space Grotesk', sans-serif !important;
    font-weight: 900 !important;
    background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: textGlowPulse 3s ease-in-out infinite alternate;
}
@keyframes textGlowPulse {
    0% { filter: drop-shadow(0 0 1px rgba(56, 189, 248, 0.3)); }
    100% { filter: drop-shadow(0 0 6px rgba(167, 139, 250, 0.6)); }
}

/* ── Database Overview Premium Card ── */
.db-card {
    background: rgba(30, 41, 59, 0.55) !important;
    border: 1px solid rgba(56, 189, 248, 0.1) !important;
    border-radius: 12px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 25px rgba(0, 0, 0, 0.2);
    transition: border-color 0.3s, box-shadow 0.3s;
}
.db-card:hover {
    border-color: rgba(56, 189, 248, 0.35) !important;
    box-shadow: 0 4px 30px rgba(56, 189, 248, 0.12);
}
.db-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.08), transparent);
    animation: scanPulse 8s linear infinite;
}
@keyframes scanPulse {
    0% { left: -100%; }
    100% { left: 100%; }
}

.db-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    color: #38bdf8 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 12px;
}

.db-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}
.db-row:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}

.db-label {
    color: #94a3b8;
    font-size: 0.8rem;
}

.db-value {
    color: #38bdf8;
    font-weight: 800;
    font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
    text-shadow: 0 0 6px rgba(56, 189, 248, 0.3);
    animation: databaseValueGlow 2.5s ease-in-out infinite alternate;
}
@keyframes databaseValueGlow {
    0% { opacity: 0.8; text-shadow: 0 0 4px rgba(56, 189, 248, 0.2); }
    100% { opacity: 1; text-shadow: 0 0 10px rgba(56, 189, 248, 0.5); }
}

/* ── Footer Anim ── */
.sidebar-footer {
    font-size: 0.7rem;
    color: #64748b;
    text-align: center;
    letter-spacing: 0.04em;
    margin-top: 10px;
    animation: footerPulse 3s ease-in-out infinite alternate;
}
@keyframes footerPulse {
    0% { opacity: 0.55; }
    100% { opacity: 0.9; color: #818cf8; text-shadow: 0 0 6px rgba(129, 140, 248, 0.25); }
}
</style>
""", unsafe_allow_html=True)



# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZE DATABASE & LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════
try:
    client = get_chroma_client()
    collection = get_collection(client)
except Exception as e:
    st.error(f"Error initializing ChromaDB: {e}")
    st.stop()

env_api_key = os.getenv("GEMINI_API_KEY", "")
csv_papers = load_papers_csv()
docs = list_documents(collection)
total_docs = len(docs)
total_pages = sum(d["total_pages"] for d in docs)
cat_dist = get_category_distribution(csv_papers)
year_dist = get_year_distribution(csv_papers)
valid_years = [int(p.get("year", 0)) for p in csv_papers
               if str(p.get("year", "")).isdigit() and 2000 <= int(p.get("year", 0)) <= 2030]
year_range = f"{min(valid_years)}–{max(valid_years)}" if valid_years else "N/A"
num_categories = len(cat_dist)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; margin-bottom: 8px;">
        <span class="sidebar-logo" style="font-size:2.2rem; display:inline-block;">🔬</span>
        <div class="sidebar-title" style="font-size:1.15rem; font-weight:800; margin-top:2px;">NovaRAG</div>
        <div style="font-size:0.7rem; color:#64748B; letter-spacing:0.06em;
                    text-transform:uppercase; margin-top:2px;">Research Studio</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # API Key
    if not env_api_key:
        st.markdown("##### 🔑 API Configuration")
        api_key_input = st.text_input(
            "Gemini API Key",
            value=st.session_state.get("api_key", ""),
            type="password",
            help="Google Gemini API Key."
        )
        if api_key_input:
            st.session_state["api_key"] = api_key_input
        st.markdown("---")
    else:
        st.session_state["api_key"] = env_api_key

    # Configuration defaults (hidden from UI)
    simulate_failover = False
    include_excerpts = False

    st.markdown(
        f"""
        <div class="db-card">
            <div class="db-title">
                📊 Database Overview
            </div>
            <div class="db-row">
                <span class="db-label">📄 Papers</span>
                <span class="db-value">{total_docs}</span>
            </div>
            <div class="db-row">
                <span class="db-label">📖 Pages</span>
                <span class="db-value">{total_pages:,}</span>
            </div>
            <div class="db-row">
                <span class="db-label">🏷️ Categories</span>
                <span class="db-value">{num_categories}</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown("")
    st.markdown('<div class="sidebar-footer">NovaRAG Research Studio v1.0.0</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="dashboard-title">NovaRAG Research Dashboard</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="dashboard-subtitle">'
    'Enterprise-Grade Retrieval-Augmented Generation &amp; Report Builder'
    '</div>',
    unsafe_allow_html=True
)


# ═══════════════════════════════════════════════════════════════════════════════
# METRIC CARDS
# ═══════════════════════════════════════════════════════════════════════════════
m1, m2, m3, m4 = st.columns(4, gap="medium")

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Indexed Papers</div>
        <div class="metric-value">{total_docs}<span class="metric-unit">files</span></div>
    </div>""", unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Pages</div>
        <div class="metric-value">{total_pages:,}<span class="metric-unit">pages</span></div>
    </div>""", unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Research Categories</div>
        <div class="metric-value">{num_categories}<span class="metric-unit">domains</span></div>
    </div>""", unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Year Span</div>
        <div class="metric-value">{year_range}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")


# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS ROW
# ═══════════════════════════════════════════════════════════════════════════════
ch1, ch2 = st.columns(2, gap="medium")

with ch1:
    st.markdown("""<div class="glass-card">
        <div class="card-title">📊 Papers by Category</div>
    </div>""", unsafe_allow_html=True)
    if cat_dist:
        fig_donut = create_donut_chart(cat_dist)
        st.plotly_chart(fig_donut, width="stretch",
                        config={"displayModeBar": False})
    else:
        st.info("No paper data available for chart.")

with ch2:
    st.markdown("""<div class="glass-card">
        <div class="card-title">📈 Papers by Year</div>
    </div>""", unsafe_allow_html=True)
    if year_dist:
        fig_area = create_area_chart(year_dist)
        st.plotly_chart(fig_area, width="stretch",
                        config={"displayModeBar": False})
    else:
        st.info("No paper data available for chart.")

st.markdown("")


# ═══════════════════════════════════════════════════════════════════════════════
# TABS — Search & Synthesize  |  Manage Document Corpus
# ═══════════════════════════════════════════════════════════════════════════════
tab_search, tab_manage = st.tabs([
    "🔍 Search & Synthesize",
    "📂 Manage Document Corpus"
])


# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — SEARCH & SYNTHESIZE
# ──────────────────────────────────────────────────────────────────────────────
with tab_search:
    st.markdown(
        '<p style="color:#94A3B8; font-size:0.88rem; margin-bottom:14px;">'
        'Query the indexed papers, review safety audits, and compile PDF briefs.</p>',
        unsafe_allow_html=True
    )

    # Search bar
    col_q, col_btn = st.columns([5, 1])
    with col_q:
        search_query = st.text_input(
            "Enter research topic or query:",
            placeholder="e.g., Attention Mechanism in Transformers or Deep Learning Optimization...",
            label_visibility="collapsed"
        )
    with col_btn:
        search_btn = st.button("⚡ Synthesize", width="stretch", type="primary")

    # Perform search
    if search_btn or (search_query and st.session_state.get("run_search", False)):
        st.session_state["run_search"] = False

        if not search_query.strip():
            st.warning("Please enter a valid search topic.")
        else:
            # ── INPUT GUARDRAILS ──
            is_safe, input_reason = check_input_guardrail(search_query)

            st.markdown("#### 🔒 Security & Groundedness Audit")
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                if is_safe:
                    st.markdown(
                        '<span class="badge badge-pass">Passed</span> '
                        'Input Guardrail: Clear', unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<span class="badge badge-fail">Blocked</span> '
                        f'Input Guardrail: {input_reason}', unsafe_allow_html=True)

            if not is_safe:
                st.error("⚠️ Query blocked by safety guidelines. Please modify your query.")
            else:
                # ── RAG PIPELINE ──
                with st.spinner("Retrieving from ChromaDB, reranking with FlashRank, analyzing..."):
                    rag_result = run_rag_query(
                        query=search_query,
                        api_key=st.session_state.get("api_key", env_api_key),
                        simulate_api_failure=simulate_failover
                    )

                if not rag_result["success"] and rag_result.get("status") == "error":
                    st.error(rag_result["message"])
                else:
                    # ── OUTPUT GUARDRAILS ──
                    contexts = [chunk["text"] for chunk in rag_result["raw_chunks"]]

                    if rag_result["status"] == "success":
                        output_safe, output_reason, overlap_score = check_output_guardrail(
                            rag_result["summary"], contexts
                        )
                    else:
                        output_safe, output_reason, overlap_score = (
                            True, "Fallback raw data. Grounding N/A.", 1.0
                        )

                    with col_g2:
                        if rag_result["status"] == "success":
                            if output_safe:
                                st.markdown(
                                    f'<span class="badge badge-pass">Passed</span> '
                                    f'Groundedness: {overlap_score:.1%}',
                                    unsafe_allow_html=True)
                            else:
                                st.markdown(
                                    f'<span class="badge badge-warning">Warning</span> '
                                    f'Groundedness: {overlap_score:.1%} (Hallucination Risk)',
                                    unsafe_allow_html=True)
                        else:
                            st.markdown(
                                '<span class="badge badge-info">Info</span> '
                                'Groundedness: N/A (API Offline)',
                                unsafe_allow_html=True)

                    st.markdown("---")

                    # ── RESULTS ──
                    if rag_result["status"] == "fallback":
                        st.warning(f"⚠️ **Resiliency Fallback Engaged:** {rag_result['message']}")

                    # Reasoning flow
                    if rag_result.get("thinking"):
                        with st.expander("🔄 Reasoning Flow", expanded=True):
                            st.markdown(
                                f'<div class="thinking-card">{rag_result["thinking"]}</div>',
                                unsafe_allow_html=True)

                    # Synthesis
                    st.markdown("### 📝 Synthesis Summary")
                    st.markdown(rag_result["summary"])

                    # ── PDF REPORT ──
                    reports_dir = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "reports")
                    os.makedirs(reports_dir, exist_ok=True)

                    clean_q = "".join(
                        c if c.isalnum() else "_" for c in search_query
                    ).lower()[:15]
                    report_fn = (
                        f"report_{clean_q}_"
                        f"{datetime.datetime.now().strftime('%H%M%S')}.pdf"
                    )
                    report_path = os.path.join(reports_dir, report_fn)

                    guardrail_data = {
                        "input_safe": is_safe,
                        "output_safe": output_safe,
                        "output_score": overlap_score,
                    }

                    try:
                        generate_pdf_report(
                            output_path=report_path,
                            query=search_query,
                            summary=rag_result["summary"],
                            sources=rag_result["raw_chunks"],
                            guardrail_results=guardrail_data,
                            include_excerpts=include_excerpts,
                        )
                        with open(report_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            label="📥 Download PDF Research Brief",
                            data=pdf_bytes,
                            file_name=f"NovaRAG_Report_{clean_q}.pdf",
                            mime="application/pdf",
                        )
                    except Exception as pdf_err:
                        st.error(f"Failed to generate PDF Report: {pdf_err}")

                    st.markdown("---")

                    # ── RETRIEVED SOURCES ──
                    st.markdown("### 📚 Retrieved & Reranked Sources")
                    for chunk in rag_result["raw_chunks"]:
                        st.markdown(
                            f"""
                            <div class="source-card">
                                <div style="font-weight:600; font-size:0.92rem; color:#A78BFA;">
                                    [{chunk['rank']}] {chunk['title']} — Page {chunk['page']}
                                </div>
                                <div style="font-size:0.82rem; color:#94A3B8; margin-top:6px;
                                            font-style:italic; line-height:1.5;">
                                    "{chunk['text'][:500]}{'...' if len(chunk['text']) > 500 else ''}"
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — MANAGE DOCUMENT CORPUS
# ──────────────────────────────────────────────────────────────────────────────
with tab_manage:
    st.markdown("### 📂 Document Corpus Control Center")
    st.markdown(
        '<p style="color:#94A3B8; font-size:0.88rem; margin-bottom:14px;">'
        'Add, inspect, or delete papers from the ChromaDB vector index.</p>',
        unsafe_allow_html=True
    )

    # ── Upload Section ──
    st.markdown("""<div class="glass-card">
        <div class="card-title">📤 Upload Research Papers</div>
    </div>""", unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload PDFs to ingest page-by-page:",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("🚀 Process & Index Papers"):
            success_count = 0
            fail_count = 0
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Ingesting {uploaded_file.name}...")
                try:
                    file_bytes = uploaded_file.read()
                    doc_id, pages_count = add_pdf_to_vector_store(
                        collection=collection,
                        file_bytes=file_bytes,
                        file_name=uploaded_file.name
                    )
                    if pages_count > 0:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as ingest_err:
                    st.error(f"Error ingesting {uploaded_file.name}: {ingest_err}")
                    fail_count += 1
                progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.empty()
            progress_bar.empty()

            if success_count > 0:
                st.success(
                    f"Indexed {success_count} research paper(s) into ChromaDB!"
                )
                st.rerun()
            if fail_count > 0:
                st.warning(f"Failed to process {fail_count} file(s).")

    st.markdown("---")

    # ── Filter Bar ──
    st.markdown("""<div class="glass-card">
        <div class="card-title">🔎 Filter & Browse Indexed Papers</div>
    </div>""", unsafe_allow_html=True)

    current_docs = list_documents(collection)
    enriched = enrich_docs_with_csv(current_docs, csv_papers)

    # Build filter options
    all_categories = sorted(set(d["category"] for d in enriched)) if enriched else []
    all_years = sorted(set(d["year"] for d in enriched if d["year"] != "—")) if enriched else []

    fcol1, fcol2, fcol3 = st.columns([2, 2, 4])
    with fcol1:
        cat_filter = st.selectbox(
            "Category Filter",
            options=["All"] + all_categories,
            index=0
        )
    with fcol2:
        year_filter = st.selectbox(
            "Year Filter",
            options=["All"] + all_years,
            index=0
        )

    # Apply filters
    filtered = enriched
    if cat_filter != "All":
        filtered = [d for d in filtered if d["category"] == cat_filter]
    if year_filter != "All":
        filtered = [d for d in filtered if d["year"] == year_filter]

    st.markdown("")

    # ── Document Table ──
    if not filtered:
        st.info("No documents match the current filters, or the index is empty.")
    else:
        # Table header
        st.markdown(f"""
        <div class="table-header">
            <span class="th th-rank">#</span>
            <span class="th th-title">Paper Title</span>
            <span class="th th-meta">Category</span>
            <span class="th th-meta">Year</span>
            <span class="th th-meta">Pages</span>
            <span class="th th-meta">Action</span>
        </div>
        """, unsafe_allow_html=True)

        for idx, doc in enumerate(filtered):
            cat_color = CATEGORY_COLORS.get(doc["category"], "#64748B")

            # Row layout: rank | title | category badge | year | pages | delete
            r1, r2, r3, r4, r5 = st.columns([0.3, 4, 1.5, 0.7, 0.8])

            with r1:
                st.markdown(
                    f'<div style="text-align:center; color:#64748B; '
                    f'font-weight:700; font-size:0.82rem; padding-top:6px;">'
                    f'{idx + 1}</div>',
                    unsafe_allow_html=True
                )

            with r2:
                st.markdown(
                    f'<div style="color:#CBD5E1; font-weight:500; '
                    f'font-size:0.85rem; padding-top:4px; '
                    f'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">'
                    f'📄 {doc["paper_title"]}</div>',
                    unsafe_allow_html=True
                )

            with r3:
                st.markdown(
                    f'<div style="padding-top:4px;">'
                    f'<span class="cat-badge" style="background:{cat_color}20; '
                    f'color:{cat_color}; border:1px solid {cat_color}33;">'
                    f'{doc["category"]}</span></div>',
                    unsafe_allow_html=True
                )

            with r4:
                st.markdown(
                    f'<div style="text-align:center; color:#94A3B8; '
                    f'font-size:0.82rem; padding-top:6px;">'
                    f'{doc["year"]}</div>',
                    unsafe_allow_html=True
                )

            with r5:
                if st.button("🗑️", key=f"del_{doc['document_id']}",
                             help=f"Delete {doc['paper_title']}"):
                    delete_document(collection, doc["document_id"])
                    st.success(f"Deleted '{doc['paper_title']}'")
                    st.rerun()

        # Summary footer
        st.markdown(
            f'<div style="text-align:right; color:#64748B; font-size:0.78rem; '
            f'margin-top:8px; padding-right:16px;">'
            f'Showing {len(filtered)} of {len(enriched)} indexed documents'
            f'</div>',
            unsafe_allow_html=True
        )
