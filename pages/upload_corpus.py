"""
NovaRAG Research Studio — Upload & Corpus Management Page.

Upload PDFs, manage the ChromaDB vector index, view corpus statistics,
and delete/re-index documents.
"""

import streamlit as st
from utils.components import (
    render_page_header, render_glass_card, render_metric_card,
    render_empty_state
)
from utils.helpers import (
    get_category_distribution, CATEGORY_COLORS, categorize_paper,
    load_papers_csv
)
from ingest import (
    get_chroma_client, get_collection, add_pdf_to_vector_store,
    delete_document, list_documents
)


def render(collection, csv_papers, **kwargs):
    """Renders the Upload & Corpus Management page."""

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Upload & Corpus Management",
        "Add, inspect, and manage research papers in the ChromaDB vector index",
        icon="📤"
    )

    # ── Corpus Statistics ──
    docs = list_documents(collection)
    total_docs = len(docs)
    total_pages = sum(d["total_pages"] for d in docs)
    total_chunks = collection.count() if collection else 0

    s1, s2, s3, s4 = st.columns(4, gap="medium")
    with s1:
        render_metric_card("Indexed Papers", total_docs, "files", "📄", "#3B82F6")
    with s2:
        render_metric_card("Total Pages", f"{total_pages:,}", "pages", "📖", "#8B5CF6")
    with s3:
        render_metric_card("Vector Chunks", f"{total_chunks:,}", "chunks", "🧬", "#10B981")
    with s4:
        cat_dist = get_category_distribution(csv_papers)
        render_metric_card("Categories", len(cat_dist), "domains", "🏷️", "#F59E0B")

    st.markdown("")

    # ── Upload Section ──
    render_glass_card("Upload Research Papers", icon="📤",
                      content="Upload PDF files to ingest and index page-by-page into the vector store")

    uploaded_files = st.file_uploader(
        "Upload PDFs to ingest:",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        st.markdown(f"""
        <div class="glass-card" style="border-left:3px solid #8B5CF6;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.3rem;">📎</span>
                <div>
                    <div style="font-size:0.9rem; font-weight:600; color:#E2E8F0;">
                        {len(uploaded_files)} file(s) selected
                    </div>
                    <div style="font-size:0.78rem; color:#64748B;">
                        {', '.join(f.name for f in uploaded_files[:3])}{'...' if len(uploaded_files) > 3 else ''}
                    </div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if st.button("🚀 Process & Index Papers", type="primary", use_container_width=True):
            success_count = 0
            fail_count = 0
            ingested_doc_ids = []
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.markdown(f"""
                <div style="display:flex; align-items:center; gap:8px; color:#CBD5E1; font-size:0.88rem;">
                    <div class="pulse-dot" style="width:8px; height:8px; border-radius:50%;
                         background:#8B5CF6; animation: pulseAnim 1s infinite;"></div>
                    Ingesting <strong>{uploaded_file.name}</strong>...
                </div>
                <style>
                @keyframes pulseAnim {{
                    0%, 100% {{ opacity: 0.3; }}
                    50% {{ opacity: 1; }}
                }}
                </style>""", unsafe_allow_html=True)
                try:
                    file_bytes = uploaded_file.read()
                    doc_id, pages_count = add_pdf_to_vector_store(
                        collection=collection,
                        file_bytes=file_bytes,
                        file_name=uploaded_file.name
                    )
                    if pages_count > 0:
                        success_count += 1
                        ingested_doc_ids.append((uploaded_file.name, doc_id))
                    else:
                        fail_count += 1
                except Exception as ingest_err:
                    st.error(f"Error ingesting {uploaded_file.name}: {ingest_err}")
                    fail_count += 1
                progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.empty()
            progress_bar.empty()

            if success_count > 0:
                st.success(f"✅ Indexed {success_count} research paper(s) into ChromaDB!")
                st.session_state["last_ingested"] = ingested_doc_ids
                st.rerun()
            if fail_count > 0:
                st.warning(f"⚠️ Failed to process {fail_count} file(s).")

    st.markdown("---")

    # ── Indexed Documents List ──
    render_glass_card("Indexed Documents", icon="📂",
                      content="Manage documents currently in the vector index")

    if not docs:
        render_empty_state("No documents indexed yet. Upload PDFs above to get started.", "📭")
    else:
        # Category breakdown
        cat_counts = {}
        for d in docs:
            cat = categorize_paper(d.get("title", ""))
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        # Show category badges
        cat_html = " ".join([
            f'<span class="cat-badge" style="background:{CATEGORY_COLORS.get(c, "#64748B")}20; '
            f'color:{CATEGORY_COLORS.get(c, "#64748B")}; '
            f'border:1px solid {CATEGORY_COLORS.get(c, "#64748B")}33; margin-right:6px; margin-bottom:4px;">'
            f'{c} ({v})</span>'
            for c, v in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
        ])
        st.markdown(f'<div style="margin-bottom:16px;">{cat_html}</div>', unsafe_allow_html=True)

        for idx, doc in enumerate(docs):
            cat = categorize_paper(doc.get("title", ""))
            cat_color = CATEGORY_COLORS.get(cat, "#64748B")

            col_info, col_actions = st.columns([5, 1])

            with col_info:
                title_display = doc.get("title", "Unknown").replace(".pdf", "").replace("_", " ")
                st.markdown(f"""
                <div class="paper-card" style="border-left:3px solid {cat_color};">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <div style="font-size:0.92rem; font-weight:600; color:#E2E8F0; margin-bottom:4px;">
                                📄 {title_display}
                            </div>
                            <div style="display:flex; gap:12px; align-items:center;">
                                <span class="cat-badge" style="background:{cat_color}20;
                                      color:{cat_color}; border:1px solid {cat_color}33;">
                                    {cat}
                                </span>
                                <span style="font-size:0.75rem; color:#64748B;">
                                    {doc['total_pages']} pages
                                </span>
                                <span style="font-size:0.75rem; color:#64748B;">
                                    ID: {doc['document_id'][:12]}...
                                </span>
                            </div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

            with col_actions:
                st.markdown("<div style='padding-top:12px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"del_{doc['document_id']}",
                             help=f"Delete {doc['title']}", use_container_width=True):
                    delete_document(collection, doc["document_id"])
                    st.success(f"Deleted '{doc['title']}'")
                    st.rerun()

        st.markdown(
            f'<div style="text-align:right; color:#64748B; font-size:0.78rem; '
            f'margin-top:8px; padding-right:16px;">'
            f'Total: {len(docs)} indexed documents'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)
