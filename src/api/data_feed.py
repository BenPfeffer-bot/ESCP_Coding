"""
Polling des Treasury yields CBOE via Yahoo Finance.

Tickers:
    ^IRX  -> 13-week T-bill
    ^FVX  -> 5Y T-notes yield
    ^TNX  -> 10Y T-notes yield
    ^TYX  -> 30Y T-bonds yield
-> à savoir les yield CBOE sont quotés 10x du yield
"""

import numpy as np
import yfinance as yf 
import time
from datetime import datetime
from typing import Dict, Optional, Callable
from fredapi import Fred

from settings import get_logger
from settings import *
class DataFeed:
    """
    On va crée une classe pour faciliter le polling des données via yfinance, même si on n'a pas les données en live on va essayer de s'en rapprocher le plus possible.
    Usage:
    -> feed: DataFeed()
    -> yields: feed.fetch_snapchot()
    -> mats, rates: feed.to_bootstrap_inputs(yields)
    """
    # On pose nos constantes (type les tickers des obligs sur différentes maturité et le facteur multiplicatif par rapport aux données CBOE)
    YFINANCE_TICKERS = {
        "^IRX": 0.25,   # 13-week T-Bill (13/52)
        "^FVX": 5.0,    # 5Y Note
        "^TNX": 10.0,   # 10Y Note
        "^TYX": 30.0,   # 30Y Bond
    }
    
    FREDAPI_SERIES = {
        "6-Month": "DGS6MO",
        "1-Year": "DGS1",
        "2-Year": "DGS2",
        "3-Year": "DGS3",
        "7-Year": "DGS7",
        "20-Year": "DGS20"
    }
    
    CBOE_MULTIPLIER = 10.0  # CBOE quotes at 10× yield

    logger = get_logger(name="data-feed")
    fred = Fred(api_key=FRED_API_KEY)
    
    def __init__(self):
        """On mets place notre init avec les charactérisques principales pour le feed des données"""
        self.tickers = list[str](self.TICKER_MAP.keys())
        self.maturities = list[float](self.TICKER_MAP.values())
        self.last_upddate = None
        self.last_yields = None

        self.logger.info("Initialized DataFeed: last_update=%s, last_yields=%s", self.last_update, self.last_yields)

    def fetch_snapshot(self) -> Dict[float, float]:
        """
        Récuperer les derniers taux disponibles pour chaque stickers.
        Output -> maturity & yield
        """
        #try:
        pass
        # 1/ def yfinance datas
        # 2/ def fredapi datas sur ce qui manque
        # 3/ def tables formatting + clean
        #  
    def yfinance_datas(self) -> Dict(float, float):
        """
        On va recup les maturités associés a la constante ticker_map
        soit 13wk/5y/10y/30y
        Output -> Dataframe ready to merge
        """

    def fredapi_datas(self, api_key=FRED_API_KEY, observation_start=None):
        """
        Fetch les derniers Treasury yields pour les maturités non couvertes par yfinance
        Retourne: dict {maturity_years: yield_decimal}
        """
        yields = {}
        for series_id, maturity in FREDAPI_SERIES.items():
            data = fred_client
    