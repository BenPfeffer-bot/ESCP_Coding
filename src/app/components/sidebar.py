"""
Contient :
  - Statut des données (dernière mise à jour)
  - Bouton refresh
  - Selector de méthode d'interpolation
  - Infos sur le projet
"""

import streamlit as st
from datetime import datetime

from src.app.state import (
    KEY_LAST_UPDATE,
    KEY_INTERP_METHOD,
    KEY_MATS,
    KEY_RATES,
)
from src.app.components.data_loader import load_market_data


def render_sidebar():
    """Rend la sidebar globale. À appeler au début de chaque page."""

    with st.sidebar:
        # ── Statut des données ────────────────────────
        st.markdown("#### Market Data")

        last_update = st.session_state.get(KEY_LAST_UPDATE)
        if last_update:
            age = datetime.now() - last_update
            age_seconds = int(age.total_seconds())

            if age_seconds < 60:
                age_str = f"{age_seconds}s ago"
            elif age_seconds < 3600:
                age_str = f"{age_seconds // 60}m ago"
            else:
                age_str = f"{age_seconds // 3600}h ago"

            st.success(f"✓ Loaded ({age_str})")

            # Stats rapides
            mats = st.session_state.get(KEY_MATS)
            rates = st.session_state.get(KEY_RATES)
            if mats is not None and rates is not None:
                st.caption(
                    f"**{len(mats)}** points | "
                    f"**{rates.min() * 100:.2f}%** → **{rates.max() * 100:.2f}%**"
                )
        else:
            st.warning("⚠ No data loaded")

        # Bouton refresh
        if st.button("🔄 Refresh data", use_container_width=True):
            with st.spinner("Fetching live data..."):
                success = load_market_data(force_refresh=True)
                if success:
                    st.success("Data refreshed")
                    st.rerun()

        st.divider()

        # ── Paramètres ────────────────────────────────
        st.markdown("#### Settings")

        # Sélection de la méthode d'interpolation
        method = st.selectbox(
            "Interpolation",
            options=["cubic_spline", "linear"],
            index=0 if st.session_state.get(KEY_INTERP_METHOD) == "cubic_spline" else 1,
            help="Méthode d'interpolation de la courbe des zero rates",
        )

        # Si changé → reload avec la nouvelle méthode
        if method != st.session_state.get(KEY_INTERP_METHOD):
            st.session_state[KEY_INTERP_METHOD] = method
            with st.spinner("Rebuilding interpolator..."):
                load_market_data(force_refresh=False)
            st.rerun()

        st.divider()

        # ── Footer ────────────────────────────────────
        st.caption(
            "**Data sources:**\n"
            "- yfinance (CBOE indices)\n"
            "- FRED (Treasury CMT)\n\n"
            "**Cache:** SQLite + Streamlit"
        )
