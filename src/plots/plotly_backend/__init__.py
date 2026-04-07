"""
src/plots/plotly_backend — Versions Plotly des plots.
"""

from src.plots.plotly_backend.theme import (
    COLORS,
    PLOTLY_TEMPLATE,
    apply_template,
)
from src.plots.plotly_backend.curves import (
    plot_par_rates,
    plot_zero_rates,
    plot_discount_factors,
    plot_forward_rates,
    plot_curves_grid,
)
from src.plots.plotly_backend.risks import (
    plot_kr_dv01_ladder,
    plot_stress_test,
)
from src.plots.plotly_backend.history import (
    plot_historical_maturity,
    plot_curve_evolution,
)

__all__ = [
    "COLORS",
    "PLOTLY_TEMPLATE",
    "apply_template",
    # curves
    "plot_par_rates",
    "plot_zero_rates",
    "plot_discount_factors",
    "plot_forward_rates",
    "plot_curves_grid",
    # risk
    "plot_kr_dv01_ladder",
    "plot_stress_test",
    # history
    "plot_historical_maturity",
    "plot_curve_evolution",
]
