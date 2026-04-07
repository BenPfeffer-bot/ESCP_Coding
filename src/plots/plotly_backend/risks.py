import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Optional

from src.plots.plotly_backend.theme import (
    COLORS,
    apply_template,
    format_money,
)


# ═══════════════════════════════════════════════════════════
#  PLOT — KR-DV01 LADDER
# ═══════════════════════════════════════════════════════════


def plot_kr_dv01_ladder(
    kr_dv01: Dict[float, float],
    title: str = "Key Rate DV01 Ladder",
    show_values: bool = True,
    log_scale: bool = False,
) -> go.Figure:
    """
    Bar chart interactif des Key Rate DV01 par maturité.

    Couleurs signées : vert pour positif, rouge pour négatif.
    Hover affiche la valeur exacte de chaque bucket.
    """
    fig = go.Figure()

    # Tri et formatage
    maturities = sorted(kr_dv01.keys())
    values = [kr_dv01[m] for m in maturities]

    colors = [COLORS["positive"] if v > 0 else COLORS["negative"] for v in values]

    x_labels = [f"{int(m * 12)}M" if m < 1 else f"{int(m)}Y" for m in maturities]

    # Annotations sur les barres
    text_values = [f"{v:,.0f}" for v in values] if show_values else None
    text_positions = ["outside" if v >= 0 else "outside" for v in values]

    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=values,
            marker=dict(
                color=colors,
                line=dict(color="white", width=1.5),
            ),
            text=text_values,
            textposition=text_positions,
            textfont=dict(size=10, color=COLORS["neutral"]),
            hovertemplate=(
                "<b>%{x}</b><br>KR-DV01: %{y:,.2f} EUR/bp<br><extra></extra>"
            ),
            showlegend=False,
        )
    )

    # Total en annotation (box en haut à gauche)
    total = sum(values)
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.02,
        y=0.98,
        text=f"<b>Total: {format_money(total, 'EUR')}</b>",
        showarrow=False,
        font=dict(size=12, color=COLORS["primary"]),
        bgcolor=COLORS["bg_alt"],
        bordercolor=COLORS["light"],
        borderwidth=1,
        borderpad=6,
        xanchor="left",
        yanchor="top",
    )

    # Layout
    yaxis_config = dict(
        title="DV01 (EUR/bp)",
        zeroline=True,
        zerolinewidth=1.5,
        zerolinecolor=COLORS["neutral"],
    )

    if log_scale:
        # Symlog via transformation — Plotly n'a pas de symlog natif
        # On utilise une échelle log classique en gardant les signes visuels
        yaxis_config["type"] = "log"
        # Note : en log pur, les valeurs négatives disparaissent.
        # Alternative : on garde en linéaire mais on applique une
        # transformation sqrt pour compresser visuellement.
        # Pour l'instant on reste en linéaire — le log est rarement utile
        # dans Plotly grâce au zoom interactif.
        yaxis_config["type"] = "linear"  # override : on reste linéaire

    fig.update_layout(
        title=title,
        xaxis=dict(title="Maturity bucket"),
        yaxis=yaxis_config,
        height=500,
        bargap=0.2,
    )

    # Marge verticale pour les annotations
    y_min = min(values)
    y_max = max(values)
    y_range = y_max - y_min
    fig.update_yaxes(range=[y_min - y_range * 0.1, y_max + y_range * 0.15])

    return apply_template(fig)


# ═══════════════════════════════════════════════════════════
#  PLOT — STRESS TEST (avec sous-plot convexité)
# ═══════════════════════════════════════════════════════════


def plot_stress_test(
    shifts_bp: np.ndarray,
    pnl_values: np.ndarray,
    dv01: Optional[float] = None,
    convexity: Optional[float] = None,
    title: str = "Stress Test — Parallel Shift",
    show_residuals: bool = True,
) -> go.Figure:
    """
    P&L en fonction d'un parallel shift + sous-plot isolant la convexité.

    Le top plot montre P&L global avec approximations linéaire et quadratique.
    Le bottom plot isole l'effet convexité (résidu Full - Linear).
    """
    if show_residuals and dv01 is not None:
        fig = make_subplots(
            rows=2,
            cols=1,
            row_heights=[0.65, 0.35],
            shared_xaxes=True,
            vertical_spacing=0.12,
            subplot_titles=(None, "Convexity effect (isolated)"),
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # ═══════════════════════════════════════════════════
    #  TOP : P&L global
    # ═══════════════════════════════════════════════════

    # Full reprice
    fig.add_trace(
        go.Scatter(
            x=shifts_bp,
            y=pnl_values,
            mode="lines+markers",
            name="Full reprice",
            line=dict(color=COLORS["primary"], width=2.5),
            marker=dict(size=8, color=COLORS["primary"]),
            hovertemplate=("Shift: %{x} bp<br>P&L: %{y:,.0f} EUR<br><extra></extra>"),
        ),
        row=1,
        col=1,
    )

    # Linear approximation
    if dv01 is not None:
        linear_approx = -dv01 * shifts_bp
        fig.add_trace(
            go.Scatter(
                x=shifts_bp,
                y=linear_approx,
                mode="lines",
                name="Linear (DV01 only)",
                line=dict(color=COLORS["accent"], width=1.5, dash="dash"),
                opacity=0.75,
                hovertemplate=(
                    "Shift: %{x} bp<br>Linear: %{y:,.0f} EUR<br><extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

    # Quadratic approximation
    if dv01 is not None and convexity is not None:
        quad_approx = -dv01 * shifts_bp + 0.5 * convexity * shifts_bp**2
        fig.add_trace(
            go.Scatter(
                x=shifts_bp,
                y=quad_approx,
                mode="lines",
                name="Quadratic (+ convexity)",
                line=dict(color=COLORS["positive"], width=1.5, dash="dot"),
                opacity=0.85,
                hovertemplate=(
                    "Shift: %{x} bp<br>Quadratic: %{y:,.0f} EUR<br><extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

    # Reference lines (0,0)
    fig.add_hline(
        y=0,
        line=dict(color=COLORS["neutral"], width=0.6),
        opacity=0.5,
        row=1,
        col=1,
    )
    fig.add_vline(
        x=0,
        line=dict(color=COLORS["neutral"], width=0.6),
        opacity=0.5,
        row=1,
        col=1,
    )

    # ═══════════════════════════════════════════════════
    #  BOTTOM : convexité isolée
    # ═══════════════════════════════════════════════════
    if show_residuals and dv01 is not None:
        linear_approx = -dv01 * shifts_bp
        residuals = pnl_values - linear_approx

        # Résidu avec remplissage
        fig.add_trace(
            go.Scatter(
                x=shifts_bp,
                y=residuals,
                mode="lines+markers",
                name="Residual (Full − Linear)",
                line=dict(color=COLORS["primary"], width=2.0),
                marker=dict(size=6, color=COLORS["primary"]),
                fill="tozeroy",
                fillcolor="rgba(31, 78, 121, 0.12)",
                hovertemplate=(
                    "Shift: %{x} bp<br>Residual: %{y:,.0f} EUR<br><extra></extra>"
                ),
            ),
            row=2,
            col=1,
        )

        # Approximation quadratique de la convexité
        if convexity is not None:
            quad_residual = 0.5 * convexity * shifts_bp**2
            fig.add_trace(
                go.Scatter(
                    x=shifts_bp,
                    y=quad_residual,
                    mode="lines",
                    name="½ × Convexity × shift²",
                    line=dict(color=COLORS["positive"], width=1.5, dash="dot"),
                    opacity=0.9,
                    hovertemplate=(
                        "Shift: %{x} bp<br>"
                        "Theoretical: %{y:,.0f} EUR<br>"
                        "<extra></extra>"
                    ),
                ),
                row=2,
                col=1,
            )

        # Reference lines
        fig.add_hline(
            y=0,
            line=dict(color=COLORS["neutral"], width=0.6),
            opacity=0.5,
            row=2,
            col=1,
        )
        fig.add_vline(
            x=0,
            line=dict(color=COLORS["neutral"], width=0.6),
            opacity=0.5,
            row=2,
            col=1,
        )

    # ═══════════════════════════════════════════════════
    #  Axes & layout
    # ═══════════════════════════════════════════════════
    fig.update_yaxes(title_text="P&L (EUR)", tickformat=",", row=1, col=1)

    if show_residuals and dv01 is not None:
        fig.update_xaxes(title_text="Parallel shift (bp)", row=2, col=1)
        fig.update_yaxes(
            title_text="Convexity effect (EUR)",
            tickformat=",",
            row=2,
            col=1,
        )
    else:
        fig.update_xaxes(title_text="Parallel shift (bp)", row=1, col=1)

    fig.update_layout(
        title=title,
        height=700 if show_residuals else 500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
        ),
    )

    return apply_template(fig)
