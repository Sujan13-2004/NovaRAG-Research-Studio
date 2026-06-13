"""
NovaRAG Research Studio — Plotly Chart Builders.

Reusable chart components used across Dashboard, Analytics, and Browse pages.
"""

import plotly.graph_objects as go
from utils.helpers import CATEGORY_COLORS


def create_donut_chart(categories):
    """Creates a Plotly donut chart for paper categories."""
    labels = list(categories.keys())
    values = list(categories.values())
    colors = [CATEGORY_COLORS.get(c, "#64748B") for c in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.58,
        marker=dict(colors=colors, line=dict(color="#0F172A", width=2)),
        textinfo="percent",
        textfont=dict(size=11, color="#CBD5E1", family="Inter"),
        hovertemplate="<b>%{label}</b><br>Papers: %{value}<br>Share: %{percent}<extra></extra>",
        direction="clockwise",
        sort=False,
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", family="Inter"),
        showlegend=True,
        legend=dict(
            font=dict(size=10, color="#94A3B8"),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom", y=-0.35,
            xanchor="center", x=0.5,
        ),
        margin=dict(l=10, r=10, t=10, b=70),
        height=340,
    )
    return fig


def create_area_chart(year_dist):
    """Creates a Plotly area chart for papers published per year."""
    years = list(year_dist.keys())
    counts = list(year_dist.values())

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=counts,
        fill="tozeroy",
        line=dict(color="#8B5CF6", width=2.5),
        fillcolor="rgba(139,92,246,0.12)",
        mode="lines+markers",
        marker=dict(size=7, color="#A78BFA",
                    line=dict(color="#0F172A", width=1.5)),
        hovertemplate="<b>%{x}</b><br>Papers: %{y}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#64748B",
                   gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=11), dtick=1),
        yaxis=dict(color="#64748B",
                   gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=11)),
        font=dict(color="#CBD5E1", family="Inter"),
        margin=dict(l=40, r=20, t=10, b=40),
        height=340,
        hovermode="x unified",
    )
    return fig


def create_bar_chart(labels, values, color="#8B5CF6", title=""):
    """Creates a horizontal bar chart for analytics."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker=dict(
            color=color,
            line=dict(color="rgba(255,255,255,0.1)", width=1),
        ),
        hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#64748B", gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=11)),
        yaxis=dict(color="#CBD5E1", tickfont=dict(size=11), autorange="reversed"),
        font=dict(color="#CBD5E1", family="Inter"),
        margin=dict(l=10, r=20, t=30, b=30),
        height=max(200, len(labels) * 35 + 60),
        title=dict(text=title, font=dict(size=13, color="#E2E8F0")) if title else None,
    )
    return fig


def create_line_chart(x_vals, y_vals, color="#10B981", title=""):
    """Creates a line chart for trend visualizations."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals,
        mode="lines+markers",
        line=dict(color=color, width=2.5),
        marker=dict(size=7, color=color,
                    line=dict(color="#0F172A", width=1.5)),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3], 16)},{int(color[3:5], 16)},{int(color[5:7], 16)},0.08)",
        hovertemplate="<b>Query %{x}</b><br>Score: %{y:.1%}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#64748B", gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=11)),
        yaxis=dict(color="#64748B", gridcolor="rgba(255,255,255,0.04)",
                   tickfont=dict(size=11), tickformat=".0%"),
        font=dict(color="#CBD5E1", family="Inter"),
        margin=dict(l=50, r=20, t=30, b=30),
        height=300,
        title=dict(text=title, font=dict(size=13, color="#E2E8F0")) if title else None,
    )
    return fig


def create_gauge_chart(value, title="Score", max_val=1.0):
    """Creates a gauge chart for displaying scores like groundedness."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        number=dict(suffix="%", font=dict(size=28, color="#E2E8F0")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#64748B",
                      tickfont=dict(size=10, color="#64748B")),
            bar=dict(color="#8B5CF6"),
            bgcolor="rgba(30,41,59,0.5)",
            bordercolor="rgba(255,255,255,0.06)",
            steps=[
                dict(range=[0, 55], color="rgba(239,68,68,0.15)"),
                dict(range=[55, 75], color="rgba(245,158,11,0.15)"),
                dict(range=[75, 100], color="rgba(16,185,129,0.15)"),
            ],
            threshold=dict(
                line=dict(color="#10B981", width=3),
                thickness=0.8,
                value=55,
            ),
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", family="Inter"),
        margin=dict(l=30, r=30, t=40, b=10),
        height=220,
        title=dict(text=title, font=dict(size=12, color="#94A3B8"),
                   y=0.95, x=0.5, xanchor="center"),
    )
    return fig
