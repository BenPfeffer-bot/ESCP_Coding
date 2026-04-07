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

    Couleurs signées : vert pour positif, rouge pour négatif.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(11, 6))
    else:
        fig = ax.figure

    maturities = sorted(kr_dv01.keys())
    values = [kr_dv01[m] for m in maturities]

    colors = [COLORS["positive"] if v > 0 else COLORS["negative"] for v in values]

    x_labels = [f"{int(m * 12)}M" if m < 1 else f"{int(m)}Y" for m in maturities]
    x_pos = np.arange(len(maturities))

    bars = ax.bar(
        x_pos,
        values,
        color=colors,
        edgecolor="white",
        linewidth=1.2,
        zorder=3,
    )

    ax.axhline(0, color=COLORS["neutral"], linewidth=0.8, zorder=2)

    # Annotations sur chaque barre
    if show_values:
        for bar, v in zip(bars, values):
            height = bar.get_height()
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

    # Échelle log symétrique
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
    ax.set_title(title, pad=15)  # ← padding pour éviter chevauchement

    # ── FIX : marge verticale pour éviter le chevauchement du titre ──
    # En log scale, la barre dominante est très haute et l'annotation
    # peut déborder. On force de la marge en haut.
    if log_scale:
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(bottom=y_min, top=y_max * 3)  # 3x de marge en haut
    else:
        # En linéaire, un peu de marge aussi pour la propreté
        y_min, y_max = ax.get_ylim()
        margin = (y_max - y_min) * 0.1
        ax.set_ylim(bottom=y_min - margin * 0.2, top=y_max + margin)

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
    show_residuals: bool = True,
) -> Figure:
    """
    Plot le P&L en fonction d'un parallel shift + sous-plot de la convexité.

    Le top plot montre le P&L global avec les approximations linéaire
    et quadratique. Le bottom plot isole l'effet convexité (résidu
    Full - Linear) pour le rendre visible même quand il est petit
    devant la linéarité.

    Args:
        shifts_bp: array des shifts en bp
        pnl_values: array des P&L correspondants en €
        dv01: DV01 pour l'approximation linéaire
        convexity: convexité dollar pour l'approximation quadratique
        title: titre du plot principal
        ax: ignoré si show_residuals=True (on crée toujours 2 subplots)
        show_residuals: si True, ajoute le sous-plot de la convexité isolée

    Returns:
        Figure matplotlib
    """
    if show_residuals and dv01 is not None:
        # Layout 2 subplots : P&L en haut, résidu en bas
        fig, (ax_main, ax_resid) = plt.subplots(
            2,
            1,
            figsize=(10, 8),
            gridspec_kw={"height_ratios": [2, 1]},
            sharex=True,
        )
    else:
        if ax is None:
            fig, ax_main = plt.subplots()
        else:
            fig = ax.figure
            ax_main = ax
        ax_resid = None

    # ═══════════════════════════════════════════════════
    #  TOP PLOT : P&L global
    # ═══════════════════════════════════════════════════
    ax_main.plot(
        shifts_bp,
        pnl_values,
        marker="o",
        markersize=7,
        color=COLORS["primary"],
        linewidth=2.2,
        label="Full reprice",
        zorder=3,
    )

    if dv01 is not None:
        linear_approx = -dv01 * shifts_bp
        ax_main.plot(
            shifts_bp,
            linear_approx,
            color=COLORS["accent"],
            linewidth=1.2,
            linestyle="--",
            alpha=0.7,
            label="Linear (DV01 only)",
            zorder=2,
        )

    if dv01 is not None and convexity is not None:
        quad_approx = -dv01 * shifts_bp + 0.5 * convexity * shifts_bp**2
        ax_main.plot(
            shifts_bp,
            quad_approx,
            color=COLORS["positive"],
            linewidth=1.2,
            linestyle=":",
            alpha=0.8,
            label="Quadratic (+ convexity)",
            zorder=2,
        )

    ax_main.axhline(0, color=COLORS["neutral"], linewidth=0.6, alpha=0.5)
    ax_main.axvline(0, color=COLORS["neutral"], linewidth=0.6, alpha=0.5)
    ax_main.set_ylabel("P&L (EUR)")
    ax_main.set_title(title, pad=10)
    ax_main.legend(loc="best")
    ax_main.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # ═══════════════════════════════════════════════════
    #  BOTTOM PLOT : résidus (convexité isolée)
    # ═══════════════════════════════════════════════════
    if ax_resid is not None:
        # Full - Linear isole l'effet non-linéaire, dominé par la convexité
        linear_approx = -dv01 * shifts_bp
        residuals = pnl_values - linear_approx

        ax_resid.plot(
            shifts_bp,
            residuals,
            marker="o",
            markersize=6,
            color=COLORS["primary"],
            linewidth=2.0,
            label="Residual (Full − Linear)",
            zorder=3,
        )

        # Remplissage pour renforcer visuellement la forme en U
        ax_resid.fill_between(
            shifts_bp,
            0,
            residuals,
            color=COLORS["primary"],
            alpha=0.15,
            zorder=1,
        )

        if convexity is not None:
            quad_residual = 0.5 * convexity * shifts_bp**2
            ax_resid.plot(
                shifts_bp,
                quad_residual,
                color=COLORS["positive"],
                linewidth=1.5,
                linestyle=":",
                alpha=0.9,
                label="½ × Convexity × shift²",
                zorder=2,
            )

        ax_resid.axhline(0, color=COLORS["neutral"], linewidth=0.6, alpha=0.5)
        ax_resid.axvline(0, color=COLORS["neutral"], linewidth=0.6, alpha=0.5)
        ax_resid.set_xlabel("Parallel shift (bp)")
        ax_resid.set_ylabel("Convexity effect (EUR)")
        ax_resid.set_title("Convexity effect (isolated)", fontsize=11, pad=8)
        ax_resid.legend(loc="best", fontsize=9)
        ax_resid.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    else:
        ax_main.set_xlabel("Parallel shift (bp)")

    fig.tight_layout()
    return fig
