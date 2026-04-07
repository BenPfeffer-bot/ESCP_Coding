import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Optional, Union

from src.plots.theme import COLORS, apply_style, format_pct
from src.curves.interpolation import YieldCurveInterpolator


# Applique le style au load du module
apply_style()


def _make_smooth_grid(maturities: np.ndarray, n_points: int = 200) -> np.ndarray:
    """
    Génère une grille fine entre min et max des maturités, pour des
    courbes lisses interpolées.
    """
    return np.linspace(maturities[0], maturities[-1], n_points)


# ═══════════════════════════════════════════════════════════
#  PLOT 1 — PAR SWAP RATES
# ═══════════════════════════════════════════════════════════
def plot_par_rates(
    maturities: np.ndarray,
    rates: np.ndarray,
    title: str = "Par Swap Rates",
    ax: Optional[plt.Axes] = None,
) -> Figure:
    """
    Plot les taux swap par utilisés en input du bootstrap.

    Args:
        maturities: array des maturités en années
        rates: array des taux en décimal
        title: titre du plot
        ax: axe matplotlib existant (optionnel, pour subplot)

    Returns:
        Figure matplotlib
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # Plot principal — markers + line
    ax.plot(
        maturities,
        rates * 100,
        marker="o",
        markersize=8,
        color=COLORS["primary"],
        label="Par rates",
        zorder=3,
    )

    # Annotations sur chaque point
    for m, r in zip(maturities, rates):
        ax.annotate(
            format_pct(r, 2),
            xy=(m, r * 100),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=COLORS["neutral"],
        )

    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Rate (%)")
    ax.set_title(title)
    ax.set_xlim(0, maturities[-1] * 1.05)

    # Marge verticale pour les annotations
    y_min = rates.min() * 100 - 0.3
    y_max = rates.max() * 100 + 0.5
    ax.set_ylim(y_min, y_max)

    return fig


# ═══════════════════════════════════════════════════════════
#  PLOT 2 — ZERO RATES (continuous compounding, lisse)
# ═══════════════════════════════════════════════════════════


def plot_zero_rates(
    interpolator: YieldCurveInterpolator,
    title: str = "Zero Coupon Rates (continuous)",
    ax: Optional[plt.Axes] = None,
    show_nodes: bool = True,
) -> Figure:
    """
    Plot la courbe zéro-coupon lisse via l'interpolator.
    Affiche aussi les nœuds bootstrappés en marqueurs.

    Args:
        interpolator: YieldCurveInterpolator déjà construit
        title: titre du plot
        ax: axe matplotlib existant (optionnel)
        show_nodes: si True, marque les nœuds bootstrappés

    Returns:
        Figure matplotlib
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # Courbe lisse via interpolator
    t_grid = _make_smooth_grid(interpolator.maturities)
    y_grid = interpolator.zero_rate_curve(t_grid)

    ax.plot(
        t_grid,
        y_grid * 100,
        color=COLORS["primary"],
        label="Zero rate (interpolated)",
        zorder=2,
    )

    # Nœuds bootstrappés en marqueurs
    if show_nodes:
        ax.scatter(
            interpolator.maturities,
            interpolator.zero_rates * 100,
            s=60,
            color=COLORS["accent"],
            edgecolors="white",
            linewidth=1.5,
            label="Bootstrap nodes",
            zorder=3,
        )

    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Zero rate (%)")
    ax.set_title(title)
    ax.set_xlim(0, interpolator.maturities[-1] * 1.05)
    ax.legend()

    return fig


# ═══════════════════════════════════════════════════════════
#  PLOT 3 — DISCOUNT FACTORS
# ═══════════════════════════════════════════════════════════


def plot_discount_factors(
    interpolator: YieldCurveInterpolator,
    title: str = "Discount Factors",
    ax: Optional[plt.Axes] = None,
    show_nodes: bool = True,
) -> Figure:
    """
    Plot les discount factors Z(0, T) interpolés.

    Args:
        interpolator: YieldCurveInterpolator déjà construit
        title: titre du plot
        ax: axe matplotlib existant (optionnel)
        show_nodes: si True, marque les nœuds bootstrappés

    Returns:
        Figure matplotlib
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # Courbe lisse
    t_grid = _make_smooth_grid(interpolator.maturities)
    z_grid = np.array([interpolator.discount_factor(t) for t in t_grid])

    ax.plot(
        t_grid,
        z_grid,
        color=COLORS["primary"],
        label="Z(0, T) interpolated",
        zorder=2,
    )

    # Aire sous la courbe pour visualiser la décroissance
    ax.fill_between(
        t_grid,
        0,
        z_grid,
        color=COLORS["primary"],
        alpha=0.08,
        zorder=1,
    )

    # Nœuds bootstrappés
    if show_nodes:
        ax.scatter(
            interpolator.maturities,
            interpolator.discount_factors,
            s=60,
            color=COLORS["accent"],
            edgecolors="white",
            linewidth=1.5,
            label="Bootstrap nodes",
            zorder=3,
        )

    # Reference line à Z=1
    ax.axhline(1.0, color=COLORS["neutral"], linewidth=0.6, linestyle="--", alpha=0.5)

    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Discount factor")
    ax.set_title(title)
    ax.set_xlim(0, interpolator.maturities[-1] * 1.05)
    ax.set_ylim(0, 1.05)
    ax.legend()

    return fig


# ═══════════════════════════════════════════════════════════
#  PLOT 4 — FORWARD RATES
# ═══════════════════════════════════════════════════════════


def plot_forward_rates(
    interpolator: YieldCurveInterpolator,
    title: str = "Instantaneous Forward Rates",
    ax: Optional[plt.Axes] = None,
    forward_horizon: float = 0.25,
) -> Figure:
    """
    Plot les forward rates implicites.

    Calcule des forwards "courts" entre T et T + horizon (par défaut 3M)
    sur toute la grille de maturités.

    Args:
        interpolator: YieldCurveInterpolator déjà construit
        title: titre du plot
        ax: axe matplotlib existant (optionnel)
        forward_horizon: horizon des forwards en années (défaut 0.25 = 3M)

    Returns:
        Figure matplotlib
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # Grille pour les forwards : exclut les dernières mats où T+horizon dépasse
    t_grid = np.linspace(
        interpolator.maturities[0],
        interpolator.maturities[-1] - forward_horizon,
        200,
    )

    # Calcul des forwards
    f_grid = np.array(
        [interpolator.forward_rate(t, t + forward_horizon) for t in t_grid]
    )

    # Plot principal
    ax.plot(
        t_grid,
        f_grid * 100,
        color=COLORS["primary"],
        label=f"{int(forward_horizon * 12)}M forwards",
        zorder=2,
    )

    # Overlay : zero rate pour comparaison
    y_grid = interpolator.zero_rate_curve(t_grid)
    ax.plot(
        t_grid,
        y_grid * 100,
        color=COLORS["accent"],
        linewidth=1.2,
        linestyle="--",
        alpha=0.7,
        label="Zero rate (reference)",
        zorder=2,
    )

    ax.set_xlabel("Start date (years)")
    ax.set_ylabel("Rate (%)")
    ax.set_title(title)
    ax.set_xlim(0, interpolator.maturities[-1] * 1.05)
    ax.legend()

    return fig


# ═══════════════════════════════════════════════════════════
#  GRILLE COMBINÉE — 4 plots en une seule figure
# ═══════════════════════════════════════════════════════════


def plot_curves_grid(
    maturities: np.ndarray,
    rates: np.ndarray,
    interpolator: YieldCurveInterpolator,
    suptitle: str = "Yield Curve Dashboard",
) -> Figure:
    """
    Génère une grille 2×2 avec les 4 plots de courbes.
    Idéal pour un export PDF ou un screenshot dashboard.

    Args:
        maturities: array des maturités d'input
        rates: array des par swap rates
        interpolator: YieldCurveInterpolator déjà construit
        suptitle: titre principal

    Returns:
        Figure matplotlib avec 4 subplots
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    plot_par_rates(maturities, rates, ax=axes[0, 0])
    plot_zero_rates(interpolator, ax=axes[0, 1])
    plot_discount_factors(interpolator, ax=axes[1, 0])
    plot_forward_rates(interpolator, ax=axes[1, 1])

    fig.suptitle(suptitle, fontsize=15, fontweight="bold", y=1.00)
    fig.tight_layout()

    return fig
