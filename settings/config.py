"""
config.py — Constantes de configuration du projet.

Contient :
  - Secrets chargés depuis .env (clés API)
  - Mappings statiques (tickers, séries FRED)
  - Paramètres opérationnels (intervalles de polling, etc.)

Aucun path ici — voir paths.py pour ça.
"""

import os
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")

if FRED_API_KEY is None:
    import warnings

    warnings.warn(
        "FRED_API_KEY non défini dans .env — le gap-fill FRED sera désactivé. "
        "Crée un fichier .env avec: FRED_API_KEY=ta_cle_ici"
    )

# yfinance — CBOE Treasury indices
# Mapping {ticker: maturité_en_années}
TICKERS_YFINANCE = {
    "^IRX": 0.25,  # 13-week T-Bill
    "^FVX": 5.0,  # 5Y Note
    "^TNX": 10.0,  # 10Y Note
    "^TYX": 30.0,  # 30Y Bond
}

# CBOE_MULTIPLIER = 10.0  # Diviseur pour la conversion CBOE quote → yield %

# FRED — Treasury Constant Maturity Rates
# Mapping {maturité_en_années: series_id}
FREDAPI_SERIES = {
    0.5: "DGS6MO",
    1.0: "DGS1",
    2.0: "DGS2",
    3.0: "DGS3",
    7.0: "DGS7",
    20.0: "DGS20",
}

POLL_INTERVAL = 30  # secondes entre deux fetch en mode live

USE_CACHE_BY_DEFAULT = True

# Pricing & Risk
DEFAULT_INTERPOLATION_METHOD = "cubic_spline"  # ou "linear"
DEFAULT_BUMP_SIZE = 0.0001  # 1 bp en décimal, pour le calcul du DV01
