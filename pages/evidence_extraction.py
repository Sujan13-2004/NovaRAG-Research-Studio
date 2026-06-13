"""
NovaRAG Research Studio — Evidence Extraction Page.

Dedicated page for extracting facts, page numbers, supporting quotes,
and building evidence matrices from research papers.
"""

import os
import datetime
import streamlit as st
from utils.components import (
    render_page_header, render_glass_card, render_source_card,
    render_thinking_card, render_badge, render_empty_state
)
from ingest import list_documents
from rag_pipeline import run_rag_query
from guardrails import check_input_guardrail


def render(collection, csv_papers, **kwargs):
    """Renders the Evidence Extraction page."""

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Evidence Extraction",
        "Extract facts, page numbers, supporting quotes, and build evidence matrices",
        icon="🔎"
    )

    env_api_key = os.getenv("GEMINI_API_KEY", "")

    # ── Document Scope ──
    render_glass_card("Document Scope", icon="📄",
                      content="Select a specific document or search the entire corpus")

    scope_docs = list_documents(collection)
    scope_options = ["🌐 All Papers (Full Corpus)"] + [
        f"📄 {d['title']}" for d in scope_docs
    ]
    scope_doc_ids = [None] + [d["document_id"] for d in scope_docs]

    selected_scope_idx = st.selectbox(
        "Document scope:",
        range(len(scope_options)),
        format_func=lambda i: scope_options[i],
        index=0,
        label_visibility="collapsed"
    )
    selected_doc_id = scope_doc_ids[selected_scope_idx]

    st.markdown("")

    # ── Query Input ──
    render_glass_card("Evidence Query", icon="🔍",
                      content="Describe the facts or evidence you want to extract")

    query = st.text_area(
        "Enter your evidence extraction query:",
        placeholder="e.g., Extract all facts about model accuracy, dataset sizes, and evaluation metrics...",
        height=100,
        label_visibility="collapsed"
    )

    col_btn, col_space = st.columns([1, 3])
    with col_btn:
        extract_btn = st.button("🔎 Extract Evidence", type="primary", use_container_width=True)

    if extract_btn:
        if not query.strip():
            st.warning("Please enter an evidence extraction query.")
        else:
            # Input guardrail
            is_safe, input_reason = check_input_guardrail(query.strip())
            if not is_safe:
                st.error(f"⚠️ Query blocked: {input_reason}")
            else:
                settings = st.session_state.get("rag_settings", {})

                with st.spinner("Extracting evidence-backed facts from document excerpts..."):
                    rag_result = run_rag_query(
                        query=query.strip(),
                        api_key=st.session_state.get("api_key", env_api_key),
                        document_id=selected_doc_id,
                        query_intent="EVIDENCE_EXTRACTION",
                        top_k_retrieve=settings.get("top_k_retrieve", 20),
                        top_n_rerank=settings.get("top_n_rerank", 7),
                        max_chunks_per_doc=settings.get("max_chunks_per_doc", 3),
                    )

                if not rag_result["success"] and rag_result.get("status") == "error":
                    st.error(rag_result["message"])
                else:
                    # Audit
                    st.markdown("#### 🔒 Extraction Audit")
                    ea1, ea2 = st.columns(2)
                    with ea1:
                        st.markdown(f'{render_badge("Passed", "pass")} Input Guardrail: Clear',
                                    unsafe_allow_html=True)
                    with ea2:
                        chunks_count = rag_result.get("chunks_retrieved_count", 0)
                        papers_count = rag_result.get("unique_papers_count", 0)
                        st.markdown(
                            f'{render_badge(f"{chunks_count} chunks", "info")} '
                            f'from {render_badge(f"{papers_count} papers", "info")}',
                            unsafe_allow_html=True)

                    st.markdown("---")

                    if rag_result["status"] == "fallback":
                        st.warning(f"⚠️ **Fallback:** {rag_result['message']}")

                    if rag_result.get("thinking"):
                        with st.expander("🔄 Reasoning Flow", expanded=False):
                            render_thinking_card(rag_result["thinking"])

                    # ── Evidence Display ──
                    st.markdown("### 🔍 Extracted Evidence")

                    summary = rag_result.get("summary", "")
                    if "Unsupported by document" in summary:
                        st.markdown(f"""
                        <div class="glass-card" style="border-left:4px solid #F59E0B; padding:20px;">
                            <div style="font-size:1rem; color:#F59E0B; font-weight:600; margin-bottom:8px;">
                                ⚠️ No Evidence Found
                            </div>
                            <div style="font-size:0.92rem; color:#94A3B8;">
                                The query could not be supported by the available document excerpts.
                            </div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        # Parse evidence blocks
                        evidence_blocks = _parse_evidence(summary)

                        if evidence_blocks:
                            for i, block in enumerate(evidence_blocks):
                                confidence = block.get("confidence", "Medium")
                                conf_color = {"High": "#10B981", "Medium": "#F59E0B", "Low": "#EF4444"}.get(
                                    confidence, "#64748B")

                                st.markdown(f"""
                                <div class="evidence-row">
                                    <div style="display:flex; justify-content:space-between; align-items:center;
                                         margin-bottom:8px;">
                                        <span style="font-size:0.88rem; font-weight:600; color:#E2E8F0;">
                                            Fact {i + 1}
                                        </span>
                                        <span class="badge" style="background:{conf_color}20; color:{conf_color};
                                              border:1px solid {conf_color}33;">
                                            {confidence} Confidence
                                        </span>
                                    </div>
                                    <div style="font-size:0.9rem; color:#CBD5E1; margin-bottom:6px;
                                         line-height:1.6;">
                                        {block.get('fact', '')}
                                    </div>
                                    <div style="display:flex; gap:16px; margin-top:8px;">
                                        <span style="font-size:0.78rem; color:#64748B;">
                                            📄 Page: {block.get('page', 'N/A')}
                                        </span>
                                    </div>
                                    <div style="font-size:0.82rem; color:#94A3B8; font-style:italic;
                                         margin-top:6px; padding:8px 12px; background:rgba(15,23,42,0.4);
                                         border-radius:6px; line-height:1.5;">
                                        "{block.get('quote', '')}"
                                    </div>
                                </div>""", unsafe_allow_html=True)

                            # Evidence matrix summary
                            st.markdown("")
                            render_glass_card("Evidence Matrix Summary", icon="📊")
                            em1, em2, em3 = st.columns(3)
                            with em1:
                                st.markdown(f"""
                                <div class="metric-card" style="border-left:3px solid #10B981;">
                                    <div class="metric-label">Total Facts</div>
                                    <div class="metric-value">{len(evidence_blocks)}</div>
                                </div>""", unsafe_allow_html=True)
                            with em2:
                                high = sum(1 for b in evidence_blocks if b.get("confidence") == "High")
                                st.markdown(f"""
                                <div class="metric-card" style="border-left:3px solid #F59E0B;">
                                    <div class="metric-label">High Confidence</div>
                                    <div class="metric-value">{high}</div>
                                </div>""", unsafe_allow_html=True)
                            with em3:
                                pages = set(b.get("page", "") for b in evidence_blocks if b.get("page"))
                                st.markdown(f"""
                                <div class="metric-card" style="border-left:3px solid #3B82F6;">
                                    <div class="metric-label">Unique Pages</div>
                                    <div class="metric-value">{len(pages)}</div>
                                </div>""", unsafe_allow_html=True)
                        else:
                            # Fallback: display raw text
                            st.markdown(f"""
                            <div class="glass-card" style="border-left:4px solid #60A5FA; padding:20px;">
                                <div style="font-size:1.05rem; color:#E2E8F0; line-height:1.8;
                                     white-space:pre-wrap;">{summary}</div>
                            </div>""", unsafe_allow_html=True)

                    st.markdown("---")

                    # ── Sources ──
                    with st.expander("📚 Retrieved Sources", expanded=False):
                        for chunk in rag_result["raw_chunks"]:
                            render_source_card(chunk)

                    # Log query
                    if "query_history" not in st.session_state:
                        st.session_state["query_history"] = []
                    st.session_state["query_history"].append({
                        "query": query.strip(),
                        "intent": "EVIDENCE_EXTRACTION",
                        "success": rag_result.get("success", False),
                        "groundedness_score": 0,
                        "groundedness": "N/A",
                        "chunks_retrieved": rag_result.get("chunks_retrieved_count", 0),
                        "unique_papers": rag_result.get("unique_papers_count", 0),
                        "timestamp": datetime.datetime.now().isoformat(),
                    })

    st.markdown('</div>', unsafe_allow_html=True)


def _parse_evidence(text):
    """Parses structured evidence extraction output into blocks."""
    import re
    blocks = []
    current = {}

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            if current.get("fact"):
                blocks.append(current)
                current = {}
            continue

        if line.lower().startswith("fact:"):
            if current.get("fact"):
                blocks.append(current)
            current = {"fact": line[5:].strip()}
        elif line.lower().startswith("page:"):
            current["page"] = line[5:].strip()
        elif line.lower().startswith("supporting quote:"):
            quote = line[17:].strip().strip('"')
            current["quote"] = quote
        elif line.lower().startswith("confidence:"):
            current["confidence"] = line[11:].strip()
        elif current.get("fact") and not current.get("quote"):
            current["fact"] += " " + line

    if current.get("fact"):
        blocks.append(current)

    return blocks
