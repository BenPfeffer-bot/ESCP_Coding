"""
Génère :
  - KR-DV01 ladder
  - Stress test (P&L vs shift)
  - Historical maturity plot (si données dispo)
  - Curve evolution plot (si données dispo)

Usage:
    python -m src.tests.test_plots_risk
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

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
from src.utils.cache import get_maturity_history, get_curve_history, get_db_stats
from src.plots.risks import plot_kr_dv01_ladder, plot_stress_test
from src.plots.history import plot_historical_maturity, plot_curve_evolution


EXPORT_DIR = Path("plots/risks")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 60)
    print("  PLOTS RISK & HISTORY — VISUAL TEST")
    print("=" * 60)

    # ── Pipeline data ─────────────────────────────────
    print("\n[1/4] Pipeline data...")
    feed = DataFeed()
    mats, rates = feed.fetch_snapshot()
    dfs = bootstrap_discount_factors(mats, rates)
    interp = YieldCurveInterpolator(mats, dfs, method="cubic_spline")
    print(f"   ✓ Curve loaded ({len(mats)} points)")

    # ── Swap test : 5Y receiver at-par ────────────────
    print("\n[2/4] Building test swap...")
    swap_5y = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
    par_5y = swap_5y.par_rate(interp)
    swap = VanillaSwap(
        notional=10_000_000, fixed_rate=par_5y, maturity=5.0, direction="receiver"
    )
    print(f"   ✓ 5Y receiver at-par ({par_5y * 100:.4f}%)")

    # ── KR-DV01 ladder ────────────────────────────────
    print("\n[3/4] Generating risk plots...")
    kr_dv01 = compute_key_rate_dv01(swap, mats, rates)

    fig1 = plot_kr_dv01_ladder(kr_dv01)
    out1 = EXPORT_DIR / "05_kr_dv01_ladder.png"
    fig1.savefig(out1)
    plt.close(fig1)
    print(f"   ✓ {out1}")

    # Version log scale (utile vu la concentration sur le 5Y)
    fig1b = plot_kr_dv01_ladder(
        kr_dv01,
        title="KR-DV01 Ladder (log scale)",
        log_scale=True,
    )
    out1b = EXPORT_DIR / "05b_kr_dv01_ladder_log.png"
    fig1b.savefig(out1b)
    plt.close(fig1b)
    print(f"   ✓ {out1b}")

    # ── Stress test ───────────────────────────────────
    print("\n   Computing stress test...")
    shifts_bp = np.array([-100, -75, -50, -25, 0, 25, 50, 75, 100])
    pnl_values = []
    for shift in shifts_bp:
        bumped_rates = rates + shift / 10000
        npv_shifted = reprice(swap, mats, bumped_rates)
        pnl_values.append(npv_shifted)
    pnl_values = np.array(pnl_values)

    dv01 = compute_dv01(swap, mats, rates)
    convexity = compute_convexity(swap, mats, rates)

    fig2 = plot_stress_test(
        shifts_bp,
        pnl_values,
        dv01=dv01,
        convexity=convexity,
    )
    out2 = EXPORT_DIR / "06_stress_test.png"
    fig2.savefig(out2)
    plt.close(fig2)
    print(f"   ✓ {out2}")

    # ── Historical plots ──────────────────────────────
    print("\n[4/4] Generating historical plots...")
    stats = get_db_stats()
    print(
        f"   DB stats: {stats['nb_snapshots']} snapshots, "
        f"{stats['nb_dates']} dates, range: {stats['date_range']}"
    )

    # Historical 10Y
    dates_10y, rates_10y = get_maturity_history(10.0)
    fig3 = plot_historical_maturity(
        dates_10y,
        rates_10y,
        maturity_label="10Y",
    )
    out3 = EXPORT_DIR / "07_historical_10y.png"
    fig3.savefig(out3)
    plt.close(fig3)
    print(f"   ✓ {out3} ({len(dates_10y)} points)")

    # Curve evolution
    history = get_curve_history(n_days=10)
    fig4 = plot_curve_evolution(history)
    out4 = EXPORT_DIR / "08_curve_evolution.png"
    fig4.savefig(out4)
    plt.close(fig4)
    print(f"   ✓ {out4} ({len(history)} curves)")

    print("\n" + "=" * 60)
    print(f"  ✅ All plots generated in {EXPORT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
