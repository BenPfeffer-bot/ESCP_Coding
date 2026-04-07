"""
Wrappers autour de st.metric avec formatage financier cohérent.
"""

import streamlit as st
from typing import Optional


def money_metric(
    label: str,
    value: float,
    delta: Optional[float] = None,
    currency: str = "EUR",
    help: Optional[str] = None,
    decimals: int = 2,
):
    """
    Metric card pour un montant en devise.

    Args:
        label: titre de la card
        value: montant
        delta: variation (optionnelle)
        currency: code devise (EUR, USD)
        help: tooltip
        decimals: nombre de décimales
    """
    symbol = {"EUR": "€", "USD": "$"}.get(currency, currency + " ")
    formatted_value = f"{symbol}{value:,.{decimals}f}"

    delta_str = None
    if delta is not None:
        delta_str = f"{symbol}{delta:+,.{decimals}f}"

    st.metric(label=label, value=formatted_value, delta=delta_str, help=help)


def rate_metric(
    label: str,
    value: float,
    delta_bp: Optional[float] = None,
    help: Optional[str] = None,
    decimals: int = 4,
):
    """
    Metric card pour un taux en pourcentage.

    Args:
        label: titre
        value: taux en décimal
        delta_bp: variation en bp (optionnelle)
        help: tooltip
        decimals: nombre de décimales sur le %
    """
    formatted = f"{value * 100:.{decimals}f}%"
    delta_str = f"{delta_bp:+.1f} bp" if delta_bp is not None else None

    st.metric(label=label, value=formatted, delta=delta_str, help=help)


def bp_metric(
    label: str,
    value: float,
    help: Optional[str] = None,
    decimals: int = 2,
):
    """Metric card pour une valeur en €/bp (DV01, KR-DV01)."""
    formatted = f"€{value:,.{decimals}f}"
    st.metric(label=label, value=formatted, help=help)
