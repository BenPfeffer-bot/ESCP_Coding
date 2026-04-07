import numpy as np
import pytest

from src.instruments.vanilla_swaps import VanillaSwap


class TestVanillaSwapBasics:
    """Tests basiques de construction et de pricing."""

    def test_swap_construction(self):
        """Un swap doit se construire avec les paramètres standards."""
        swap = VanillaSwap(
            notional=10_000_000,
            fixed_rate=0.04,
            maturity=5.0,
            payment_frequency=1.0,
            direction="receiver",
        )
        assert swap.notional == 10_000_000
        assert swap.fixed_rate == 0.04
        assert swap.maturity == 5.0
        assert swap.direction == "receiver"

    def test_par_rate_returns_positive_value(self, upward_interpolator):
        """Le par rate doit être un taux raisonnable (positif, < 100%)."""
        swap = VanillaSwap(
            notional=10_000_000,
            fixed_rate=0.0,
            maturity=5.0,
            direction="receiver",
        )
        par = swap.par_rate(upward_interpolator)
        assert 0 < par < 1.0, f"Par rate {par} should be in (0, 1)"


class TestSwapAtPar:
    """Un swap at-par doit avoir NPV ≈ 0."""

    def test_npv_zero_at_par_5y(self, upward_interpolator):
        """Swap 5Y receiver at-par : NPV doit être ~0."""
        # Calcule le par rate
        temp = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
        par = temp.par_rate(upward_interpolator)

        # Construit le swap au par rate
        swap = VanillaSwap(
            notional=10_000_000,
            fixed_rate=par,
            maturity=5.0,
            direction="receiver",
        )
        npv = swap.npv(upward_interpolator)

        assert abs(npv) < 1e-6, f"NPV at par should be ~0, got {npv}"

    def test_npv_zero_at_par_10y(self, upward_interpolator):
        """Même test sur 10Y."""
        temp = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=10.0)
        par = temp.par_rate(upward_interpolator)

        swap = VanillaSwap(
            notional=10_000_000,
            fixed_rate=par,
            maturity=10.0,
            direction="receiver",
        )
        npv = swap.npv(upward_interpolator)

        assert abs(npv) < 1e-6


class TestSwapDirectionality:
    """Receiver et payer doivent être parfaitement opposés."""

    def test_receiver_payer_opposite_signs(self, upward_interpolator):
        """
        Pour le même swap configuré en receiver vs payer,
        les NPV doivent être opposées en signe.
        """
        params = dict(
            notional=10_000_000,
            fixed_rate=0.05,  # Au-dessus du par sur courbe upward
            maturity=5.0,
            payment_frequency=1.0,
        )

        swap_recv = VanillaSwap(**params, direction="receiver")
        swap_pay = VanillaSwap(**params, direction="payer")

        npv_recv = swap_recv.npv(upward_interpolator)
        npv_pay = swap_pay.npv(upward_interpolator)

        # Opposés en signe, égaux en valeur absolue
        np.testing.assert_allclose(npv_recv, -npv_pay, rtol=1e-10)

    def test_receiver_npv_positive_when_fixed_above_par(self, upward_interpolator):
        """
        Receiver = on reçoit le fixe. Si fixed_rate > par_rate,
        on reçoit plus que le marché → NPV positive.
        """
        temp = VanillaSwap(notional=10_000_000, fixed_rate=0.0, maturity=5.0)
        par = temp.par_rate(upward_interpolator)

        # Fixed rate 50bp au-dessus du par
        swap = VanillaSwap(
            notional=10_000_000,
            fixed_rate=par + 0.005,
            maturity=5.0,
            direction="receiver",
        )
        npv = swap.npv(upward_interpolator)

        assert npv > 0, "Receiver above par should have positive NPV"


class TestSwapNotionalScaling:
    """La NPV doit être linéaire dans le notional."""

    def test_npv_linear_in_notional(self, upward_interpolator):
        """
        Doubler le notional doit doubler la NPV.
        Linéarité de la PV par rapport au notional.
        """
        params = dict(
            fixed_rate=0.05,
            maturity=5.0,
            direction="receiver",
        )

        swap_10m = VanillaSwap(notional=10_000_000, **params)
        swap_20m = VanillaSwap(notional=20_000_000, **params)

        npv_10m = swap_10m.npv(upward_interpolator)
        npv_20m = swap_20m.npv(upward_interpolator)

        np.testing.assert_allclose(npv_20m, 2 * npv_10m, rtol=1e-10)
