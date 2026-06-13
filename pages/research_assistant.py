"""
NovaRAG Research Studio — Research Assistant Page.

Dedicated page for querying papers with intent-aware rendering,
query history, citation panel, and safety audit.
"""

import os
import datetime
import streamlit as st
from utils.components import (
    render_page_header, render_glass_card, render_source_card,
    render_thinking_card, render_badge
)
from ingest import list_documents
from rag_pipeline import run_rag_query
from guardrails import check_input_guardrail, check_output_guardrail, validate_citations
from intent_classifier import classify_intent, get_intent_display_info, QueryIntent
from pdf_generator import generate_pdf_report


def render(collection, csv_papers, **kwargs):
    """Renders the Research Assistant page."""

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Research Assistant",
        "Query indexed papers, review safety audits, and generate research briefs",
        icon="🔍"
    )

    env_api_key = os.getenv("GEMINI_API_KEY", "")

    # ── Layout: Main + History Sidebar ──
    col_main, col_history = st.columns([3, 1], gap="medium")

    with col_history:
        render_glass_card("Query History", icon="🕐")
        history = st.session_state.get("query_history", [])
        if history:
            for i, q in enumerate(reversed(history[-15:])):
                query_text = q.get("query", "")[:40]
                success = q.get("success", False)
                color = "#10B981" if success else "#EF4444"
                st.markdown(f"""
                <div style="padding:6px 10px; border-left:2px solid {color};
                     margin-bottom:4px; border-radius:4px;
                     background:rgba(15,23,42,0.3); cursor:pointer;">
                    <div style="font-size:0.78rem; color:#CBD5E1; font-weight:500;
                         white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        {query_text}...
                    </div>
                    <div style="font-size:0.65rem; color:#64748B; margin-top:2px;">
                        {q.get('intent', 'N/A')} · {q.get('groundedness', 'N/A')}
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center; padding:20px; color:#64748B; font-size:0.82rem;">
                No queries yet.<br>Start researching!
            </div>""", unsafe_allow_html=True)

    with col_main:
        # ── Document Scope Selector ──
        scope_docs = list_documents(collection)
        scope_options = ["🌐 All Papers (Full Corpus)"] + [
            f"📄 {d['title']}" for d in scope_docs
        ]
        scope_doc_ids = [None] + [d["document_id"] for d in scope_docs]

        selected_scope_idx = st.selectbox(
            "Query Scope",
            range(len(scope_options)),
            format_func=lambda i: scope_options[i],
            index=0,
            help="Restrict retrieval to a specific uploaded document, or search the full corpus."
        )
        selected_doc_id = scope_doc_ids[selected_scope_idx]
        is_single_doc_mode = selected_doc_id is not None

        # Check for pre-filled query from landing page
        default_query = ""
        if "prefilled_query" in st.session_state and st.session_state["prefilled_query"]:
            default_query = st.session_state["prefilled_query"]
            st.session_state["prefilled_query"] = None
            st.session_state["run_search"] = True

        # ── Search Bar ──
        col_q, col_btn = st.columns([5, 1])
        with col_q:
            placeholder_text = (
                "e.g., Summarize this paper's methodology and findings..."
                if is_single_doc_mode
                else "e.g., Attention Mechanism in Transformers or Deep Learning Optimization..."
            )
            search_query = st.text_input(
                "Enter research topic or query:",
                value=default_query,
                placeholder=placeholder_text,
                label_visibility="collapsed"
            )
        with col_btn:
            btn_label = "📄 Summarize" if is_single_doc_mode else "⚡ Synthesize"
            search_btn = st.button(btn_label, use_container_width=True, type="primary")


        # ── Perform Search ──
        if search_btn or (search_query and st.session_state.get("run_search", False)):
            st.session_state["run_search"] = False

            effective_query = search_query.strip()
            if is_single_doc_mode and not effective_query:
                doc_title = scope_docs[selected_scope_idx - 1]["title"]
                effective_query = f"Summarize the key findings, methodology, and conclusions of: {doc_title}"

            if not effective_query:
                st.warning("Please enter a valid search topic.")
            else:
                # ── INPUT GUARDRAILS ──
                is_safe, input_reason = check_input_guardrail(effective_query)

                st.markdown("#### 🔒 Security & Groundedness Audit")
                col_g1, col_g2, col_g3 = st.columns(3)

                with col_g1:
                    if is_safe:
                        st.markdown(
                            f'{render_badge("Passed", "pass")} '
                            'Input Guardrail: Clear', unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f'{render_badge("Blocked", "fail")} '
                            f'Input Guardrail: {input_reason}', unsafe_allow_html=True)

                if not is_safe:
                    st.error("⚠️ Query blocked by safety guidelines. Please modify your query.")
                else:
                    # ── INTENT CLASSIFICATION ──
                    detected_intent = classify_intent(effective_query, is_single_doc_mode)
                    intent_info = get_intent_display_info(detected_intent)

                    badge_text = intent_info["icon"] + " " + intent_info["label"]
                    badge_variant = intent_info["badge_class"].replace("badge-", "")
                    st.markdown(
                        f'<div style="margin-bottom:10px;">'
                        f'{render_badge(badge_text, badge_variant)} '
                        f'<span style="color:#64748B; font-size:0.82rem;">{intent_info["description"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    # ── Retrieve settings from session state ──
                    settings = st.session_state.get("rag_settings", {})

                    # ── RAG PIPELINE ──
                    spinner_msg = {
                        QueryIntent.FACTUAL_QA: "Searching sources for a direct answer...",
                        QueryIntent.EVIDENCE_EXTRACTION: "Extracting evidence-backed facts...",
                        QueryIntent.DOCUMENT_SUMMARY: "Retrieving excerpts, reranking, summarizing...",
                        QueryIntent.RESEARCH_SYNTHESIS: "Retrieving from ChromaDB, reranking with FlashRank, analyzing...",
                    }[detected_intent]

                    with st.spinner(spinner_msg):
                        rag_result = run_rag_query(
                            query=effective_query,
                            api_key=st.session_state.get("api_key", env_api_key),
                            document_id=selected_doc_id,
                            query_intent=detected_intent.value,
                            top_k_retrieve=settings.get("top_k_retrieve", 20),
                            top_n_rerank=settings.get("top_n_rerank", 7),
                            max_chunks_per_doc=settings.get("max_chunks_per_doc", 3),
                        )

                    if not rag_result["success"] and rag_result.get("status") == "error":
                        st.error(rag_result["message"])
                        # Log failed query
                        _log_query(effective_query, detected_intent.value, False, 0)
                    else:
                        # ── OUTPUT GUARDRAILS ──
                        contexts = [chunk["text"] for chunk in rag_result["raw_chunks"]]

                        if rag_result["status"] == "success":
                            output_safe, output_reason, overlap_score = check_output_guardrail(
                                rag_result["summary"], contexts
                            )
                            citation_info = validate_citations(
                                rag_result["summary"], rag_result["raw_chunks"],
                                query_intent=detected_intent.value
                            )
                        else:
                            output_safe, output_reason, overlap_score = (
                                True, "Fallback raw data. Grounding N/A.", 1.0
                            )
                            citation_info = None

                        with col_g2:
                            if rag_result["status"] == "success":
                                if output_safe:
                                    st.markdown(
                                        f'{render_badge("Passed", "pass")} '
                                        f'Groundedness: {overlap_score:.1%}',
                                        unsafe_allow_html=True)
                                else:
                                    st.markdown(
                                        f'{render_badge("Warning", "warning")} '
                                        f'Groundedness: {overlap_score:.1%} (Hallucination Risk)',
                                        unsafe_allow_html=True)
                            else:
                                st.markdown(
                                    f'{render_badge("Info", "info")} '
                                    'Groundedness: N/A (API Offline)',
                                    unsafe_allow_html=True)

                        with col_g3:
                            if citation_info and rag_result["status"] == "success":
                                if citation_info.get("is_refusal"):
                                    st.markdown(
                                        f'{render_badge("Passed", "pass")} '
                                        'Citations: N/A (Refusal)',
                                        unsafe_allow_html=True)
                                elif detected_intent == QueryIntent.EVIDENCE_EXTRACTION:
                                    st.markdown(
                                        f'{render_badge("Passed", "pass")} '
                                        'Citations: N/A (Extracted)',
                                        unsafe_allow_html=True)
                                else:
                                    cov = citation_info["citation_coverage"]
                                    if cov >= 0.6:
                                        st.markdown(
                                            f'{render_badge("Passed", "pass")} '
                                            f'Citations: {cov:.1%} coverage',
                                            unsafe_allow_html=True)
                                    else:
                                        st.markdown(
                                            f'{render_badge("Warning", "warning")} '
                                            f'Citations: {cov:.1%} coverage (Low)',
                                            unsafe_allow_html=True)
                            else:
                                st.markdown(
                                    f'{render_badge("Info", "info")} '
                                    'Citations: N/A',
                                    unsafe_allow_html=True)

                        st.markdown("---")

                        # Log successful query
                        _log_query(
                            effective_query, detected_intent.value,
                            rag_result.get("success", False), overlap_score,
                            rag_result.get("chunks_retrieved_count", 0),
                            rag_result.get("unique_papers_count", 0),
                        )

                        # ── RESULTS (intent-aware rendering) ──
                        if rag_result["status"] == "fallback":
                            st.warning(f"⚠️ **Resiliency Fallback Engaged:** {rag_result['message']}")

                        if detected_intent == QueryIntent.FACTUAL_QA:
                            _render_factual_qa(rag_result)
                        elif detected_intent == QueryIntent.EVIDENCE_EXTRACTION:
                            _render_evidence_extraction(rag_result)
                        else:
                            _render_synthesis(rag_result, search_query, is_safe,
                                             output_safe, overlap_score, citation_info,
                                             env_api_key)

    st.markdown('</div>', unsafe_allow_html=True)


def _log_query(query, intent, success, score, chunks=0, papers=0):
    """Logs a query to session state history for analytics."""
    if "query_history" not in st.session_state:
        st.session_state["query_history"] = []
    st.session_state["query_history"].append({
        "query": query,
        "intent": intent,
        "success": success,
        "groundedness_score": score,
        "groundedness": f"{score:.1%}" if score else "N/A",
        "chunks_retrieved": chunks,
        "unique_papers": papers,
        "timestamp": datetime.datetime.now().isoformat(),
    })


def _render_factual_qa(rag_result):
    """Renders factual QA results."""
    if rag_result.get("thinking"):
        with st.expander("🔄 Reasoning Flow", expanded=False):
            render_thinking_card(rag_result["thinking"])

    st.markdown("### 🎯 Direct Answer")
    st.markdown(
        f'<div class="glass-card" style="border-left: 4px solid #10B981; '
        f'padding: 20px 24px;">'
        f'<div style="font-size: 1.1rem; color: #E2E8F0; line-height: 1.7;">'
        f'{rag_result["summary"]}'
        f'</div></div>',
        unsafe_allow_html=True
    )

    st.markdown("---")
    with st.expander("📚 Retrieved Sources", expanded=False):
        for chunk in rag_result["raw_chunks"]:
            render_source_card(chunk)


def _render_evidence_extraction(rag_result):
    """Renders evidence extraction results."""
    if rag_result.get("thinking"):
        with st.expander("🔄 Reasoning Flow", expanded=False):
            render_thinking_card(rag_result["thinking"])

    st.markdown("### 🔍 Extracted Evidence")
    st.markdown(
        f'<div class="glass-card" style="border-left: 4px solid #60A5FA; '
        f'padding: 20px 24px;">'
        f'<div style="font-size: 1.05rem; color: #E2E8F0; line-height: 1.8; white-space: pre-wrap;">'
        f'{rag_result["summary"]}'
        f'</div></div>',
        unsafe_allow_html=True
    )

    st.markdown("---")
    with st.expander("📚 Retrieved Sources", expanded=False):
        for chunk in rag_result["raw_chunks"]:
            render_source_card(chunk)


def _render_synthesis(rag_result, search_query, is_safe, output_safe,
                      overlap_score, citation_info, env_api_key):
    """Renders document summary / research synthesis results."""
    if rag_result.get("thinking"):
        with st.expander("🔄 Reasoning Flow", expanded=True):
            render_thinking_card(rag_result["thinking"])

    st.markdown("### 📝 Synthesis Summary")
    st.markdown(rag_result["summary"])

    # ── PDF REPORT ──
    reports_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
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
        "citation_info": citation_info,
    }

    try:
        generate_pdf_report(
            output_path=report_path,
            query=search_query,
            summary=rag_result["summary"],
            sources=rag_result["raw_chunks"],
            guardrail_results=guardrail_data,
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
        render_source_card(chunk)
