"""
streamlit_app.py — Entry point du dashboard Rates Desk.

Lance avec : streamlit run app/streamlit_app.py
"""

import streamlit as st

from src.app.state import init_state
from src.app.components.sidebar import render_sidebar
from src.app.components.data_loader import ensure_market_data_loaded
from src.app.state import has_market_data, KEY_MATS, KEY_RATES

# ═══════════════════════════════════════════════════════════
#  CONFIGURATION DE LA PAGE
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ESCP Coding Project - Rates Desk",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**ESCP Coding Project Rates Desk** — US Treasury Pricer & Risk Engine\n\n"
            "A pedagogical quant finance project covering the full "
            "pipeline of a rates trading desk: data feed → bootstrap → "
            "interpolation → pricing → risk analytics."
        ),
    },
)


# ═══════════════════════════════════════════════════════════
#  INIT
# ═══════════════════════════════════════════════════════════

init_state()
render_sidebar()

# Charge les données si pas encore fait
ensure_market_data_loaded()


# ═══════════════════════════════════════════════════════════
#  PAGE D'ACCUEIL
# ═══════════════════════════════════════════════════════════

st.title("📊 ESCP Project - Rates")
st.caption("US Treasury Pricer & Risk Engine — April 2026")

st.markdown("""
Welcome to the **Rates Desk** dashboard. This project replicates the core tooling 
of a junior trader on a rates desk, from live data feed to interactive pricing 
and risk analytics.
""")

# ── Vue d'ensemble : les 4 pages ──────────────────────────

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 📈 Curves")
        st.markdown(
            "Visualize today's yield curve — par rates, zero rates, "
            "discount factors, and forward rates."
        )
        st.caption("Interactive charts with hover, zoom, and export.")

    with st.container(border=True):
        st.markdown("### 📊 Risk")
        st.markdown(
            "Compute sensitivities of a swap — DV01, convexity, "
            "KR-DV01 ladder, and stress tests."
        )
        st.caption("Bump & reprice methodology.")

with col2:
    with st.container(border=True):
        st.markdown("### 💰 Pricer")
        st.markdown(
            "Price any vanilla IRS interactively — adjust notional, "
            "maturity, fixed rate, and direction."
        )
        st.caption("Real-time NPV and par rate calculation.")

    with st.container(border=True):
        st.markdown("### 📜 History")
        st.markdown(
            "Track the evolution of yields over time — historical "
            "time series and curve evolution."
        )
        st.caption("Backed by SQLite snapshot storage.")

st.divider()

# ── Snapshot de la courbe du jour ─────────────────────────


if has_market_data():
    st.markdown("### Today's Snapshot")

    mats = st.session_state[KEY_MATS]
    rates = st.session_state[KEY_RATES]

    # Metrics clés
    col1, col2, col3, col4 = st.columns(4)

    # 3M / short end
    idx_3m = 0  # Premier point = 3M
    col1.metric(
        "3M",
        f"{rates[idx_3m] * 100:.3f}%",
        help=f"Short end — {mats[idx_3m]}Y",
    )

    # 2Y / belly
    idx_2y = next((i for i, m in enumerate(mats) if abs(m - 2.0) < 0.01), None)
    if idx_2y is not None:
        col2.metric("2Y", f"{rates[idx_2y] * 100:.3f}%")

    # 10Y / benchmark
    idx_10y = next((i for i, m in enumerate(mats) if abs(m - 10.0) < 0.01), None)
    if idx_10y is not None:
        col3.metric("10Y", f"{rates[idx_10y] * 100:.3f}%", help="Benchmark")

    # 30Y / long end
    idx_30y = next((i for i, m in enumerate(mats) if abs(m - 30.0) < 0.01), None)
    if idx_30y is not None:
        col4.metric("30Y", f"{rates[idx_30y] * 100:.3f}%")

    # Spread 2s10s (classique indicateur de la forme de la courbe)
    if idx_2y is not None and idx_10y is not None:
        spread_2s10s = (rates[idx_10y] - rates[idx_2y]) * 10000

        st.markdown(f"**2s10s spread**: `{spread_2s10s:+.1f} bp`")
        if spread_2s10s < 0:
            st.caption("⚠️ Inverted curve — historical recession signal")
        elif spread_2s10s < 20:
            st.caption("📊 Flat curve — low risk premium")
        else:
            st.caption("📈 Normal curve — positive term premium")

    st.divider()

    # Instructions
    st.info(
        "👈 Use the sidebar to navigate between pages, refresh data, "
        "or change interpolation method."
    )
else:
    st.warning("Market data not loaded. Click **Refresh data** in the sidebar.")
