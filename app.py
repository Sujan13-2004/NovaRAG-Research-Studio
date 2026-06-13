"""
NovaRAG Research Studio — Main Application Shell.

Single-entry-point router that manages sidebar navigation
and delegates rendering to page modules.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from ingest import get_chroma_client, get_collection, list_documents
from utils.theme import inject_custom_css
from utils.helpers import load_papers_csv, CATEGORY_COLORS


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
# ENTRANCE GATE & STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════
if "show_landing" not in st.session_state:
    st.session_state["show_landing"] = True
if "loading_state" not in st.session_state:
    st.session_state["loading_state"] = False

if st.session_state["loading_state"]:
    from pages.landing import render_loader
    render_loader()
    st.stop()
elif st.session_state["show_landing"]:
    from pages.landing import render_landing
    render_landing()
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# INJECT CUSTOM CSS FOR DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
inject_custom_css()



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
if env_api_key:
    st.session_state["api_key"] = env_api_key

csv_papers = load_papers_csv()


# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZE SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "🏠 Dashboard"
if "query_history" not in st.session_state:
    st.session_state["query_history"] = []
if "rag_settings" not in st.session_state:
    st.session_state["rag_settings"] = {
        "top_k_retrieve": 20,
        "top_n_rerank": 7,
        "max_chunks_per_doc": 3,
        "groundedness_threshold": 0.55,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NAVIGATION PAGES
# ═══════════════════════════════════════════════════════════════════════════════
NAV_PAGES = {
    "MAIN": [
        "🏠 Dashboard",
        "🔍 Research Assistant",
        "📤 Upload & Corpus",
        "📚 Browse Papers",
    ],
    "RESEARCH": [
        "🔬 Research Synthesis",
        "🔎 Evidence Extraction",
    ],
    "SYSTEM": [
        "🛡️ Safety & Guardrails",
        "📊 Analytics",
        "📑 Reports",
        "⚙️ Settings",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo and Branding
    st.markdown("""
    <div style="text-align:center; margin-bottom: 8px;">
        <span class="sidebar-logo" style="font-size:2.2rem; display:inline-block;">🔬</span>
        <div class="sidebar-title" style="font-size:1.15rem; font-weight:800; margin-top:2px;">NovaRAG</div>
        <div style="font-size:0.7rem; color:#64748B; letter-spacing:0.06em;
                    text-transform:uppercase; margin-top:2px;">Research Studio</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Navigation ──
    # Main section
    st.markdown('<div class="nav-section-label">Navigation</div>', unsafe_allow_html=True)
    for page in NAV_PAGES["MAIN"]:
        is_active = st.session_state["current_page"] == page
        if st.button(
            page,
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["current_page"] = page
            st.rerun()

    # Research section
    st.markdown('<div class="nav-section-label">Research Tools</div>', unsafe_allow_html=True)
    for page in NAV_PAGES["RESEARCH"]:
        is_active = st.session_state["current_page"] == page
        if st.button(
            page,
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["current_page"] = page
            st.rerun()

    # System section
    st.markdown('<div class="nav-section-label">System</div>', unsafe_allow_html=True)
    for page in NAV_PAGES["SYSTEM"]:
        is_active = st.session_state["current_page"] == page
        if st.button(
            page,
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["current_page"] = page
            st.rerun()

    st.markdown("---")

    # ── Database Overview Card ──
    docs = list_documents(collection)
    total_docs = len(docs)
    total_pages = sum(d["total_pages"] for d in docs)
    total_chunks = collection.count() if collection else 0

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
                <span class="db-label">🧬 Chunks</span>
                <span class="db-value">{total_chunks:,}</span>
            </div>
            <div class="db-row">
                <span class="db-label">⚡ Queries</span>
                <span class="db-value">{len(st.session_state.get('query_history', []))}</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown("")
    st.markdown('<div class="sidebar-footer">NovaRAG Research Studio v2.0.0</div>',
                unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
current_page = st.session_state["current_page"]

if current_page == "🏠 Dashboard":
    from pages.dashboard import render
    render(collection, csv_papers)

elif current_page == "🔍 Research Assistant":
    from pages.research_assistant import render
    render(collection, csv_papers)

elif current_page == "📤 Upload & Corpus":
    from pages.upload_corpus import render
    render(collection, csv_papers)

elif current_page == "📚 Browse Papers":
    from pages.browse_papers import render
    render(collection, csv_papers)

elif current_page == "🔬 Research Synthesis":
    from pages.research_synthesis import render
    render(collection, csv_papers)

elif current_page == "🔎 Evidence Extraction":
    from pages.evidence_extraction import render
    render(collection, csv_papers)

elif current_page == "🛡️ Safety & Guardrails":
    from pages.safety_audit import render
    render(collection, csv_papers)

elif current_page == "📊 Analytics":
    from pages.analytics import render
    render(collection, csv_papers)

elif current_page == "📑 Reports":
    from pages.reports import render
    render(collection, csv_papers)

elif current_page == "⚙️ Settings":
    from pages.settings import render
    render(collection, csv_papers)

else:
    from pages.dashboard import render
    render(collection, csv_papers)


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY COMPATIBILITY — Keep categorize_paper importable for audit.py
# ═══════════════════════════════════════════════════════════════════════════════
from utils.helpers import categorize_paper  # noqa: F401, E402
