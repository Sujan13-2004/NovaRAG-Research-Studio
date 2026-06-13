"""
NovaRAG Research Studio — Reusable UI Components.

Streamlit HTML/markdown components used across page modules.
"""

import streamlit as st


def render_metric_card(label, value, unit="", icon="📊", accent_color="#8B5CF6"):
    """Renders a premium metric card with icon and hover effect."""
    st.markdown(f"""
    <div class="metric-card" style="border-left: 3px solid {accent_color};">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
            <span style="font-size:1.4rem; filter: drop-shadow(0 0 4px {accent_color}40);">{icon}</span>
            <div class="metric-label">{label}</div>
        </div>
        <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
    </div>""", unsafe_allow_html=True)


def render_glass_card(title, content="", icon="", extra_style=""):
    """Renders a glass-morphism card container."""
    icon_html = f'<span style="font-size:1.1rem;">{icon}</span> ' if icon else ""
    content_html = f'<div style="color:#94A3B8; font-size:0.88rem; line-height:1.6; margin-top:8px;">{content}</div>' if content else ""
    st.markdown(f"""
    <div class="glass-card" style="{extra_style}">
        <div class="card-title">{icon_html}{title}</div>
        {content_html}
    </div>""", unsafe_allow_html=True)


def render_badge(text, variant="info"):
    """Returns badge HTML string (use within markdown calls)."""
    return f'<span class="badge badge-{variant}">{text}</span>'


def render_source_card(chunk):
    """Renders a source/citation card for a retrieved chunk."""
    text_preview = chunk['text'][:500] + ('...' if len(chunk['text']) > 500 else '')
    st.markdown(f"""
    <div class="source-card">
        <div style="font-weight:600; font-size:0.92rem; color:#A78BFA;">
            [{chunk['rank']}] {chunk['title']} — Page {chunk['page']}
        </div>
        <div style="font-size:0.82rem; color:#94A3B8; margin-top:6px;
                    font-style:italic; line-height:1.5;">
            "{text_preview}"
        </div>
    </div>""", unsafe_allow_html=True)


def render_thinking_card(text):
    """Renders the reasoning flow / chain-of-thought card."""
    st.markdown(
        f'<div class="thinking-card">{text}</div>',
        unsafe_allow_html=True
    )


def render_page_header(title, subtitle="", icon=""):
    """Renders a standardized page header with optional subtitle."""
    icon_html = f'<span style="font-size:1.6rem; margin-right:8px;">{icon}</span>' if icon else ""
    st.markdown(f"""
    <div style="margin-bottom:6px;">
        <div class="dashboard-title" style="display:flex; align-items:center;">
            {icon_html}{title}
        </div>
    </div>""", unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f'<div class="dashboard-subtitle">{subtitle}</div>',
            unsafe_allow_html=True
        )


def render_action_card(title, description, icon="⚡", button_label="Go",
                       accent_color="#8B5CF6"):
    """Renders a clickable action card. Returns True if button was clicked."""
    st.markdown(f"""
    <div class="glass-card" style="border-left: 3px solid {accent_color};
         cursor:pointer; transition: transform 0.2s, box-shadow 0.2s;">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <span style="font-size:1.8rem; filter: drop-shadow(0 0 6px {accent_color}40);">{icon}</span>
            <div>
                <div style="font-size:0.95rem; font-weight:700; color:#E2E8F0;">{title}</div>
                <div style="font-size:0.78rem; color:#64748B; margin-top:2px;">{description}</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
    return st.button(button_label, key=f"action_{title.replace(' ', '_').lower()}", use_container_width=True)


def render_stat_row(label, value, color="#38bdf8"):
    """Returns an HTML string for a stat row (used inside cards)."""
    return f"""
    <div class="db-row">
        <span class="db-label">{label}</span>
        <span class="db-value" style="color:{color};">{value}</span>
    </div>"""


def render_empty_state(message, icon="📭"):
    """Renders a centered empty state message."""
    st.markdown(f"""
    <div style="text-align:center; padding:60px 20px;">
        <div style="font-size:3rem; margin-bottom:16px; opacity:0.6;">{icon}</div>
        <div style="font-size:1rem; color:#64748B; font-weight:500;">{message}</div>
    </div>""", unsafe_allow_html=True)


def render_loading_pulse():
    """Renders a CSS pulse loading animation."""
    st.markdown("""
    <div style="display:flex; justify-content:center; align-items:center; gap:8px; padding:40px;">
        <div class="pulse-dot" style="animation-delay:0s;"></div>
        <div class="pulse-dot" style="animation-delay:0.15s;"></div>
        <div class="pulse-dot" style="animation-delay:0.3s;"></div>
    </div>
    <style>
    .pulse-dot {
        width: 10px; height: 10px; border-radius: 50%;
        background: #8B5CF6;
        animation: pulseAnim 1.2s ease-in-out infinite;
    }
    @keyframes pulseAnim {
        0%, 100% { opacity: 0.3; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.2); }
    }
    </style>
    """, unsafe_allow_html=True)
