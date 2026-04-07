import numpy as np
import pytest

from src.curves.interpolation import YieldCurveInterpolator
from src.curves.bootstrapper import bootstrap_discount_factors


class TestInterpolatorConstruction:
    """Tests de la construction de l'interpolator."""

    def test_interpolator_builds_successfully(self, upward_curve):
        """L'interpolator doit se construire sans erreur."""
        mats, rates = upward_curve
        dfs = bootstrap_discount_factors(mats, rates)
        interp = YieldCurveInterpolator(mats, dfs, method="cubic_spline")
        assert interp is not None

    def test_interpolator_supports_linear_method(self, upward_curve):
        """La méthode linear est aussi supportée."""
        mats, rates = upward_curve
        dfs = bootstrap_discount_factors(mats, rates)
        interp = YieldCurveInterpolator(mats, dfs, method="linear")
        assert interp is not None


class TestInterpolatorOnNodes:
    """L'interpolation doit retourner les valeurs exactes sur les nœuds."""

    def test_discount_factor_exact_on_nodes(self, upward_curve):
        """Z(T_i) interpolé doit égaler le DF d'input pour chaque nœud."""
        mats, rates = upward_curve
        dfs = bootstrap_discount_factors(mats, rates)
        interp = YieldCurveInterpolator(mats, dfs, method="cubic_spline")

        for i, T in enumerate(mats):
            z_interp = interp.discount_factor(T)
            np.testing.assert_allclose(z_interp, dfs[i], rtol=1e-10)

    def test_linear_interpolation_exact_on_nodes(self, upward_curve):
        """Même test avec linear interpolation."""
        mats, rates = upward_curve
        dfs = bootstrap_discount_factors(mats, rates)
        interp = YieldCurveInterpolator(mats, dfs, method="linear")

        for i, T in enumerate(mats):
            z_interp = interp.discount_factor(T)
            np.testing.assert_allclose(z_interp, dfs[i], rtol=1e-10)


class TestInterpolatorBetweenNodes:
    """Tests sur les valeurs entre les nœuds."""

    def test_discount_factor_monotone_decreasing(self, upward_interpolator):
        """Sur une grille fine, Z(T) doit rester décroissant."""
        T_grid = np.linspace(1.0, 10.0, 100)
        z_values = np.array([upward_interpolator.discount_factor(t) for t in T_grid])
        diffs = np.diff(z_values)
        assert np.all(diffs < 0), "DFs should be monotone decreasing"

    def test_discount_factor_in_unit_interval(self, upward_interpolator):
        """Z(T) doit toujours être entre 0 et 1."""
        T_grid = np.linspace(1.0, 10.0, 100)
        z_values = np.array([upward_interpolator.discount_factor(t) for t in T_grid])
        assert np.all(z_values > 0)
        assert np.all(z_values <= 1.0)

    def test_forward_rate_positive_for_upward_curve(self, upward_interpolator):
        """Sur une courbe upward, les forwards doivent être positifs."""
        # Forwards sur quelques couples (T1, T2)
        couples = [(1.0, 2.0), (2.0, 5.0), (5.0, 10.0)]
        for T1, T2 in couples:
            f = upward_interpolator.forward_rate(T1, T2)
            assert f > 0, f"Forward rate {T1}-{T2} should be positive on upward curve"


class TestInterpolatorEdgeCases:
    """Cas limites et erreurs."""

    def test_forward_rate_requires_T2_greater_than_T1(self, upward_interpolator):
        """forward_rate(T1, T2) avec T2 ≤ T1 doit lever une erreur."""
        with pytest.raises((AssertionError, ValueError)):
            upward_interpolator.forward_rate(5.0, 5.0)

        with pytest.raises((AssertionError, ValueError)):
            upward_interpolator.forward_rate(5.0, 3.0)
