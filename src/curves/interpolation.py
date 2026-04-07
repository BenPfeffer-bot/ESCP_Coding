"""
interpolation.py — Module 2 : Interpolation de la courbe
=========================================================
Objectif : obtenir Z(0, T) pour n'importe quel T, pas seulement
les maturités cotées.

Méthodes à implémenter :
  1. Linéaire sur les zero rates
  2. Cubic spline sur les zero rates
  3. Log-linéaire sur les discount factors (bonus)

Hint : scipy.interpolate.CubicSpline et interp1d sont tes amis.
"""

import numpy as np
from settings import get_logger
from scipy.interpolate import interp1d, CubicSpline
from src.curves.bootstrapper import bootstrap_discount_factors
from src.api.data_feed import DataFeed

# Ajout du logger module-level pour debug global éventuel
logger = get_logger(name="interpolation")


class YieldCurveInterpolator:
    """
    Interpole une courbe de taux entre les nœuds bootstrappés.

    Usage:
        interp = YieldCurveInterpolator(maturities, discount_factors)
        z_3_5Y = interp.discount_factor(3.5)
        y_3_5Y = interp.zero_rate(3.5)
    """

    def __init__(
        self,
        maturities: np.ndarray,
        discount_factors: np.ndarray,
        method: str = "cubic_spline",  # "linear", "cubic_spline", "log_linear"
    ):
        """
        Paramètres
        ----------
        maturities : array — nœuds bootstrappés (en années)
        discount_factors : array — Z(0, T_i) correspondants
        method : str — méthode d'interpolation
        """
        self.maturities = maturities
        self.discount_factors = discount_factors
        self.method = method
        self.logger = get_logger(name="interpolation")

        # Pré-calculer les zero rates pour interpolation
        self.zero_rates = -np.log(discount_factors) / maturities

        self.logger.debug(
            f"Obj interpolator init | method={self.method} | "
            f"maturities={self.maturities} | "
            f"discount_factors={self.discount_factors} | "
            f"zero_rates={self.zero_rates}"
        )

        self._build_interpolator()

    def _build_interpolator(self):
        """Construit l'objet interpolateur interne."""

        # Check de tri — scipy plante avec un message obscur si c'est pas trié
        assert np.all(np.diff(self.maturities) > 0), (
            "maturities doivent être strictement croissantes"
        )

        # Méthode linéaire
        if self.method == "linear":
            self._interp = interp1d(
                self.maturities,
                self.zero_rates,
                kind="linear",
                fill_value="extrapolate",
            )
        # Méthode cubic (+ relevant)
        elif self.method == "cubic_spline":
            self._interp = CubicSpline(self.maturities, self.zero_rates)

        # Méthode log-lin // Interpoler sur ln(Z) = -y*T
        elif self.method == "log_linear":
            # On interpole log(Z(0,T)) de façon linéaire, puis on reconstruit Z
            # ln(Z) = -y*T donc: on stocke ln(Z) comme y cible à interpoler
            ln_z = np.log(self.discount_factors)
            self._ln_z_interp = interp1d(
                self.maturities, ln_z, kind="linear", fill_value="extrapolate"
            )

            def log_linear_zero_rate(T):
                # ln(Z(0,T)) interpolé
                ln_z_T = float(self._ln_z_interp(T))
                # y(T) = -ln(Z(0,T))/T
                if T == 0:
                    return 0.0
                return -ln_z_T / T

            self._interp = log_linear_zero_rate
        else:
            self.logger.error(f"Unknown method received: {self.method}")
            raise ValueError(f"Unknown method: {self.method}")

        self.logger.info(
            f"Interpolator built | method={self.method} | "
            f"{len(self.maturities)} nodes | "
            f"range=[{self.maturities[0]:.2f}Y, {self.maturities[-1]:.2f}Y]"
        )

    def zero_rate(self, T: float) -> float:
        # sans float() ça peut casser des comparaisons d'égalité strictes plus tard
        z = float(self._interp(T))
        self.logger.debug(f"zero_rate({T}) = {z}")
        return z

    def discount_factor(self, T: float) -> float:
        """
        Retourne le discount factor interpolé Z(0, T).
        On utilise la formule: Z(0, T) = exp(-y(T) * T)
        """
        y_T = self.zero_rate(T)
        df = np.exp(-y_T * T)
        self.logger.debug(f"discount_factor({T}) = {df} (y_T={y_T})")
        return df

    def forward_rate(self, T1: float, T2: float) -> float:
        """
        Retourne le taux forward entre T1 et T2

        Formule: f(T1, T2) = -ln(Z(0,T2) / Z(0,T1)) / (T2 - T1)
        """
        # Eviter que T1 = T2
        assert T2 > T1, (
            f"T2 doit être strictement supérieur à T1 (reçu: T1={T1}, T2={T2})"
        )
        Z1 = self.discount_factor(T1)
        Z2 = self.discount_factor(T2)
        fwd = -np.log(Z2 / Z1) / (T2 - T1)
        self.logger.debug(f"forward_rate({T1}, {T2}) = {fwd} (Z1={Z1}, Z2={Z2})")
        return fwd

    def zero_rate_curve(self, maturities: np.ndarray) -> np.ndarray:
        """
        Retourne la courbe de taux zéro pour un vecteur de maturités.
        Utile pour les plots.
        """
        res = np.array([self.zero_rate(T) for T in maturities])
        self.logger.debug(f"zero_rate_curve({maturities}) = {res}")
        return res


# =============================================================================
# TESTS — Décommente et lance pour valider ton implémentation
# =============================================================================

if __name__ == "__main__":
    logger = get_logger(name="interpolation_test")
    logger.info("===" * 15)
    # Fetch live data + bootstrap
    logger.info("Fetching live yield data and bootstrapping discount factors...")
    feed = DataFeed()
    mats, rates = feed.fetch_snapshot()

    if mats is None:
        logger.error("❌ Snapshot failed, abort")
        print("❌ Snapshot failed, abort")
        exit(1)

    logger.info(f"Fetched maturities: {mats}")
    logger.info(f"Fetched rates: {rates}")

    dfs = bootstrap_discount_factors(mats, rates)
    logger.info(f"Bootstrapped discount factors: {dfs}")

    # Build interpolator
    interp = YieldCurveInterpolator(mats, dfs, method="cubic_spline")
    logger.info("YieldCurveInterpolator successfully built.")

    # Test 1 : exactitude aux nœuds
    logger.info("=== Test 1 : Exactitude sur les nœuds connus ===")
    print("\n=== Test 1 : nœuds connus ===")
    for i, T in enumerate(mats):
        z_interp = interp.discount_factor(T)
        err = abs(z_interp - dfs[i])
        logger.debug(
            f"Node {i}: T={T:.2f} | Z_boot={dfs[i]:.8f} | Z_interp={z_interp:.8f} | err={err:.2e}"
        )
        assert err < 1e-10, f"Mismatch at {T}Y: err={err:.2e}"
        print(
            f"  {T:5.2f}Y : Z_boot={dfs[i]:.8f} | Z_interp={z_interp:.8f} | err={err:.2e}"
        )
    logger.info("✅ Tous les nœuds OK")
    print("✅ Tous les nœuds OK")

    # Test 2 : interpolation entre nœuds
    logger.info("=== Test 2 : Interpolation entre nœuds ===")
    print("\n=== Test 2 : interpolation entre nœuds ===")
    for T in [3.5, 4.0, 6.0, 8.0, 12.0, 25.0]:
        z = interp.discount_factor(T)
        y = interp.zero_rate(T)
        logger.debug(f"Inter-node T={T:5.2f}Y | y={y * 100:.4f}% | Z={z:.8f}")
        print(f"  T={T:5.2f}Y | y={y * 100:.4f}% | Z={z:.8f}")

    # Test 3 : forwards positifs
    logger.info("=== Test 3 : Vérification des forwards positifs ===")
    print("\n=== Test 3 : forwards positifs ===")
    test_pairs = [(1, 2), (2, 5), (5, 10), (10, 20), (20, 30)]
    for T1, T2 in test_pairs:
        f = interp.forward_rate(T1, T2)
        status = "✅" if f > 0 else "❌ NEGATIVE"
        logger.debug(f"Forward rate f({T1}, {T2}) = {f * 100:.4f}% | status={status}")
        print(f"  f({T1}Y, {T2}Y) = {f * 100:.4f}%  {status}")
