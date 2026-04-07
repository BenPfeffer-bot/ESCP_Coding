"""
Génère les 4 plots individuels + la grille combinée et les sauvegarde en PNG dans notebooks/exports/.

Usage:
    python -m src.tests.test_plots_curves
"""

from pathlib import Path
import matplotlib.pyplot as plt

from src.api.data_feed import DataFeed
from src.curves.bootstrapper import bootstrap_discount_factors
from src.curves.interpolation import YieldCurveInterpolator
from src.plots.curves import (
    plot_par_rates,
    plot_zero_rates,
    plot_discount_factors,
    plot_forward_rates,
    plot_curves_grid,
)


# Dossier d'export
EXPORT_DIR = Path("plots/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 60)
    print("  PLOTS CURVES — VISUAL TEST")
    print("=" * 60)

    # ── 1. Pipeline data ──────────────────────────────
    print("\n[1/3] Fetching data...")
    feed = DataFeed()
    mats, rates = feed.fetch_snapshot()
    print(f"   ok {len(mats)} points fetched")

    # ── 2. Bootstrap + interpolation ──────────────────
    print("\n[2/3] Bootstrap + interpolation...")
    dfs = bootstrap_discount_factors(mats, rates)
    interp = YieldCurveInterpolator(mats, dfs, method="cubic_spline")
    print(f"   ok - Bootstrap: ({len(dfs)} discount factors)")
    print("  ok - Interpolator built (cubic_spline)")

    # ── 3. Génération des plots ───────────────────────
    print("\n[3/3] Generating plots...")

    # Plot 1
    fig1 = plot_par_rates(mats, rates)
    out1 = EXPORT_DIR / "01_par_rates.png"
    fig1.savefig(out1)
    plt.close(fig1)
    print(f"   ok - {out1}")

    # Plot 2
    fig2 = plot_zero_rates(interp)
    out2 = EXPORT_DIR / "02_zero_rates.png"
    fig2.savefig(out2)
    plt.close(fig2)
    print(f"   ok - {out2}")

    # Plot 3
    fig3 = plot_discount_factors(interp)
    out3 = EXPORT_DIR / "03_discount_factors.png"
    fig3.savefig(out3)
    plt.close(fig3)
    print(f"   ok {out3}")

    # Plot 4
    fig4 = plot_forward_rates(interp)
    out4 = EXPORT_DIR / "04_forward_rates.png"
    fig4.savefig(out4)
    plt.close(fig4)
    print(f"   ok {out4}")

    # Grille combinée
    fig5 = plot_curves_grid(
        mats, rates, interp, suptitle="US Treasury Yield Curve — 2026-04-07"
    )
    out5 = EXPORT_DIR / "00_dashboard_grid.png"
    fig5.savefig(out5)
    plt.close(fig5)
    print(f"   ok {out5}")

    print("\n" + "=" * 60)
    print(f"  done - 5 plots generated in {EXPORT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
