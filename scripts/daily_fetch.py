"""
Script de fetch quotidien automatisé.
Lancé par GitHub Actions tous les jours ouvrés à 22h UTC, ou
manuellement via :
    python -m scripts.daily_fetch

Responsabilités :
  1. Fetch un snapshot live via DataFeed (force_refresh=True)
  2. Vérifier que le fetch a produit des données valides
  3. Logger les statistiques pour l'interface GitHub Actions
  4. Retourner un exit code propre pour que le workflow détecte les échecs
"""

import sys
from datetime import datetime

from src.api.data_feed import DataFeed
from src.utils.cache import get_db_stats
from settings.logs import get_logger


logger = get_logger(name="daily-fetch")


def main() -> int:
    """
    Point d'entrée du script.

    Returns:
        0 si succès, 1 si échec
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"Daily fetch started at {start_time.isoformat()}")
    logger.info("=" * 60)

    try:
        # ── 1. Fetch live data ────────────────────────
        logger.info("Fetching market data (force_refresh=True)...")
        feed = DataFeed(use_cache=True)
        mats, rates = feed.fetch_snapshot(force_refresh=True)

        # ── 2. Validation basique ─────────────────────
        if mats is None or len(mats) == 0:
            logger.error("❌ Fetch returned no data")
            return 1

        if len(mats) < 5:
            logger.warning(
                f"⚠️  Only {len(mats)} maturities fetched — "
                f"expected ~10. Curve will be degraded."
            )

        # ── 3. Log des résultats ──────────────────────
        logger.info(f"✅ Fetched {len(mats)} points:")
        for m, r in zip(mats, rates):
            mat_label = f"{int(m * 12):>3}M" if m < 1 else f"{int(m):>3}Y"
            logger.info(f"   {mat_label} : {r * 100:.4f}%")

        # ── 4. Stats DB ───────────────────────────────
        stats = get_db_stats()
        logger.info("")
        logger.info("Database state after fetch:")
        logger.info(f"   Total snapshots : {stats['nb_snapshots']}")
        logger.info(f"   Distinct dates  : {stats['nb_dates']}")
        logger.info(f"   Date range      : {stats['date_range']}")
        logger.info(f"   Total rows      : {stats['nb_rows']}")

        # ── 5. Done ───────────────────────────────────
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("")
        logger.info(f"✅ Daily fetch completed in {elapsed:.1f}s")
        return 0

    except Exception as e:
        logger.error(f"❌ Daily fetch failed: {type(e).__name__}: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
