"""
Extraire les discount factors Z(0, T) à partir des taux swap par.

On va utiliser la théorie appliqué dans le livre de Wilmott & Jha:
    Z(0, T_1) = 1 / (1 + r_s(T_1) * tau_1)
    Z(0, T_{j+1}) = (1 - r_s * tau * sum Z_i) / (1 + r_s * tau_j)
"""
import numpy as np
from settings import get_logger
from typing import Tuple

logger = get_logger(name="bootstrapper")

def bootstrap_discount_factors(maturities: np.ndarray, par_swap_rates: np.ndarray) -> np.ndarray:
    """
    Bootstrap les discounts factors à partir des taux swap par.
    
    Params:
    - maturities : array — maturités en années, triées croissant
    - par_swap_rates : array — taux swap par (décimal, ex: 0.03 = 3%)

    Return:
    discount_factors : array — Z(0, T_i) pour chaque maturité
    """
    n = len(maturities)
    assert n == len(par_swap_rates), "Maturities and rates must have same length"
    
    logger.info(f"Démarrage bootstrap DF: maturities={maturities}, par_swap_rates={par_swap_rates}")
    discount_factors = np.zeros(n)

    for j in range(n):
        tau_j = maturities[0] if j == 0 else maturities[j] - maturities[j - 1]
        r_s = par_swap_rates[j]

        # Somme des coupons actualisés déjà connus
        pv_coupons_known = 0.0
        for i in range(j):
            tau_i = maturities[0] if i == 0 else maturities[i] - maturities[i - 1]
            pv_coupons_known += r_s * tau_i * discount_factors[i]
        logger.debug(
            f"j={j}, tau_j={tau_j}, r_s={r_s}, pv_coupons_known={pv_coupons_known}"
        )
        # Résolution du DF courant
        discount_factors[j] = (1.0 - pv_coupons_known) / (1.0 + r_s * tau_j)
        logger.info(f"DF[{j}] (T={maturities[j]}) = {discount_factors[j]}")

    # ajoute un sanity check
    if not np.all(np.diff(discount_factors) < 0):
        logger.error(
            f"Discount factors non monotones — courbe invalide\n"
            f"DFs: {discount_factors}\n"
            f"Vérifier les yields d'input."
        )
        raise ValueError(
            f"Discount factors non monotones — courbe invalide\n"
            f"DFs: {discount_factors}\n"
            f"Vérifier les yields d'input."
        )

    logger.info(f"DF finaux bootstrappés: {discount_factors}")
    return discount_factors


def discount_factors_to_zero_rates(
    maturities: np.ndarray,
    discount_factors: np.ndarray,
    compounding: str = "continuous"
) -> np.ndarray:
    """
    Convertit les discount factors en taux zéro-coupon.
    
    "continuous": y = -ln(Z) / T
    "annuel":  y = Z^(-1/T) - 1
    """
    logger.info(f"Conversion DF -> zero rates (compounding={compounding})")
    if compounding == "continuous":
        zero_rates = -np.log(discount_factors) / maturities
    elif compounding == "annual":
        zero_rates = discount_factors ** (-1.0 / maturities) - 1.0
    else:
        logger.error(f"Unknown compounding: {compounding}")
        raise ValueError(f"Unknown compounding: {compounding}")
    logger.info(f"Zero rates calculés: {zero_rates}")
    return zero_rates


def extract_forward_rates(
    maturities: np.ndarray,
    discount_factors: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Taux forward implicites entre maturités consécutives.
    f = -ln(Z(T_{i+1}) / Z(T_i)) / (T_{i+1} - T_i)
    """
    logger.info("Extraction des taux forward implicites")
    n = len(maturities)
    forward_rates = np.zeros(n)
    forward_mids = np.zeros(n)
    
    forward_rates[0] = -np.log(discount_factors[0]) / maturities[0]
    forward_mids[0] = maturities[0] / 2.0
    logger.debug(f"Forward[0] (T={maturities[0]/2.0:.4f}) = {forward_rates[0]}")

    for i in range(1, n):
        dt = maturities[i] - maturities[i - 1]
        forward_rates[i] = -np.log(discount_factors[i] / discount_factors[i - 1]) / dt
        forward_mids[i] = (maturities[i] + maturities[i - 1]) / 2.0
        logger.debug(f"Forward[{i}] (T={forward_mids[i]:.4f}) = {forward_rates[i]}")
    
    logger.info(f"Taux forwards calculés: {forward_rates}")
    return forward_mids, forward_rates


def validate_bootstrapping(
    maturities: np.ndarray,
    par_swap_rates: np.ndarray,
    discount_factors: np.ndarray,
    tolerance: float = 1e-10
) -> bool:
    """Vérifie que chaque swap re-price à par (PV = 1)"""
    logger.info("Validation du bootstrapping...")
    n = len(maturities)
    for j in range(n):
        pv_fixed = 0.0
        for i in range(j + 1):
            tau_i = maturities[0] if i == 0 else maturities[i] - maturities[i - 1]
            pv_fixed += par_swap_rates[j] * tau_i * discount_factors[i]
        pv_fixed += discount_factors[j]
        logger.debug(f"Swap {j} | PV_fixed={pv_fixed} (tol={tolerance})")
        if abs(pv_fixed - 1.0) >= tolerance:
            logger.warning(f"Échec: swap {j}, PV={pv_fixed}, cible=1.0")
            return False
    logger.info("Validation du bootstrapping: SUCCÈS")
    return True

# ===========================================================================
# TEST
# ===========================================================================

# if __name__ == "__main__":
#     from src.api.data_feed import DataFeed
#     datafeed = DataFeed()
#     maturites, rates = datafeed.fetch_snapshot()
#     logger.info(f"Snapshot obtenu: maturities={maturites}, rates={rates}")
#     discount_factors = bootstrap_discount_factors(maturites, rates)
#     logger.info(f"Discount factors bootstrappés : {discount_factors}")
#     print("Discount factors bootstrappés :", discount_factors)
