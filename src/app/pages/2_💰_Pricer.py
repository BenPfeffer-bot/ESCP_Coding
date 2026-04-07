"""
Pricer — Page de pricing interactif d'un IRS vanille.

Permet de configurer un swap via sliders et voit la NPV / par rate
se recalculer en temps réel.
"""

import streamlit as st
import numpy as np

from src.app.state import (
    init_state,
    has_market_data,
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

from src.instruments.vanilla_swaps import VanillaSwap


# ═══════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Pricer — Rates Desk",
    page_icon="💰",
    layout="wide",
)

init_state()
render_sidebar()


# ═══════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════

st.title("💰 Swap Pricer")
st.caption("Price a vanilla IRS interactively. NPV and par rate update in real-time.")

if not ensure_market_data_loaded():
    st.stop()

mats = st.session_state[KEY_MATS]
rates = st.session_state[KEY_RATES]
interp = st.session_state[KEY_INTERP]


# ═══════════════════════════════════════════════════════════
#  CONTROLS
# ═══════════════════════════════════════════════════════════

st.markdown("### Trade Parameters")

col1, col2, col3, col4 = st.columns(4)

with col1:
    notional = st.number_input(
        "Notional (EUR)",
        min_value=1_000_000,
        max_value=1_000_000_000,
        value=st.session_state[KEY_SWAP_NOTIONAL],
        step=1_000_000,
        format="%d",
        help="Swap notional in EUR",
    )
    st.session_state[KEY_SWAP_NOTIONAL] = notional

with col2:
    maturity = st.slider(
        "Maturity (years)",
        min_value=1.0,
        max_value=30.0,
        value=float(st.session_state[KEY_SWAP_MATURITY]),
        step=0.5,
        help="Swap maturity in years",
    )
    st.session_state[KEY_SWAP_MATURITY] = maturity

with col3:
    direction = st.radio(
        "Direction",
        options=["receiver", "payer"],
        index=0 if st.session_state[KEY_SWAP_DIRECTION] == "receiver" else 1,
        horizontal=True,
        help="Receiver = receives fixed (long duration). Payer = pays fixed (short duration).",
    )
    st.session_state[KEY_SWAP_DIRECTION] = direction

with col4:
    frequency = st.selectbox(
        "Payment frequency",
        options=[1.0, 0.5, 0.25],
        format_func=lambda f: {1.0: "Annual", 0.5: "Semi-annual", 0.25: "Quarterly"}[f],
        index=0,
        help="Coupon payment frequency",
    )
    st.session_state[KEY_SWAP_FREQUENCY] = frequency


# ═══════════════════════════════════════════════════════════
#  CALCULATE PAR RATE (pour initialiser le fixed rate slider)
# ═══════════════════════════════════════════════════════════

# On construit un swap temporaire at-par pour obtenir le par rate
temp_swap = VanillaSwap(
    notional=notional,
    fixed_rate=0.0,
    maturity=maturity,
    payment_frequency=frequency,
    direction=direction,
)
par_rate = temp_swap.par_rate(interp)

# Si le fixed rate du state n'a jamais été initialisé, on le met au par rate
if st.session_state[KEY_SWAP_FIXED_RATE] is None:
    st.session_state[KEY_SWAP_FIXED_RATE] = par_rate


# Slider pour le fixed rate avec le par rate comme référence
st.markdown("### Fixed Rate")

col_slider, col_reset = st.columns([5, 1])

with col_slider:
    # Range autour du par rate : ±200 bp
    fixed_rate_pct = st.slider(
        "Fixed rate (%)",
        min_value=(par_rate - 0.02) * 100,
        max_value=(par_rate + 0.02) * 100,
        value=st.session_state[KEY_SWAP_FIXED_RATE] * 100,
        step=0.01,
        format="%.4f%%",
        help=f"Par rate: {par_rate * 100:.4f}%",
    )
    fixed_rate = fixed_rate_pct / 100
    st.session_state[KEY_SWAP_FIXED_RATE] = fixed_rate

with col_reset:
    st.write("")  # spacer
    if st.button("🔄 At par", use_container_width=True, help="Reset to par rate"):
        st.session_state[KEY_SWAP_FIXED_RATE] = par_rate
        st.rerun()


# ═══════════════════════════════════════════════════════════
#  PRICE THE SWAP
# ═══════════════════════════════════════════════════════════

swap = VanillaSwap(
    notional=notional,
    fixed_rate=fixed_rate,
    maturity=maturity,
    payment_frequency=frequency,
    direction=direction,
)

npv = swap.npv(interp)
spread_bp = (fixed_rate - par_rate) * 10000


# ═══════════════════════════════════════════════════════════
#  RESULTS
# ═══════════════════════════════════════════════════════════

st.divider()
st.markdown("### Results")

col1, col2, col3, col4 = st.columns(4)

# NPV avec delta coloré
col1.metric(
    label="NPV",
    value=f"€{npv:,.2f}",
    delta=f"{npv:+,.0f}" if abs(npv) > 1 else None,
    help="Net Present Value of the swap",
)

col2.metric(
    label="Par Rate",
    value=f"{par_rate * 100:.4f}%",
    help="Fixed rate that makes NPV = 0",
)

col3.metric(
    label="Spread vs Par",
    value=f"{spread_bp:+.1f} bp",
    delta_color="off",
    help="Difference between the chosen fixed rate and the par rate",
)

# Break-even : valeur du coupon par année
annual_coupon = fixed_rate * notional * frequency
col4.metric(
    label="Annual Coupon",
    value=f"€{annual_coupon:,.0f}",
    help=f"Fixed-leg coupon payment per period ({frequency}Y)",
)


# ═══════════════════════════════════════════════════════════
#  SWAP DETAILS
# ═══════════════════════════════════════════════════════════

st.divider()

with st.expander("📄 Swap details", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Trade**")
        st.markdown(f"- Notional: **€{notional:,.0f}**")
        st.markdown(f"- Direction: **{direction.capitalize()}**")
        st.markdown(f"- Maturity: **{maturity}Y**")
        st.markdown(f"- Payment frequency: **{frequency}Y**")
        st.markdown(f"- Fixed rate: **{fixed_rate * 100:.4f}%**")

    with col2:
        st.markdown("**Pricing**")
        pv_fixed = swap.pv_fixed_leg(interp)
        pv_float = swap.pv_floating_leg(interp)
        st.markdown(f"- PV fixed leg (per 1€): **{pv_fixed:.8f}**")
        st.markdown(f"- PV floating leg (per 1€): **{pv_float:.8f}**")
        st.markdown(f"- NPV: **€{npv:,.2f}**")
        st.markdown(f"- Par rate: **{par_rate * 100:.4f}%**")
        st.markdown(f"- Spread vs par: **{spread_bp:+.2f} bp**")


# ═══════════════════════════════════════════════════════════
#  CASH FLOWS
# ═══════════════════════════════════════════════════════════

with st.expander("💵 Cash flows", expanded=False):
    import pandas as pd

    # Génère le schedule et les cash-flows
    payment_dates = swap.payment_dates

    cashflows = []
    for t in payment_dates:
        z_t = interp.discount_factor(t)
        # Coupon fixe (par 1 de notional, puis scale)
        tau = frequency  # simplification : équi-spacé
        coupon_fixed = fixed_rate * tau * notional
        pv_coupon = coupon_fixed * z_t

        cashflows.append(
            {
                "Payment date (Y)": t,
                "Discount factor": z_t,
                "Fixed coupon (EUR)": coupon_fixed,
                "PV coupon (EUR)": pv_coupon,
            }
        )

    df_cf = pd.DataFrame(cashflows)

    # Style
    st.dataframe(
        df_cf.style.format(
            {
                "Payment date (Y)": "{:.2f}",
                "Discount factor": "{:.8f}",
                "Fixed coupon (EUR)": "{:,.2f}",
                "PV coupon (EUR)": "{:,.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    # Total
    total_pv = df_cf["PV coupon (EUR)"].sum()
    st.caption(
        f"Sum of PV coupons: **€{total_pv:,.2f}** "
        f"(+ principal fictif: €{interp.discount_factor(maturity) * notional:,.2f})"
    )


# ═══════════════════════════════════════════════════════════
#  NAVIGATION
# ═══════════════════════════════════════════════════════════

st.divider()
st.info(
    "💡 This swap configuration is shared with the **Risk** page. "
    "Navigate there to see DV01, convexity, and KR-DV01 ladder."
)
