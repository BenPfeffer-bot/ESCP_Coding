"""
state.py — Gestion du session_state Streamlit.

Centralise l'initialisation des variables persistantes entre les reruns.
"""

import streamlit as st


# ═══════════════════════════════════════════════════════════
#  CLÉS DU SESSION STATE
# ═══════════════════════════════════════════════════════════

# Données de marché
KEY_MATS = "market_maturities"
KEY_RATES = "market_rates"
KEY_DFS = "market_discount_factors"
KEY_INTERP = "market_interpolator"
KEY_LAST_UPDATE = "market_last_update"

# Paramètres globaux
KEY_INTERP_METHOD = "interpolation_method"
KEY_FORCE_REFRESH = "force_refresh"

# Swap courant (partagé entre Pricer et Risk)
KEY_SWAP_NOTIONAL = "swap_notional"
KEY_SWAP_MATURITY = "swap_maturity"
KEY_SWAP_FIXED_RATE = "swap_fixed_rate"
KEY_SWAP_DIRECTION = "swap_direction"
KEY_SWAP_FREQUENCY = "swap_frequency"


def init_state():
    """
    Initialise les valeurs par défaut du session_state.
    Appelé au début de chaque page pour garantir que les clés existent.
    """
    defaults = {
        # Market data
        KEY_MATS: None,
        KEY_RATES: None,
        KEY_DFS: None,
        KEY_INTERP: None,
        KEY_LAST_UPDATE: None,
        # Settings
        KEY_INTERP_METHOD: "cubic_spline",
        KEY_FORCE_REFRESH: False,
        # Swap defaults
        KEY_SWAP_NOTIONAL: 10_000_000,
        KEY_SWAP_MATURITY: 5.0,
        KEY_SWAP_FIXED_RATE: None,  #  sera initialisé au par rate
        KEY_SWAP_DIRECTION: "receiver",
        KEY_SWAP_FREQUENCY: 1.0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def has_market_data() -> bool:
    """True si les données de marché sont chargées dans le state."""
    return (
        st.session_state.get(KEY_MATS) is not None
        and st.session_state.get(KEY_RATES) is not None
        and st.session_state.get(KEY_INTERP) is not None
    )
