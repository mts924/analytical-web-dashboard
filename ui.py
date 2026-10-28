"""Look and feel of the dashboard: colors, chart template and small layout helpers.

The font itself (Inter) is set in .streamlit/config.toml, so it applies to every widget."""
import html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

PALETTE = ["#0B3C5D", "#D9822B", "#2A9D8F", "#8A5A9E", "#6B7C93", "#B23A48", "#4F9DDE", "#9CA3AF"]
DIVERGING = [[0.0, "#B23A48"], [0.5, "#F5F6F8"], [1.0, "#0B3C5D"]]  # red = negative, navy = positive
GREEN, RED = "#15803D", "#B23A48"
FONT = "Inter, -apple-system, 'Segoe UI', Roboto, sans-serif"

# One Plotly template for every chart: palette, fonts, light grid, legend above the plot
pio.templates["dashboard"] = go.layout.Template(layout=go.Layout(
    font=dict(family=FONT, size=13, color="#14213D"),
    colorway=PALETTE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(showgrid=False, linecolor="#D0D5DD"),
    yaxis=dict(gridcolor="#EEF0F3", zeroline=False),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
))
pio.templates.default = "plotly_white+dashboard"

CSS = """
<style>
.block-container { padding-top: 2.5rem; max-width: 1250px; }
footer, #MainMenu { visibility: hidden; }

/* Header */
.hero h1 { font-size: 2.1rem; font-weight: 700; letter-spacing: -0.02em; margin: 0; padding: 0; color: #14213D; }
.hero p { color: #5B6B7F; margin: .35rem 0 1.4rem 0; font-size: 1rem; }

/* KPI cards */
[data-testid="stMetric"] {
    background: #F4F6F8; border: 1px solid #E4E8EE; border-radius: 12px; padding: 12px 16px;
    box-shadow: 0 1px 2px rgba(16, 24, 40, .05);
}
[data-testid="stMetricLabel"] p { color: #5B6B7F; font-size: .82rem; font-weight: 500; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    font-size: 1.75rem; font-weight: 600; font-variant-numeric: tabular-nums;
}

/* Insight box */
.insight {
    border-left: 4px solid #0B3C5D; background: #F4F6F8; border-radius: 4px 10px 10px 4px;
    padding: 14px 18px; margin: 1rem 0 1.4rem 0; color: #14213D; line-height: 1.5;
}

/* Tabs, expanders, tables, sidebar */
.stTabs [data-baseweb="tab-list"] { gap: 1.6rem; }
.stTabs [data-baseweb="tab"] p { font-weight: 500; font-size: .95rem; }
[data-testid="stExpander"] { border-radius: 10px; border-color: #E4E8EE; }
[data-testid="stAlert"] { border-radius: 10px; }
[data-testid="stDataFrame"] { border: 1px solid #E4E8EE; border-radius: 10px; overflow: hidden; }
[data-testid="stSidebar"] h3 { font-size: 1.05rem; font-weight: 600; margin-bottom: .2rem; }

/* Chart titles live outside the figure so they never collide with the legend */
.chart-title { font-weight: 600; font-size: 1rem; color: #14213D; margin: 1.2rem 0 .2rem 0; }
.mobile-hint { display: none; color: #5B6B7F; font-size: .85rem; margin: -.6rem 0 1rem 0; }

/* Footer */
.footer {
    color: #8A97A8; font-size: .8rem; border-top: 1px solid #E4E8EE; margin-top: 2.5rem; padding-top: 1rem;
}

/* Phones: KPI cards two per row, smaller title and cards */
@media (max-width: 640px) {
    .block-container { padding: 1.5rem 1rem 3rem 1rem; }
    .hero h1 { font-size: 1.6rem; }
    .hero p { font-size: .92rem; margin-bottom: 1rem; }
    .mobile-hint { display: block; }
    [data-testid="stColumn"]:has([data-testid="stMetric"]) { min-width: calc(50% - 1rem) !important; }
    [data-testid="stMetric"] { padding: 10px 12px; }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * { font-size: 1.35rem; }
    [data-testid="stMetricLabel"] p { font-size: .72rem; }
    .insight { padding: 10px 14px; font-size: .92rem; }
}
</style>
"""


def apply():
    """Inject the CSS. Call once, right after st.set_page_config()."""
    st.markdown(CSS, unsafe_allow_html=True)


def header(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def insight(html):
    st.markdown(f'<div class="insight">{html}</div>', unsafe_allow_html=True)


def mobile_hint():
    """Visible on phones only: the sidebar is folded away there."""
    st.markdown('<div class="mobile-hint">Tap the » arrow at the top left to choose assets and period.</div>',
                unsafe_allow_html=True)


def footer(text):
    st.markdown(f'<div class="footer">{text}</div>', unsafe_allow_html=True)


def chart(fig, **kwargs):
    """Drop-in replacement for st.plotly_chart: title above the chart, cleaner axes and hover, no toolbar."""
    title = fig.layout.title.text
    if title:
        st.markdown(f'<div class="chart-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    fig.update_layout(title_text=None)
    fig.update_xaxes(title_text=None)
    fig.update_yaxes(title_text=None)
    fig.update_layout(legend_title_text=None)
    if fig.layout.height is None:
        fig.update_layout(height=420)
    if fig.data and all(t.type == "scatter" for t in fig.data):
        fig.update_layout(hovermode="x unified")
    kwargs.setdefault("config", {"displayModeBar": False})
    st.plotly_chart(fig, **kwargs)
