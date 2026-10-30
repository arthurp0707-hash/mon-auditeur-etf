"""
Télécharge les cours d'ETF via yfinance et les met en cache CSV.

Usage :
    python data/download.py                 # tickers par défaut (QQQ, SPY)
    python data/download.py QQQ SPY VTI     # tickers explicites
    python data/download.py --force         # ignore le cache et retélécharge
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

# Permet d'importer src/ quand on lance depuis la racine
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import CACHE_DIR, DEFAULT_INTERVAL, DEFAULT_PERIOD, DEFAULT_TICKERS  # noqa: E402


def cache_path(ticker: str) -> Path:
    return CACHE_DIR / f"{ticker}_{DEFAULT_PERIOD}_{DEFAULT_INTERVAL}.csv"


def download_one(ticker: str, period: str = DEFAULT_PERIOD,
                 interval: str = DEFAULT_INTERVAL, force: bool = False) -> Path:
    """Télécharge un ticker et l'écrit en CSV. Retourne le chemin du cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = cache_path(ticker)
    if out.exists() and not force:
        print(f"[cache] {ticker} déjà présent -> {out.name}")
        return out

    print(f"[download] {ticker} ({period}, {interval}) ...")
    df = yf.download(ticker, period=period, interval=interval,
                     auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise RuntimeError(f"Aucune donnée renvoyée pour {ticker}")

    # yfinance récent renvoie des colonnes MultiIndex (ticker, field).
    # On aplatit pour avoir des colonnes simples : Open, High, Low, Close, Volume.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index.name = "Date"
    df.to_csv(out)
    print(f"[ok] {ticker}: {len(df)} lignes -> {out}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Télécharge les cours d'ETF en cache CSV.")
    parser.add_argument("tickers", nargs="*", default=DEFAULT_TICKERS,
                        help="Tickers Yahoo Finance (défaut: QQQ SPY)")
    parser.add_argument("--force", action="store_true", help="Ignore le cache")
    args = parser.parse_args()

    tickers = args.tickers or DEFAULT_TICKERS
    for t in tickers:
        try:
            download_one(t.upper(), force=args.force)
        except Exception as e:
            print(f"[erreur] {t}: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
