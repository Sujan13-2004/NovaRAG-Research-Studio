"""
NovaRAG Research Studio — Browse Papers Page.

Search, filter, and explore indexed research papers with metadata cards.
"""

import streamlit as st
import os
from utils.components import (
    render_page_header, render_glass_card, render_empty_state
)
from utils.helpers import (
    enrich_docs_with_csv, categorize_paper, CATEGORY_COLORS
)
from ingest import list_documents
from rag_pipeline import run_rag_query
from guardrails import check_output_guardrail, validate_citations


def render(collection, csv_papers, **kwargs):
    """Renders the Browse Papers page."""

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Browse Papers",
        "Search, filter, and explore your indexed research paper corpus",
        icon="📚"
    )

    env_api_key = os.getenv("GEMINI_API_KEY", "")

    # ── Load & Enrich Documents ──
    current_docs = list_documents(collection)
    enriched = enrich_docs_with_csv(current_docs, csv_papers)

    if not enriched:
        render_empty_state("No documents indexed yet. Upload papers to get started.", "📭")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Filter Bar ──
    render_glass_card("Search & Filter", icon="🔎")

    all_categories = sorted(set(d["category"] for d in enriched))
    all_years = sorted(set(d["year"] for d in enriched if d["year"] != "—"))

    f1, f2, f3 = st.columns([3, 1.5, 1.5])
    with f1:
        title_search = st.text_input(
            "Search by title",
            placeholder="Type to filter papers by title...",
            label_visibility="collapsed"
        )
    with f2:
        cat_filter = st.selectbox(
            "Category",
            options=["All Categories"] + all_categories,
            index=0
        )
    with f3:
        year_filter = st.selectbox(
            "Year",
            options=["All Years"] + all_years,
            index=0
        )

    # ── Apply Filters ──
    filtered = enriched
    if title_search:
        filtered = [d for d in filtered
                    if title_search.lower() in d["paper_title"].lower()]
    if cat_filter != "All Categories":
        filtered = [d for d in filtered if d["category"] == cat_filter]
    if year_filter != "All Years":
        filtered = [d for d in filtered if d["year"] == year_filter]

    # ── Results Summary ──
    st.markdown(
        f'<div style="color:#64748B; font-size:0.82rem; margin:8px 0 16px 0;">'
        f'Showing {len(filtered)} of {len(enriched)} papers'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Paper Cards ──
    for idx, doc in enumerate(filtered):
        cat_color = CATEGORY_COLORS.get(doc["category"], "#64748B")

        col_card, col_action = st.columns([5, 1])

        with col_card:
            st.markdown(f"""
            <div class="paper-card" style="border-left:3px solid {cat_color};">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="flex:1;">
                        <div style="font-size:0.95rem; font-weight:600; color:#E2E8F0;
                             margin-bottom:6px; line-height:1.4;">
                            📄 {doc['paper_title']}
                        </div>
                        <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;
                             margin-bottom:6px;">
                            <span class="cat-badge" style="background:{cat_color}20;
                                  color:{cat_color}; border:1px solid {cat_color}33;">
                                {doc['category']}
                            </span>
                            <span style="font-size:0.75rem; color:#94A3B8;">
                                📅 {doc['year']}
                            </span>
                            <span style="font-size:0.75rem; color:#94A3B8;">
                                📖 {doc['total_pages']} pages
                            </span>
                        </div>
                        <div style="font-size:0.78rem; color:#64748B;">
                            ✍️ {doc['authors'][:80]}{'...' if len(doc.get('authors', '')) > 80 else ''}
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        with col_action:
            st.markdown("<div style='padding-top:8px;'></div>", unsafe_allow_html=True)
            if st.button("📄 Summarize", key=f"browse_sum_{doc['document_id']}",
                         use_container_width=True):
                st.session_state["browse_summarize_doc"] = doc
            if st.button("🔍 Details", key=f"browse_det_{doc['document_id']}",
                         use_container_width=True):
                st.session_state["browse_detail_doc"] = doc

    # ── Detail Expander ──
    if st.session_state.get("browse_detail_doc"):
        doc = st.session_state.pop("browse_detail_doc")
        cat_color = CATEGORY_COLORS.get(doc["category"], "#64748B")
        st.markdown("---")
        st.markdown(f"### 📋 Document Details: {doc['paper_title']}")
        d1, d2, d3, d4 = st.columns(4, gap="small")
        with d1:
            st.markdown(f"""
            <div class="metric-card" style="border-left:3px solid {cat_color};">
                <div class="metric-label">Category</div>
                <div style="font-size:1rem; font-weight:700; color:{cat_color};">{doc['category']}</div>
            </div>""", unsafe_allow_html=True)
        with d2:
            st.markdown(f"""
            <div class="metric-card" style="border-left:3px solid #8B5CF6;">
                <div class="metric-label">Year</div>
                <div style="font-size:1.2rem; font-weight:700; color:#A78BFA;">{doc['year']}</div>
            </div>""", unsafe_allow_html=True)
        with d3:
            st.markdown(f"""
            <div class="metric-card" style="border-left:3px solid #10B981;">
                <div class="metric-label">Pages</div>
                <div style="font-size:1.2rem; font-weight:700; color:#10B981;">{doc['total_pages']}</div>
            </div>""", unsafe_allow_html=True)
        with d4:
            st.markdown(f"""
            <div class="metric-card" style="border-left:3px solid #3B82F6;">
                <div class="metric-label">Authors</div>
                <div style="font-size:0.82rem; font-weight:500; color:#CBD5E1; line-height:1.4;">
                    {doc['authors'][:100]}
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Quick Summarize Panel ──
    if st.session_state.get("browse_summarize_doc"):
        doc = st.session_state.pop("browse_summarize_doc")
        st.markdown("---")
        st.markdown(f"### 📄 Summarizing: {doc['paper_title']}")

        with st.spinner(f"Generating focused summary of '{doc['paper_title']}'..."):
            sum_result = run_rag_query(
                query=f"Summarize the key findings, methodology, and conclusions of: {doc['paper_title']}",
                api_key=st.session_state.get("api_key", env_api_key),
                document_id=doc["document_id"],
            )

        if sum_result["success"]:
            sum_contexts = [chunk["text"] for chunk in sum_result["raw_chunks"]]
            sum_safe, sum_reason, sum_score = check_output_guardrail(
                sum_result["summary"], sum_contexts
            )
            sum_citation = validate_citations(
                sum_result["summary"], sum_result["raw_chunks"]
            )

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                badge_var = "pass" if sum_safe else "warning"
                st.markdown(
                    f'<span class="badge badge-{badge_var}">{"Passed" if sum_safe else "Warning"}</span> '
                    f'Groundedness: {sum_score:.1%}',
                    unsafe_allow_html=True)
            with col_s2:
                if sum_citation.get("is_refusal"):
                    st.markdown(
                        '<span class="badge badge-info">Info</span> Citation Coverage: N/A',
                        unsafe_allow_html=True)
                else:
                    cov = sum_citation["citation_coverage"]
                    st.markdown(
                        f'<span class="badge badge-info">Info</span> '
                        f'Citation Coverage: {cov:.1%}',
                        unsafe_allow_html=True)

            st.markdown(sum_result["summary"])
        else:
            st.error(sum_result["message"])

    st.markdown('</div>', unsafe_allow_html=True)
