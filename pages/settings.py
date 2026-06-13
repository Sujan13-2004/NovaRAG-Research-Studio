"""
NovaRAG Research Studio — Settings Page.

Application configuration for API keys, model selection,
retrieval parameters, reranking, and groundedness thresholds.
"""

import os
import streamlit as st
from utils.components import (
    render_page_header, render_glass_card, render_metric_card
)


def render(collection, csv_papers, **kwargs):
    """Renders the Settings page."""

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Settings",
        "Configure API keys, model parameters, retrieval settings, and groundedness thresholds",
        icon="⚙️"
    )

    # Initialize settings in session state
    if "rag_settings" not in st.session_state:
        st.session_state["rag_settings"] = {
            "top_k_retrieve": 20,
            "top_n_rerank": 7,
            "max_chunks_per_doc": 3,
            "groundedness_threshold": 0.55,
        }

    settings = st.session_state["rag_settings"]

    # ── Two-column layout ──
    col_left, col_right = st.columns(2, gap="medium")

    with col_left:
        # ── API Configuration ──
        render_glass_card("API Configuration", icon="🔑",
                          content="Configure your Gemini API key for LLM generation")

        env_key = os.getenv("GEMINI_API_KEY", "")
        if env_key:
            st.markdown(f"""
            <div class="glass-card" style="border-left:3px solid #10B981;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.3rem;">✅</span>
                    <div>
                        <div style="font-size:0.9rem; font-weight:600; color:#10B981;">
                            API Key Configured
                        </div>
                        <div style="font-size:0.78rem; color:#64748B; margin-top:2px;">
                            Loaded from environment variable (GEMINI_API_KEY)
                        </div>
                        <div style="font-size:0.75rem; color:#475569; margin-top:2px;
                             font-family:'JetBrains Mono', monospace;">
                            {env_key[:8]}...{env_key[-4:]}
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            api_key_input = st.text_input(
                "Gemini API Key",
                value=st.session_state.get("api_key", ""),
                type="password",
                help="Enter your Google Gemini API Key"
            )
            if api_key_input:
                st.session_state["api_key"] = api_key_input
                st.success("API key saved to session.")

        st.markdown("")

        # ── Model Information ──
        render_glass_card("Model Configuration", icon="🤖",
                          content="Gemini model fallback chain used for generation")

        models = [
            ("gemini-2.0-flash", "Primary", "#10B981"),
            ("gemini-2.5-flash-lite", "Fallback 1", "#F59E0B"),
            ("gemini-2.5-flash", "Fallback 2", "#EF4444"),
        ]

        for model_name, role, color in models:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:10px; padding:8px 0;
                 border-bottom:1px solid rgba(255,255,255,0.03);">
                <span style="font-size:0.6rem; width:6px; height:6px; border-radius:50%;
                      background:{color}; display:inline-block;"></span>
                <span style="font-size:0.85rem; color:#CBD5E1; font-family:'JetBrains Mono', monospace;">
                    {model_name}
                </span>
                <span class="badge" style="background:{color}20; color:{color};
                      border:1px solid {color}33; font-size:0.6rem;">
                    {role}
                </span>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

        # ── Embedding Model ──
        render_glass_card("Embedding & Reranking", icon="🧬",
                          content="Local models used for vector embeddings and reranking")

        st.markdown("""
        <div style="padding:4px 0;">
            <div style="display:flex; justify-content:space-between; padding:6px 0;
                 border-bottom:1px solid rgba(255,255,255,0.03);">
                <span style="font-size:0.82rem; color:#94A3B8;">Embedding Model</span>
                <span style="font-size:0.82rem; color:#38bdf8; font-family:'JetBrains Mono', monospace;">
                    all-MiniLM-L6-v2
                </span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:6px 0;
                 border-bottom:1px solid rgba(255,255,255,0.03);">
                <span style="font-size:0.82rem; color:#94A3B8;">Reranker</span>
                <span style="font-size:0.82rem; color:#38bdf8; font-family:'JetBrains Mono', monospace;">
                    FlashRank (ms-marco-MiniLM)
                </span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:6px 0;">
                <span style="font-size:0.82rem; color:#94A3B8;">Vector Store</span>
                <span style="font-size:0.82rem; color:#38bdf8; font-family:'JetBrains Mono', monospace;">
                    ChromaDB (Persistent)
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

    with col_right:
        # ── Retrieval Settings ──
        render_glass_card("Retrieval Settings", icon="🔧",
                          content="Configure the RAG pipeline retrieval parameters")

        new_top_k = st.slider(
            "Top-K Retrieve (initial candidates)",
            min_value=5, max_value=50, value=settings["top_k_retrieve"],
            help="Number of unique document candidates to retrieve before reranking"
        )

        new_top_n = st.slider(
            "Top-N Rerank (final context)",
            min_value=3, max_value=20, value=settings["top_n_rerank"],
            help="Number of top reranked results to use as LLM context"
        )

        new_max_chunks = st.slider(
            "Max Chunks per Document",
            min_value=1, max_value=10, value=settings["max_chunks_per_doc"],
            help="Maximum number of chunks to keep per unique document in general query mode"
        )

        st.markdown("")

        # ── Groundedness Settings ──
        render_glass_card("Groundedness Thresholds", icon="🛡️",
                          content="Configure the 3-tier groundedness scoring thresholds")

        new_threshold = st.slider(
            "Groundedness Pass Threshold",
            min_value=0.0, max_value=1.0,
            value=settings["groundedness_threshold"],
            step=0.05,
            format="%.0f%%",
            help="Composite score threshold below which a hallucination warning is triggered"
        )

        st.markdown(f"""
        <div style="margin-top:8px;">
            <div style="font-size:0.78rem; color:#64748B; margin-bottom:8px;">
                Scoring Weights (fixed)
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <span class="badge badge-info">N-gram Overlap: 40%</span>
                <span class="badge badge-info">Entity Verification: 30%</span>
                <span class="badge badge-info">Citation Coverage: 30%</span>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("")

        # ── Save Button ──
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            st.session_state["rag_settings"] = {
                "top_k_retrieve": new_top_k,
                "top_n_rerank": new_top_n,
                "max_chunks_per_doc": new_max_chunks,
                "groundedness_threshold": new_threshold,
            }
            st.success("✅ Settings saved successfully!")

        # ── Current Settings Display ──
        st.markdown("")
        render_glass_card("Current Configuration", icon="📋")

        current = st.session_state["rag_settings"]
        for key, value in current.items():
            label = key.replace("_", " ").title()
            display_val = f"{value:.0%}" if isinstance(value, float) else str(value)
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:4px 0;
                 border-bottom:1px solid rgba(255,255,255,0.03);">
                <span style="font-size:0.82rem; color:#94A3B8;">{label}</span>
                <span style="font-size:0.82rem; color:#38bdf8; font-weight:600;
                      font-family:'JetBrains Mono', monospace;">{display_val}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
