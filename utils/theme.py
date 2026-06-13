"""
NovaRAG Research Studio — Custom CSS Theme.

All styling extracted from the original app.py plus new navigation,
page transition, and enterprise dashboard styles.
"""

import streamlit as st


def inject_custom_css():
    """Injects the full custom CSS theme into the Streamlit app."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Orbitron:wght@700;900&family=Space+Grotesk:wght@700&display=swap');

/* ── Global ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp,
[data-testid="stAppViewContainer"],
.main,
.reportview-container,
[data-testid="stMain"],
[data-testid="stApp"] {
    background-color: #05070f !important;
    background-image:
        radial-gradient(circle at 20% 30%, rgba(0, 255, 255, 0.05) 0%, transparent 60%),
        radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.04) 0%, transparent 60%),
        linear-gradient(rgba(56, 189, 248, 0.015) 1.5px, transparent 1.5px),
        linear-gradient(90deg, rgba(56, 189, 248, 0.015) 1.5px, transparent 1.5px) !important;
    background-size: 100% 100%, 100% 100%, 100px 100px, 100px 100px !important;
    background-repeat: no-repeat, no-repeat, repeat, repeat !important;
}

/* ── Header Styling ── */
header[data-testid="stHeader"],
.stHeader,
.stAppHeader,
[data-testid="stHeader"] {
    background: linear-gradient(270deg, #0f172a, #1e3a8a, #3b82f6, #1d4ed8) !important;
    background-size: 400% 400% !important;
    animation: headerGradient 8s ease infinite !important;
    color: white !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
    overflow: hidden !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}

@keyframes headerGradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

header[data-testid="stHeader"]::before,
.stHeader::before,
.stAppHeader::before,
[data-testid="stHeader"]::before {
    content: "NovaRAG Research Studio";
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    white-space: nowrap;
    font-family: 'Orbitron', 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 900;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    background: linear-gradient(90deg, #00ffff, #3b82f6, #00ffff);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 8px rgba(0, 255, 255, 0.4));
    animation: textShine 4s linear infinite, textGlow 3s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 1;
}

@keyframes textShine {
    0% { background-position: 0% center; }
    100% { background-position: 200% center; }
}

@keyframes textGlow {
    0% {
        filter: drop-shadow(0 0 4px rgba(0, 255, 255, 0.3)) drop-shadow(0 0 8px rgba(59, 130, 246, 0.2));
    }
    100% {
        filter: drop-shadow(0 0 10px rgba(0, 255, 255, 0.6)) drop-shadow(0 0 16px rgba(59, 130, 246, 0.5));
    }
}

@media (max-width: 768px) {
    header[data-testid="stHeader"]::before,
    .stHeader::before,
    .stAppHeader::before,
    [data-testid="stHeader"]::before {
        font-size: 1.1rem;
        letter-spacing: 0.08em;
    }
}

header[data-testid="stHeader"] *,
.stHeader *,
.stAppHeader *,
[data-testid="stHeader"] * {
    color: white !important;
    fill: white !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebarNav"] {
    display: none !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] { color: #CBD5E1; }

/* ── Navigation Items ── */
.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.25s ease;
    margin-bottom: 3px;
    text-decoration: none;
    color: #94A3B8;
    font-size: 0.88rem;
    font-weight: 500;
}
.nav-item:hover {
    background: rgba(139, 92, 246, 0.08);
    color: #C084FC;
}
.nav-item.active {
    background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(59,130,246,0.1));
    color: #C084FC;
    font-weight: 600;
    border-left: 3px solid #8B5CF6;
    box-shadow: 0 2px 12px rgba(139, 92, 246, 0.1);
}
.nav-item .nav-icon {
    font-size: 1.15rem;
    min-width: 24px;
    text-align: center;
}
.nav-section-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 12px 16px 4px 16px;
}

/* ── Dashboard Title ── */
.dashboard-title {
    font-size: 1.85rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818CF8 0%, #A78BFA 40%, #C084FC 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
    margin-bottom: 2px;
}
.dashboard-subtitle {
    font-size: 0.88rem;
    color: #64748B;
    font-weight: 400;
    margin-bottom: 1.2rem;
}

/* ── Metric Cards ── */
.metric-card {
    background: rgba(30,41,59,0.65);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 20px 22px;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    transition: border-color 0.3s, box-shadow 0.3s, transform 0.2s;
}
.metric-card:hover {
    border-color: rgba(139,92,246,0.3);
    box-shadow: 0 4px 24px rgba(139,92,246,0.08);
    transform: translateY(-2px);
}
.metric-label {
    font-size: 0.7rem; font-weight: 600; color: #64748B;
    text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 6px;
}
.metric-value {
    font-size: 1.95rem; font-weight: 800; color: #F1F5F9; line-height: 1;
}
.metric-unit {
    font-size: 0.85rem; font-weight: 400; color: #94A3B8; margin-left: 4px;
}

/* ── Glass Card ── */
.glass-card {
    background: rgba(30,41,59,0.45);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 14px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: border-color 0.3s, box-shadow 0.3s;
}
.glass-card:hover {
    border-color: rgba(255,255,255,0.1);
}
.card-title {
    font-size: 0.95rem; font-weight: 700; color: #E2E8F0;
    margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
}

/* ── Thinking Card ── */
.thinking-card {
    background: rgba(17,24,39,0.6);
    border-left: 4px solid #8B5CF6;
    border-radius: 4px 12px 12px 4px;
    padding: 16px; margin-bottom: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem; color: #C084FC;
}

/* ── Source Card ── */
.source-card {
    background: rgba(15,23,42,0.5);
    border: 1px solid rgba(255,255,255,0.04);
    border-left: 3px solid #0D9488;
    border-radius: 8px;
    padding: 14px 18px; margin-bottom: 10px;
    transition: border-left-color 0.2s, background 0.2s;
}
.source-card:hover {
    border-left-color: #8B5CF6;
    background: rgba(15,23,42,0.7);
}

/* ── Badges ── */
.badge {
    display: inline-block; padding: 4px 10px; border-radius: 9999px;
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; margin-right: 8px;
}
.badge-pass  { background: rgba(16,185,129,0.12); color: #10B981; border: 1px solid rgba(16,185,129,0.2); }
.badge-warning { background: rgba(245,158,11,0.12); color: #F59E0B; border: 1px solid rgba(245,158,11,0.2); }
.badge-fail  { background: rgba(239,68,68,0.12); color: #EF4444; border: 1px solid rgba(239,68,68,0.2); }
.badge-info  { background: rgba(59,130,246,0.12); color: #3B82F6; border: 1px solid rgba(59,130,246,0.2); }

/* ── Category Badge ── */
.cat-badge {
    display: inline-block; padding: 3px 8px; border-radius: 6px;
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.03em;
}

/* ── Data Table ── */
.doc-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    transition: background 0.15s;
}
.doc-row:hover { background: rgba(139,92,246,0.05); }
.doc-row:nth-child(even) { background: rgba(15,23,42,0.25); }
.doc-row:nth-child(even):hover { background: rgba(139,92,246,0.07); }

.doc-rank {
    font-size: 0.8rem; font-weight: 700; color: #64748B;
    min-width: 28px; text-align: center;
}
.doc-title-cell {
    flex: 1; font-size: 0.85rem; color: #CBD5E1; font-weight: 500;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.doc-meta {
    font-size: 0.75rem; color: #64748B; min-width: 70px; text-align: center;
}

.table-header {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 16px;
    background: rgba(30,41,59,0.8);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px 10px 0 0;
}
.th { font-size: 0.7rem; font-weight: 700; color: #64748B;
      text-transform: uppercase; letter-spacing: 0.06em; }
.th-rank { min-width: 28px; text-align: center; }
.th-title { flex: 1; }
.th-meta  { min-width: 70px; text-align: center; }

/* ── Streamlit Widget Overrides ── */
.stTextInput > div > div > input {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(139,92,246,0.5) !important;
    box-shadow: 0 0 0 2px rgba(139,92,246,0.15) !important;
}

.stSelectbox > div > div {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 8px 20px !important;
    transition: box-shadow 0.2s, transform 0.2s !important;
}
.stButton > button:hover {
    box-shadow: 0 4px 18px rgba(139,92,246,0.35) !important;
    transform: translateY(-1px) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(15,23,42,0.35);
    border: 1px dashed rgba(139,92,246,0.25);
    border-radius: 10px; padding: 10px;
}

/* Download button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #0D9488 0%, #14B8A6 100%) !important;
    border: none !important; border-radius: 8px !important;
    color: white !important; font-weight: 600 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(30,41,59,0.5);
    border-radius: 10px; padding: 4px; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; color: #94A3B8; font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(139,92,246,0.15) !important;
    color: #C084FC !important;
}

/* Plotly container */
[data-testid="stPlotlyChart"] { background: transparent !important; }

/* Expander */
.streamlit-expanderHeader {
    background: rgba(30,41,59,0.5) !important;
    border-radius: 8px !important;
    color: #CBD5E1 !important;
}

/* Progress bar */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #7C3AED, #8B5CF6) !important;
}

/* General text */
.stMarkdown { color: #CBD5E1; }
h1, h2, h3, h4 { color: #E2E8F0 !important; }
p, li { color: #CBD5E1; }
hr { border-color: rgba(255,255,255,0.06) !important; }

/* Checkbox */
.stCheckbox label { color: #CBD5E1 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0F172A; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

/* Success / Warning / Error boxes */
.stAlert { border-radius: 10px !important; }

/* ── Sidebar Logo & Title Animations ── */
.sidebar-logo {
    display: inline-block;
    animation: floatLogo 4s ease-in-out infinite;
}
@keyframes floatLogo {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-5px) rotate(8deg); }
}

.sidebar-title {
    font-family: 'Orbitron', 'Space Grotesk', sans-serif !important;
    font-weight: 900 !important;
    background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: textGlowPulse 3s ease-in-out infinite alternate;
}
@keyframes textGlowPulse {
    0% { filter: drop-shadow(0 0 1px rgba(56, 189, 248, 0.3)); }
    100% { filter: drop-shadow(0 0 6px rgba(167, 139, 250, 0.6)); }
}

/* ── Database Overview Premium Card ── */
.db-card {
    background: rgba(30, 41, 59, 0.55) !important;
    border: 1px solid rgba(56, 189, 248, 0.1) !important;
    border-radius: 12px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 25px rgba(0, 0, 0, 0.2);
    transition: border-color 0.3s, box-shadow 0.3s;
}
.db-card:hover {
    border-color: rgba(56, 189, 248, 0.35) !important;
    box-shadow: 0 4px 30px rgba(56, 189, 248, 0.12);
}
.db-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.08), transparent);
    animation: scanPulse 8s linear infinite;
}
@keyframes scanPulse {
    0% { left: -100%; }
    100% { left: 100%; }
}

.db-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    color: #38bdf8 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 12px;
}

.db-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}
.db-row:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}

.db-label {
    color: #94a3b8;
    font-size: 0.8rem;
}

.db-value {
    color: #38bdf8;
    font-weight: 800;
    font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
    text-shadow: 0 0 6px rgba(56, 189, 248, 0.3);
    animation: databaseValueGlow 2.5s ease-in-out infinite alternate;
}
@keyframes databaseValueGlow {
    0% { opacity: 0.8; text-shadow: 0 0 4px rgba(56, 189, 248, 0.2); }
    100% { opacity: 1; text-shadow: 0 0 10px rgba(56, 189, 248, 0.5); }
}

/* ── Footer Anim ── */
.sidebar-footer {
    font-size: 0.7rem;
    color: #64748b;
    text-align: center;
    letter-spacing: 0.04em;
    margin-top: 10px;
    animation: footerPulse 3s ease-in-out infinite alternate;
}
@keyframes footerPulse {
    0% { opacity: 0.55; }
    100% { opacity: 0.9; color: #818cf8; text-shadow: 0 0 6px rgba(129, 140, 248, 0.25); }
}

/* ── Page Transition Animation ── */
.page-content {
    animation: pageSlideIn 0.4s ease-out;
}
@keyframes pageSlideIn {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ── Paper Card (Browse Papers) ── */
.paper-card {
    background: rgba(30,41,59,0.45);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 12px;
    transition: border-color 0.3s, box-shadow 0.3s, transform 0.2s;
}
.paper-card:hover {
    border-color: rgba(139,92,246,0.25);
    box-shadow: 0 4px 20px rgba(139,92,246,0.06);
    transform: translateY(-1px);
}

/* ── Evidence Row ── */
.evidence-row {
    background: rgba(15,23,42,0.4);
    border: 1px solid rgba(255,255,255,0.04);
    border-left: 3px solid #60A5FA;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: border-left-color 0.2s;
}
.evidence-row:hover {
    border-left-color: #8B5CF6;
}

/* ── Settings Input Override ── */
.stSlider > div > div > div > div {
    background: #8B5CF6 !important;
}
.stNumberInput > div > div > input {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #E2E8F0 !important;
}

/* ── Radio buttons in sidebar ── */
[data-testid="stSidebar"] .stRadio > div {
    gap: 0 !important;
}
[data-testid="stSidebar"] .stRadio > div > label {
    background: transparent !important;
    padding: 10px 16px !important;
    border-radius: 10px !important;
    margin-bottom: 2px !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    cursor: pointer !important;
}
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: rgba(139, 92, 246, 0.08) !important;
}
[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
    background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(59,130,246,0.1)) !important;
    border-left: 3px solid #8B5CF6 !important;
}
[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
    display: none !important;
}
[data-testid="stSidebar"] .stRadio > div > label p {
    color: #94A3B8 !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) p {
    color: #C084FC !important;
    font-weight: 600 !important;
}

/* ── Multiselect ── */
.stMultiSelect > div > div {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
}

/* ── Text area ── */
.stTextArea > div > div > textarea {
    background-color: rgba(15,23,42,0.6) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
}

</style>
""", unsafe_allow_html=True)
