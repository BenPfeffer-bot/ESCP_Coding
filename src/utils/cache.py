"""
Stocke chaque snapshot fetché par DataFeed pour éviter les appels API redondants.
 Schéma "long format" (tidy) : une ligne par (snapshot, maturité)

Schema:
    snapshots (snapshot_id, fetched_at, market_date, maturity, rate, source)

Usage:
    from src.utils.cache import save_snapshot, load_latest_snapshot, has_snapshot_today

    # Sauvegarder
    yields = {0.25: 0.0369, 5.0: 0.0398, ...}
    sources = {0.25: 'yfinance', 5.0: 'yfinance', ...}
    save_snapshot(yields, sources)

    # Recharger le dernier snapshot d'aujourd'hui
    result = load_latest_snapshot()
    if result is not None:
        mats, rates = result
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, date
from typing import Optional, Dict, Tuple
import numpy as np

from settings.paths import DB_FILE
from settings.logs import get_logger

logger = get_logger(name="cache")


# ═══════════════════════════════════════════════════════════
#  CONNEXION & SCHÉMA
# ═══════════════════════════════════════════════════════════


@contextmanager
def _connect():
    """
    Context manager pour la connexion SQLite.
    Garantit la fermeture même en cas d'exception.

    Usage:
        with _connect() as conn:
            conn.execute("SELECT ...")
    """
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_schema() -> None:
    """
    Crée la table snapshots et ses index si ils n'existent pas.
    Idempotent : safe à appeler à chaque démarrage.
    """
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id  INTEGER NOT NULL,
                fetched_at   TEXT NOT NULL,
                market_date  TEXT NOT NULL,
                maturity     REAL NOT NULL,
                rate         REAL NOT NULL,
                source       TEXT NOT NULL,
                PRIMARY KEY (snapshot_id, maturity)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_date 
            ON snapshots(market_date)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fetched_at 
            ON snapshots(fetched_at)
        """)
    logger.debug(f"Schema initialized at {DB_FILE}")


# Init au load du module — garantit que la table existe avant tout appel
_init_schema()


# ═══════════════════════════════════════════════════════════
#  FONCTIONS PUBLIQUES — CRITIQUES
# ═══════════════════════════════════════════════════════════


def save_snapshot(
    yields: Dict[float, float],
    sources: Dict[float, str],
    market_date: Optional[date] = None,
) -> int:
    """
    Sauvegarde un snapshot de yields dans la base.

    Args:
        yields: dict {maturity: rate_decimal}
            Ex: {0.25: 0.0369, 5.0: 0.0398, 10.0: 0.0441}
        sources: dict {maturity: 'yfinance' | 'fred'}
            Doit contenir une clé pour chaque maturité de `yields`.
        market_date: date de marché (défaut = today).

    Returns:
        snapshot_id: l'ID du snapshot créé.

    Raises:
        ValueError: si yields et sources n'ont pas les mêmes clés.
    """
    if not yields:
        raise ValueError("Cannot save empty yields dict")

    if set(yields.keys()) != set(sources.keys()):
        raise ValueError(
            f"yields and sources must have matching keys. "
            f"yields={set(yields.keys())}, sources={set(sources.keys())}"
        )

    if market_date is None:
        market_date = date.today()

    fetched_at_str = datetime.now().isoformat()
    market_date_str = market_date.isoformat()

    with _connect() as conn:
        # Génère le prochain snapshot_id
        cursor = conn.execute("SELECT COALESCE(MAX(snapshot_id), 0) + 1 FROM snapshots")
        snapshot_id = cursor.fetchone()[0]

        # Insert toutes les lignes du snapshot
        rows = [
            (snapshot_id, fetched_at_str, market_date_str, mat, rate, sources[mat])
            for mat, rate in sorted(yields.items())
        ]
        conn.executemany(
            """INSERT INTO snapshots 
               (snapshot_id, fetched_at, market_date, maturity, rate, source) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows,
        )

    logger.info(
        f"Saved snapshot #{snapshot_id} for {market_date_str} "
        f"({len(rows)} points, range: "
        f"{min(yields.values()) * 100:.2f}%-{max(yields.values()) * 100:.2f}%)"
    )
    return snapshot_id


def load_latest_snapshot(
    market_date: Optional[date] = None,
) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    Charge le dernier snapshot pour une date donnée.

    Si plusieurs snapshots existent pour la même date (ex: tu as run
    fetch_snapshot() plusieurs fois aujourd'hui), retourne celui avec
    le `fetched_at` le plus récent.

    Args:
        market_date: date de marché (défaut = today).

    Returns:
        (maturities, rates): tuple de np.ndarray triés par maturité,
        ou None si aucun snapshot n'existe pour cette date.
    """
    if market_date is None:
        market_date = date.today()

    market_date_str = market_date.isoformat()

    with _connect() as conn:
        cursor = conn.execute(
            """
            SELECT maturity, rate
            FROM snapshots
            WHERE snapshot_id = (
                SELECT snapshot_id
                FROM snapshots
                WHERE market_date = ?
                ORDER BY fetched_at DESC
                LIMIT 1
            )
            ORDER BY maturity ASC
        """,
            (market_date_str,),
        )
        rows = cursor.fetchall()

    if not rows:
        logger.debug(f"Cache miss for {market_date_str}")
        return None

    maturities = np.array([r[0] for r in rows])
    rates = np.array([r[1] for r in rows])

    logger.info(f"Cache hit for {market_date_str}: {len(rows)} points loaded")
    return maturities, rates


def has_snapshot_today() -> bool:
    """
    Raccourci pour vérifier si un snapshot existe pour aujourd'hui.
    Utile pour la logique cache-first dans data_feed.fetch_snapshot().

    Returns:
        True si au moins un snapshot existe pour today, False sinon.
    """
    today_str = date.today().isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM snapshots WHERE market_date = ? LIMIT 1", (today_str,)
        )
        return cursor.fetchone() is not None
