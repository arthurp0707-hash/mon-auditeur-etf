"""Tests R2 : le cache CSV est présent et bien formé."""
import pandas as pd
import pytest

from src.config import CACHE_DIR, DEFAULT_TICKERS


@pytest.fixture(scope="module")
def cached_files():
    """Vérifie que le cache existe (sinon on indique quoi lancer)."""
    files = {t: CACHE_DIR / f"{t}_5y_1d.csv" for t in DEFAULT_TICKERS}
    missing = [t for t, p in files.items() if not p.exists()]
    if missing:
        pytest.skip(f"Cache absent pour {missing}. Lance: python data/download.py")
    return files


def test_cache_files_exist(cached_files):
    for ticker, path in cached_files.items():
        assert path.exists(), f"{path} manquant"
        assert path.stat().st_size > 0, f"{path} vide"


def test_cache_has_expected_columns(cached_files):
    expected = {"Open", "High", "Low", "Close", "Volume"}
    for ticker, path in cached_files.items():
        df = pd.read_csv(path, index_col="Date", parse_dates=True)
        assert expected.issubset(set(df.columns)), f"{ticker}: colonnes manquantes"


def test_cache_has_enough_rows(cached_files):
    for ticker, path in cached_files.items():
        df = pd.read_csv(path, index_col="Date", parse_dates=True)
        assert len(df) > 1000, f"{ticker}: seulement {len(df)} lignes"


def test_close_prices_are_positive(cached_files):
    for ticker, path in cached_files.items():
        df = pd.read_csv(path, index_col="Date", parse_dates=True)
        assert (df["Close"] > 0).all(), f"{ticker}: prix <= 0 détecté"
