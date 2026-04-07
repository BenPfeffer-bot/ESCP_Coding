"""
vanilla_swap.py — Module 3 : Interest Rate Swap Pricer
=======================================================
Objectif : Pricer un IRS vanille off-market.

Théorie (Jha Ch.5) :
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
from curves import YieldCurveInterpolator


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
        direction: str = "receiver"   # "receiver" ou "payer"
    ):
        self.notional = notional
        self.fixed_rate = fixed_rate
        self.maturity = maturity
        self.payment_frequency = payment_frequency
        self.direction = direction
        self.logger = get_logger(name="swap-pricer")
        # TODO: Générer le schedule de paiement
        # Hint: np.arange(payment_frequency, maturity + payment_frequency/2, payment_frequency)
        # Attention aux cas limites (ex: maturity pas multiple de frequency)
        self.payment_dates = None  # TODO
    
    def _generate_schedule(self) -> np.ndarray:
        """
        Génère les dates de paiement.
        
        Ex: maturity=5, frequency=1.0 → [1.0, 2.0, 3.0, 4.0, 5.0]
        Ex: maturity=5, frequency=0.5 → [0.5, 1.0, 1.5, ..., 5.0]
        
        TODO: Implémenter
        """


        raise NotImplementedError("TODO: Implémenter _generate_schedule")
    
    def pv_fixed_leg(self, interpolator: YieldCurveInterpolator) -> float:
        """
        Calcule la PV de la jambe fixe.
        
        PV_fixe = sum_{i=1}^{N} (c * tau_i * Z(0, T_i)) + Z(0, T_N)
        
        Où :
          c = self.fixed_rate
          tau_i = durée de la période i (= payment_frequency en simplifié)
          Z(0, T_i) = discount factor interpolé à la date T_i
        """
        schedule = self.payment_dates
        taus = np.diff(np.insert(schedule, 0, 0.0))
        pv = 0
        for tau_i, T_i in zip(taus, schedule):
            Z_i = interpolator.discount_factor(T_i)
            pv += self.fixed_rate * tau_i * Z_i
    
    
    def pv_floating_leg(
        self,
        discount_factors: np.ndarray,
        maturities: np.ndarrays
    ) -> float:
        """
        Simplification : à une date de coupon, PV_float = 1.0 (par).
        """
        return 1.0

    def npv(
        self,
        discount_factors: np.ndarray,
        maturities: np.ndarray
    ) -> float:
        """
        Net Present Value du swap.
        
        Receiver : NPV = (PV_fixe - PV_float) * notional
        Payer    : NPV = (PV_float - PV_fixe) * notional
        """
        try: 
            pv_fixed = self.pv_fixed_leg(discount_factors, maturities)
            pv_float = self.pv_floating_leg(discount_factors, maturities)
        except:
            self.logger.error("Erreur dans le calcul du NPV du swap :\n")
            raise

        if self.direction == "receiver":
            self.logger.info((pv_fixed - pv_float) * self.notional)
            return (pv_fixed - pv_float) * self.notional

        elif self.direction == "payer":
            self.logger.info((pv_float - pv_fixed) * self.notional)
            return (pv_float - pv_fixed) * self.notional
        else:
            raise ValueError(f"Direction inconnue : {self.direction}")
    def par_rate(
        self,
        discount_factors: np.ndarray,
        maturities: np.ndarray
    ) -> float:
        """
        Calcule le taux swap par (le taux fixe qui rend NPV = 0).
        
        Formule : r_par = (1 - Z(0, T_N)) / (tau * sum Z(0, T_i))
        
        C'est exactement la formule inverse du bootstrapping !
        
        Utilise les payment_dates (self.payment_dates, supposée) et les DFs interpolés.
        """
        # Si self.payment_dates n'existe pas, fallback sur maturities
        try:
            payment_dates = self.payment_dates
        except AttributeError:
            payment_dates = maturities

        # On suppose des coupons d'amortissement constant
        # Calcul des taus (écarts entre les payment dates)
        taus = np.diff(np.insert(payment_dates, 0, 0.0))

        # Interpoler les DFs aux payment dates, 
        # si nécessaire (sinon prendre tel quel)
        if len(payment_dates) == len(discount_factors) and np.allclose(payment_dates, maturities):
            dfs = discount_factors
        else:
            # Interpolation sur les payment_dates
            interpolator = YieldCurveInterpolator(maturities, discount_factors)
            dfs = np.array([interpolator.discount_factor(T) for T in payment_dates])

        # Numerateur : 1 - DF(final)
        numer = 1.0 - dfs[-1]
        # Dénominateur : sum_i (tau_i * DF(T_i)) — sum sur tous LES paiements
        denom = np.sum(taus * dfs)
        
        # Sécurités
        if denom == 0:
            self.logger.error("Dénominateur nul dans le calcul du par rate")
            raise ZeroDivisionError("Dénominateur nul dans le calcul du par rate")

        r_par = numer / denom
        self.logger.info(f"Par rate calculé: {r_par} | numerator={numer} | denominator={denom}")

        return r_par
    
    def __repr__(self):
        return (
            f"VanillaSwap({self.direction}, "
            f"notional={self.notional:,.0f}, "
            f"fixed={self.fixed_rate*100:.2f}%, "
            f"maturity={self.maturity}Y)"
        )


# =============================================================================
# TESTS
# =============================================================================

# if __name__ == "__main__":
#     import sys; sys.path.insert(0, "..")
#     from data.live_market_data import get_eur_swap_data
#     from curves.bootstrapper import bootstrap_discount_factors
#     
#     data = get_eur_swap_data()
#     dfs = bootstrap_discount_factors(data["maturities"], data["par_swap_rates"])
#     
#     # Test 1 : Un swap AT PAR doit avoir NPV = 0
#     # Le taux par à 5Y est data["par_swap_rates"][3] (index du 5Y)
#     swap_at_par = VanillaSwap(
#         notional=10_000_000,
#         fixed_rate=data["par_swap_rates"][3],  # 5Y par rate
#         maturity=5.0,
#         direction="receiver"
#     )
#     npv = swap_at_par.npv(dfs, data["maturities"])
#     print(f"Swap at par NPV: {npv:.2f} (should be ~0)")
#     
#     # Test 2 : Un swap OFF-MARKET a une NPV non nulle
#     swap_off = VanillaSwap(
#         notional=10_000_000,
#         fixed_rate=0.035,  # au-dessus du par
#         maturity=5.0,
#         direction="receiver"
#     )
#     npv_off = swap_off.npv(dfs, data["maturities"])
#     print(f"Swap off-market NPV: {npv_off:,.2f} (should be > 0 for receiver)")
#     
#     # Test 3 : Par rate doit matcher le taux swap d'input
#     par = swap_at_par.par_rate(dfs, data["maturities"])
#     print(f"Par rate calculé: {par*100:.4f}% vs input: {data['par_swap_rates'][3]*100:.4f}%")