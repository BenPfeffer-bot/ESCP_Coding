"""
data_feed.py — Live Yield Data Feed via yfinance
=================================================
Polling des Treasury yields CBOE via Yahoo Finance.

Tickers:
    ^IRX  → 13-week T-bill
    ^FVX  → 5Y T-notes yield
    ^TNX  → 10Y T-notes yield
    ^TYX  → 30Y T-bonds yield

IMPORTANT: CBOE indices are quoted at 10× the yield.

TODO: Implémenter les méthodes marquées TODO.
"""

import numpy as np
import yfinance as yf
import time
from datetime import datetime
from typing import Dict, Optional, Callable


class YieldDataFeed:
    """
    Live Treasury yield feed via yfinance polling.
    
    Usage:
        feed = YieldDataFeed()
        yields = feed.fetch_snapshot()
        mats, rates = feed.to_bootstrap_inputs(yields)
        dfs = bootstrap_discount_factors(mats, rates)
    """
    
    TICKER_MAP = {
        "^IRX": 0.25,   # 13-week T-Bill (13/52)
        "^FVX": 5.0,    # 5Y Note
        "^TNX": 10.0,   # 10Y Note
        "^TYX": 30.0,   # 30Y Bond
    }
    
    CBOE_MULTIPLIER = 10.0  # CBOE quotes at 10× yield
    
    def __init__(self):
        self.tickers = list(self.TICKER_MAP.keys())
        self.maturities = list(self.TICKER_MAP.values())
        self.last_update = None
        self.last_yields = None
    
    def fetch_snapshot(self) -> Dict[float, float]:
        """
        TODO: Fetch latest yield for each ticker.
        Returns {maturity_years: yield_decimal}
        """
        raise NotImplementedError("TODO")
    
    def fetch_historical(self, period="3mo", interval="1d") -> dict:
        """TODO: Fetch historical yields."""
        raise NotImplementedError("TODO")
    
    def to_bootstrap_inputs(self, yields: Dict[float, float]) -> tuple:
        """
        TODO: Convert yields dict to (maturities_array, rates_array)
        compatible with bootstrap_discount_factors().
        """
        raise NotImplementedError("TODO")
    
    def start_live(self, callback: Callable, interval: int = 30,
                   max_iterations: Optional[int] = None):
        """TODO: Start polling loop with callback on each update."""
        raise NotImplementedError("TODO")


if __name__ == "__main__":
    feed = YieldDataFeed()
    yields = feed.fetch_snapshot()
    print("Current yields:", yields)