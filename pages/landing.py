"""
NovaRAG Research Studio — Premium Entrance Landing Page & Loading Gateway.
"""

import time
import streamlit as st

def inject_landing_css():
    """Injects custom CSS specifically for the landing page entrance experience."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Orbitron:wght@800;900&family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@500;600&display=swap');

/* HIDE STREAMLIT CHASSIS */
[data-testid="stSidebar"], 
[data-testid="stSidebarCollapsedControl"], 
.stHeader, 
header[data-testid="stHeader"],
.stAppHeader {
    display: none !important;
}

/* COMBINED LAYOUT & BACKGROUND RESET */
[data-testid="stAppViewContainer"],
.stApp,
.main,
[data-testid="stMain"],
.block-container,
[data-testid="block-container"] {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    background-color: #03050a !important;
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.04) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(56, 189, 248, 0.04) 0%, transparent 40%) !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    overflow-x: hidden !important;
}

/* BACKGROUND ANIMATED PARTICLES */
.particles {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    overflow: hidden;
    pointer-events: none;
    z-index: -1;
}
.particle {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, rgba(139, 92, 246, 0) 70%);
    filter: blur(8px);
    animation: floatParticle 20s infinite ease-in-out;
}
.p1 { width: 350px; height: 350px; top: -100px; left: -50px; animation-duration: 30s; }
.p2 { width: 450px; height: 450px; bottom: -150px; right: -50px; animation-duration: 40s; background: radial-gradient(circle, rgba(56, 189, 248, 0.1) 0%, rgba(56, 189, 248, 0) 70%); }
.p3 { width: 280px; height: 280px; top: 25%; right: 15%; animation-duration: 25s; background: radial-gradient(circle, rgba(192, 132, 252, 0.08) 0%, rgba(192, 132, 252, 0) 70%); }
.p4 { width: 220px; height: 220px; bottom: 25%; left: 10%; animation-duration: 20s; background: radial-gradient(circle, rgba(6, 182, 212, 0.06) 0%, rgba(6, 182, 212, 0) 70%); }

@keyframes floatParticle {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33% { transform: translate(40px, -60px) scale(1.08); }
    66% { transform: translate(-30px, 30px) scale(0.92); }
}

/* HERO SECTION */
.hero-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 100px 20px 40px 20px;
    position: relative;
}
.logo-container {
    position: relative;
    width: 90px; height: 90px;
    margin-bottom: 24px;
}
.logo-pulse {
    position: absolute;
    top: -5px; left: -5px; right: -5px; bottom: -5px;
    border: 2px solid rgba(139, 92, 246, 0.4);
    border-radius: 50%;
    animation: pulseLogo 3s infinite alternate;
}
@keyframes pulseLogo {
    0% { transform: scale(0.95); box-shadow: 0 0 10px rgba(139, 92, 246, 0.2); }
    100% { transform: scale(1.05); box-shadow: 0 0 25px rgba(139, 92, 246, 0.5), 0 0 15px rgba(56, 189, 248, 0.3); }
}
.logo-icon {
    font-size: 3.2rem;
    line-height: 90px;
    display: block;
    text-align: center;
    z-index: 2;
}

.landing-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 3.8rem;
    font-weight: 900;
    margin: 0;
    letter-spacing: -0.01em;
    background: linear-gradient(135deg, #ffffff 30%, #e2e8f0 70%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}
.gradient-accent {
    background: linear-gradient(135deg, #00ffff 0%, #3b82f6 50%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900;
}

/* TYPING ANIMATIONS */
.typing-container {
    height: 65px;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 15px;
}
.typing-text {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.35rem;
    font-weight: 500;
    color: #38bdf8;
    margin: 0;
    border-right: 2px solid #38bdf8;
    white-space: nowrap;
    overflow: hidden;
    width: 0;
    animation: typing1 2s steps(40, end) forwards, blink 0.75s infinite alternate;
}
.typing-text-2 {
    font-family: 'Inter', sans-serif;
    font-size: 1.0rem;
    font-weight: 400;
    color: #64748b;
    margin: 6px 0 0 0;
    border-right: 2px solid #8b5cf6;
    white-space: nowrap;
    overflow: hidden;
    width: 0;
    opacity: 0;
    animation: typing2 2s steps(45, end) 2s forwards, blink 0.75s infinite alternate;
}

@keyframes typing1 {
    from { width: 0; }
    to { width: 440px; }
}
@keyframes typing2 {
    from { width: 0; opacity: 1; }
    to { width: 410px; opacity: 1; }
}
@keyframes blink {
    50% { border-color: transparent; }
}

/* CTA BUTTON CONTAINER */
div.stButton > button {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #1d4ed8 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(139, 92, 246, 0.4) !important;
    border-radius: 30px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    padding: 14px 45px !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.4) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    animation: pulseCTA 2s infinite alternate !important;
    display: block !important;
    margin: 10px auto !important;
    width: auto !important;
    min-width: 220px !important;
}
div.stButton > button:hover {
    box-shadow: 0 0 35px rgba(139, 92, 246, 0.75), 0 0 15px rgba(56, 189, 248, 0.45) !important;
    transform: scale(1.04) translateY(-2px) !important;
    border-color: #00ffff !important;
    background: linear-gradient(135deg, #c084fc 0%, #8b5cf6 50%, #38bdf8 100%) !important;
}
@keyframes pulseCTA {
    0% { box-shadow: 0 0 12px rgba(139, 92, 246, 0.3); }
    100% { box-shadow: 0 0 24px rgba(139, 92, 246, 0.6); }
}

/* SECTION HEADERS */
.section-wrapper {
    max-width: 1200px;
    margin: 0 auto;
    padding: 60px 24px 20px 24px;
}
.section-header {
    text-align: center;
    margin-bottom: 40px;
    max-width: 1200px;
    margin-left: auto;
    margin-right: auto;
    padding: 0 24px;
}
.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    margin-bottom: 10px;
    color: #f1f5f9;
}
.section-subtitle {
    font-size: 1.0rem;
    color: #64748b;
    max-width: 600px;
    margin: 0 auto;
}

/* FEATURES SECTION */
.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
    max-width: 1200px;
    margin-left: auto;
    margin-right: auto;
    padding: 0 24px;
}
.feature-card {
    background: rgba(15, 23, 42, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 28px 24px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: all 0.3s ease;
    opacity: 0;
    transform: translateY(20px);
    animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
.feature-card:hover {
    border-color: rgba(139, 92, 246, 0.25);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3), 0 0 20px rgba(139, 92, 246, 0.05);
    transform: translateY(-4px);
    background: rgba(15, 23, 42, 0.6);
}
.feature-icon {
    font-size: 2.2rem;
    margin-bottom: 18px;
    display: inline-block;
}
.feature-card-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0 0 8px 0;
}
.feature-desc {
    font-size: 0.88rem;
    color: #94a3b8;
    line-height: 1.6;
    margin: 0;
}

/* STATS SECTION */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 40px;
    margin-bottom: 40px;
    max-width: 1200px;
    margin-left: auto;
    margin-right: auto;
    padding: 0 24px;
}
.stat-card {
    background: rgba(30, 41, 59, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.03);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: all 0.3s ease;
}
.stat-card:hover {
    border-color: rgba(56, 189, 248, 0.2);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    transform: translateY(-2px);
    background: rgba(30, 41, 59, 0.35);
}
.stat-number {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.4rem;
    font-weight: 900;
    background: linear-gradient(135deg, #00ffff 0%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 6px;
}
.stat-label {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.stat-icon {
    font-size: 2.0rem;
    margin-bottom: 10px;
}
.stat-label-large {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #cbd5e1;
    margin-top: 4px;
}

/* INTERACTIVE DEMO (COLUMNS OVERRIDE) */
[data-testid="column"] div.stButton > button {
    background: rgba(30, 41, 59, 0.45) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    color: #e2e8f0 !important;
    border-radius: 14px !important;
    padding: 22px 18px !important;
    text-align: left !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    white-space: normal !important;
    height: auto !important;
    min-height: 90px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    line-height: 1.4 !important;
    width: 100% !important;
    margin: 0 !important;
    animation: none !important;
}
[data-testid="column"] div.stButton > button:hover {
    border-color: rgba(56, 189, 248, 0.5) !important;
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.15), 0 8px 30px rgba(0, 0, 0, 0.3) !important;
    transform: translateY(-4px) !important;
    background: rgba(30, 41, 59, 0.7) !important;
    color: #38bdf8 !important;
}

/* FOOTER */
.landing-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    background: rgba(10, 15, 30, 0.7);
    padding: 40px 24px 20px 24px;
    margin-top: 80px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}
.footer-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 30px;
}
.footer-info {
    flex: 1 1 400px;
}
.footer-brand {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.2rem;
    font-weight: 800;
    color: #f1f5f9;
    margin-bottom: 12px;
}
.footer-desc {
    font-size: 0.85rem;
    color: #64748b;
    line-height: 1.6;
    max-width: 500px;
    margin: 0;
}
.footer-tech {
    flex: 1 1 400px;
}
.tech-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
}
.tech-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.tech-badge {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.18);
    color: #c084fc;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}
.footer-bottom {
    max-width: 1200px;
    margin: 30px auto 0 auto;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.03);
    text-align: center;
}
.footer-copy {
    font-size: 0.78rem;
    color: #475569;
}

/* STAGGERED ENTRANCE */
@keyframes fadeInUp {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.feature-card:nth-child(1) { animation-delay: 0.1s; }
.feature-card:nth-child(2) { animation-delay: 0.2s; }
.feature-card:nth-child(3) { animation-delay: 0.3s; }
.feature-card:nth-child(4) { animation-delay: 0.4s; }
.feature-card:nth-child(5) { animation-delay: 0.5s; }
.feature-card:nth-child(6) { animation-delay: 0.6s; }

/* RESPONSIVE DESIGN */
@media (max-width: 768px) {
    .landing-title {
        font-size: 2.3rem !important;
    }
    .typing-container {
        height: auto;
        margin-bottom: 10px;
    }
    .typing-text {
        font-size: 1.05rem !important;
        white-space: normal !important;
        border-right: none !important;
        width: auto !important;
        animation: none !important;
    }
    .typing-text-2 {
        font-size: 0.85rem !important;
        white-space: normal !important;
        border-right: none !important;
        width: auto !important;
        opacity: 1 !important;
        animation: none !important;
    }
    .hero-section {
        padding: 60px 15px 30px 15px;
    }
    .section-title {
        font-size: 1.7rem;
    }
    .footer-content {
        flex-direction: column;
    }
}
</style>
""", unsafe_allow_html=True)


def inject_loader_css():
    """Injects custom CSS specifically for the sequential loader."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@800;900&family=JetBrains+Mono:wght@500;600&display=swap');

/* HIDE STREAMLIT CHASSIS */
[data-testid="stSidebar"], 
[data-testid="stSidebarCollapsedControl"], 
.stHeader, 
header[data-testid="stHeader"],
.stAppHeader {
    display: none !important;
}

[data-testid="stAppViewContainer"] {
    padding: 0 !important;
    background: #03050a !important;
}

.block-container {
    max-width: 100% !important;
    padding: 0 !important;
}

.loader-bg {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: #03050a;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 999999;
    overflow: hidden;
}

/* BACKGROUND PARTICLES FOR LOADER */
.loader-bg .particles {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none;
    z-index: -1;
}
.loader-bg .particle {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, rgba(139, 92, 246, 0) 70%);
    filter: blur(15px);
}
.lp1 { width: 400px; height: 400px; top: -100px; left: -100px; }
.lp2 { width: 400px; height: 400px; bottom: -100px; right: -100px; background: radial-gradient(circle, rgba(56, 189, 248, 0.08) 0%, rgba(56, 189, 248, 0) 70%); }

.loader-card {
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 24px;
    padding: 50px 40px;
    text-align: center;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: 0 0 50px rgba(139, 92, 246, 0.12), 0 20px 40px rgba(0, 0, 0, 0.4);
    max-width: 460px;
    width: 90%;
}

.loader-spinner-container {
    position: relative;
    width: 110px; height: 110px;
    margin: 0 auto 28px auto;
}
.loader-icon {
    font-size: 3.4rem;
    line-height: 110px;
    text-align: center;
    position: relative;
    z-index: 2;
    animation: floatIcon 3s ease-in-out infinite;
}
@keyframes floatIcon {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-6px) rotate(5deg); }
}

.pulse-ring {
    position: absolute;
    top: -8px; left: -8px; right: -8px; bottom: -8px;
    border: 2px solid rgba(139, 92, 246, 0.4);
    border-radius: 50%;
    animation: loaderPulseRing 1.8s infinite ease-out;
}
.pulse-ring-2 {
    position: absolute;
    top: -8px; left: -8px; right: -8px; bottom: -8px;
    border: 2px solid rgba(56, 189, 248, 0.3);
    border-radius: 50%;
    animation: loaderPulseRing 1.8s infinite ease-out;
    animation-delay: 0.9s;
}

@keyframes loaderPulseRing {
    0% { transform: scale(0.85); opacity: 0.8; }
    100% { transform: scale(1.25); opacity: 0; box-shadow: 0 0 30px rgba(139, 92, 246, 0); }
}

.loader-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.9rem;
    font-weight: 900;
    color: #f8fafc;
    letter-spacing: 0.12em;
    margin-bottom: 24px;
    text-transform: uppercase;
}

.loader-progress-bar {
    background: rgba(255, 255, 255, 0.04);
    border-radius: 10px;
    height: 6px;
    width: 100%;
    overflow: hidden;
    margin-bottom: 20px;
    border: 1px solid rgba(255, 255, 255, 0.03);
}

.loader-progress-fill {
    background: linear-gradient(90deg, #00ffff, #8b5cf6);
    height: 100%;
    width: 0%;
    transition: width 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
    box-shadow: 0 0 12px rgba(0, 255, 255, 0.5);
}

.loader-status-container {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: #64748b;
    margin-top: 10px;
    min-height: 20px;
}
.loader-status-text {
    font-weight: 600;
    color: #38bdf8;
    text-shadow: 0 0 8px rgba(56, 189, 248, 0.35);
    animation: statusPulse 1.5s infinite alternate;
}
.loader-percent {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    color: #e2e8f0;
}

@keyframes statusPulse {
    0% { opacity: 0.8; }
    100% { opacity: 1; }
}
</style>
""", unsafe_allow_html=True)


def render_landing():
    """Renders the premium dark-themed entrance landing page."""
    inject_landing_css()

    # Background and styles are applied globally via inject_landing_css
    # No opening wrapper tags used to avoid layout offset bugs
    
    # ── Background Particles ──
    st.markdown("""
    <div class="particles">
        <div class="particle p1"></div>
        <div class="particle p2"></div>
        <div class="particle p3"></div>
        <div class="particle p4"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── 1. Hero Section & Branding ──
    st.markdown("""
    <div class="hero-section">
        <div class="logo-container">
            <div class="logo-pulse"></div>
            <span class="logo-icon">🔬</span>
        </div>
        <h1 class="landing-title">NovaRAG <span class="gradient-accent">Research Studio</span></h1>
        <div class="typing-container">
            <p class="typing-text">Enterprise-Grade AI Research Assistant</p>
            <p class="typing-text-2">Powered by Retrieval-Augmented Generation</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 2. Call To Action Button ──
    st.markdown('<div class="cta-anchor"></div>', unsafe_allow_html=True)
    if st.button("Enter NovaRAG", key="enter_novarag_btn", use_container_width=True):
        st.session_state["loading_state"] = True
        st.rerun()

    # Layout is controlled via features/stats grid max-width constraints

    # ── 3. Feature Highlights Section ──
    st.markdown("""
    <div class="section-header">
        <h2 class="section-title">Core Capabilities</h2>
        <p class="section-subtitle">A state-of-the-art literature synthesizer, semantic query extraction matrix, and guardrail auditor.</p>
    </div>
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon">🔬</div>
            <h3 class="feature-card-title">Academic Research Synthesis</h3>
            <p class="feature-desc">Synthesize multiple documents into cohesive research briefs with cited justifications.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <h3 class="feature-card-title">Intelligent Document Retrieval</h3>
            <p class="feature-desc">Locate exact evidence patterns across thousands of pages using semantic index mapping.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3 class="feature-card-title">FlashRank Reranking</h3>
            <p class="feature-desc">Apply deep re-ranking filters to ensure the most relevant contexts serve the generation pipeline.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🛡️</div>
            <h3 class="feature-card-title">Groundedness & Safety Audits</h3>
            <p class="feature-desc">Detect hallucination risks and enforce input/output guardrails with strict confidence levels.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📑</div>
            <h3 class="feature-card-title">Automated PDF Report Generation</h3>
            <p class="feature-desc">Compile professional, print-ready PDF briefs containing clean citation summaries and audits.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🧬</div>
            <h3 class="feature-card-title">Gemini-Powered Reasoning</h3>
            <p class="feature-desc">Leverage advanced multimodal models for structured synthesis, analysis, and factual QA.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 4. Statistics Section ──
    st.markdown("""
    <div class="section-header" style="margin-top: 60px;">
        <h2 class="section-title">Performance Metrics</h2>
        <p class="section-subtitle">Engineered to process dense research documentation at enterprise scale.</p>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">5000+</div>
            <div class="stat-label">Pages Supported</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">1000+</div>
            <div class="stat-label">Research Papers</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🏢</div>
            <div class="stat-label-large">Enterprise RAG Architecture</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">⚡</div>
            <div class="stat-label-large">Real-Time PDF Generation</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🛡️</div>
            <div class="stat-label-large">Grounded Citations</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🔍</div>
            <div class="stat-label-large">Hallucination Detection</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 5. Interactive Demo Section ──
    st.markdown("""
    <div class="section-header" style="margin-top: 60px;">
        <h2 class="section-title">Interactive Demo</h2>
        <p class="section-subtitle">Click a sample query below to instantly launch the reasoning pipeline and examine the citations.</p>
    </div>
    """, unsafe_allow_html=True)

    d1, d2, d3 = st.columns(3, gap="medium")
    with d1:
        st.markdown('<div class="demo-card-anchor"></div>', unsafe_allow_html=True)
        if st.button("🔍 Compare RAG and Fine-Tuning", key="demo_q1", use_container_width=True):
            st.session_state["prefilled_query"] = "Compare RAG and Fine-Tuning"
            st.session_state["current_page"] = "🔍 Research Assistant"
            st.session_state["loading_state"] = True
            st.rerun()

    with d2:
        st.markdown('<div class="demo-card-anchor"></div>', unsafe_allow_html=True)
        if st.button("🏥 Generate Literature Review on AI in Healthcare", key="demo_q2", use_container_width=True):
            st.session_state["prefilled_query"] = "Generate Literature Review on AI in Healthcare"
            st.session_state["current_page"] = "🔍 Research Assistant"
            st.session_state["loading_state"] = True
            st.rerun()

    with d3:
        st.markdown('<div class="demo-card-anchor"></div>', unsafe_allow_html=True)
        if st.button("📄 Summarize Uploaded Research Paper", key="demo_q3", use_container_width=True):
            st.session_state["prefilled_query"] = "Summarize Uploaded Research Paper"
            st.session_state["current_page"] = "🔍 Research Assistant"
            st.session_state["loading_state"] = True
            st.rerun()

    # End features section

    # ── 6. Professional Footer ──
    st.markdown("""
    <footer class="landing-footer">
        <div class="footer-content">
            <div class="footer-info">
                <div class="footer-brand">🔬 NovaRAG Research Studio</div>
                <p class="footer-desc">Enterprise-Grade AI Research Assistant utilizing semantic index mapping, vector synthesis, and hallucination safety audits.</p>
            </div>
            <div class="footer-tech">
                <div class="tech-title">Technology Stack</div>
                <div class="tech-badges">
                    <span class="tech-badge">Python</span>
                    <span class="tech-badge">Streamlit</span>
                    <span class="tech-badge">ChromaDB</span>
                    <span class="tech-badge">FlashRank</span>
                    <span class="tech-badge">Gemini</span>
                    <span class="tech-badge">PDF Generation</span>
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            <div class="footer-copy">&copy; 2026 NovaRAG Research Studio. All Rights Reserved.</div>
        </div>
    </footer>
    """, unsafe_allow_html=True)

    # End landing container


def render_loader():
    """Renders the premium animated welcome loader with sequential status messages."""
    inject_loader_css()

    st.markdown("""
    <div class="loader-bg">
        <div class="particles">
            <div class="particle lp1"></div>
            <div class="particle lp2"></div>
        </div>
        <div class="loader-card">
            <div class="loader-spinner-container">
                <div class="pulse-ring"></div>
                <div class="pulse-ring-2"></div>
                <span class="loader-icon">🔬</span>
            </div>
            <h2 class="loader-title">NovaRAG</h2>
            <div class="loader-progress-bar">
                <div class="loader-progress-fill" id="progress-fill"></div>
            </div>
    """, unsafe_allow_html=True)

    # Status message updates
    status_placeholder = st.empty()

    steps = [
        "Initializing Vector Database...",
        "Loading Research Corpus...",
        "Activating Retrieval Engine...",
        "Starting FlashRank...",
        "Launching NovaRAG..."
    ]

    for i, step in enumerate(steps):
        percentage = int((i + 1) * 20)
        status_placeholder.markdown(f"""
        <div class="loader-status-container">
            <div class="loader-status-text">{step}</div>
            <div class="loader-percent">{percentage}%</div>
        </div>
        <style>
        .loader-progress-fill {{
            width: {percentage}% !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        time.sleep(0.7)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Transition completed
    st.session_state["show_landing"] = False
    st.session_state["loading_state"] = False
    st.rerun()
