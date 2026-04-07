"""
Sous-modules:
    theme    : palette de couleurs et styles communs
    curves   : plots des courbes (par rates, zero rates, DFs, forwards)
    risk     : plots des sensibilités (KR-DV01 ladder)
    history  : plots historiques (séries temporelles)
"""

from src.plots.theme import COLORS, apply_style
from src.plots.curves import (
    plot_par_rates,
    plot_zero_rates,
    plot_discount_factors,
    plot_forward_rates,
    plot_curves_grid,
)

__all__ = [
    "COLORS",
    "apply_style",
    "plot_par_rates",
    "plot_zero_rates",
    "plot_discount_factors",
    "plot_forward_rates",
    "plot_curves_grid",
]
