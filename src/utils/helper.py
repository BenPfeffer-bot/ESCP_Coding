from src.curves.interpolation import YieldCurveInterpolator
from src.curves.bootstrapper import bootstrap_discount_factors


def reprice(swap, maturities, par_rates):
    """Helper : bootstrap + interpolate + price en une seule étape."""
    dfs = bootstrap_discount_factors(maturities, par_rates)
    interp = YieldCurveInterpolator(maturities, dfs, method="cubic_spline")
    return swap.npv(interp)
