"""
Génère tous les plots en HTML pour validation visuelle

Usage:
    python -m src.tests.test_plots_plotly_all
"""

from pathlib import Path
import numpy as np

from src.api.data_feed import DataFeed
from src.curves.bootstrapper import bootstrap_discount_factors
from src.curves.interpolation import YieldCurveInterpolator
from src.instruments.vanilla_swaps import VanillaSwap
from src.risks.sensitivities import (
    compute_dv01,
    compute_convexity,
    compute_key_rate_dv01,
)
from src.utils.helper import reprice
from src.utils.cache import get_maturity_history, get_curve_history

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


EXPORT_DIR = Path("plots/plotly")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def save_fig(fig, filename):
    """Helper pour sauver une figure Plotly en HTML."""
    out = EXPORT_DIR / filename
    fig.write_html(
        str(out),
        include_plotlyjs="cdn",
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        },
    )
    print(f"   ✓ {out}")


def main():
    print("=" * 60)
    print("  PLOTLY BACKEND — FULL VISUAL TEST")
    print("=" * 60)

    # ── Pipeline data ─────────────────────────────────
    print("\n[1/5] Fetching data...")
    feed = DataFeed()
    mats, rates = feed.fetch_snapshot()
    dfs = bootstrap_discount_factors(mats, rates)
    interp = YieldCurveInterpolator(mats, dfs, method="cubic_spline")
    print(f"   ✓ {len(mats)} points, interpolator built")

    # ── CURVES plots ──────────────────────────────────
    print("\n[2/5] Curves plots...")
    save_fig(plot_par_rates(mats, rates), "01_par_rates.html")
    save_fig(plot_zero_rates(interp), "02_zero_rates.html")
    save_fig(plot_discount_factors(interp), "03_discount_factors.html")
    save_fig(plot_forward_rates(interp), "04_forward_rates.html")
    save_fig(
        plot_curves_grid(
            mats, rates, interp, suptitle="US Treasury — Interactive Dashboard"
        ),
        "00_dashboard_grid.html",
    )

    # ── Swap pour les plots risk ──────────────────────
    print("\n[3/5] Building test swap...")
    swap_5y = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
    par_5y = swap_5y.par_rate(interp)
    swap = VanillaSwap(
        notional=10_000_000, fixed_rate=par_5y, maturity=5.0, direction="receiver"
    )
    print(f"   ✓ 5Y receiver at-par ({par_5y * 100:.4f}%)")

    # ── RISK plots ────────────────────────────────────
    print("\n[4/5] Risk plots...")

    # KR-DV01
    kr_dv01 = compute_key_rate_dv01(swap, mats, rates)
    save_fig(plot_kr_dv01_ladder(kr_dv01), "05_kr_dv01_ladder.html")

    # Stress test
    shifts_bp = np.array([-100, -75, -50, -25, 0, 25, 50, 75, 100])
    pnl_values = np.array([reprice(swap, mats, rates + s / 10000) for s in shifts_bp])
    dv01 = compute_dv01(swap, mats, rates)
    convexity = compute_convexity(swap, mats, rates)

    save_fig(
        plot_stress_test(shifts_bp, pnl_values, dv01=dv01, convexity=convexity),
        "06_stress_test.html",
    )

    # ── HISTORY plots ─────────────────────────────────
    print("\n[5/5] History plots...")

    dates_10y, rates_10y = get_maturity_history(10.0)
    save_fig(
        plot_historical_maturity(dates_10y, rates_10y, "10Y"), "07_historical_10y.html"
    )

    history = get_curve_history(n_days=10)
    save_fig(plot_curve_evolution(history), "08_curve_evolution.html")

    print("\n" + "=" * 60)
    print(f"  ✅ 9 HTML files generated in {EXPORT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
