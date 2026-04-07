"""
Unit tests pour bootstrapper

Stratégie : tester avec des courbes synthétiques où on connaît
la solution analytique, pour vérifier que le bootstrap retourne
les bonnes valeurs.
"""

import numpy as np
import pytest

from src.curves.bootstrapper import (
    bootstrap_discount_factors,
    discount_factors_to_zero_rates,
    extract_forward_rates,
)


class TestBootstrapDiscountFactors:
    """Tests de la fonction bootstrap principale."""

    def test_returns_correct_length(self, flat_curve_3pct):
        """Le bootstrap doit retourner autant de DFs que de maturités."""
        mats, rates = flat_curve_3pct
        dfs = bootstrap_discount_factors(mats, rates)
        assert len(dfs) == len(mats)

    def test_dfs_are_decreasing(self, flat_curve_3pct):
        """Pour une courbe avec rates positifs, les DFs sont strictement décroissants."""
        mats, rates = flat_curve_3pct
        dfs = bootstrap_discount_factors(mats, rates)
        diffs = np.diff(dfs)
        assert np.all(diffs < 0), "Discount factors should be strictly decreasing"

    def test_dfs_are_positive(self, flat_curve_3pct):
        """Tous les DFs doivent être positifs et inférieurs ou égaux à 1."""
        mats, rates = flat_curve_3pct
        dfs = bootstrap_discount_factors(mats, rates)
        assert np.all(dfs > 0)
        assert np.all(dfs <= 1.0)

    def test_first_df_matches_simple_discount(self, flat_curve_3pct):
        """
        Pour la première maturité, Z(0, T1) = 1 / (1 + r * T1).
        C'est le cas dégénéré du bootstrap (pas de terme de correction).
        """
        mats, rates = flat_curve_3pct
        dfs = bootstrap_discount_factors(mats, rates)

        T1 = mats[0]
        r1 = rates[0]
        expected_z1 = 1.0 / (1.0 + r1 * T1)

        np.testing.assert_allclose(dfs[0], expected_z1, rtol=1e-10)

    def test_flat_curve_3pct_specific_value(self, flat_curve_3pct):
        """
        Sur une courbe plate à 3% avec maturités [1, 2, 3, 5, 7, 10],
        le 1Y doit être 1/1.03 = 0.970874.
        """
        mats, rates = flat_curve_3pct
        dfs = bootstrap_discount_factors(mats, rates)
        np.testing.assert_allclose(dfs[0], 1 / 1.03, rtol=1e-10)

    def test_higher_rates_give_lower_dfs(self, flat_curve_3pct, flat_curve_5pct):
        """À maturité égale, des rates plus élevés → DFs plus faibles."""
        mats_3, rates_3 = flat_curve_3pct
        mats_5, rates_5 = flat_curve_5pct

        dfs_3 = bootstrap_discount_factors(mats_3, rates_3)
        dfs_5 = bootstrap_discount_factors(mats_5, rates_5)

        assert np.all(dfs_5 < dfs_3), "Higher rates should produce lower DFs"


class TestDiscountFactorsToZeroRates:
    """Tests de la conversion DF → zero rate."""

    def test_continuous_compounding_inverse(self):
        """
        En continuous compounding, y = -ln(Z) / T doit être l'inverse
        de Z = exp(-y * T).
        """
        # On construit des Z arbitraires et on vérifie le round-trip
        T = np.array([1.0, 2.0, 5.0, 10.0])
        y_input = np.array([0.03, 0.035, 0.04, 0.045])
        Z = np.exp(-y_input * T)

        y_output = discount_factors_to_zero_rates(T, Z, compounding="continuous")
        np.testing.assert_allclose(y_output, y_input, rtol=1e-10)

    def test_zero_rate_positive_for_normal_curve(self, flat_curve_3pct):
        """Pour une courbe normale, les zero rates sont positifs."""
        mats, rates = flat_curve_3pct
        dfs = bootstrap_discount_factors(mats, rates)
        zero_rates = discount_factors_to_zero_rates(mats, dfs)
        assert np.all(zero_rates > 0)


class TestExtractForwardRates:
    """Tests de l'extraction des forward rates."""

    def test_returns_tuple_with_forwards_and_dates(self, flat_curve_3pct):
        """extract_forward_rates retourne (forwards, midpoints/dates)."""
        mats, rates = flat_curve_3pct
        dfs = bootstrap_discount_factors(mats, rates)
        result = extract_forward_rates(mats, dfs)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_forwards_close_to_par_for_flat_curve(self, flat_curve_3pct):
        """
        Sur une courbe plate à 3% en par swap rates, les forwards
        sont légèrement inférieurs (~2.95%) à cause de l'écart entre
        par rate et zero rate équivalent.
        """
        mats, rates = flat_curve_3pct
        dfs = bootstrap_discount_factors(mats, rates)
        _, forwards = extract_forward_rates(
            mats, dfs
        )  # ← inversé : (midpoints, forwards)

        forwards = np.asarray(forwards)
        assert np.all(np.abs(forwards - 0.03) < 0.005)

    def test_forwards_positive_for_normal_curve(self, upward_curve):
        """Sur une courbe normale, tous les forwards doivent être positifs."""
        mats, rates = upward_curve
        dfs = bootstrap_discount_factors(mats, rates)
        _, forwards = extract_forward_rates(mats, dfs)  # ← inversé

        forwards = np.asarray(forwards)
        assert np.all(forwards > 0)
