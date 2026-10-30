"""
Outils appelables par le LLM (brique 1).

Chaque fonction est un outil : elle lit le cache CSV et renvoie un résultat
chiffré. Le LLM ne calcule rien lui-même ; il demande à un outil, et la
barrière (brique 3) vérifie ensuite que les chiffres de la réponse viennent
d'ici.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import CACHE_DIR

TRADING_DAYS = 252


def _load(ticker: str) -> pd.DataFrame:
    """
    Charge le CSV en cache pour un ticker.
    Si le cache est absent, tente un telechargement a la volee (cache
    dynamique), puis relit. Erreur claire si le telechargement echoue.
    """
    path = CACHE_DIR / f"{ticker}_5y_1d.csv"
    if not path.exists():
        try:
            import yfinance as yf
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            df = yf.download(ticker, period="5y", interval="1d",
                             auto_adjust=True, progress=False)
            if df is None or df.empty:
                raise RuntimeError(f"aucune donnee pour {ticker}")
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.index.name = "Date"
            df.to_csv(path)
        except Exception as e:
            raise FileNotFoundError(
                f"Cache absent pour {ticker} et telechargement impossible ({e}). "
                f"Lance: python data/download.py {ticker}"
            )
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    return df.sort_index()


def compute_metric(ticker: str, metric: str) -> float:
    """
    Calcule une métrique sur l'historique complet du ticker.

    metric : "rendement_annualise" | "volatilite" | "prix_dernier"
    Retourne un float. C'est CETTE valeur qui pourra apparaître dans la réponse.
    """
    df = _load(ticker)
    closes = df["Close"].astype(float)

    if metric == "prix_dernier":
        return float(closes.iloc[-1])

    if metric == "rendement_annualise":
        debut, fin = closes.iloc[0], closes.iloc[-1]
        n_annees = len(closes) / TRADING_DAYS
        if debut <= 0 or n_annees <= 0:
            raise ValueError("Données insuffisantes pour le rendement")
        return float((fin / debut) ** (1 / n_annees) - 1) * 100  # en %

    if metric == "volatilite":
        rets = closes.pct_change().dropna()
        return float(rets.std() * np.sqrt(TRADING_DAYS) * 100)  # en %

    raise ValueError(f"Métrique inconnue : {metric}")


def get_price(ticker: str, date: str) -> float:
    """Prix de clôture à une date (format YYYY-MM-DD)."""
    df = _load(ticker)
    try:
        return float(df.loc[date, "Close"])
    except KeyError:
        raise ValueError(f"Pas de cotation pour {ticker} le {date}")


def classer_etfs(tickers, metric="rendement_annualise"):
    """
    Classe plusieurs ETF selon une metrique. Retourne une liste triee
    [(ticker, valeur), ...] du meilleur au moins bon.
    C'est ce qui permet de repondre a "quel est le meilleur ETF monde ?".
    """
    resultats = []
    for t in tickers:
        try:
            v = compute_metric(t, metric)
            resultats.append((t, v))
        except Exception:
            continue
    resultats.sort(key=lambda x: x[1], reverse=True)
    return resultats
