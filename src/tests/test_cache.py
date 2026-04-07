"""
test_cache.py — Test standalone du module cache.

Usage:
    python -m src.utils.test_cache

Crée un faux snapshot, le sauvegarde, le recharge, et vérifie
que les valeurs matchent. Inspecte aussi la base après les opérations.
"""

import numpy as np
from datetime import date, timedelta

from src.utils.cache import (
    save_snapshot,
    load_latest_snapshot,
    has_snapshot_today,
    _connect,
)
from settings import DB_FILE


def test_save_and_load():
    """Test basique : save → load → vérification."""
    print("\n=== Test 1 : save_snapshot + load_latest_snapshot ===")

    # Données fake mais réalistes
    fake_yields = {
        0.25: 0.0369,
        0.50: 0.0375,
        1.00: 0.0385,
        2.00: 0.0396,
        5.00: 0.0398,
        10.00: 0.0441,
        30.00: 0.0498,
    }
    fake_sources = {
        0.25: "yfinance",
        0.50: "fred",
        1.00: "fred",
        2.00: "fred",
        5.00: "yfinance",
        10.00: "yfinance",
        30.00: "yfinance",
    }

    # Save
    snapshot_id = save_snapshot(fake_yields, fake_sources)
    print(f"  ✓ Saved snapshot #{snapshot_id}")

    # Load
    result = load_latest_snapshot()
    assert result is not None, "Load returned None after save"
    mats, rates = result

    # Vérifications
    assert len(mats) == len(fake_yields), (
        f"Expected {len(fake_yields)} maturities, got {len(mats)}"
    )

    expected_mats = sorted(fake_yields.keys())
    np.testing.assert_array_equal(mats, expected_mats)

    expected_rates = np.array([fake_yields[m] for m in expected_mats])
    np.testing.assert_array_almost_equal(rates, expected_rates, decimal=10)

    print(f"  ✓ Loaded {len(mats)} points, all values match")
    print(f"  ✓ Maturities: {mats}")
    print(f"  ✓ Rates:      {rates}")


def test_has_snapshot_today():
    """Test du raccourci has_snapshot_today."""
    print("\n=== Test 2 : has_snapshot_today ===")

    has = has_snapshot_today()
    print(f"  has_snapshot_today() = {has}")
    assert has is True, "Should be True after test 1 saved a snapshot"
    print("  ✓ Returns True after save")


def test_multiple_snapshots_same_day():
    """Test que load_latest retourne bien le DERNIER snapshot du jour."""
    print("\n=== Test 3 : multiple snapshots same day ===")

    # Premier snapshot
    yields_1 = {1.0: 0.0380, 5.0: 0.0400}
    sources_1 = {1.0: "fred", 5.0: "yfinance"}
    id_1 = save_snapshot(yields_1, sources_1)

    # Second snapshot avec valeurs différentes
    import time

    time.sleep(0.01)  # Garantir un fetched_at différent
    yields_2 = {1.0: 0.0385, 5.0: 0.0405}
    sources_2 = {1.0: "fred", 5.0: "yfinance"}
    id_2 = save_snapshot(yields_2, sources_2)

    print(f"  Saved snapshot #{id_1} then #{id_2}")

    # Load doit retourner le second
    mats, rates = load_latest_snapshot()
    assert rates[0] == 0.0385, f"Expected 0.0385 (latest), got {rates[0]}"
    assert rates[1] == 0.0405, f"Expected 0.0405 (latest), got {rates[1]}"
    print(f"  ✓ load_latest_snapshot() returns the most recent values")


def test_load_nonexistent_date():
    """Test que load_latest retourne None pour une date sans snapshot."""
    print("\n=== Test 4 : load nonexistent date ===")

    # Date dans le futur lointain — aucun snapshot ne devrait exister
    future = date.today() + timedelta(days=10000)
    result = load_latest_snapshot(market_date=future)

    assert result is None, f"Expected None, got {result}"
    print(f"  ✓ Returns None for date {future}")


def test_validation_errors():
    """Test des validations d'input."""
    print("\n=== Test 5 : input validation ===")

    # Empty yields
    try:
        save_snapshot({}, {})
        assert False, "Should have raised ValueError for empty yields"
    except ValueError as e:
        print(f"  ✓ Empty yields rejected: {e}")

    # Mismatched keys
    try:
        save_snapshot({1.0: 0.04}, {2.0: "fred"})
        assert False, "Should have raised ValueError for mismatched keys"
    except ValueError as e:
        print(f"  ✓ Mismatched keys rejected: {e}")


def inspect_database():
    """Inspecte le contenu actuel de la base."""
    print("\n=== Database inspection ===")
    print(f"  DB file: {DB_FILE}")
    print(f"  Size: {DB_FILE.stat().st_size} bytes")

    with _connect() as conn:
        # Total rows
        cursor = conn.execute("SELECT COUNT(*) FROM snapshots")
        total = cursor.fetchone()[0]
        print(f"  Total rows: {total}")

        # Distinct snapshots
        cursor = conn.execute("SELECT COUNT(DISTINCT snapshot_id) FROM snapshots")
        n_snapshots = cursor.fetchone()[0]
        print(f"  Distinct snapshots: {n_snapshots}")

        # Distinct dates
        cursor = conn.execute("SELECT COUNT(DISTINCT market_date) FROM snapshots")
        n_dates = cursor.fetchone()[0]
        print(f"  Distinct market dates: {n_dates}")

        # Sources
        cursor = conn.execute("SELECT source, COUNT(*) FROM snapshots GROUP BY source")
        for source, count in cursor.fetchall():
            print(f"  Source '{source}': {count} rows")


def cleanup():
    """Optionnel : nettoie les snapshots de test."""
    print("\n=== Cleanup ===")
    response = input("Delete all test snapshots? [y/N]: ")
    if response.lower() == "y":
        with _connect() as conn:
            cursor = conn.execute("DELETE FROM snapshots")
            print(f"  Deleted {cursor.rowcount} rows")
    else:
        print("  Skipped (snapshots kept in DB)")


if __name__ == "__main__":
    print("=" * 60)
    print("  CACHE MODULE — STANDALONE TESTS")
    print("=" * 60)

    test_save_and_load()
    test_has_snapshot_today()
    test_multiple_snapshots_same_day()
    test_load_nonexistent_date()
    test_validation_errors()
    inspect_database()
    cleanup()

    print("\n" + "=" * 60)
    print("  ✅ All tests passed")
    print("=" * 60)
