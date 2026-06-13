"""
NovaRAG Research Studio — Research Synthesis Page.

Dedicated multi-paper synthesis page for literature reviews,
comparative analysis, and academic report generation.
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
from pdf_generator import generate_pdf_report


def render(collection, csv_papers, **kwargs):
    """Renders the Research Synthesis page."""

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Research Synthesis",
        "Generate literature reviews, compare papers, and produce multi-paper academic reports",
        icon="🔬"
    )

    env_api_key = os.getenv("GEMINI_API_KEY", "")

    # ── Mode Selector ──
    render_glass_card("Synthesis Mode", icon="🎯",
                      content="Choose the type of research synthesis to generate")

    mode = st.radio(
        "Select synthesis mode:",
        ["📝 Literature Review", "🔄 Paper Comparison", "🧬 Multi-Paper Synthesis"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("")

    # ── Common: Document Selection ──
    docs = list_documents(collection)

    if mode == "🔄 Paper Comparison":
        render_glass_card("Select Papers to Compare", icon="📄")
        if docs:
            paper_options = [f"{d['title']}" for d in docs]
            selected_papers = st.multiselect(
                "Select 2 or more papers:",
                options=paper_options,
                default=paper_options[:2] if len(paper_options) >= 2 else paper_options,
                help="Choose papers to compare side-by-side"
            )

            if selected_papers and len(selected_papers) >= 2:
                paper_titles = ", ".join(selected_papers[:5])
                default_query = f"Compare the methodologies, key findings, and conclusions of: {paper_titles}"
            else:
                default_query = ""
                if selected_papers and len(selected_papers) < 2:
                    st.info("Please select at least 2 papers for comparison.")
        else:
            st.info("No documents indexed. Please upload papers first.")
            default_query = ""
    else:
        default_query = ""

    # ── Query Input ──
    render_glass_card("Research Query", icon="💬")

    if mode == "📝 Literature Review":
        placeholder = "e.g., Generate a literature review on federated learning in healthcare..."
    elif mode == "🔄 Paper Comparison":
        placeholder = "e.g., Compare the accuracy and methodologies of the selected papers..."
    else:
        placeholder = "e.g., Synthesize findings on deep learning for medical imaging across all papers..."

    query = st.text_area(
        "Enter your research query:",
        value=default_query,
        placeholder=placeholder,
        height=100,
        label_visibility="collapsed"
    )

    col_btn, col_space = st.columns([1, 3])
    with col_btn:
        generate_btn = st.button("🔬 Generate Synthesis", type="primary", use_container_width=True)

    if generate_btn:
        if not query.strip():
            st.warning("Please enter a research query.")
        else:
            # ── Input Guardrail ──
            is_safe, input_reason = check_input_guardrail(query.strip())
            if not is_safe:
                st.error(f"⚠️ Query blocked: {input_reason}")
            else:
                # ── RAG Pipeline (forced RESEARCH_SYNTHESIS intent) ──
                settings = st.session_state.get("rag_settings", {})

                with st.spinner("Retrieving from corpus, reranking with FlashRank, synthesizing across sources..."):
                    rag_result = run_rag_query(
                        query=query.strip(),
                        api_key=st.session_state.get("api_key", env_api_key),
                        query_intent="RESEARCH_SYNTHESIS",
                        top_k_retrieve=settings.get("top_k_retrieve", 20),
                        top_n_rerank=settings.get("top_n_rerank", 7),
                        max_chunks_per_doc=settings.get("max_chunks_per_doc", 3),
                    )

                if not rag_result["success"] and rag_result.get("status") == "error":
                    st.error(rag_result["message"])
                else:
                    # ── Guardrails ──
                    contexts = [c["text"] for c in rag_result["raw_chunks"]]
                    if rag_result["status"] == "success":
                        output_safe, output_reason, overlap_score = check_output_guardrail(
                            rag_result["summary"], contexts
                        )
                        citation_info = validate_citations(
                            rag_result["summary"], rag_result["raw_chunks"],
                            query_intent="RESEARCH_SYNTHESIS"
                        )
                    else:
                        output_safe, overlap_score = True, 1.0
                        citation_info = None

                    # ── Audit Badges ──
                    st.markdown("#### 🔒 Security & Groundedness Audit")
                    ag1, ag2, ag3 = st.columns(3)
                    with ag1:
                        st.markdown(f'{render_badge("Passed", "pass")} Input Guardrail: Clear',
                                    unsafe_allow_html=True)
                    with ag2:
                        if rag_result["status"] == "success":
                            var = "pass" if output_safe else "warning"
                            st.markdown(
                                f'{render_badge("Passed" if output_safe else "Warning", var)} '
                                f'Groundedness: {overlap_score:.1%}',
                                unsafe_allow_html=True)
                    with ag3:
                        if citation_info:
                            cov = citation_info.get("citation_coverage", 0)
                            var = "pass" if cov >= 0.6 else "warning"
                            st.markdown(
                                f'{render_badge("Passed" if cov >= 0.6 else "Warning", var)} '
                                f'Citations: {cov:.1%}',
                                unsafe_allow_html=True)

                    st.markdown("---")

                    # ── Results ──
                    if rag_result["status"] == "fallback":
                        st.warning(f"⚠️ **Fallback:** {rag_result['message']}")

                    if rag_result.get("thinking"):
                        with st.expander("🔄 Reasoning Flow", expanded=True):
                            render_thinking_card(rag_result["thinking"])

                    st.markdown("### 📝 Research Synthesis")
                    st.markdown(rag_result["summary"])

                    # ── PDF Report ──
                    reports_dir = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
                    os.makedirs(reports_dir, exist_ok=True)
                    clean_q = "".join(c if c.isalnum() else "_" for c in query).lower()[:15]
                    report_fn = f"synthesis_{clean_q}_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
                    report_path = os.path.join(reports_dir, report_fn)

                    try:
                        generate_pdf_report(
                            output_path=report_path,
                            query=query.strip(),
                            summary=rag_result["summary"],
                            sources=rag_result["raw_chunks"],
                            guardrail_results={
                                "input_safe": True,
                                "output_safe": output_safe,
                                "output_score": overlap_score,
                                "citation_info": citation_info,
                            },
                        )
                        with open(report_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            label="📥 Download Synthesis Report",
                            data=pdf_bytes,
                            file_name=f"NovaRAG_Synthesis_{clean_q}.pdf",
                            mime="application/pdf",
                        )
                    except Exception as e:
                        st.error(f"PDF generation failed: {e}")

                    st.markdown("---")

                    # ── Sources ──
                    st.markdown("### 📚 Sources Used")
                    for chunk in rag_result["raw_chunks"]:
                        render_source_card(chunk)

                    # Log query
                    if "query_history" not in st.session_state:
                        st.session_state["query_history"] = []
                    st.session_state["query_history"].append({
                        "query": query.strip(),
                        "intent": "RESEARCH_SYNTHESIS",
                        "success": rag_result.get("success", False),
                        "groundedness_score": overlap_score,
                        "groundedness": f"{overlap_score:.1%}",
                        "chunks_retrieved": rag_result.get("chunks_retrieved_count", 0),
                        "unique_papers": rag_result.get("unique_papers_count", 0),
                        "timestamp": datetime.datetime.now().isoformat(),
                    })

    st.markdown('</div>', unsafe_allow_html=True)
