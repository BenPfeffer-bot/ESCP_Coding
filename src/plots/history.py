import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from datetime import date
from typing import Optional, List

from src.plots.theme import COLORS, apply_style


apply_style()


# ═══════════════════════════════════════════════════════════
#  PLOT — HISTORICAL MATURITY (séries temporelles d'un point)
# ═══════════════════════════════════════════════════════════


def plot_historical_maturity(
    dates: List[date],
    rates: List[float],
    maturity_label: str,
    title: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
) -> Figure:
    """
    Plot l'évolution d'un yield à une maturité donnée sur le temps.

    Args:
        dates: liste de dates
        rates: liste de rates en décimal
        maturity_label: label pour la légende (ex: "10Y")
        title: titre (défaut: auto)
        ax: axe matplotlib existant

    Returns:
        Figure matplotlib
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    if not dates:
        ax.text(
            0.5,
            0.5,
            "No historical data available\n(run multiple snapshots over several days)",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=11,
            color=COLORS["neutral"],
            style="italic",
        )
        ax.set_title(title or f"{maturity_label} — Historical")
        return fig

    # Conversion en numpy pour le plot
    rates_pct = np.array(rates) * 100

    ax.plot(
        dates,
        rates_pct,
        marker="o",
        markersize=4,
        color=COLORS["primary"],
        linewidth=1.8,
        label=maturity_label,
        zorder=3,
    )

    # Stats descriptives en annotation
    if len(rates) > 1:
        stats = (
            f"Min:  {rates_pct.min():.2f}%\n"
            f"Max:  {rates_pct.max():.2f}%\n"
            f"Mean: {rates_pct.mean():.2f}%\n"
            f"σ:    {rates_pct.std():.3f}%"
        )
        ax.text(
            0.98,
            0.97,
            stats,
            transform=ax.transAxes,
            fontsize=9,
            family="monospace",
            color=COLORS["neutral"],
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(
                boxstyle="round,pad=0.4",
                facecolor=COLORS["bg_alt"],
                edgecolor=COLORS["light"],
            ),
        )

    # Format dates sur l'axe x
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate(rotation=30, ha="right")

    ax.set_xlabel("Date")
    ax.set_ylabel("Rate (%)")
    ax.set_title(title or f"{maturity_label} Treasury Yield — Historical")

    return fig


# ═══════════════════════════════════════════════════════════
#  PLOT — CURVE EVOLUTION (overlay de courbes à différentes dates)
# ═══════════════════════════════════════════════════════════


def plot_curve_evolution(
    curves_history: List[dict],
    title: str = "Yield Curve Evolution",
    ax: Optional[plt.Axes] = None,
    max_curves: int = 5,
) -> Figure:
    """
    Overlay de plusieurs courbes pour visualiser l'évolution du jour.

    Args:
        curves_history: liste de dicts retournés par get_curve_history()
            chaque dict contient {'date': str, 'maturities': [...], 'rates': [...]}
        title: titre du plot
        ax: axe matplotlib existant
        max_curves: nombre max de courbes à afficher (les plus récentes)

    Returns:
        Figure matplotlib
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 6))
    else:
        fig = ax.figure

    if not curves_history:
        ax.text(
            0.5,
            0.5,
            "No historical curves available",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=11,
            color=COLORS["neutral"],
            style="italic",
        )
        ax.set_title(title)
        return fig

    # Garder les N dernières courbes
    curves = curves_history[:max_curves]

    # Colormap : gradient du gris au bleu (plus récent = plus foncé)
    n = len(curves)
    cmap = plt.cm.Blues
    colors = cmap(np.linspace(0.4, 1.0, n))

    for i, curve in enumerate(curves):
        mats = np.array(curve["maturities"])
        rates = np.array(curve["rates"]) * 100

        # Plus récent = plus opaque + plus épais
        is_latest = i == 0
        ax.plot(
            mats,
            rates,
            color=colors[n - i - 1],
            linewidth=2.5 if is_latest else 1.2,
            alpha=1.0 if is_latest else 0.6,
            label=curve["date"],
            marker="o" if is_latest else None,
            markersize=5,
            zorder=3 if is_latest else 2,
        )

    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Rate (%)")
    ax.set_title(title)
    ax.legend(loc="lower right", title="Date")

    return fig
