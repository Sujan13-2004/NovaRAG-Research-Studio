"""
NovaRAG Research Studio — Safety & Guardrails Page.

Centralized safety dashboard showing input/output guardrail status,
groundedness metrics, citation coverage, and security audit history.
"""

import streamlit as st
from utils.components import (
    render_page_header, render_glass_card, render_metric_card,
    render_badge, render_empty_state
)
from utils.charts import create_gauge_chart, create_line_chart
from guardrails import check_input_guardrail


def render(collection, csv_papers, **kwargs):
    """Renders the Safety & Guardrails page."""

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Safety & Guardrails",
        "Monitor input/output guardrails, groundedness metrics, and citation coverage",
        icon="🛡️"
    )

    history = st.session_state.get("query_history", [])

    # ── Overview Metrics ──
    total_queries = len(history)
    successful = sum(1 for q in history if q.get("success"))
    scores = [q.get("groundedness_score", 0) for q in history if q.get("groundedness_score")]
    avg_score = sum(scores) / len(scores) if scores else 0

    s1, s2, s3, s4 = st.columns(4, gap="medium")
    with s1:
        render_metric_card("Total Queries", total_queries, "", "📊", "#3B82F6")
    with s2:
        render_metric_card("Successful", successful, "", "✅", "#10B981")
    with s3:
        render_metric_card("Failed", total_queries - successful, "", "❌", "#EF4444")
    with s4:
        render_metric_card("Avg Groundedness", f"{avg_score:.0%}" if scores else "—", "", "🛡️", "#8B5CF6")

    st.markdown("")

    # ── Two-column layout ──
    col_left, col_right = st.columns(2, gap="medium")

    with col_left:
        # ── Groundedness Gauge ──
        render_glass_card("Groundedness Score", icon="🎯")
        if scores:
            fig_gauge = create_gauge_chart(avg_score, "Average Groundedness")
            st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})
        else:
            render_empty_state("No groundedness data yet", "📊")

        # ── Input Guardrail Tester ──
        st.markdown("")
        render_glass_card("Input Guardrail Tester", icon="🧪",
                          content="Test a query against input guardrails without running RAG")

        test_query = st.text_input(
            "Test query:",
            placeholder="Enter a test query to check safety...",
            key="guardrail_test_input"
        )

        if st.button("🔒 Test Guardrail", key="test_guardrail_btn"):
            if test_query.strip():
                is_safe, reason = check_input_guardrail(test_query.strip())
                if is_safe:
                    st.markdown(f"""
                    <div class="glass-card" style="border-left:4px solid #10B981;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-size:1.5rem;">✅</span>
                            <div>
                                <div style="font-size:0.95rem; font-weight:600; color:#10B981;">
                                    Query Passed
                                </div>
                                <div style="font-size:0.82rem; color:#94A3B8; margin-top:2px;">
                                    {reason}
                                </div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="glass-card" style="border-left:4px solid #EF4444;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-size:1.5rem;">🚫</span>
                            <div>
                                <div style="font-size:0.95rem; font-weight:600; color:#EF4444;">
                                    Query Blocked
                                </div>
                                <div style="font-size:0.82rem; color:#94A3B8; margin-top:2px;">
                                    {reason}
                                </div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

    with col_right:
        # ── Groundedness Trend ──
        render_glass_card("Groundedness Trend", icon="📈")
        if len(scores) >= 2:
            x_vals = list(range(1, len(scores) + 1))
            fig_trend = create_line_chart(x_vals, scores, "#8B5CF6", "Score per Query")
            st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
        elif scores:
            st.markdown(f"""
            <div style="text-align:center; padding:40px; color:#64748B; font-size:0.88rem;">
                Only 1 query recorded. More queries needed for trend visualization.
            </div>""", unsafe_allow_html=True)
        else:
            render_empty_state("Run some queries to see trends", "📈")

        # ── Citation Coverage Stats ──
        st.markdown("")
        render_glass_card("Citation Coverage Metrics", icon="📎")

        if history:
            intents = {}
            for q in history:
                intent = q.get("intent", "Unknown")
                intents[intent] = intents.get(intent, 0) + 1

            for intent, count in sorted(intents.items(), key=lambda x: x[1], reverse=True):
                pct = count / total_queries * 100
                color = {
                    "RESEARCH_SYNTHESIS": "#8B5CF6",
                    "FACTUAL_QA": "#3B82F6",
                    "DOCUMENT_SUMMARY": "#10B981",
                    "EVIDENCE_EXTRACTION": "#F59E0B",
                }.get(intent, "#64748B")

                st.markdown(f"""
                <div style="margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span style="font-size:0.82rem; color:#CBD5E1; font-weight:500;">{intent}</span>
                        <span style="font-size:0.78rem; color:#64748B;">{count} ({pct:.0f}%)</span>
                    </div>
                    <div style="background:rgba(15,23,42,0.5); border-radius:4px; height:6px;
                         overflow:hidden;">
                        <div style="background:{color}; height:100%; width:{pct}%;
                             border-radius:4px; transition:width 0.5s;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            render_empty_state("No queries processed yet", "📎")

    st.markdown("")

    # ── Audit History ──
    render_glass_card("Security Audit History", icon="📜",
                      content="Log of all guardrail checks from this session")

    if history:
        for q in reversed(history[-20:]):
            success = q.get("success", False)
            color = "#10B981" if success else "#EF4444"
            score = q.get("groundedness", "N/A")
            intent = q.get("intent", "N/A")
            query_text = q.get("query", "")[:60]
            timestamp = q.get("timestamp", "")[:19].replace("T", " ")

            st.markdown(f"""
            <div class="source-card" style="border-left-color:{color};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size:0.85rem; color:#E2E8F0; font-weight:500;">
                            {query_text}{'...' if len(q.get('query', '')) > 60 else ''}
                        </div>
                        <div style="font-size:0.72rem; color:#64748B; margin-top:3px;">
                            {timestamp}
                        </div>
                    </div>
                    <div style="display:flex; gap:6px; align-items:center;">
                        {render_badge(intent, "info")}
                        {render_badge(score, "pass" if success else "warning")}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        render_empty_state("No audit history yet. Run some queries to populate this log.", "📜")

    st.markdown('</div>', unsafe_allow_html=True)
