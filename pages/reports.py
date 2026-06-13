"""
NovaRAG Research Studio — Report Center Page.

Browse, search, download, and manage generated PDF research reports.
"""

import os
import datetime
import streamlit as st
from utils.components import (
    render_page_header, render_glass_card, render_metric_card,
    render_empty_state
)


def render(collection, csv_papers, **kwargs):
    """Renders the Report Center page."""

    st.markdown('<div class="page-content">', unsafe_allow_html=True)

    render_page_header(
        "Report Center",
        "Browse, download, and manage your generated research reports",
        icon="📑"
    )

    # ── Scan reports directory ──
    reports_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    report_files = []
    for f in os.listdir(reports_dir):
        if f.endswith(".pdf"):
            fpath = os.path.join(reports_dir, f)
            stat = os.stat(fpath)
            report_files.append({
                "filename": f,
                "path": fpath,
                "size_kb": stat.st_size / 1024,
                "created": datetime.datetime.fromtimestamp(stat.st_mtime),
            })

    # Sort by creation date (newest first)
    report_files.sort(key=lambda x: x["created"], reverse=True)

    # ── Metrics ──
    total_reports = len(report_files)
    total_size = sum(r["size_kb"] for r in report_files)

    m1, m2, m3 = st.columns(3, gap="medium")
    with m1:
        render_metric_card("Total Reports", total_reports, "PDFs", "📑", "#8B5CF6")
    with m2:
        render_metric_card("Total Size", f"{total_size:.1f}", "KB", "💾", "#3B82F6")
    with m3:
        if report_files:
            latest = report_files[0]["created"].strftime("%b %d, %H:%M")
            render_metric_card("Latest Report", latest, "", "🕐", "#10B981")
        else:
            render_metric_card("Latest Report", "—", "", "🕐", "#10B981")

    st.markdown("")

    if not report_files:
        render_empty_state(
            "No reports generated yet. Use the Research Assistant or Research Synthesis page to generate reports.",
            "📑"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Search & Filter ──
    render_glass_card("Search Reports", icon="🔎")

    search_text = st.text_input(
        "Search reports by filename:",
        placeholder="Type to filter reports...",
        label_visibility="collapsed"
    )

    if search_text:
        report_files = [r for r in report_files
                        if search_text.lower() in r["filename"].lower()]

    st.markdown(
        f'<div style="color:#64748B; font-size:0.82rem; margin:8px 0 16px 0;">'
        f'Showing {len(report_files)} report(s)'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Report Cards ──
    for idx, report in enumerate(report_files):
        col_info, col_actions = st.columns([4, 1.5])

        with col_info:
            # Extract query hint from filename
            name_parts = report["filename"].replace("report_", "").replace("synthesis_", "").replace(".pdf", "")
            name_clean = name_parts.rsplit("_", 1)[0].replace("_", " ").title()
            date_str = report["created"].strftime("%B %d, %Y at %H:%M")

            st.markdown(f"""
            <div class="paper-card" style="border-left:3px solid #8B5CF6;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <span style="font-size:2rem; opacity:0.8;">📄</span>
                    <div style="flex:1;">
                        <div style="font-size:0.92rem; font-weight:600; color:#E2E8F0;
                             margin-bottom:4px;">
                            {name_clean}
                        </div>
                        <div style="display:flex; gap:16px; flex-wrap:wrap;">
                            <span style="font-size:0.75rem; color:#94A3B8;">
                                📅 {date_str}
                            </span>
                            <span style="font-size:0.75rem; color:#94A3B8;">
                                💾 {report['size_kb']:.1f} KB
                            </span>
                            <span style="font-size:0.75rem; color:#64748B; font-family:'JetBrains Mono', monospace;">
                                {report['filename']}
                            </span>
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        with col_actions:
            st.markdown("<div style='padding-top:8px;'></div>", unsafe_allow_html=True)

            # Download button
            try:
                with open(report["path"], "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="📥 Download",
                    data=pdf_bytes,
                    file_name=report["filename"],
                    mime="application/pdf",
                    key=f"dl_{report['filename']}",
                    use_container_width=True
                )
            except Exception:
                st.markdown(
                    '<span style="color:#EF4444; font-size:0.8rem;">Error reading file</span>',
                    unsafe_allow_html=True
                )

            # Delete button
            if st.button("🗑️ Delete", key=f"del_report_{idx}", use_container_width=True):
                try:
                    os.remove(report["path"])
                    st.success(f"Deleted {report['filename']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
