"""
On utilise @st.cache_data pour éviter de re-fetcher à chaque interaction.
Le cache Streamlit est invalidé quand les paramètres changent.
"""

import streamlit as st
import numpy as np
from datetime import datetime
from typing import Tuple

from src.api.data_feed import DataFeed
from src.curves.bootstrapper import bootstrap_discount_factors
from src.curves.interpolation import YieldCurveInterpolator
from src.app.state import (
    KEY_MATS,
    KEY_RATES,
    KEY_DFS,
    KEY_INTERP,
    KEY_LAST_UPDATE,
    KEY_INTERP_METHOD,
)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_fetch_snapshot(
    force_refresh: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fetch un snapshot avec cache Streamlit.

    Le TTL de 1h évite de re-hit les APIs trop souvent pendant une session.
    Le SQLite cache sous-jacent fait sa propre gestion (daily).

    Args:
        force_refresh: bypass tous les caches (Streamlit + SQLite)

    Returns:
        (maturities, rates) en np.ndarray
    """
    feed = DataFeed(use_cache=not force_refresh)
    mats, rates = feed.fetch_snapshot(force_refresh=force_refresh)
    return mats, rates


def load_market_data(force_refresh: bool = False) -> bool:
    """
    Charge les données de marché dans le session_state.

    Pipeline complet : fetch → bootstrap → interpolate.
    Stocke les résultats dans st.session_state pour partage entre pages.

    Args:
        force_refresh: si True, bypass les caches et re-fetch

    Returns:
        True si le load a réussi, False sinon
    """
    try:
        # 1. Fetch (avec ou sans cache)
        if force_refresh:
            # Invalide le cache Streamlit et re-fetch
            _cached_fetch_snapshot.clear()

        mats, rates = _cached_fetch_snapshot(force_refresh=force_refresh)

        if mats is None or len(mats) == 0:
            st.error("❌ Failed to fetch market data")
            return False

        # 2. Bootstrap
        dfs = bootstrap_discount_factors(mats, rates)

        # 3. Interpolator
        method = st.session_state.get(KEY_INTERP_METHOD, "cubic_spline")
        interp = YieldCurveInterpolator(mats, dfs, method=method)

        # 4. Store dans session_state
        st.session_state[KEY_MATS] = mats
        st.session_state[KEY_RATES] = rates
        st.session_state[KEY_DFS] = dfs
        st.session_state[KEY_INTERP] = interp
        st.session_state[KEY_LAST_UPDATE] = datetime.now()

        return True

    except Exception as e:
        st.error(f"❌ Error loading market data: {e}")
        return False


def ensure_market_data_loaded() -> bool:
    """
    S'assure que les données sont chargées. Si non, les charge.
    À appeler au début de chaque page qui a besoin de données.

    Returns:
        True si les données sont disponibles après l'appel
    """
    from src.app.state import has_market_data

    if not has_market_data():
        with st.spinner("Loading market data..."):
            return load_market_data()
    return True
