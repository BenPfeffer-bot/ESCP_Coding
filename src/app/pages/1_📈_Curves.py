"""
Curves — Page de visualisation des courbes de taux.

Affiche les 4 plots principaux :
  - Par swap rates
  - Zero rates
  - Discount factors
  - Forward rates
"""

import streamlit as st
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app.state import init_state, has_market_data, KEY_MATS, KEY_RATES, KEY_INTERP
from src.app.components.sidebar import render_sidebar
from src.app.components.data_loader import ensure_market_data_loaded

from src.plots.plotly_backend.curves import (
    plot_par_rates,
    plot_zero_rates,
    plot_discount_factors,
    plot_forward_rates,
)


# ═══════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Curves — Rates Desk",
    page_icon="📈",
    layout="wide",
)

init_state()
render_sidebar()


# ═══════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════

st.title("📈 Yield Curve")
st.caption("Visualize the par, zero, discount factor, and forward rate curves.")

# Vérifie que les données sont chargées
if not ensure_market_data_loaded():
    st.stop()

mats = st.session_state[KEY_MATS]
rates = st.session_state[KEY_RATES]
interp = st.session_state[KEY_INTERP]


# ═══════════════════════════════════════════════════════════
#  OPTIONS D'AFFICHAGE
# ═══════════════════════════════════════════════════════════

with st.expander("⚙️ Display options", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        show_nodes = st.checkbox(
            "Show bootstrap nodes",
            value=True,
            help="Display the interpolation nodes as red markers",
        )

    with col2:
        forward_horizon_months = st.select_slider(
            "Forward horizon",
            options=[1, 3, 6, 12],
            value=3,
            help="Horizon (in months) for the forward rate calculation",
            format_func=lambda m: f"{m}M",
        )
    forward_horizon = forward_horizon_months / 12.0


# ═══════════════════════════════════════════════════════════
#  PLOTS — GRILLE 2×2
# ═══════════════════════════════════════════════════════════

# Row 1 : Par rates + Zero rates
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Par Swap Rates")
    fig = plot_par_rates(mats, rates, title="")
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

with col2:
    st.markdown("#### Zero Coupon Rates")
    fig = plot_zero_rates(interp, title="", show_nodes=show_nodes)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


# Row 2 : Discount factors + Forward rates
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### Discount Factors")
    fig = plot_discount_factors(interp, title="", show_nodes=show_nodes)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

with col4:
    st.markdown(f"#### {forward_horizon_months}M Forward Rates")
    fig = plot_forward_rates(
        interp,
        title="",
        forward_horizon=forward_horizon,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


# ═══════════════════════════════════════════════════════════
#  TABLEAU DE DONNÉES
# ═══════════════════════════════════════════════════════════

st.divider()

with st.expander("📋 Raw data", expanded=False):
    import pandas as pd
    import numpy as np

    dfs = st.session_state["market_discount_factors"]
    zero_rates = -np.log(dfs) / mats

    df = pd.DataFrame(
        {
            "Maturity (Y)": mats,
            "Par rate (%)": rates * 100,
            "Zero rate (%)": zero_rates * 100,
            "Discount factor": dfs,
        }
    )

    st.dataframe(
        df.style.format(
            {
                "Maturity (Y)": "{:.2f}",
                "Par rate (%)": "{:.4f}",
                "Zero rate (%)": "{:.4f}",
                "Discount factor": "{:.8f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    # Export CSV
    csv = df.to_csv(index=False)
    st.download_button(
        "⬇️ Download CSV",
        data=csv,
        file_name=f"yield_curve_{st.session_state.get('market_last_update', 'today').strftime('%Y%m%d') if hasattr(st.session_state.get('market_last_update'), 'strftime') else 'today'}.csv",
        mime="text/csv",
    )
