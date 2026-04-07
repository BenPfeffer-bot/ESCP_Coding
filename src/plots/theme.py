"""
theme.py — Charte graphique commune à tous les plots.

Centralise les couleurs, fonts et styles matplotlib pour garantir
la cohérence visuelle sur l'ensemble du projet.
"""

import matplotlib.pyplot as plt
from cycler import cycler


# ═══════════════════════════════════════════════════════════
#  PALETTE DE COULEURS
# ═══════════════════════════════════════════════════════════

COLORS = {
    # Couleurs principales (sobres, professionnelles)
    "primary": "#1F4E79",  # Bleu profond — courbes principales
    "secondary": "#2E75B6",  # Bleu clair — courbes secondaires
    "accent": "#C00000",  # Rouge — annotations, alertes
    "neutral": "#595959",  # Gris foncé — texte, axes
    "light": "#D9D9D9",  # Gris clair — gridlines
    # Couleurs sémantiques pour les sensibilités
    "positive": "#2E7D32",  # Vert — gains, KR-DV01 positif
    "negative": "#C62828",  # Rouge foncé — pertes, KR-DV01 négatif
    "neutral_bar": "#9E9E9E",  # Gris — neutralité
    # Couleurs pour overlays multi-courbes (par méthode d'interpolation)
    "linear": "#FF9800",  # Orange
    "cubic": "#1F4E79",  # Bleu profond (= primary)
    "log_linear": "#7B1FA2",  # Violet
    # Couleurs pour comparaison de devises
    "usd": "#B22234",  # Rouge USA
    "eur": "#003399",  # Bleu UE
    # Background
    "bg": "#FFFFFF",  # Blanc — fond principal
    "bg_alt": "#F5F5F5",  # Gris très clair — fond panels
}


# ═══════════════════════════════════════════════════════════
#  STYLE GLOBAL
# ═══════════════════════════════════════════════════════════


def apply_style():
    """
    Applique le style commun à tous les plots matplotlib.
    À appeler une fois au début d'un script ou notebook.
    """
    plt.rcParams.update(
        {
            # Figure
            "figure.figsize": (10, 6),
            "figure.dpi": 100,
            "figure.facecolor": COLORS["bg"],
            "savefig.dpi": 150,
            "savefig.facecolor": COLORS["bg"],
            "savefig.bbox": "tight",
            # Axes
            "axes.facecolor": COLORS["bg"],
            "axes.edgecolor": COLORS["neutral"],
            "axes.labelcolor": COLORS["neutral"],
            "axes.titlecolor": COLORS["neutral"],
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "axes.axisbelow": True,  # Grid derrière les courbes
            "axes.spines.top": False,
            "axes.spines.right": False,
            # Grid
            "grid.color": COLORS["light"],
            "grid.linewidth": 0.6,
            "grid.linestyle": "-",
            "grid.alpha": 0.7,
            # Ticks
            "xtick.color": COLORS["neutral"],
            "ytick.color": COLORS["neutral"],
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "xtick.direction": "out",
            "ytick.direction": "out",
            # Lines
            "lines.linewidth": 2.0,
            "lines.markersize": 6,
            # Legend
            "legend.frameon": True,
            "legend.framealpha": 0.95,
            "legend.edgecolor": COLORS["light"],
            "legend.fontsize": 10,
            "legend.loc": "best",
            # Font
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
            "font.size": 10,
            # Color cycle pour les multi-line plots
            "axes.prop_cycle": cycler(
                color=[
                    COLORS["primary"],
                    COLORS["accent"],
                    COLORS["positive"],
                    COLORS["secondary"],
                    COLORS["log_linear"],
                ]
            ),
        }
    )


# ═══════════════════════════════════════════════════════════
#  HELPERS DE FORMATAGE
# ═══════════════════════════════════════════════════════════


def format_pct(rate: float, decimals: int = 2) -> str:
    """Formate un taux décimal en pourcentage. Ex: 0.0441 → '4.41%'."""
    return f"{rate * 100:.{decimals}f}%"


def format_bp(rate_diff: float, decimals: int = 1) -> str:
    """Formate une différence de taux en bps. Ex: 0.00045 → '+4.5 bp'."""
    bps = rate_diff * 10000
    sign = "+" if bps >= 0 else ""
    return f"{sign}{bps:.{decimals}f} bp"


def format_money(amount: float, currency: str = "EUR") -> str:
    """Formate un montant. Ex: 1234567.89 → '€1,234,568'."""
    symbols = {"EUR": "€", "USD": "$"}
    sym = symbols.get(currency, currency + " ")
    return f"{sym}{amount:,.0f}"
