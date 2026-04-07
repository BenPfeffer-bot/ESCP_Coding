"""
Fixtures partagées entre tous les tests.

Pytest découvre automatiquement ce fichier et rend les fixtures disponibles dans tous les tests sous tests
"""

import numpy as np
import pytest

from src.curves.bootstrapper import bootstrap_discount_factors
from src.curves.interpolation import YieldCurveInterpolator


# ═══════════════════════════════════════════════════════════
#  COURBES SYNTHÉTIQUES (déterministes, indépendantes des APIs)
# ═══════════════════════════════════════════════════════════


@pytest.fixture
def flat_curve_3pct():
    """
    Courbe plate à 3% sur les maturités standards.
    Cas analytique de référence.
    """
    maturities = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0])
    rates = np.full_like(maturities, 0.03)
    return maturities, rates


@pytest.fixture
def flat_curve_5pct():
    """Courbe plate à 5% — pour tester avec un autre niveau."""
    maturities = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0])
    rates = np.full_like(maturities, 0.05)
    return maturities, rates


@pytest.fixture
def upward_curve():
    """Courbe upward-sloping réaliste (3% à 1Y → 5% à 30Y)."""
    maturities = np.array([0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0])
    rates = np.array(
        [0.030, 0.032, 0.035, 0.038, 0.040, 0.042, 0.044, 0.046, 0.048, 0.050]
    )
    return maturities, rates


@pytest.fixture
def inverted_curve():
    """Courbe inversée (signe de récession)."""
    maturities = np.array([0.25, 1.0, 2.0, 5.0, 10.0, 30.0])
    rates = np.array([0.055, 0.052, 0.048, 0.045, 0.042, 0.040])
    return maturities, rates


# ═══════════════════════════════════════════════════════════
#  INTERPOLATORS PRÉ-CONSTRUITS
# ═══════════════════════════════════════════════════════════


@pytest.fixture
def flat_interpolator(flat_curve_3pct):
    """Interpolator construit sur la courbe plate à 3%."""
    mats, rates = flat_curve_3pct
    dfs = bootstrap_discount_factors(mats, rates)
    return YieldCurveInterpolator(mats, dfs, method="cubic_spline")


@pytest.fixture
def upward_interpolator(upward_curve):
    """Interpolator construit sur la courbe upward-sloping."""
    mats, rates = upward_curve
    dfs = bootstrap_discount_factors(mats, rates)
    return YieldCurveInterpolator(mats, dfs, method="cubic_spline")
