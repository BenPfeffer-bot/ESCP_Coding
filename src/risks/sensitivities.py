"""
Objectif : Calculer DV01, duration, et convexité par bump & reprice.

Méthode (Jha Ch.5, Ch.8) :
    1. Bumper toute la courbe de ±1bp
    2. Re-bootstrapper les discount factors
    3. Re-pricer le swap
    4. DV01 = (V_down - V_up) / 2
    5. Convexité = (V_up + V_down - 2*V_mid) / (bump²)

On peut aussi calculer un DV01 "ladder" : bumper chaque point de la courbe individuellement pour voir la sensibilité par maturité (key rate DV01)
"""

import numpy as np
from typing import Dict, Tuple
from settings import get_logger

from src.curves.interpolation import YieldCurveInterpolator
from src.curves.bootstrapper import bootstrap_discount_factors
from src.api.data_feed import DataFeed
from src.instruments.vanilla_swaps import VanillaSwap
from src.utils.helper import reprice

logger = get_logger(name="sensitivities")


def compute_dv01(swap, maturities, par_swap_rates, bump_size=0.0001):
    logger.info("Calcul DV01 : bumper toute la courbe de ±%.4f", bump_size)
    npv_up = reprice(swap, maturities, par_swap_rates + bump_size)
    npv_down = reprice(swap, maturities, par_swap_rates - bump_size)
    dv01 = (npv_down - npv_up) / 2.0
    logger.debug(f"NPV up: {npv_up:.6f}, NPV down: {npv_down:.6f}, DV01: {dv01:.6f}")
    return dv01


def compute_convexity(swap, maturities, par_swap_rates, bump_size=0.0001):
    logger.info("Calcul convexité : bumper toute la courbe de ±%.4f", bump_size)
    npv_up = reprice(swap, maturities, par_swap_rates + bump_size)
    npv_down = reprice(swap, maturities, par_swap_rates - bump_size)
    npv_mid = reprice(swap, maturities, par_swap_rates)
    convexity = npv_up + npv_down - 2 * npv_mid
    logger.debug(
        f"NPV up: {npv_up:.6f}, NPV down: {npv_down:.6f}, NPV mid: {npv_mid:.6f}, Convexity: {convexity:.6f}"
    )
    return convexity


# def compute_modified_duration(
#     swap, maturities: np.ndarray, par_swap_rates: np.ndarray, bump_size: float = 0.0001
# ) -> float:
#     """
#     Duration modifiée = DV01 / NPV_mid * 10000

#     (En années — combien de % le prix bouge pour 1% de mouvement de taux.)
#     """
#     # DV01 (valeur monétaire pour 1bp)
#     rates_up = par_swap_rates + bump_size
#     dfs_up = bootstrap_discount_factors(maturities, rates_up)
#     interp_up = YieldCurveInterpolator(maturities, dfs_up, method="cubic_spline")
#     npv_up = swap.npv(interp_up)

#     rates_down = par_swap_rates - bump_size
#     dfs_down = bootstrap_discount_factors(maturities, rates_down)
#     interp_down = YieldCurveInterpolator(maturities, dfs_down, method="cubic_spline")
#     npv_down = swap.npv(interp_down)

#     dv01 = (npv_down - npv_up) / 2.0

#     # NPV mid (état courant)
#     dfs_mid = bootstrap_discount_factors(maturities, par_swap_rates)
#     interp_mid = YieldCurveInterpolator(maturities, dfs_mid, method="cubic_spline")
#     npv_mid = swap.npv(interp_mid)

#     if npv_mid == 0:
#         return 0.0  # pour éviter division par zéro
#     mod_duration = dv01 / npv_mid * 10000  # (en années)
#     return mod_duration


def compute_key_rate_dv01(swap, maturities, par_swap_rates, bump_size=0.0001):
    logger.info("Calcul Key Rate DV01 (ladder) avec bump %.4f", bump_size)
    kr_dv01 = {}
    for i in range(len(par_swap_rates)):
        rates_up = par_swap_rates.copy()
        rates_up[i] += bump_size
        npv_up = reprice(swap, maturities, rates_up)

        rates_down = par_swap_rates.copy()
        rates_down[i] -= bump_size
        npv_down = reprice(swap, maturities, rates_down)

        kr_dv01[maturities[i]] = (npv_down - npv_up) / 2.0
        logger.debug(
            f"KR-DV01[{maturities[i]:.2f}Y]: bump up npv={npv_up:.6f}, bump down npv={npv_down:.6f}, kr_dv01={kr_dv01[maturities[i]]:.6f}"
        )
    return kr_dv01


def print_risk_report(swap, maturities, par_swap_rates):
    """Rapport complet des sensibilités d'un swap."""
    logger.info("Génération du Risk Report pour le swap: %s", repr(swap))
    # NPV mid
    dfs_mid = bootstrap_discount_factors(maturities, par_swap_rates)
    interp_mid = YieldCurveInterpolator(maturities, dfs_mid, method="cubic_spline")
    npv = swap.npv(interp_mid)

    # Sensitivities
    dv01 = compute_dv01(swap, maturities, par_swap_rates)
    convexity = compute_convexity(swap, maturities, par_swap_rates)
    kr_dv01 = compute_key_rate_dv01(swap, maturities, par_swap_rates)

    # Output
    logger.info(f"NPV       : {npv:,.2f} EUR")
    logger.info(f"DV01      : {dv01:,.2f} EUR/bp")
    logger.info(f"Convexity : {convexity:,.4f} EUR/bp²")
    logger.info("Key Rate DV01 Ladder:")
    total_kr = 0.0
    for mat in sorted(kr_dv01.keys()):
        v = kr_dv01[mat]
        logger.info(f"  {mat:5.2f}Y : {v:>12,.2f}")
        total_kr += v
    logger.info(f"  Sum    : {total_kr:>12,.2f}")
    logger.info(f"  Parallel DV01 (check): {dv01:,.2f}")
    logger.info(f"  Diff   : {abs(total_kr - dv01):.2e}")

    print("\n" + "═" * 50)
    print(f"{'RISK REPORT':^50}")
    print("═" * 50)
    print(f"Swap: {swap}")
    print(f"NPV       : {npv:>15,.2f} EUR")
    print(f"DV01      : {dv01:>15,.2f} EUR/bp")
    print(f"Convexity : {convexity:>15,.4f} EUR/bp²")
    print()
    print("Key Rate DV01 Ladder:")
    print("─" * 30)
    total_kr = 0.0
    for mat in sorted(kr_dv01.keys()):
        v = kr_dv01[mat]
        print(f"  {mat:5.2f}Y : {v:>12,.2f}")
        total_kr += v
    print("─" * 30)
    print(f"  Sum    : {total_kr:>12,.2f}")
    print(f"  Parallel DV01 (check): {dv01:,.2f}")
    print(f"  Diff   : {abs(total_kr - dv01):.2e}")
    print("═" * 50)


if __name__ == "__main__":
    # Pipeline
    logger.info("=====" * 10)
    logger.info("Début du pipeline de test des sensibilités (main).")
    logger.info("=====" * 10)
    feed = DataFeed()
    mats, rates = feed.fetch_snapshot()

    # Swap test : 5Y receiver at-par
    dfs = bootstrap_discount_factors(mats, rates)
    interp = YieldCurveInterpolator(mats, dfs, method="cubic_spline")

    swap_5y = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
    par_5y = swap_5y.par_rate(interp)
    swap = VanillaSwap(
        notional=10_000_000, fixed_rate=par_5y, maturity=5.0, direction="receiver"
    )

    # Test 1 : DV01 order of magnitude
    print("\n=== Test 1 : DV01 order of magnitude ===")
    logger.info("Test 1 : Calcul du DV01 (order of magnitude)")
    dv01 = compute_dv01(swap, mats, rates)
    print(f"DV01 5Y receiver 10M€: {dv01:,.2f} EUR/bp")
    print(f"Expected ~4500 EUR/bp (duration ~4.5 × 1bp × 10M)")
    logger.info(f"DV01 5Y receiver 10M€: {dv01:,.2f} EUR/bp")
    assert 3000 < dv01 < 6000, f"DV01 hors range attendue: {dv01}"
    print("✅ DV01 dans la range attendue")
    logger.info("✅ DV01 dans la range attendue")

    # Test 2 : Signe DV01
    print("\n=== Test 2 : Signe DV01 ===")
    logger.info("Test 2 : Vérification des signes DV01 pour receiver/payer")
    swap_payer = VanillaSwap(10_000_000, par_5y, 5.0, direction="payer")
    dv01_payer = compute_dv01(swap_payer, mats, rates)
    print(f"DV01 receiver: {dv01:>12,.2f} (should be > 0)")
    print(f"DV01 payer   : {dv01_payer:>12,.2f} (should be < 0)")
    logger.info(f"DV01 receiver : {dv01:,.2f} (should be > 0)")
    logger.info(f"DV01 payer   : {dv01_payer:,.2f} (should be < 0)")
    assert dv01 > 0 and dv01_payer < 0
    print("✅ Signes corrects")
    logger.info("✅ Signes DV01 corrects")

    # Test 3 : Convexité positive
    print("\n=== Test 3 : Convexité positive ===")
    logger.info("Test 3 : Vérification de la convexité positive")
    convexity = compute_convexity(swap, mats, rates)
    print(f"Convexity: {convexity:.6f} EUR")
    logger.info(f"Convexity: {convexity:.6f} EUR")
    assert convexity > 0, "Convexité doit être positive pour un receiver"
    print("✅ Convexité positive")
    logger.info("✅ Convexité positive")

    # Test 4 : Cohérence somme KR-DV01 vs parallèle
    print("\n=== Test 4 : Cohérence somme KR-DV01 ===")
    logger.info("Test 4 : Vérification cohérence Key Rate DV01 vs DV01 parallèle")
    kr_dv01 = compute_key_rate_dv01(swap, mats, rates)
    sum_kr = sum(kr_dv01.values())
    diff_pct = abs(sum_kr - dv01) / abs(dv01) * 100
    print(f"Sum KR-DV01    : {sum_kr:>12,.2f}")
    print(f"Parallel DV01  : {dv01:>12,.2f}")
    print(f"Diff           : {abs(sum_kr - dv01):>12,.2f} ({diff_pct:.4f}%)")
    logger.info(
        f"Sum KR-DV01 : {sum_kr:,.2f}, Parallel DV01 : {dv01:,.2f}, Diff = {abs(sum_kr - dv01):.2e} ({diff_pct:.4f}%)"
    )
    assert diff_pct < 1.0, f"Écart somme/parallel > 1%: {diff_pct}%"
    print("✅ Cohérence somme KR-DV01")
    logger.info("✅ Cohérence somme KR-DV01")

    # Test 5 : Risk report
    print_risk_report(swap, mats, rates)
    print_risk_report(swap, mats, rates)
    print_risk_report(swap, mats, rates)
