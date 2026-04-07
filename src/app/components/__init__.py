"""
components/ — Composants réutilisables du dashboard.
"""

from src.app.components.data_loader import (
    load_market_data,
    ensure_market_data_loaded,
)
from src.app.components.sidebar import render_sidebar
from src.app.components.metric_cards import (
    money_metric,
    rate_metric,
    bp_metric,
)

__all__ = [
    "load_market_data",
    "ensure_market_data_loaded",
    "render_sidebar",
    "money_metric",
    "rate_metric",
    "bp_metric",
]
