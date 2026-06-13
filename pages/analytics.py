"""
NovaRAG Research Studio — Analytics Dashboard Page.

Session-based analytics with query statistics, topic analysis,
retrieval metrics, and groundedness trends.
"""

import streamlit as st
from collections import Counter
from utils.components import (
    render_page_header, render_glass_card, render_metric_card,
    render_empty_state
)
from utils.charts import create_bar_chart, create_line_chart, create_donut_chart


def render(collection, csv_papers, **kwargs):
    """Renders the Analytics Dashboard page."""

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Analytics Dashboard",
        "Query statistics, retrieval metrics, and performance trends",
        icon="📊"
    )

    history = st.session_state.get("query_history", [])

    if not history:
        render_empty_state(
            "No analytics data available yet. Run some queries in the Research Assistant to populate this dashboard.",
            "📊"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Overview Metrics ──
    total_queries = len(history)
    successful = sum(1 for q in history if q.get("success"))
    failed = total_queries - successful
    scores = [q.get("groundedness_score", 0) for q in history if q.get("groundedness_score")]
    avg_score = sum(scores) / len(scores) if scores else 0
    total_chunks = sum(q.get("chunks_retrieved", 0) for q in history)
    total_papers = sum(q.get("unique_papers", 0) for q in history)

    m1, m2, m3, m4, m5 = st.columns(5, gap="small")
    with m1:
        render_metric_card("Total Queries", total_queries, "", "📊", "#3B82F6")
    with m2:
        render_metric_card("Success Rate", f"{successful/total_queries:.0%}" if total_queries else "—",
                           "", "✅", "#10B981")
    with m3:
        render_metric_card("Avg Groundedness", f"{avg_score:.0%}" if scores else "—",
                           "", "🛡️", "#8B5CF6")
    with m4:
        render_metric_card("Chunks Retrieved", f"{total_chunks:,}", "", "🧬", "#F59E0B")
    with m5:
        render_metric_card("Papers Consulted", f"{total_papers:,}", "", "📚", "#EC4899")

    st.markdown("")

    # ── Charts Row 1 ──
    ch1, ch2 = st.columns(2, gap="medium")

    with ch1:
        # ── Query Intent Distribution ──
        render_glass_card("Query Intent Distribution", icon="🎯")
        intent_counts = Counter(q.get("intent", "Unknown") for q in history)
        if intent_counts:
            intent_colors = {
                "RESEARCH_SYNTHESIS": "#8B5CF6",
                "FACTUAL_QA": "#3B82F6",
                "DOCUMENT_SUMMARY": "#10B981",
                "EVIDENCE_EXTRACTION": "#F59E0B",
            }
            fig_donut = create_donut_chart(dict(intent_counts))
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    with ch2:
        # ── Groundedness Trend ──
        render_glass_card("Groundedness Trend", icon="📈")
        if len(scores) >= 2:
            x_vals = list(range(1, len(scores) + 1))
            fig_trend = create_line_chart(x_vals, scores, "#8B5CF6", "")
            st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
        else:
            render_empty_state("Need 2+ queries for trend", "📈")

    st.markdown("")

    # ── Charts Row 2 ──
    ch3, ch4 = st.columns(2, gap="medium")

    with ch3:
        # ── Top Searched Topics (word frequency) ──
        render_glass_card("Top Searched Topics", icon="🔤")

        # Extract common words from queries
        stop_words = {"the", "a", "an", "in", "of", "and", "or", "for", "to", "is",
                      "on", "with", "by", "from", "this", "that", "how", "what", "are",
                      "was", "were", "be", "been", "all", "papers", "paper", "e.g.",
                      "e.g", "summarize", "compare", "key", "findings", "methodology"}
        all_words = []
        for q in history:
            words = q.get("query", "").lower().split()
            all_words.extend([w.strip(".,!?:;\"'()") for w in words
                              if len(w) > 3 and w.lower() not in stop_words])

        word_counts = Counter(all_words).most_common(10)
        if word_counts:
            labels = [w[0] for w in word_counts]
            values = [w[1] for w in word_counts]
            fig_topics = create_bar_chart(labels, values, "#8B5CF6", "")
            st.plotly_chart(fig_topics, use_container_width=True, config={"displayModeBar": False})
        else:
            render_empty_state("Not enough data yet", "🔤")

    with ch4:
        # ── Retrieval Metrics ──
        render_glass_card("Retrieval Metrics", icon="🧬")

        chunks_per_query = [q.get("chunks_retrieved", 0) for q in history if q.get("chunks_retrieved")]
        papers_per_query = [q.get("unique_papers", 0) for q in history if q.get("unique_papers")]

        if chunks_per_query:
            avg_chunks = sum(chunks_per_query) / len(chunks_per_query)
            avg_papers = sum(papers_per_query) / len(papers_per_query) if papers_per_query else 0
            max_chunks = max(chunks_per_query)
            max_papers = max(papers_per_query) if papers_per_query else 0

            rm1, rm2 = st.columns(2)
            with rm1:
                st.markdown(f"""
                <div class="metric-card" style="border-left:3px solid #10B981; padding:14px;">
                    <div class="metric-label">Avg Chunks/Query</div>
                    <div class="metric-value" style="font-size:1.4rem;">{avg_chunks:.1f}</div>
                </div>""", unsafe_allow_html=True)
            with rm2:
                st.markdown(f"""
                <div class="metric-card" style="border-left:3px solid #3B82F6; padding:14px;">
                    <div class="metric-label">Avg Papers/Query</div>
                    <div class="metric-value" style="font-size:1.4rem;">{avg_papers:.1f}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("")
            rm3, rm4 = st.columns(2)
            with rm3:
                st.markdown(f"""
                <div class="metric-card" style="border-left:3px solid #F59E0B; padding:14px;">
                    <div class="metric-label">Max Chunks</div>
                    <div class="metric-value" style="font-size:1.4rem;">{max_chunks}</div>
                </div>""", unsafe_allow_html=True)
            with rm4:
                st.markdown(f"""
                <div class="metric-card" style="border-left:3px solid #EC4899; padding:14px;">
                    <div class="metric-label">Max Papers</div>
                    <div class="metric-value" style="font-size:1.4rem;">{max_papers}</div>
                </div>""", unsafe_allow_html=True)
        else:
            render_empty_state("No retrieval data yet", "🧬")

    st.markdown("")

    # ── Query Log Table ──
    render_glass_card("Full Query Log", icon="📋")

    # Table header
    st.markdown("""
    <div class="table-header">
        <span class="th" style="min-width:30px; text-align:center;">#</span>
        <span class="th th-title">Query</span>
        <span class="th th-meta">Intent</span>
        <span class="th th-meta">Score</span>
        <span class="th th-meta">Status</span>
    </div>""", unsafe_allow_html=True)

    for i, q in enumerate(reversed(history)):
        success = q.get("success", False)
        color = "#10B981" if success else "#EF4444"
        score = q.get("groundedness", "N/A")
        intent = q.get("intent", "N/A")
        query_text = q.get("query", "")[:50]

        st.markdown(f"""
        <div class="doc-row">
            <span class="doc-rank">{len(history) - i}</span>
            <span class="doc-title-cell">{query_text}{'...' if len(q.get('query', '')) > 50 else ''}</span>
            <span class="doc-meta" style="min-width:120px;">
                <span class="badge badge-info" style="font-size:0.62rem;">{intent}</span>
            </span>
            <span class="doc-meta">{score}</span>
            <span class="doc-meta">
                <span class="badge {'badge-pass' if success else 'badge-fail'}" style="font-size:0.62rem;">
                    {'OK' if success else 'FAIL'}
                </span>
            </span>
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
