import numpy as np
import plotly.graph_objects as go
from datetime import date
from typing import Optional, List

from src.plots.plotly_backend.theme import (
    COLORS,
    apply_template,
)


# ═══════════════════════════════════════════════════════════
#  PLOT — HISTORICAL MATURITY
# ═══════════════════════════════════════════════════════════


def plot_historical_maturity(
    dates: List[date],
    rates: List[float],
    maturity_label: str,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Série temporelle d'une maturité spécifique.
    Gère les cas "vide" et "1 seul point" avec un placeholder.
    """
    fig = go.Figure()

    # ── Cas 1 : aucune donnée ──────────────────────────
    if not dates:
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            text=(
                f"<i>No historical data for {maturity_label}</i><br><br>"
                f"<i>Run more snapshots to build history</i>"
            ),
            showarrow=False,
            font=dict(size=13, color=COLORS["neutral"]),
            bgcolor=COLORS["bg_alt"],
            bordercolor=COLORS["light"],
            borderwidth=1,
            borderpad=20,
            xanchor="center",
            yanchor="middle",
        )
        fig.update_layout(
            title=title or f"{maturity_label} — Historical",
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return apply_template(fig)

    # ── Cas 2 : un seul point ──────────────────────────
    if len(dates) < 2:
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            text=(
                f"<i>Only 1 snapshot available</i><br><br>"
                f"<b>Date:</b> {dates[0]}<br>"
                f"<b>Rate:</b> {rates[0] * 100:.3f}%<br><br>"
                f"<i>Accumulate more snapshots<br>to see historical evolution</i>"
            ),
            showarrow=False,
            font=dict(size=12, color=COLORS["neutral"]),
            bgcolor=COLORS["bg_alt"],
            bordercolor=COLORS["light"],
            borderwidth=1,
            borderpad=20,
            xanchor="center",
            yanchor="middle",
            align="center",
        )
        fig.update_layout(
            title=title or f"{maturity_label} — Historical",
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return apply_template(fig)

    # ── Cas 3 : plot normal ────────────────────────────
    rates_pct = np.array(rates) * 100

    # Série temporelle avec remplissage
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=rates_pct,
            mode="lines+markers",
            name=maturity_label,
            line=dict(color=COLORS["primary"], width=2),
            marker=dict(size=5, color=COLORS["primary"]),
            fill="tozeroy",
            fillcolor="rgba(31, 78, 121, 0.08)",
            hovertemplate=(
                "<b>%{x|%Y-%m-%d}</b><br>Rate: %{y:.4f}%<br><extra></extra>"
            ),
        )
    )

    # Stats en annotation
    stats_text = (
        f"<b>Min:</b>  {rates_pct.min():.2f}%<br>"
        f"<b>Max:</b>  {rates_pct.max():.2f}%<br>"
        f"<b>Mean:</b> {rates_pct.mean():.2f}%<br>"
        f"<b>σ:</b>    {rates_pct.std():.3f}%"
    )
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.98,
        y=0.98,
        text=stats_text,
        showarrow=False,
        font=dict(size=11, family="monospace", color=COLORS["neutral"]),
        bgcolor=COLORS["bg_alt"],
        bordercolor=COLORS["light"],
        borderwidth=1,
        borderpad=8,
        xanchor="right",
        yanchor="top",
        align="left",
    )

    fig.update_layout(
        title=title or f"{maturity_label} Treasury Yield — Historical",
        xaxis=dict(title="Date", tickformat="%Y-%m-%d"),
        yaxis=dict(title="Rate (%)"),
        height=500,
        showlegend=False,
    )

    # Range y cohérente pour ne pas zoomer trop sur les petites variations
    y_min = rates_pct.min() - 0.1
    y_max = rates_pct.max() + 0.1
    fig.update_yaxes(range=[y_min, y_max])

    return apply_template(fig)


# ═══════════════════════════════════════════════════════════
#  PLOT — CURVE EVOLUTION
# ═══════════════════════════════════════════════════════════


def plot_curve_evolution(
    curves_history: List[dict],
    title: str = "Yield Curve Evolution",
    max_curves: int = 5,
) -> go.Figure:
    """
    Overlay de plusieurs courbes à différentes dates.
    La plus récente est mise en avant (plus épaisse, opacité max).
    """
    fig = go.Figure()

    if not curves_history:
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            text="<i>No historical curves available</i>",
            showarrow=False,
            font=dict(size=13, color=COLORS["neutral"]),
            bgcolor=COLORS["bg_alt"],
            bordercolor=COLORS["light"],
            borderwidth=1,
            borderpad=20,
        )
        fig.update_layout(
            title=title,
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return apply_template(fig)

    # Garder les N dernières courbes
    curves = curves_history[:max_curves]
    n = len(curves)

    # Gradient de bleus : plus récent = plus foncé
    # On reverse pour que le plus récent soit ajouté en dernier (au-dessus)
    for i, curve in enumerate(reversed(curves)):
        idx_from_latest = n - 1 - i  # 0 pour plus récent, n-1 pour plus ancien
        is_latest = idx_from_latest == 0

        mats = np.array(curve["maturities"])
        rates_pct = np.array(curve["rates"]) * 100

        # Opacité et largeur selon ancienneté
        opacity = 1.0 if is_latest else 0.5 + 0.1 * i
        width = 3.0 if is_latest else 1.5

        # Couleur : gradient de bleu clair vers primary
        if is_latest:
            color = COLORS["primary"]
        else:
            # Plus ancien = plus clair
            shade = int(180 - idx_from_latest * 20)
            color = f"rgb({shade}, {shade + 20}, {min(255, shade + 60)})"

        fig.add_trace(
            go.Scatter(
                x=mats,
                y=rates_pct,
                mode="lines+markers" if is_latest else "lines",
                name=curve["date"],
                line=dict(color=color, width=width),
                marker=dict(size=6, color=color) if is_latest else dict(),
                opacity=opacity,
                hovertemplate=(
                    f"<b>{curve['date']}</b><br>"
                    "Maturity: %{x:.2f}Y<br>"
                    "Rate: %{y:.4f}%<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=title,
        xaxis=dict(title="Maturity (years)"),
        yaxis=dict(title="Rate (%)"),
        height=500,
        legend=dict(
            title="Date",
            yanchor="bottom",
            y=0.02,
            xanchor="right",
            x=0.98,
        ),
    )

    return apply_template(fig)
