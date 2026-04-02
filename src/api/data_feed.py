"""
Polling des Treasury yields CBOE via Yahoo Finance.

Tickers:
    ^IRX  -> 13-week T-bill
    ^FVX  -> 5Y T-notes yield
    ^TNX  -> 10Y T-notes yield
    ^TYX  -> 30Y T-bonds yield
-> à savoir les yield CBOE sont quotés 10x du yield
"""

import time
import numpy as np
import yfinance as yf
from datetime import datetime
from typing import Dict
from fredapi import Fred

from settings import get_logger, FRED_API_KEY, TICKERS_YFINANCE, POLL_INTERVAL, FREDAPI_SERIES

class DataFeed:
    """
    On va crée une classe pour faciliter le polling des données via yfinance, même si on n'a pas les données en live on va essayer de s'en rapprocher le plus possible.
    Usage:
    -> feed: DataFeed()
    -> yields: feed.fetch_snapchot()
    -> mats, rates: feed.to_bootstrap_inputs(yields)
    """

    CBOE_MULTIPLIER = 10.0  # CBOE quotes at 10× yield

    def __init__(self):
        """On mets place notre init avec les charactérisques principales pour le feed des données"""
        # Logger d'instance — pour s'assurer que le handler n'est pas partagé/global
        self.logger = get_logger(name="data-feed")
        self.tickers = list(TICKERS_YFINANCE.keys())
        self.maturities = list(TICKERS_YFINANCE.values())
        self.last_update = None
        self.last_yields = None
        self.fred = Fred(api_key=FRED_API_KEY)
        self.logger.info(f"DataFeed initialisé: tickers={self.tickers}")

    def yfinance_datas(self) -> Dict[float, float]:
        """
        On va recup les maturités associés a la constante ticker_map
        soit 13wk/5y/10y/30y
        Output -> Dataframe ready to merge
        """
        yf_data = yf.download(
            self.tickers,
            period="1d",
            interval="1m",
            progress=False,
        )

        if yf_data.empty:
            self.logger.warning("yfinance: aucune donnée reçue")
            return {}

        latest = yf_data["Close"].iloc[-1]

        yields_dict = {}
        for ticker, mat in zip(self.tickers, self.maturities):
            raw = latest[ticker]
            yields_dict[mat] = (raw / self.CBOE_MULTIPLIER) / 100  # → décimal
        
        self.logger.info(f"yfinance yields: {yields_dict}")
        return yields_dict

    def fredapi_datas(self, observation_start=None) -> Dict[float, float]:
        """
        Fetch les derniers Treasury yields pour les maturités non couvertes par yfinance.
        Retourne: dict {maturité_années: yield_décimal}
        """
        yields = {}
        for maturity, series_id in FREDAPI_SERIES.items():
            try:
                data = self.fred.get_series(series_id, observation_start=observation_start)
                latest = data.dropna().iloc[-1]
                yields[maturity] = latest / 100
            except Exception as e:
                self.logger.warning(f"FRED {series_id} (mat={maturity}): {e}")

        self.logger.info(f"FRED yields: {yields}")
        return yields

    def merge_datas(self, yf_yields: Dict, fred_yields: Dict) -> tuple:
        """
        Fusionne les deux sources et trie par maturité croissante.
        yf_yields écrase fred_yields en cas de conflit (CBOE prioritaire).
        Retourne: (maturites: np.ndarray, rates: np.ndarray)
        """
        # je pose qd mm un debugging sur le merge car 
        # par expérience souvent y'a des problèmes dessus
        try:
            # on pose les datas dans un dict, 
            # on s'assures de bien prendre toutes les valeurs
            merged = {**fred_yields, **yf_yields}

            # Simple tri des maturités
            sorted_mats = sorted(merged.keys())
            # on pose nos deux composants - 1D
            maturites = np.array(sorted_mats)
            # petite boucle pour récuperer les taux de la table consolidés
            rates = np.array([merged[m] for m in sorted_mats])
        except Exception as e:
            self.logger.error(f"Erreur merge: {e}")
            raise

        self.logger.info(f"Merge OK — {len(maturites)} points: {list(zip(maturites, rates))}")
        return maturites, rates

    def fetch_snapshot(self) -> tuple:
        """
        Simule un environnement live en boucle infinie
        À chaque itération: fetch yfinance + FRED, merge, mise à jour de l'état.
        Retourne le dernier (maturites, rates) à l'interruption (KeyboardInterrupt).
        """
        maturites, rates = None, None
        while True:
            try:
                yf_yields = self.yfinance_datas()
                fred_yields = self.fredapi_datas()
                maturites, rates = self.merge_datas(yf_yields, fred_yields)
                self.last_update = datetime.now()
                self.last_yields = dict(zip(maturites, rates))
                self.logger.info(
                    f"[{self.last_update:%H:%M:%S}] Snapshot OK — {len(maturites)} maturités"
                )
            except Exception as e:
                self.logger.error(f"Erreur snapshot: {e}")

            time.sleep(POLL_INTERVAL)

datafeed = DataFeed()
datafeed.fetch_snapshot()
