"""
NovaRAG Research Studio — Dashboard Home Page.

Professional landing page with project overview cards, statistics,
charts, and quick action navigation.
"""

import streamlit as st
from utils.helpers import (
    load_papers_csv, get_category_distribution, get_year_distribution,
    CATEGORY_COLORS
)
from utils.charts import create_donut_chart, create_area_chart
from utils.components import (
    render_metric_card, render_page_header, render_glass_card,
    render_empty_state
)
from ingest import list_documents


def render(collection, csv_papers, **kwargs):
    """Renders the Dashboard Home page."""

    # Wrap everything in a page-content div for transition animation
    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Research Dashboard",
        "Enterprise-Grade Retrieval-Augmented Generation & Report Builder",
        icon="🏠"
    )

    # ── Load Stats ──
    docs = list_documents(collection)
    total_docs = len(docs)
    total_pages = sum(d["total_pages"] for d in docs)
    total_chunks = collection.count() if collection else 0
    cat_dist = get_category_distribution(csv_papers)
    year_dist = get_year_distribution(csv_papers)
    valid_years = [int(p.get("year", 0)) for p in csv_papers
                   if str(p.get("year", "")).isdigit() and 2000 <= int(p.get("year", 0)) <= 2030]
    year_range = f"{min(valid_years)}–{max(valid_years)}" if valid_years else "N/A"
    num_categories = len(cat_dist)
    total_queries = len(st.session_state.get("query_history", []))

    # ── Metric Cards Row 1 ──
    st.markdown("")
    m1, m2, m3, m4 = st.columns(4, gap="medium")
    with m1:
        render_metric_card("Indexed Papers", total_docs, "files", "📄", "#3B82F6")
    with m2:
        render_metric_card("Total Pages", f"{total_pages:,}", "pages", "📖", "#8B5CF6")
    with m3:
        render_metric_card("Vector Chunks", f"{total_chunks:,}", "chunks", "🧬", "#10B981")
    with m4:
        render_metric_card("Queries Processed", total_queries, "queries", "⚡", "#F59E0B")

    # ── Metric Cards Row 2 ──
    st.markdown("")
    m5, m6, m7, m8 = st.columns(4, gap="medium")
    with m5:
        render_metric_card("Research Categories", num_categories, "domains", "🏷️", "#EC4899")
    with m6:
        render_metric_card("Year Span", year_range, "", "📅", "#0EA5E9")
    with m7:
        # Groundedness stats
        history = st.session_state.get("query_history", [])
        if history:
            scores = [q.get("groundedness_score", 0) for q in history if q.get("groundedness_score")]
            avg_score = sum(scores) / len(scores) if scores else 0
            render_metric_card("Avg Groundedness", f"{avg_score:.0%}", "", "🛡️", "#14B8A6")
        else:
            render_metric_card("Avg Groundedness", "—", "", "🛡️", "#14B8A6")
    with m8:
        # Success rate
        if history:
            success = sum(1 for q in history if q.get("success", False))
            rate = success / len(history) if history else 0
            render_metric_card("Success Rate", f"{rate:.0%}", "", "✅", "#10B981")
        else:
            render_metric_card("Success Rate", "—", "", "✅", "#10B981")

    st.markdown("")

    # ── Charts Row ──
    ch1, ch2 = st.columns(2, gap="medium")

    with ch1:
        render_glass_card("Papers by Category", icon="📊")
        if cat_dist:
            fig_donut = create_donut_chart(cat_dist)
            st.plotly_chart(fig_donut, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            render_empty_state("No paper data available", "📊")

    with ch2:
        render_glass_card("Papers by Year", icon="📈")
        if year_dist:
            fig_area = create_area_chart(year_dist)
            st.plotly_chart(fig_area, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            render_empty_state("No paper data available", "📈")

    st.markdown("")

    # ── Quick Actions ──
    render_glass_card("Quick Actions", icon="⚡",
                      content="Jump to any section of the research studio")

    qa1, qa2, qa3, qa4, qa5 = st.columns(5, gap="small")

    with qa1:
        st.markdown("""
        <div class="glass-card" style="text-align:center; border-left:3px solid #8B5CF6; padding:16px;">
            <div style="font-size:1.6rem; margin-bottom:8px;">🔍</div>
            <div style="font-size:0.82rem; font-weight:600; color:#E2E8F0;">Research</div>
            <div style="font-size:0.7rem; color:#64748B; margin-top:2px;">Query papers</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Open", key="qa_research", use_container_width=True):
            st.session_state["current_page"] = "🔍 Research Assistant"
            st.rerun()

    with qa2:
        st.markdown("""
        <div class="glass-card" style="text-align:center; border-left:3px solid #3B82F6; padding:16px;">
            <div style="font-size:1.6rem; margin-bottom:8px;">📤</div>
            <div style="font-size:0.82rem; font-weight:600; color:#E2E8F0;">Upload</div>
            <div style="font-size:0.7rem; color:#64748B; margin-top:2px;">Add papers</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Open", key="qa_upload", use_container_width=True):
            st.session_state["current_page"] = "📤 Upload & Corpus"
            st.rerun()

    with qa3:
        st.markdown("""
        <div class="glass-card" style="text-align:center; border-left:3px solid #10B981; padding:16px;">
            <div style="font-size:1.6rem; margin-bottom:8px;">📚</div>
            <div style="font-size:0.82rem; font-weight:600; color:#E2E8F0;">Browse</div>
            <div style="font-size:0.7rem; color:#64748B; margin-top:2px;">Explore papers</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Open", key="qa_browse", use_container_width=True):
            st.session_state["current_page"] = "📚 Browse Papers"
            st.rerun()

    with qa4:
        st.markdown("""
        <div class="glass-card" style="text-align:center; border-left:3px solid #F59E0B; padding:16px;">
            <div style="font-size:1.6rem; margin-bottom:8px;">🔬</div>
            <div style="font-size:0.82rem; font-weight:600; color:#E2E8F0;">Synthesize</div>
            <div style="font-size:0.7rem; color:#64748B; margin-top:2px;">Multi-paper review</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Open", key="qa_synthesis", use_container_width=True):
            st.session_state["current_page"] = "🔬 Research Synthesis"
            st.rerun()

    with qa5:
        st.markdown("""
        <div class="glass-card" style="text-align:center; border-left:3px solid #EF4444; padding:16px;">
            <div style="font-size:1.6rem; margin-bottom:8px;">📊</div>
            <div style="font-size:0.82rem; font-weight:600; color:#E2E8F0;">Analytics</div>
            <div style="font-size:0.7rem; color:#64748B; margin-top:2px;">View metrics</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Open", key="qa_analytics", use_container_width=True):
            st.session_state["current_page"] = "📊 Analytics"
            st.rerun()

    # ── Recent Queries ──
    if history:
        st.markdown("")
        render_glass_card("Recent Queries", icon="🕐")
        for q in reversed(history[-5:]):
            query_text = q.get("query", "")[:80]
            intent = q.get("intent", "RESEARCH_SYNTHESIS")
            success = q.get("success", False)
            badge_class = "badge-pass" if success else "badge-fail"
            badge_text = "Success" if success else "Failed"
            st.markdown(f"""
            <div class="source-card" style="border-left-color: {'#10B981' if success else '#EF4444'};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#E2E8F0; font-size:0.88rem; font-weight:500;">
                        {query_text}{'...' if len(q.get('query', '')) > 80 else ''}
                    </span>
                    <div>
                        <span class="badge badge-info">{intent}</span>
                        <span class="badge {badge_class}">{badge_text}</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
