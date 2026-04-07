"""
Version interactive des 4 plots de src/plots/curves.py :
  1. Par swap rates
  2. Zero rates
  3. Discount factors
  4. Forward rates

+ une grille combinée via make_subplots.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional

from src.plots.plotly_backend.theme import (
    COLORS,
    apply_template,
    format_pct,
)
from src.curves.interpolation import YieldCurveInterpolator


# ═══════════════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════════════


def _make_smooth_grid(maturities: np.ndarray, n_points: int = 200) -> np.ndarray:
    """Grille fine pour les courbes interpolées."""
    return np.linspace(maturities[0], maturities[-1], n_points)


# ═══════════════════════════════════════════════════════════
#  PLOT 1 — PAR SWAP RATES
# ═══════════════════════════════════════════════════════════


def plot_par_rates(
    maturities: np.ndarray,
    rates: np.ndarray,
    title: str = "Par Swap Rates",
) -> go.Figure:
    """
    Plot interactif des par swap rates.
    Hover montre la maturité et le taux exact.
    """
    fig = go.Figure()

    # Trace principale : markers + line avec hover custom
    fig.add_trace(
        go.Scatter(
            x=maturities,
            y=rates * 100,
            mode="lines+markers+text",
            name="Par rates",
            line=dict(color=COLORS["primary"], width=2.5),
            marker=dict(
                size=10,
                color=COLORS["primary"],
                line=dict(color="white", width=1.5),
            ),
            text=[format_pct(r, 2) for r in rates],
            textposition="top center",
            textfont=dict(size=10, color=COLORS["neutral"]),
            hovertemplate=("<b>%{x:.2f}Y</b><br>Rate: %{y:.4f}%<br><extra></extra>"),
        )
    )

    # Layout
    y_min = rates.min() * 100 - 0.3
    y_max = rates.max() * 100 + 0.6

    fig.update_layout(
        title=title,
        xaxis=dict(
            title="Maturity (years)",
            range=[0, maturities[-1] * 1.05],
        ),
        yaxis=dict(
            title="Rate (%)",
            range=[y_min, y_max],
        ),
        showlegend=False,
        height=450,
    )

    return apply_template(fig)


# ═══════════════════════════════════════════════════════════
#  PLOT 2 — ZERO RATES
# ═══════════════════════════════════════════════════════════


def plot_zero_rates(
    interpolator: YieldCurveInterpolator,
    title: str = "Zero Coupon Rates (continuous)",
    show_nodes: bool = True,
) -> go.Figure:
    """
    Courbe zero-coupon interpolée lisse + nœuds bootstrappés.
    """
    fig = go.Figure()

    # Courbe lisse interpolée
    t_grid = _make_smooth_grid(interpolator.maturities)
    y_grid = interpolator.zero_rate_curve(t_grid)

    fig.add_trace(
        go.Scatter(
            x=t_grid,
            y=y_grid * 100,
            mode="lines",
            name="Zero rate (interpolated)",
            line=dict(color=COLORS["primary"], width=2.5),
            hovertemplate=(
                "<b>%{x:.2f}Y</b><br>Zero rate: %{y:.4f}%<br><extra></extra>"
            ),
        )
    )

    # Nœuds bootstrappés
    if show_nodes:
        fig.add_trace(
            go.Scatter(
                x=interpolator.maturities,
                y=interpolator.zero_rates * 100,
                mode="markers",
                name="Bootstrap nodes",
                marker=dict(
                    size=11,
                    color=COLORS["accent"],
                    line=dict(color="white", width=2),
                ),
                hovertemplate=(
                    "<b>%{x:.2f}Y (node)</b><br>Zero rate: %{y:.4f}%<br><extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=title,
        xaxis=dict(
            title="Maturity (years)",
            range=[0, interpolator.maturities[-1] * 1.05],
        ),
        yaxis=dict(title="Zero rate (%)"),
        height=450,
        legend=dict(
            yanchor="bottom",
            y=0.02,
            xanchor="right",
            x=0.98,
        ),
    )

    return apply_template(fig)


# ═══════════════════════════════════════════════════════════
#  PLOT 3 — DISCOUNT FACTORS
# ═══════════════════════════════════════════════════════════


def plot_discount_factors(
    interpolator: YieldCurveInterpolator,
    title: str = "Discount Factors",
    show_nodes: bool = True,
) -> go.Figure:
    """
    Discount factors Z(0, T) avec aire de remplissage pour
    visualiser la décroissance exponentielle.
    """
    fig = go.Figure()

    t_grid = _make_smooth_grid(interpolator.maturities)
    z_grid = np.array([interpolator.discount_factor(t) for t in t_grid])

    # Aire de remplissage (dessiné en premier pour être derrière)
    fig.add_trace(
        go.Scatter(
            x=t_grid,
            y=z_grid,
            mode="lines",
            name="Z(0, T)",
            line=dict(color=COLORS["primary"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(31, 78, 121, 0.08)",
            hovertemplate=("<b>%{x:.2f}Y</b><br>DF: %{y:.6f}<br><extra></extra>"),
        )
    )

    # Nœuds bootstrappés
    if show_nodes:
        fig.add_trace(
            go.Scatter(
                x=interpolator.maturities,
                y=interpolator.discount_factors,
                mode="markers",
                name="Bootstrap nodes",
                marker=dict(
                    size=11,
                    color=COLORS["accent"],
                    line=dict(color="white", width=2),
                ),
                hovertemplate=(
                    "<b>%{x:.2f}Y (node)</b><br>DF: %{y:.6f}<br><extra></extra>"
                ),
            )
        )

    # Reference line à Z = 1
    fig.add_hline(
        y=1.0,
        line=dict(color=COLORS["neutral"], width=0.8, dash="dash"),
        opacity=0.5,
    )

    fig.update_layout(
        title=title,
        xaxis=dict(
            title="Maturity (years)",
            range=[0, interpolator.maturities[-1] * 1.05],
        ),
        yaxis=dict(
            title="Discount factor",
            range=[0, 1.05],
        ),
        height=450,
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
        ),
    )

    return apply_template(fig)


# ═══════════════════════════════════════════════════════════
#  PLOT 4 — FORWARD RATES
# ═══════════════════════════════════════════════════════════


def plot_forward_rates(
    interpolator: YieldCurveInterpolator,
    title: str = "Instantaneous Forward Rates",
    forward_horizon: float = 0.25,
) -> go.Figure:
    """
    Forwards implicites de courte durée + zero rate en overlay.
    """
    fig = go.Figure()

    # Grille pour forwards
    t_grid = np.linspace(
        interpolator.maturities[0],
        interpolator.maturities[-1] - forward_horizon,
        200,
    )

    f_grid = np.array(
        [interpolator.forward_rate(t, t + forward_horizon) for t in t_grid]
    )

    # Forwards
    horizon_label = f"{int(forward_horizon * 12)}M"
    fig.add_trace(
        go.Scatter(
            x=t_grid,
            y=f_grid * 100,
            mode="lines",
            name=f"{horizon_label} forwards",
            line=dict(color=COLORS["primary"], width=2.5),
            hovertemplate=(
                "<b>Start: %{x:.2f}Y</b><br>Forward: %{y:.4f}%<br><extra></extra>"
            ),
        )
    )

    # Zero rate en référence (dashed)
    y_grid = interpolator.zero_rate_curve(t_grid)
    fig.add_trace(
        go.Scatter(
            x=t_grid,
            y=y_grid * 100,
            mode="lines",
            name="Zero rate (reference)",
            line=dict(color=COLORS["accent"], width=1.5, dash="dash"),
            opacity=0.7,
            hovertemplate=(
                "<b>%{x:.2f}Y</b><br>Zero rate: %{y:.4f}%<br><extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(
            title="Start date (years)",
            range=[0, interpolator.maturities[-1] * 1.05],
        ),
        yaxis=dict(title="Rate (%)"),
        height=450,
        legend=dict(
            yanchor="bottom",
            y=0.02,
            xanchor="right",
            x=0.98,
        ),
    )

    return apply_template(fig)


# ═══════════════════════════════════════════════════════════
#  GRILLE COMBINÉE — 2×2 avec make_subplots
# ═══════════════════════════════════════════════════════════


def plot_curves_grid(
    maturities: np.ndarray,
    rates: np.ndarray,
    interpolator: YieldCurveInterpolator,
    suptitle: str = "Yield Curve Dashboard",
) -> go.Figure:
    """
    Grille 2×2 avec les 4 plots de courbes.
    Layout adapté au dashboard Streamlit (full-width).
    """
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Par Swap Rates",
            "Zero Rates",
            "Discount Factors",
            "Forward Rates",
        ),
        horizontal_spacing=0.1,
        vertical_spacing=0.15,
    )

    # ── (1,1) Par rates ──────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=maturities,
            y=rates * 100,
            mode="lines+markers",
            line=dict(color=COLORS["primary"], width=2.5),
            marker=dict(size=8, color=COLORS["primary"]),
            name="Par rates",
            showlegend=False,
            hovertemplate="%{x:.2f}Y: %{y:.4f}%<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # ── (1,2) Zero rates ─────────────────────────────
    t_grid = _make_smooth_grid(interpolator.maturities)
    y_grid = interpolator.zero_rate_curve(t_grid)

    fig.add_trace(
        go.Scatter(
            x=t_grid,
            y=y_grid * 100,
            mode="lines",
            line=dict(color=COLORS["primary"], width=2.5),
            name="Zero rate",
            showlegend=False,
            hovertemplate="%{x:.2f}Y: %{y:.4f}%<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=interpolator.maturities,
            y=interpolator.zero_rates * 100,
            mode="markers",
            marker=dict(
                size=9, color=COLORS["accent"], line=dict(color="white", width=1.5)
            ),
            name="Nodes",
            showlegend=False,
            hovertemplate="%{x:.2f}Y (node): %{y:.4f}%<extra></extra>",
        ),
        row=1,
        col=2,
    )

    # ── (2,1) Discount factors ───────────────────────
    z_grid = np.array([interpolator.discount_factor(t) for t in t_grid])

    fig.add_trace(
        go.Scatter(
            x=t_grid,
            y=z_grid,
            mode="lines",
            line=dict(color=COLORS["primary"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(31, 78, 121, 0.08)",
            name="Z(0, T)",
            showlegend=False,
            hovertemplate="%{x:.2f}Y: %{y:.6f}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=interpolator.maturities,
            y=interpolator.discount_factors,
            mode="markers",
            marker=dict(
                size=9, color=COLORS["accent"], line=dict(color="white", width=1.5)
            ),
            name="Nodes DF",
            showlegend=False,
            hovertemplate="%{x:.2f}Y (node): %{y:.6f}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    # ── (2,2) Forward rates ──────────────────────────
    forward_horizon = 0.25
    t_grid_fwd = np.linspace(
        interpolator.maturities[0],
        interpolator.maturities[-1] - forward_horizon,
        200,
    )
    f_grid = np.array(
        [interpolator.forward_rate(t, t + forward_horizon) for t in t_grid_fwd]
    )

    fig.add_trace(
        go.Scatter(
            x=t_grid_fwd,
            y=f_grid * 100,
            mode="lines",
            line=dict(color=COLORS["primary"], width=2.5),
            name="3M fwd",
            showlegend=False,
            hovertemplate="Start %{x:.2f}Y: %{y:.4f}%<extra></extra>",
        ),
        row=2,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=t_grid_fwd,
            y=interpolator.zero_rate_curve(t_grid_fwd) * 100,
            mode="lines",
            line=dict(color=COLORS["accent"], width=1.5, dash="dash"),
            name="Zero ref",
            showlegend=False,
            opacity=0.7,
            hovertemplate="%{x:.2f}Y: %{y:.4f}%<extra></extra>",
        ),
        row=2,
        col=2,
    )

    # ── Axes labels ──────────────────────────────────
    fig.update_xaxes(title_text="Maturity (years)", row=1, col=1)
    fig.update_xaxes(title_text="Maturity (years)", row=1, col=2)
    fig.update_xaxes(title_text="Maturity (years)", row=2, col=1)
    fig.update_xaxes(title_text="Start date (years)", row=2, col=2)

    fig.update_yaxes(title_text="Rate (%)", row=1, col=1)
    fig.update_yaxes(title_text="Zero rate (%)", row=1, col=2)
    fig.update_yaxes(title_text="Discount factor", row=2, col=1)
    fig.update_yaxes(title_text="Rate (%)", row=2, col=2)

    # ── Layout global ────────────────────────────────
    fig.update_layout(
        title=dict(
            text=suptitle,
            font=dict(size=18),
            x=0.5,
            xanchor="center",
        ),
        height=800,
        showlegend=False,
    )

    return apply_template(fig)
