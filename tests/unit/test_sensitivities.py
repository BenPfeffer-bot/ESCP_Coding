import numpy as np
import pytest

from src.instruments.vanilla_swaps import VanillaSwap
from src.risks.sensitivities import (
    compute_dv01,
    compute_convexity,
    compute_key_rate_dv01,
)


# ═══════════════════════════════════════════════════════════
#  HELPER : crée un swap at-par 5Y
# ═══════════════════════════════════════════════════════════


@pytest.fixture
def at_par_5y_swap(upward_curve, upward_interpolator):
    """Construit un swap 5Y receiver at-par sur la courbe upward."""
    temp = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
    par = temp.par_rate(upward_interpolator)
    return VanillaSwap(
        notional=10_000_000,
        fixed_rate=par,
        maturity=5.0,
        direction="receiver",
    )


# ═══════════════════════════════════════════════════════════
#  DV01
# ═══════════════════════════════════════════════════════════


class TestDV01:
    """Tests du calcul de DV01."""

    def test_dv01_positive_for_receiver(self, at_par_5y_swap, upward_curve):
        """Un receiver vanille doit avoir un DV01 positif."""
        mats, rates = upward_curve
        dv01 = compute_dv01(at_par_5y_swap, mats, rates)
        assert dv01 > 0, "Receiver DV01 should be positive (long duration)"

    def test_dv01_negative_for_payer(self, upward_curve, upward_interpolator):
        """Un payer vanille doit avoir un DV01 négatif."""
        mats, rates = upward_curve
        temp = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
        par = temp.par_rate(upward_interpolator)

        swap = VanillaSwap(
            notional=10_000_000,
            fixed_rate=par,
            maturity=5.0,
            direction="payer",
        )
        dv01 = compute_dv01(swap, mats, rates)
        assert dv01 < 0

    def test_dv01_symmetric_directions(self, upward_curve, upward_interpolator):
        """DV01 receiver = -DV01 payer (symétrie parfaite)."""
        mats, rates = upward_curve
        temp = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
        par = temp.par_rate(upward_interpolator)

        swap_r = VanillaSwap(
            notional=10_000_000, fixed_rate=par, maturity=5.0, direction="receiver"
        )
        swap_p = VanillaSwap(
            notional=10_000_000, fixed_rate=par, maturity=5.0, direction="payer"
        )

        dv01_r = compute_dv01(swap_r, mats, rates)
        dv01_p = compute_dv01(swap_p, mats, rates)

        np.testing.assert_allclose(dv01_r, -dv01_p, rtol=1e-10)

    def test_dv01_scales_with_notional(self, upward_curve, upward_interpolator):
        """DV01 doit être linéaire dans le notional."""
        mats, rates = upward_curve
        temp = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
        par = temp.par_rate(upward_interpolator)

        swap_10m = VanillaSwap(
            notional=10_000_000, fixed_rate=par, maturity=5.0, direction="receiver"
        )
        swap_20m = VanillaSwap(
            notional=20_000_000, fixed_rate=par, maturity=5.0, direction="receiver"
        )

        dv01_10m = compute_dv01(swap_10m, mats, rates)
        dv01_20m = compute_dv01(swap_20m, mats, rates)

        np.testing.assert_allclose(dv01_20m, 2 * dv01_10m, rtol=1e-8)

    def test_dv01_grows_with_maturity(self, upward_curve, upward_interpolator):
        """À fixed rate at-par, DV01 doit croître avec la maturité."""
        mats, rates = upward_curve

        dv01_values = []
        for maturity in [2.0, 5.0, 10.0]:
            temp = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=maturity)
            par = temp.par_rate(upward_interpolator)
            swap = VanillaSwap(
                notional=10_000_000,
                fixed_rate=par,
                maturity=maturity,
                direction="receiver",
            )
            dv01 = compute_dv01(swap, mats, rates)
            dv01_values.append(dv01)

        # Vérifie la monotonicité
        assert dv01_values[0] < dv01_values[1] < dv01_values[2]


# ═══════════════════════════════════════════════════════════
#  CONVEXITÉ
# ═══════════════════════════════════════════════════════════


class TestConvexity:
    """Tests du calcul de convexité dollar."""

    def test_convexity_positive_for_receiver(self, at_par_5y_swap, upward_curve):
        """La convexité d'un swap vanille (receiver) doit être positive."""
        mats, rates = upward_curve
        convexity = compute_convexity(at_par_5y_swap, mats, rates)
        assert convexity > 0

    def test_convexity_grows_with_maturity(self, upward_curve, upward_interpolator):
        """À notional égal et at-par, la convexité croît avec la maturité."""
        mats, rates = upward_curve

        convexities = []
        for maturity in [2.0, 5.0, 10.0]:
            temp = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=maturity)
            par = temp.par_rate(upward_interpolator)
            swap = VanillaSwap(
                notional=10_000_000,
                fixed_rate=par,
                maturity=maturity,
                direction="receiver",
            )
            c = compute_convexity(swap, mats, rates)
            convexities.append(c)

        assert convexities[0] < convexities[1] < convexities[2]


# ═══════════════════════════════════════════════════════════
#  KEY RATE DV01
# ═══════════════════════════════════════════════════════════


class TestKeyRateDV01:
    """Tests de la décomposition KR-DV01."""

    def test_kr_dv01_returns_dict_with_all_maturities(
        self, at_par_5y_swap, upward_curve
    ):
        """compute_key_rate_dv01 doit retourner un dict avec une clé par maturité."""
        mats, rates = upward_curve
        kr = compute_key_rate_dv01(at_par_5y_swap, mats, rates)

        assert isinstance(kr, dict)
        assert len(kr) == len(mats)
        # Toutes les maturités doivent être présentes comme clés
        for m in mats:
            assert m in kr or float(m) in kr

    def test_sum_kr_dv01_equals_parallel_dv01(self, at_par_5y_swap, upward_curve):
        """
        La propriété fondamentale : la somme des KR-DV01 doit ≈ DV01 parallèle.
        Tolérance large parce que ce sont deux calculs numériques différents.
        """
        mats, rates = upward_curve

        dv01_parallel = compute_dv01(at_par_5y_swap, mats, rates)
        kr = compute_key_rate_dv01(at_par_5y_swap, mats, rates)
        sum_kr = sum(kr.values())

        # Tolérance : 0.1% de différence relative max
        diff_rel = abs(sum_kr - dv01_parallel) / abs(dv01_parallel)
        assert diff_rel < 1e-3, (
            f"Sum KR-DV01 ({sum_kr:.4f}) should match parallel DV01 "
            f"({dv01_parallel:.4f}). Diff: {diff_rel * 100:.4f}%"
        )

    def test_kr_dv01_concentrated_near_swap_maturity(
        self, at_par_5y_swap, upward_curve
    ):
        """
        Pour un swap 5Y, la majorité du risque doit être sur le bucket 5Y
        (ou les buckets adjacents).
        """
        mats, rates = upward_curve
        kr = compute_key_rate_dv01(at_par_5y_swap, mats, rates)

        # Trouve le bucket 5Y
        kr_5y = kr.get(5.0, kr.get(np.float64(5.0)))
        assert kr_5y is not None, "5Y bucket should exist"

        # Sum total
        total = sum(kr.values())

        # Le 5Y doit représenter au moins 80% du total
        ratio = abs(kr_5y / total)
        assert ratio > 0.80, (
            f"5Y bucket should contain >80% of total DV01, got {ratio * 100:.1f}%"
        )
