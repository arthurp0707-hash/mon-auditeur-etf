"""
Resolution de ticker (robustesse des questions mal formulees).

Deux strategies, dans l'ordre :
  1. Dictionnaire de correspondances (fiable, deterministe) : "etf monde",
     "msci world", "iwda", "cw8", les fautes de frappe courantes.
  2. yf.Lookup (API structuree par type d'instrument) en secours.
Si rien ne marche, retourne (None, None) : l'agent refusera honnetement.
"""
import yfinance as yf


# Correspondances manuelles : le plus fiable pour les cas frequents.
# Cle = texte cherche (minuscule), valeur = (ticker Yahoo, nom lisible).
_CORRESPONDANCES = {
    "qqq": ("QQQ", "Invesco QQQ Trust"),
    "spy": ("SPY", "SPDR S&P 500 ETF"),
    "iwda": ("IWDA.AS", "iShares Core MSCI World"),
    "swda": ("SWDA.L", "iShares Core MSCI World (LSE)"),
    "cw8": ("CW8.PA", "Amundi MSCI World"),
    "amundi": ("CW8.PA", "Amundi MSCI World"),
    "world": ("IWDA.AS", "iShares Core MSCI World"),
    "msci world": ("IWDA.AS", "iShares Core MSCI World"),
    "etf monde": ("IWDA.AS", "iShares Core MSCI World"),
    "monde": ("IWDA.AS", "iShares Core MSCI World"),
    "s&p": ("SPY", "SPDR S&P 500 ETF"),
    "sp500": ("SPY", "SPDR S&P 500 ETF"),
    "nasdaq": ("QQQ", "Invesco QQQ Trust"),
}


def resoudre_ticker(texte):
    """
    Cherche un ETF a partir d'un texte libre.
    Retourne (ticker, nom) ou (None, None).
    """
    if not texte or not texte.strip():
        return None, None

    bas = texte.lower().strip()

    # 1. Priorite aux tickers explicites (cw8, iwda, swda, qqq, spy),
    #    car "Amundi MSCI World" contient "msci world" mais doit donner CW8.
    tickers_explicites = ["cw8", "iwda", "swda", "qqq", "spy"]
    for t in tickers_explicites:
        if t in bas:
            return _CORRESPONDANCES[t]

    # 2. Puis les noms generiques (etf monde, msci world...), par longueur
    for cle in sorted(_CORRESPONDANCES, key=len, reverse=True):
        if cle in bas:
            return _CORRESPONDANCES[cle]

    # 2. Secours : yf.Lookup (API structuree par type)
    try:
        lookup = yf.Lookup(texte)
        etfs = lookup.get_etf(count=5)
        if etfs is not None and not etfs.empty:
            # La premiere ligne est le meilleur match
            symbol = etfs.index[0]
            nom = etfs.iloc[0].get("name", "") if hasattr(etfs.iloc[0], "get") else ""
            if symbol:
                return str(symbol), str(nom)
    except Exception:
        pass

    return None, None
