"""
Risk — Page des sensibilités d'un swap.

Calcule et affiche DV01, convexité, KR-DV01 ladder et stress test
pour le swap configuré dans la page Pricer.
"""

import streamlit as st
import numpy as np

from src.app.state import (
    init_state,
    KEY_MATS,
    KEY_RATES,
    KEY_INTERP,
    KEY_SWAP_NOTIONAL,
    KEY_SWAP_MATURITY,
    KEY_SWAP_FIXED_RATE,
    KEY_SWAP_DIRECTION,
    KEY_SWAP_FREQUENCY,
)
from src.app.components.sidebar import render_sidebar
from src.app.components.data_loader import ensure_market_data_loaded
from src.app.components.metric_cards import money_metric, bp_metric

from src.instruments.vanilla_swaps import VanillaSwap
from src.risks.sensitivities import (
    compute_dv01,
    compute_convexity,
    compute_key_rate_dv01,
)
from src.utils.helper import reprice

from src.plots.plotly_backend.risks import (
    plot_kr_dv01_ladder,
    plot_stress_test,
)


# ═══════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Risk — Rates Desk",
    page_icon="📊",
    layout="wide",
)

init_state()
render_sidebar()


# ═══════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════

st.title("📊 Risk Analytics")
st.caption("Sensitivities of the swap configured in the Pricer page.")

if not ensure_market_data_loaded():
    st.stop()

mats = st.session_state[KEY_MATS]
rates = st.session_state[KEY_RATES]
interp = st.session_state[KEY_INTERP]


# ═══════════════════════════════════════════════════════════
#  CHECK SWAP CONFIGURÉ
# ═══════════════════════════════════════════════════════════

if st.session_state[KEY_SWAP_FIXED_RATE] is None:
    st.warning(
        "⚠️ No swap configured yet. Go to the **Pricer** page first to define a swap."
    )
    st.stop()

# Reconstruire le swap depuis le state
swap = VanillaSwap(
    notional=st.session_state[KEY_SWAP_NOTIONAL],
    fixed_rate=st.session_state[KEY_SWAP_FIXED_RATE],
    maturity=st.session_state[KEY_SWAP_MATURITY],
    payment_frequency=st.session_state[KEY_SWAP_FREQUENCY],
    direction=st.session_state[KEY_SWAP_DIRECTION],
)


# ═══════════════════════════════════════════════════════════
#  SWAP SUMMARY (readonly)
# ═══════════════════════════════════════════════════════════

with st.container(border=True):
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown(f"**Notional**\n€{swap.notional:,.0f}")
    col2.markdown(f"**Direction**\n{swap.direction.capitalize()}")
    col3.markdown(f"**Maturity**\n{swap.maturity}Y")
    col4.markdown(f"**Fixed rate**\n{swap.fixed_rate * 100:.4f}%")
    col5.markdown(f"**Frequency**\n{swap.payment_frequency}Y")

st.caption("💡 Change these parameters in the **Pricer** page.")


# ═══════════════════════════════════════════════════════════
#  COMPUTE SENSITIVITIES (avec spinner)
# ═══════════════════════════════════════════════════════════

with st.spinner("Computing sensitivities..."):
    npv = swap.npv(interp)
    dv01 = compute_dv01(swap, mats, rates)
    convexity = compute_convexity(swap, mats, rates)
    kr_dv01 = compute_key_rate_dv01(swap, mats, rates)


# ═══════════════════════════════════════════════════════════
#  METRICS — Top-level sensitivities
# ═══════════════════════════════════════════════════════════

st.divider()
st.markdown("### Top-level Sensitivities")

col1, col2, col3, col4 = st.columns(4)

with col1:
    money_metric(
        "NPV",
        npv,
        help="Net Present Value of the swap",
    )

with col2:
    bp_metric(
        "DV01 (parallel)",
        dv01,
        help="Change in NPV for a 1bp parallel shift of the curve. Positive = long duration.",
    )

with col3:
    bp_metric(
        "Convexity",
        convexity,
        decimals=4,
        help="Second-order sensitivity. Positive = convex (receiver vanilla).",
    )

with col4:
    # Duration implicite (DV01 / notional × 10000)
    duration_implied = (abs(dv01) / swap.notional) * 10000
    st.metric(
        "Implied Duration",
        f"{duration_implied:.2f} Y",
        help="DV01 / (Notional × 1bp) — effective duration",
    )


# ═══════════════════════════════════════════════════════════
#  KR-DV01 LADDER
# ═══════════════════════════════════════════════════════════

st.divider()
st.markdown("### Key Rate DV01 Ladder")
st.caption(
    "Sensitivity to each tenor of the curve, computed by bumping one point at a time."
)

fig_kr = plot_kr_dv01_ladder(kr_dv01, title="")
st.plotly_chart(fig_kr, use_container_width=True, config={"displaylogo": False})

# Cohérence somme vs parallèle
sum_kr = sum(kr_dv01.values())
diff_pct = abs(sum_kr - dv01) / abs(dv01) * 100 if dv01 != 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    bp_metric("Sum of KR-DV01", sum_kr, help="Should ≈ parallel DV01")
with col2:
    bp_metric("Parallel DV01", dv01, help="For comparison")
with col3:
    st.metric(
        "Consistency",
        f"{diff_pct:.4f}%",
        help="Relative difference between sum and parallel — should be ~0",
    )


# ═══════════════════════════════════════════════════════════
#  STRESS TEST
# ═══════════════════════════════════════════════════════════

st.divider()
st.markdown("### Stress Test — Parallel Shifts")
st.caption(
    "P&L for different parallel shifts of the curve, computed by full reprice. "
    "The bottom subplot isolates the convexity effect."
)

# Controls pour le stress test
col1, col2 = st.columns([2, 1])
with col1:
    shift_range = st.slider(
        "Shift range (± bp)",
        min_value=50,
        max_value=300,
        value=100,
        step=25,
        help="Range of parallel shifts to compute",
    )
with col2:
    n_points = st.number_input(
        "Number of points",
        min_value=5,
        max_value=21,
        value=9,
        step=2,
        help="Number of shifts in the range (odd number for symmetry)",
    )

# Calcul du stress test
shifts_bp = np.linspace(-shift_range, shift_range, n_points)

with st.spinner("Running stress test..."):
    pnl_values = np.array([reprice(swap, mats, rates + s / 10000) for s in shifts_bp])

fig_stress = plot_stress_test(
    shifts_bp,
    pnl_values,
    dv01=dv01,
    convexity=convexity,
    title="",
)
st.plotly_chart(fig_stress, use_container_width=True, config={"displaylogo": False})


# ═══════════════════════════════════════════════════════════
#  STRESS TEST TABLE
# ═══════════════════════════════════════════════════════════

with st.expander("📋 Stress test details", expanded=False):
    import pandas as pd

    # Table
    linear_approx = -dv01 * shifts_bp
    quad_approx = -dv01 * shifts_bp + 0.5 * convexity * shifts_bp**2

    df_stress = pd.DataFrame(
        {
            "Shift (bp)": shifts_bp,
            "P&L Full reprice (€)": pnl_values,
            "Linear approx (€)": linear_approx,
            "Quadratic approx (€)": quad_approx,
            "Convexity effect (€)": pnl_values - linear_approx,
        }
    )

    st.dataframe(
        df_stress.style.format(
            {
                "Shift (bp)": "{:+.0f}",
                "P&L Full reprice (€)": "{:+,.2f}",
                "Linear approx (€)": "{:+,.2f}",
                "Quadratic approx (€)": "{:+,.2f}",
                "Convexity effect (€)": "{:+,.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "**Convexity effect** = Full reprice − Linear. "
        "This is the P&L gain (or loss for payers) from the curvature of the swap value function."
    )


# ═══════════════════════════════════════════════════════════
#  KR-DV01 TABLE
# ═══════════════════════════════════════════════════════════

with st.expander("📋 KR-DV01 breakdown", expanded=False):
    import pandas as pd

    df_kr = pd.DataFrame(
        {
            "Maturity": [
                f"{int(m * 12)}M" if m < 1 else f"{int(m)}Y"
                for m in sorted(kr_dv01.keys())
            ],
            "KR-DV01 (EUR/bp)": [kr_dv01[m] for m in sorted(kr_dv01.keys())],
            "% of total": [
                kr_dv01[m] / sum_kr * 100 if sum_kr != 0 else 0
                for m in sorted(kr_dv01.keys())
            ],
        }
    )

    st.dataframe(
        df_kr.style.format(
            {
                "KR-DV01 (EUR/bp)": "{:+,.2f}",
                "% of total": "{:+.2f}%",
            }
        ).background_gradient(
            subset=["KR-DV01 (EUR/bp)"],
            cmap="RdYlGn",
            vmin=-abs(max(kr_dv01.values(), key=abs)),
            vmax=abs(max(kr_dv01.values(), key=abs)),
        ),
        use_container_width=True,
        hide_index=True,
    )
