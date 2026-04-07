import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Dict, Optional

from src.plots.theme import COLORS, apply_style, format_money


apply_style()


# ═══════════════════════════════════════════════════════════
#  PLOT — KR-DV01 LADDER (bar chart signé)
# ═══════════════════════════════════════════════════════════


def plot_kr_dv01_ladder(
    kr_dv01: Dict[float, float],
    title: str = "Key Rate DV01 Ladder",
    ax: Optional[plt.Axes] = None,
    show_values: bool = True,
    log_scale: bool = False,
) -> Figure:
    """
    Bar chart des Key Rate DV01 par maturité.

    Couleurs signées : vert pour positif (long duration sur ce bucket),
    rouge pour négatif (short duration). Le bucket dominant ressort
    visuellement.

    Args:
        kr_dv01: dict {maturity: dv01_value} retourné par compute_key_rate_dv01
        title: titre du plot
        ax: axe matplotlib existant (optionnel)
        show_values: si True, annote chaque barre avec sa valeur
        log_scale: si True, échelle log symétrique (utile quand le bucket
                   dominant écrase visuellement les autres)

    Returns:
        Figure matplotlib
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 6))
    else:
        fig = ax.figure

    # Tri par maturité croissante
    maturities = sorted(kr_dv01.keys())
    values = [kr_dv01[m] for m in maturities]

    # Couleurs signées
    colors = [COLORS["positive"] if v > 0 else COLORS["negative"] for v in values]

    # Labels x-axis (formatage des maturités)
    x_labels = [f"{int(m * 12)}M" if m < 1 else f"{int(m)}Y" for m in maturities]
    x_pos = np.arange(len(maturities))

    # Bar chart
    bars = ax.bar(
        x_pos,
        values,
        color=colors,
        edgecolor="white",
        linewidth=1.2,
        zorder=3,
    )

    # Reference line à 0
    ax.axhline(0, color=COLORS["neutral"], linewidth=0.8, zorder=2)

    # Annotations sur chaque barre
    if show_values:
        for bar, v in zip(bars, values):
            height = bar.get_height()
            # Position du label : au-dessus si positif, en-dessous si négatif
            offset = 3 if height >= 0 else -3
            va = "bottom" if height >= 0 else "top"

            ax.annotate(
                f"{v:,.0f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, offset),
                textcoords="offset points",
                ha="center",
                va=va,
                fontsize=8,
                color=COLORS["neutral"],
                fontweight="bold",
            )

    # Échelle log symétrique optionnelle (pour swap dont le risque est concentré)
    if log_scale:
        ax.set_yscale("symlog", linthresh=10)

    # Total en annotation
    total = sum(values)
    ax.text(
        0.02,
        0.97,
        f"Total: {format_money(total, 'EUR')}",
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        color=COLORS["primary"],
        verticalalignment="top",
        bbox=dict(
            boxstyle="round,pad=0.4",
            facecolor=COLORS["bg_alt"],
            edgecolor=COLORS["light"],
        ),
    )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel("Maturity bucket")
    ax.set_ylabel("DV01 (EUR/bp)")
    ax.set_title(title)

    return fig


# ═══════════════════════════════════════════════════════════
#  PLOT — STRESS TEST (P&L vs parallel shift)
# ═══════════════════════════════════════════════════════════


def plot_stress_test(
    shifts_bp: np.ndarray,
    pnl_values: np.ndarray,
    dv01: Optional[float] = None,
    convexity: Optional[float] = None,
    title: str = "Stress Test — Parallel Shift",
    ax: Optional[plt.Axes] = None,
) -> Figure:
    """
    Plot le P&L en fonction d'un parallel shift de la courbe.
    Affiche optionnellement l'approximation linéaire (DV01 only)
    et quadratique (DV01 + convexité) pour visualiser l'effet convexité.

    Args:
        shifts_bp: array des shifts en bp (ex: [-100, -50, 0, 50, 100])
        pnl_values: array des P&L correspondants en €
        dv01: DV01 du swap (pour tracer l'approximation linéaire)
        convexity: convexité dollar (pour l'approximation quadratique)
        title: titre du plot
        ax: axe matplotlib existant (optionnel)

    Returns:
        Figure matplotlib
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # P&L réel (full reprice)
    ax.plot(
        shifts_bp,
        pnl_values,
        marker="o",
        markersize=7,
        color=COLORS["primary"],
        linewidth=2.2,
        label="Full reprice",
        zorder=3,
    )

    # Approximation linéaire (DV01 seul)
    if dv01 is not None:
        linear_approx = -dv01 * shifts_bp
        ax.plot(
            shifts_bp,
            linear_approx,
            color=COLORS["accent"],
            linewidth=1.2,
            linestyle="--",
            alpha=0.7,
            label="Linear (DV01 only)",
            zorder=2,
        )

    # Approximation quadratique (DV01 + convexité)
    if dv01 is not None and convexity is not None:
        quad_approx = -dv01 * shifts_bp + 0.5 * convexity * shifts_bp**2
        ax.plot(
            shifts_bp,
            quad_approx,
            color=COLORS["positive"],
            linewidth=1.2,
            linestyle=":",
            alpha=0.8,
            label="Quadratic (+ convexity)",
            zorder=2,
        )

    # Reference lines
    ax.axhline(0, color=COLORS["neutral"], linewidth=0.6, alpha=0.5)
    ax.axvline(0, color=COLORS["neutral"], linewidth=0.6, alpha=0.5)

    ax.set_xlabel("Parallel shift (bp)")
    ax.set_ylabel("P&L (EUR)")
    ax.set_title(title)
    ax.legend(loc="best")

    # Format y-axis avec séparateurs de milliers
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    return fig
