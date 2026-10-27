"""Look and feel of the dashboard: colors, fonts, chart template and small layout helpers."""
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

PALETTE = ["#0B3C5D", "#D9822B", "#2A9D8F", "#8A5A9E", "#6B7C93", "#B23A48", "#4F9DDE", "#9CA3AF"]
DIVERGING = [[0.0, "#B23A48"], [0.5, "#F5F6F8"], [1.0, "#0B3C5D"]]  # red = negative, navy = positive
FONT = "Inter, -apple-system, 'Segoe UI', Roboto, sans-serif"

# One Plotly template for every chart: palette, fonts, light grid, legend above the plot
pio.templates["dashboard"] = go.layout.Template(layout=go.Layout(
    font=dict(family=FONT, size=13, color="#14213D"),
    colorway=PALETTE,
    title=dict(font=dict(size=16), x=0, xanchor="left"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(l=10, r=10, t=70, b=10),
    xaxis=dict(showgrid=False, linecolor="#D0D5DD"),
    yaxis=dict(gridcolor="#EEF0F3", zeroline=False),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
))
pio.templates.default = "plotly_white+dashboard"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}
.block-container { padding-top: 2.5rem; max-width: 1250px; }
footer, #MainMenu { visibility: hidden; }

/* Header */
.hero h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.02em; margin: 0; padding: 0; color: #14213D; }
.hero p { color: #5B6B7F; margin: .35rem 0 1.4rem 0; font-size: 1rem; }

/* KPI cards */
[data-testid="stMetric"] {
    background: #F4F6F8; border: 1px solid #E4E8EE; border-radius: 12px; padding: 14px 18px;
}
[data-testid="stMetricLabel"] p { color: #5B6B7F; font-size: .82rem; font-weight: 500; }
[data-testid="stMetricValue"] { font-weight: 600; font-variant-numeric: tabular-nums; }

/* Insight box */
.insight {
    border-left: 4px solid #0B3C5D; background: #F4F6F8; border-radius: 8px;
    padding: 14px 18px; margin: 1rem 0 1.2rem 0; color: #14213D; line-height: 1.5;
}

/* Tabs and expanders */
.stTabs [data-baseweb="tab"] p { font-weight: 500; font-size: .95rem; }
[data-testid="stExpander"] { border-radius: 10px; border-color: #E4E8EE; }
[data-testid="stAlert"] { border-radius: 10px; }
</style>
"""


def apply():
    """Inject the CSS. Call once, right after st.set_page_config()."""
    st.markdown(CSS, unsafe_allow_html=True)


def header(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def insight(html):
    st.markdown(f'<div class="insight">{html}</div>', unsafe_allow_html=True)


def chart(fig, **kwargs):
    """Drop-in replacement for st.plotly_chart with cleaner axes and hover."""
    fig.update_xaxes(title_text=None)
    fig.update_yaxes(title_text=None)
    fig.update_layout(legend_title_text=None)
    if fig.data and all(t.type == "scatter" for t in fig.data):
        fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, **kwargs)
