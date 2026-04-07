"""
History — Page historique.

Affiche l'évolution d'une maturité dans le temps et l'overlay de
courbes à différentes dates.
"""

import streamlit as st
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app.state import init_state
from src.app.components.sidebar import render_sidebar
from src.app.components.data_loader import ensure_market_data_loaded

from src.utils.cache import (
    get_maturity_history,
    get_curve_history,
    get_db_stats,
)
from src.plots.plotly_backend.history import (
    plot_historical_maturity,
    plot_curve_evolution,
)


# ═══════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="History — Rates Desk",
    page_icon="📜",
    layout="wide",
)

init_state()
render_sidebar()


# ═══════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════

st.title("📜 Historical Data")
st.caption("Track the evolution of yields and curves over time.")

if not ensure_market_data_loaded():
    st.stop()


# ═══════════════════════════════════════════════════════════
#  DB STATS
# ═══════════════════════════════════════════════════════════

stats = get_db_stats()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total snapshots",
    stats["nb_snapshots"],
    help="Number of distinct snapshots stored in the SQLite cache",
)

col2.metric(
    "Unique dates",
    stats["nb_dates"],
    help="Number of distinct market dates",
)

col3.metric(
    "Total rows",
    stats["nb_rows"],
    help="Total number of (snapshot, maturity) rows",
)

date_range_str = "N/A"
if stats["date_range"][0] is not None:
    if stats["date_range"][0] == stats["date_range"][1]:
        date_range_str = stats["date_range"][0]
    else:
        date_range_str = f"{stats['date_range'][0]} → {stats['date_range'][1]}"

col4.metric(
    "Date range",
    date_range_str,
    help="First and last dates in the cache",
)

# Avertissement si pas assez de données
if stats["nb_dates"] <= 1:
    st.warning(
        "⚠️ Only **1 date** in the cache. Historical plots will show placeholders. "
        "Run snapshots over several days to build meaningful history."
    )


# ═══════════════════════════════════════════════════════════
#  HISTORICAL MATURITY
# ═══════════════════════════════════════════════════════════

st.divider()
st.markdown("### Yield Time Series")

mats = st.session_state["market_maturities"]
maturity_options = [float(m) for m in mats]

col1, col2 = st.columns([1, 3])

with col1:
    selected_maturity = st.selectbox(
        "Maturity",
        options=maturity_options,
        format_func=lambda m: f"{int(m * 12)}M" if m < 1 else f"{int(m)}Y",
        index=maturity_options.index(10.0) if 10.0 in maturity_options else 0,
    )

with col2:
    n_days = st.slider(
        "Lookback window (days)",
        min_value=7,
        max_value=365,
        value=30,
        step=1,
        help="How many days of history to show",
    )

# Fetch history
dates, rates_hist = get_maturity_history(selected_maturity, n_days=n_days)

# Label
if selected_maturity < 1:
    label = f"{int(selected_maturity * 12)}M"
else:
    label = f"{int(selected_maturity)}Y"

fig_hist = plot_historical_maturity(
    dates,
    rates_hist,
    maturity_label=label,
    title=f"{label} Treasury Yield — Historical",
)
st.plotly_chart(fig_hist, use_container_width=True, config={"displaylogo": False})


# ═══════════════════════════════════════════════════════════
#  CURVE EVOLUTION (overlay)
# ═══════════════════════════════════════════════════════════

st.divider()
st.markdown("### Curve Evolution")
st.caption(
    "Overlay of the yield curve at different dates. "
    "The most recent curve is highlighted."
)

max_curves = st.slider(
    "Number of curves to overlay",
    min_value=2,
    max_value=10,
    value=5,
)

curves_history = get_curve_history(n_days=max_curves)

fig_evolution = plot_curve_evolution(
    curves_history,
    title="",
    max_curves=max_curves,
)
st.plotly_chart(fig_evolution, use_container_width=True, config={"displaylogo": False})


# ═══════════════════════════════════════════════════════════
#  INFO BOX
# ═══════════════════════════════════════════════════════════

st.divider()

with st.expander("ℹ️ About historical data", expanded=False):
    st.markdown("""
    **How it works:**
    
    Every time you fetch market data (automatically on load or via the 
    **Refresh data** button in the sidebar), a snapshot is stored in the 
    local SQLite database (`db/cache/yields.db`).
    
    **To build history:**
    1. Run the dashboard regularly (e.g., once per trading day)
    2. Click **Refresh data** to force a live fetch
    3. After a few days, the time series and curve evolution plots will 
       show meaningful data
    
    **Data sources:**
    - `yfinance` for CBOE indices (3M, 5Y, 10Y, 30Y)
    - FRED API for intermediate maturities (6M, 1Y, 2Y, 3Y, 7Y, 20Y)
    
    **Storage:**
    - Each snapshot is one row per (maturity, fetch) combination
    - ~10 rows per snapshot × N snapshots per day
    - Negligible disk usage (few KB per year)
    """)
