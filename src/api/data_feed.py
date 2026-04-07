"""
Polling des Treasury yields CBOE via Yahoo Finance.

Tickers:
    ^IRX  -> 13-week T-bill
    ^FVX  -> 5Y T-notes yield
    ^TNX  -> 10Y T-notes yield
    ^TYX  -> 30Y T-bonds yield
"""

import time
import traceback
import numpy as np
import yfinance as yf
from datetime import datetime
from typing import Dict
from fredapi import Fred

from settings import (
    get_logger,
    FRED_API_KEY,
    TICKERS_YFINANCE,
    POLL_INTERVAL,
    FREDAPI_SERIES,
)
from src.utils.cache import save_snapshot, load_latest_snapshot


class DataFeed:
    """
    Polling des Treasury yields via yfinance + FRED, avec cache SQLite.

    Usage:
        feed = DataFeed()                  # cache activé par défaut
        feed = DataFeed(use_cache=False)   # force le refresh à chaque fetch
        mats, rates = feed.fetch_snapshot()
        mats, rates = feed.fetch_snapshot(force_refresh=True)  # bypass ponctuel
    """

    def __init__(self, use_cache: bool = True):
        """
        Args:
            use_cache: défaut pour fetch_snapshot. Si True, utilise le cache SQLite.
        """
        self.use_cache = use_cache
        self.logger = get_logger(name="data-feed")
        self.tickers = list(TICKERS_YFINANCE.keys())
        self.maturities = list(TICKERS_YFINANCE.values())
        self.last_update = None
        self.last_yields = None
        self.fred = Fred(api_key=FRED_API_KEY)
        self._fred_cache = {}
        self._fred_cache_date = None
        self.logger.info(
            f"DataFeed initialisé: tickers={self.tickers}, use_cache={use_cache}"
        )

    def yfinance_datas(self) -> Dict[float, float]:
        """Fetch yields des 4 CBOE tickers via yfinance."""
        yf_data = yf.download(
            self.tickers,
            period="5d",
            interval="1d",
            progress=False,
        )

        if yf_data.empty:
            self.logger.warning("yfinance: aucune donnée reçue")
            return {}

        latest = yf_data["Close"].iloc[-1]

        yields_dict = {}
        for ticker, mat in zip(self.tickers, self.maturities):
            raw = latest[ticker]
            if np.isnan(raw):
                self.logger.warning(f"{ticker} = NaN, skipped")
                continue
            yields_dict[mat] = raw / 100  # → décimal

        self.logger.info(f"yfinance yields: {yields_dict}")
        return yields_dict

    def fredapi_datas(self, observation_start=None):
        """Fetch les maturités intermédiaires via FRED, avec cache daily."""
        today = datetime.now().date()
        if self._fred_cache_date == today and self._fred_cache:
            self.logger.debug("FRED cache hit (in-memory)")
            return self._fred_cache.copy()

        yields = {}
        failed = []

        for maturity, series_id in FREDAPI_SERIES.items():
            try:
                data = self.fred.get_series(
                    series_id, observation_start=observation_start
                )
                latest = data.dropna().iloc[-1]
                yields[maturity] = latest / 100
                self.logger.debug(
                    f"FRED {series_id} (mat={maturity}Y): ok → {latest / 100:.4f}"
                )
            except Exception as e:
                failed.append(series_id)
                self.logger.warning(
                    f"FRED {series_id} (mat={maturity}Y) échec "
                    f"[{type(e).__name__}]: {e}\n"
                    f"{traceback.format_exc().strip()}"
                )

        n_ok, n_total = len(yields), len(FREDAPI_SERIES)
        if failed:
            self.logger.warning(
                f"FRED: {n_ok}/{n_total} séries récupérées — échecs: {failed}"
            )
        else:
            self.logger.info(f"FRED yields ({n_ok}/{n_total}): {yields}")

        self._fred_cache = yields
        self._fred_cache_date = today
        return yields

    def merge_datas(self, yf_yields: Dict, fred_yields: Dict) -> tuple:
        """Fusionne yfinance + FRED et retourne (maturites, rates) trié."""
        try:
            merged = {**fred_yields, **yf_yields}

            for mat, rate in merged.items():
                if rate <= 0:
                    self.logger.warning(f"Yield négatif: {mat}Y = {rate * 100:.3f}%")
                if rate > 0.20:
                    self.logger.error(
                        f"Yield suspect >20%: {mat}Y = {rate * 100:.1f}% — check CBOE conversion"
                    )

            sorted_mats = sorted(merged.keys())
            maturites = np.array(sorted_mats)
            rates = np.array([merged[m] for m in sorted_mats])
        except Exception as e:
            self.logger.error(f"Erreur merge: {e}")
            raise

        self.logger.info(
            f"Merge OK — {len(maturites)} points: {list(zip(maturites, rates))}"
        )
        return maturites, rates

    def fetch_snapshot(self, force_refresh: bool = False) -> tuple:
        """
        Fetch un snapshot complet de la courbe.

        Stratégie cache-first :
          1. Si use_cache=True et force_refresh=False : essaie SQLite
          2. Si cache miss : fetch via yfinance + FRED
          3. Save en cache pour les runs suivants

        Args:
            force_refresh: bypass le cache pour forcer un fetch live.

        Returns:
            (maturites, rates) : np.ndarray triés par maturité.
        """
        # ── Étape 1 : Cache check ──────────────────────────
        if self.use_cache and not force_refresh:
            cached = load_latest_snapshot()
            if cached is not None:
                mats, rates = cached
                self.last_update = datetime.now()
                self.last_yields = dict(zip(mats, rates))
                self.logger.info(f"[CACHE] Snapshot loaded — {len(mats)} maturités")
                return mats, rates
            self.logger.info("[CACHE] Miss — fetching from APIs")
        elif force_refresh:
            self.logger.info("[CACHE] Bypass (force_refresh=True)")

        # ── Étape 2 : Fetch live ───────────────────────────
        yf_yields = self.yfinance_datas()
        fred_yields = self.fredapi_datas()
        maturites, rates = self.merge_datas(yf_yields, fred_yields)

        self.last_update = datetime.now()
        self.last_yields = dict(zip(maturites, rates))

        # ── Étape 3 : Validation de complétude ─────────────
        n_expected = len(TICKERS_YFINANCE) + len(FREDAPI_SERIES)
        n_got = len(maturites)
        if n_got < n_expected:
            missing = sorted(
                set(list(TICKERS_YFINANCE.values()) + list(FREDAPI_SERIES.keys()))
                - set(maturites.tolist())
            )
            self.logger.warning(
                f"[{self.last_update:%H:%M:%S}] Courbe dégradée: "
                f"{n_got}/{n_expected} points — manquantes: {missing}"
            )
        else:
            self.logger.info(
                f"[{self.last_update:%H:%M:%S}] Snapshot OK — {n_got} maturités"
            )

        # ── Étape 4 : Save en cache ────────────────────────
        if self.use_cache:
            try:
                yields_dict = dict(zip(maturites, rates))
                sources = {
                    float(m): "yfinance" if m in yf_yields else "fred"
                    for m in maturites
                }
                save_snapshot(yields_dict, sources)
            except Exception as e:
                self.logger.warning(f"Cache save failed: {e}")
                # Pas critique : on continue

        return maturites, rates

    def start_live(self, callback=None, max_iterations=None):
        """Polling loop : fetch + callback à chaque tick."""
        it = 0
        while max_iterations is None or it < max_iterations:
            try:
                # En live, on force_refresh pour avoir les vraies dernières données
                mats, rates = self.fetch_snapshot(force_refresh=True)
                if callback and mats is not None:
                    callback(mats, rates)
            except Exception as e:
                self.logger.error(f"Erreur: {e}")
            it += 1
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    datafeed = DataFeed()
    mats, rates = datafeed.fetch_snapshot()
    print(f"\nFetched {len(mats)} points:")
    for m, r in zip(mats, rates):
        print(f"  {m:6.2f}Y : {r * 100:.4f}%")
