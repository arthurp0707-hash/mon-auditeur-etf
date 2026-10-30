"""
Outils appelables par le LLM (brique 1).

Chaque fonction est un outil : elle lit le cache CSV et renvoie un resultat
chiffre. Le LLM ne calcule rien lui-meme ; il demande a un outil, et la
barriere (brique 3) verifie ensuite que les chiffres de la reponse viennent
d'ici.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import CACHE_DIR

TRADING_DAYS = 252


def _load(ticker):
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


def compute_metric(ticker, metric, annees=None):
    """
    Calcule une metrique sur l'historique du ticker.

    metric : "rendement_annualise" | "volatilite" | "prix_dernier"
    annees : si fourni, ne garde que les N dernieres annees (ex: 3).
    Retourne un float. C'est CETTE valeur qui pourra apparaitre dans la reponse.
    """
    df = _load(ticker)
    if annees is not None and annees > 0:
        fin = df.index.max()
        debut = fin - pd.DateOffset(years=annees)
        df = df[df.index >= debut]
    closes = df["Close"].astype(float)

    if metric == "prix_dernier":
        return float(closes.iloc[-1])

    if metric == "rendement_annualise":
        debut_v, fin_v = closes.iloc[0], closes.iloc[-1]
        n_annees = len(closes) / TRADING_DAYS
        if debut_v <= 0 or n_annees <= 0:
            raise ValueError("Donnees insuffisantes pour le rendement")
        return float((fin_v / debut_v) ** (1 / n_annees) - 1) * 100

    if metric == "volatilite":
        rets = closes.pct_change().dropna()
        return float(rets.std() * np.sqrt(TRADING_DAYS) * 100)

    raise ValueError(f"Metrique inconnue : {metric}")


def get_price(ticker, date):
    """Prix de cloture a une date (format YYYY-MM-DD)."""
    df = _load(ticker)
    try:
        return float(df.loc[date, "Close"])
    except KeyError:
        raise ValueError(f"Pas de cotation pour {ticker} le {date}")


def classer_etfs(tickers, metric="rendement_annualise", annees=None):
    """
    Classe plusieurs ETF selon une metrique. Retourne une liste triee
    [(ticker, valeur), ...] du meilleur au moins bon.
    """
    resultats = []
    for t in tickers:
        try:
            v = compute_metric(t, metric, annees=annees)
            resultats.append((t, v))
        except Exception:
            continue
    resultats.sort(key=lambda x: x[1], reverse=True)
    return resultats
