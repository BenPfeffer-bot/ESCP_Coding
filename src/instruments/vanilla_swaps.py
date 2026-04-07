"""
Objectif : Pricer un IRS vanille off-market.

Théorie (Jha) :
    - Jambe fixe = somme des coupons fixes actualisés + principal fictif
    - Jambe flottante = par (= 1.0) à une date de coupon
    - PV_fixe = sum_{i=1}^{N} c * tau_i * Z(0, T_i) + Z(0, T_N)
    - NPV (receiver) = PV_fixe - PV_float
    - NPV (payer) = PV_float - PV_fixe

Convention :
    - "Recevoir" = recevoir le fixe, payer le float (long duration)
    - "Payer" = payer le fixe, recevoir le float (short duration)
"""

import numpy as np
from settings import get_logger
from src.curves.interpolation import YieldCurveInterpolator
from src.curves.bootstrapper import bootstrap_discount_factors
from src.api.data_feed import DataFeed


class VanillaSwap:
    """
    Représente un IRS vanille.

    Usage:
        swap = VanillaSwap(
            notional=10_000_000,
            fixed_rate=0.03,
            maturity=5.0,
            payment_frequency=1.0,  # annuel
            direction="receiver"
        )
        npv = swap.price(discount_factors, maturities)
        par_rate = swap.par_rate(discount_factors, maturities)
    """

    def __init__(
        self,
        notional: float,
        fixed_rate: float,
        maturity: float,
        payment_frequency: float = 1.0,
        direction: str = "receiver",  # "receiver" ou "payer"
    ):
        self.notional = notional
        self.fixed_rate = fixed_rate
        self.maturity = maturity
        self.payment_frequency = payment_frequency
        self.direction = direction
        self.logger = get_logger(name="swap-pricer")
        self.logger.info(
            f"Initialisation VanillaSwap: notional={notional}, fixed_rate={fixed_rate}, "
            f"maturity={maturity}, payment_frequency={payment_frequency}, direction={direction}"
        )
        self.payment_dates = self._generate_schedule()
        self.logger.debug(f"Dates de paiement générées: {self.payment_dates}")

    def _generate_schedule(self) -> np.ndarray:
        """
        Génère les dates de paiement
        """
        n_payments = int(round(self.maturity / self.payment_frequency))
        payment_schedule = np.array(
            [self.payment_frequency * (i + 1) for i in range(n_payments)]
        )
        self.logger.debug(
            f"Générés n_payments={n_payments}, échéances={payment_schedule}"
        )
        return payment_schedule

    def _annuity(self, interpolator):
        """Sum of tau_i * Z(0, T_i) — utilisé dans fixed leg et par rate."""
        taus = np.diff(np.insert(self.payment_dates, 0, 0.0))
        dfs = np.array([interpolator.discount_factor(T) for T in self.payment_dates])
        annuity_sum = np.sum(taus * dfs)
        self.logger.debug(
            f"Calcul annuity: taus={taus}, dfs={dfs}, annuity_sum={annuity_sum}, Z_N={dfs[-1]}"
        )
        return annuity_sum, dfs[-1]  # annuity, Z_N

    def pv_fixed_leg(self, interpolator: YieldCurveInterpolator) -> float:
        """PV de la jambe fixe."""
        schedule = self.payment_dates
        taus = np.diff(np.insert(schedule, 0, 0.0))

        pv = 0.0
        for tau_i, T_i in zip(taus, schedule):
            Z_i = interpolator.discount_factor(T_i)
            pv += self.fixed_rate * tau_i * Z_i

        # Principal fictif à T_N
        Z_N = interpolator.discount_factor(schedule[-1])
        pv += Z_N

        return pv

    def pv_floating_leg(self, interpolator: YieldCurveInterpolator) -> float:
        """À une date de coupon, la jambe flottante vaut par."""
        return 1.0

    def npv(self, interpolator):
        pv_f = self.pv_fixed_leg(interpolator)
        pv_fl = self.pv_floating_leg(interpolator)
        sign = 1.0 if self.direction == "receiver" else -1.0
        npv_res = sign * (pv_f - pv_fl) * self.notional
        self.logger.info(
            f"NPV calculé : direction={self.direction}, PV Fixed={pv_f}, PV Floating={pv_fl}, notional={self.notional}, NPV={npv_res}"
        )
        return npv_res

    def par_rate(self, interpolator: YieldCurveInterpolator) -> float:
        """
        Calcule le taux swap par (le taux fixe qui rend NPV = 0)
        Formule : r_par = (1 - Z(0, T_N)) / (tau * sum Z(0, T_i))
        """
        annuity, Z_N = self._annuity(interpolator)
        par_rate_val = (1.0 - Z_N) / annuity
        self.logger.info(
            f"Par Rate calculé: annuity={annuity}, Z_N={Z_N}, par_rate={par_rate_val}"
        )
        return par_rate_val

    def __repr__(self):
        return (
            f"VanillaSwap({self.direction}, "
            f"notional={self.notional:,.0f}, "
            f"fixed={self.fixed_rate * 100:.2f}%, "
            f"maturity={self.maturity}Y)"
        )


# =============================================================================
# TESTS
# =============================================================================

# if __name__ == "__main__":
#     # Pipeline complet
#     feed = DataFeed()
#     mats, rates = feed.fetch_snapshot()
#     dfs = bootstrap_discount_factors(mats, rates)
#     interp = YieldCurveInterpolator(mats, dfs, method="cubic_spline")

#     # Test 1 : Par rate cohérent avec inputs bootstrappés
#     print("\n=== Test 1 : Par rate ↔ inputs bootstrap ===")
#     for i, T in enumerate(mats):
#         if T < 1.0:  # skip 3M car il a 0 coupons
#             continue
#         swap = VanillaSwap(
#             notional=10_000_000, fixed_rate=0.0, maturity=T, direction="receiver"
#         )
#         par = swap.par_rate(interp)
#         print(
#             f"  {T:5.1f}Y : par_calculated={par * 100:.4f}% | input={rates[i] * 100:.4f}%"
#         )

#     # Test 2 : Swap at-par → NPV ≈ 0
#     print("\n=== Test 2 : Swap at-par ===")
#     swap_5y = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
#     par_5y = swap_5y.par_rate(interp)
#     swap_at_par = VanillaSwap(notional=10_000_000, fixed_rate=par_5y, maturity=5.0)
#     npv = swap_at_par.npv(interp)
#     print(f"  Par rate 5Y: {par_5y * 100:.4f}%")
#     print(f"  NPV at par : {npv:.6f} (should be ~0)")

#     # Test 3 : Receiver off-market avec rate > par → NPV positive
#     print("\n=== Test 3 : Off-market direction ===")
#     swap_above = VanillaSwap(
#         notional=10_000_000,
#         fixed_rate=par_5y + 0.005,
#         maturity=5.0,
#         direction="receiver",
#     )
#     swap_below = VanillaSwap(
#         notional=10_000_000,
#         fixed_rate=par_5y - 0.005,
#         maturity=5.0,
#         direction="receiver",
#     )
#     print(
#         f"  Receiver, fixed > par: NPV = {swap_above.npv(interp):,.2f} (should be > 0)"
#     )
#     print(
#         f"  Receiver, fixed < par: NPV = {swap_below.npv(interp):,.2f} (should be < 0)"
#     )

#     # Test 4 : Symétrie receiver/payer
#     print("\n=== Test 4 : Symétrie ===")
#     rec = VanillaSwap(10e6, 0.04, 5.0, direction="receiver")
#     pay = VanillaSwap(10e6, 0.04, 5.0, direction="payer")
#     npv_r = rec.npv(interp)
#     npv_p = pay.npv(interp)
#     print(f"  NPV receiver: {npv_r:,.2f}")
#     print(f"  NPV payer   : {npv_p:,.2f}")
#     print(f"  Sum (should be ~0): {npv_r + npv_p:.2e}")
