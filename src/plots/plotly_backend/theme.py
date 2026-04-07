"""
theme.py — Charte graphique Plotly commune.

Miroir de src/plots/theme.py mais pour Plotly.
Définit un template qu'on applique à chaque figure pour garantir
la cohérence visuelle.
"""

import plotly.graph_objects as go
import plotly.io as pio


# ═══════════════════════════════════════════════════════════
#  PALETTE DE COULEURS (identique à matplotlib/theme.py)
# ═══════════════════════════════════════════════════════════

COLORS = {
    # Couleurs principales
    "primary": "#1F4E79",
    "secondary": "#2E75B6",
    "accent": "#C00000",
    "neutral": "#595959",
    "light": "#D9D9D9",
    # Sensibilités
    "positive": "#2E7D32",
    "negative": "#C62828",
    "neutral_bar": "#9E9E9E",
    # Méthodes d'interpolation
    "linear": "#FF9800",
    "cubic": "#1F4E79",
    "log_linear": "#7B1FA2",
    # Devises
    "usd": "#B22234",
    "eur": "#003399",
    # Backgrounds
    "bg": "#FFFFFF",
    "bg_alt": "#F5F5F5",
}


# ═══════════════════════════════════════════════════════════
#  TEMPLATE PLOTLY
# ═══════════════════════════════════════════════════════════

PLOTLY_TEMPLATE = go.layout.Template(
    layout=dict(
        # Fond
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        # Font global
        font=dict(
            family="DejaVu Sans, Helvetica, Arial, sans-serif",
            size=12,
            color=COLORS["neutral"],
        ),
        # Titre
        title=dict(
            font=dict(size=16, color=COLORS["neutral"]),
            x=0.5,
            xanchor="center",
            pad=dict(t=15, b=10),
        ),
        # Axes
        xaxis=dict(
            gridcolor=COLORS["light"],
            gridwidth=1,
            zerolinecolor=COLORS["neutral"],
            zerolinewidth=1,
            linecolor=COLORS["neutral"],
            linewidth=1,
            tickfont=dict(size=11, color=COLORS["neutral"]),
            title=dict(font=dict(size=12, color=COLORS["neutral"])),
            showline=True,
            mirror=False,
        ),
        yaxis=dict(
            gridcolor=COLORS["light"],
            gridwidth=1,
            zerolinecolor=COLORS["neutral"],
            zerolinewidth=1,
            linecolor=COLORS["neutral"],
            linewidth=1,
            tickfont=dict(size=11, color=COLORS["neutral"]),
            title=dict(font=dict(size=12, color=COLORS["neutral"])),
            showline=True,
            mirror=False,
        ),
        # Legend
        legend=dict(
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor=COLORS["light"],
            borderwidth=1,
            font=dict(size=11, color=COLORS["neutral"]),
        ),
        # Marges
        margin=dict(l=70, r=40, t=70, b=70),
        # Hover
        hoverlabel=dict(
            bgcolor=COLORS["bg_alt"],
            bordercolor=COLORS["primary"],
            font=dict(size=12, family="monospace"),
        ),
        # Color palette pour multi-traces
        colorway=[
            COLORS["primary"],
            COLORS["accent"],
            COLORS["positive"],
            COLORS["secondary"],
            COLORS["log_linear"],
        ],
    )
)


def apply_template(fig: go.Figure) -> go.Figure:
    """
    Applique le template du projet à une figure Plotly.
    À appeler dans chaque fonction plot après création de la figure.

    Args:
        fig: figure Plotly à styler

    Returns:
        La même figure avec le template appliqué
    """
    fig.update_layout(template=PLOTLY_TEMPLATE)
    return fig


# Enregistrement global du template (optionnel mais pratique)
pio.templates["rates_project"] = PLOTLY_TEMPLATE


# ═══════════════════════════════════════════════════════════
#  HELPERS (identiques à matplotlib/theme.py)
# ═══════════════════════════════════════════════════════════


def format_pct(rate: float, decimals: int = 2) -> str:
    """Formate un taux décimal en pourcentage."""
    return f"{rate * 100:.{decimals}f}%"


def format_bp(rate_diff: float, decimals: int = 1) -> str:
    """Formate une différence en bps."""
    bps = rate_diff * 10000
    sign = "+" if bps >= 0 else ""
    return f"{sign}{bps:.{decimals}f} bp"


def format_money(amount: float, currency: str = "EUR") -> str:
    """Formate un montant."""
    symbols = {"EUR": "€", "USD": "$"}
    sym = symbols.get(currency, currency + " ")
    return f"{sym}{amount:,.0f}"
