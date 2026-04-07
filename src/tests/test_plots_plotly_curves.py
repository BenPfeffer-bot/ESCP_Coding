"""
Génère des fichiers HTML interactifs dans plots/plotly/
que tu peux ouvrir dans un navigateur pour tester le zoom, hover, pan.

Usage:
    python -m src.tests.test_plots_plotly_curves
"""

from pathlib import Path

from src.api.data_feed import DataFeed
from src.curves.bootstrapper import bootstrap_discount_factors
from src.curves.interpolation import YieldCurveInterpolator
from src.plots.plotly_backend.curves import (
    plot_par_rates,
    plot_zero_rates,
    plot_discount_factors,
    plot_forward_rates,
    plot_curves_grid,
)


EXPORT_DIR = Path("plots/plotly/curves")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 60)
    print("  PLOTLY CURVES — VISUAL TEST")
    print("=" * 60)

    # ── Pipeline data ─────────────────────────────────
    print("\n[1/3] Fetching data...")
    feed = DataFeed()
    mats, rates = feed.fetch_snapshot()
    print(f"   ✓ {len(mats)} points fetched")

    # ── Bootstrap + interpolation ─────────────────────
    print("\n[2/3] Bootstrap + interpolation...")
    dfs = bootstrap_discount_factors(mats, rates)
    interp = YieldCurveInterpolator(mats, dfs, method="cubic_spline")
    print(f"   ✓ Interpolator built")

    # ── Génération des plots ──────────────────────────
    print("\n[3/3] Generating Plotly figures...")

    plots = [
        ("01_par_rates.html", plot_par_rates(mats, rates)),
        ("02_zero_rates.html", plot_zero_rates(interp)),
        ("03_discount_factors.html", plot_discount_factors(interp)),
        ("04_forward_rates.html", plot_forward_rates(interp)),
        (
            "00_dashboard_grid.html",
            plot_curves_grid(
                mats,
                rates,
                interp,
                suptitle="US Treasury Yield Curve — Interactive",
            ),
        ),
    ]

    for filename, fig in plots:
        out = EXPORT_DIR / filename
        fig.write_html(
            str(out),
            include_plotlyjs="cdn",  # léger : charge plotly depuis CDN
            config={
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            },
        )
        print(f"   ✓ {out}")

    print("\n" + "=" * 60)
    print(f"  ✅ 5 HTML files generated in {EXPORT_DIR}")
    print("  Open them in a browser to test interactivity")
    print("=" * 60)


if __name__ == "__main__":
    main()
