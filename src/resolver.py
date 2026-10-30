"""
Resolution de ticker et de theme (robustesse des questions mal formulees).

Trois strategies :
  1. Dictionnaire de correspondances (fiable, deterministe) : "qqq", "etf monde",
     "amundi", les fautes de frappe courantes.
  2. Resolution de secteur Yahoo Finance (11 secteurs GICS) : "tech", "energie",
     "sante"... -> top ETF du secteur via yfinance.
  3. Dictionnaire de themes specifiques (chine, petrole, semi...) avec des
     tickers verifies.
Si rien ne marche, retourne None : l'agent refusera honnetement.
"""
import yfinance as yf


# --- Correspondances ticker explicite ---
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


# --- Themes specifiques (tickers verifies) ---
_THEMES = {
    "chine": ["ICHD.AS", "FXI", "MCHI"],
    "chinois": ["ICHD.AS", "FXI", "MCHI"],
    "petrole": ["XLE", "XOP", "USO"],
    "petrol": ["XLE", "XOP", "USO"],
    "oil": ["XLE", "XOP", "USO"],
    "semi": ["SMH", "SOXX"],
    "puces": ["SMH", "SOXX"],
    "ia": ["QQQ", "ARTY", "VGT"],
    "intelligence": ["QQQ", "ARTY", "VGT"],
}


# --- Les 11 secteurs Yahoo (GICS) ---
_SECTEURS_YAHOO = {
    "basic materials": "basic-materials",
    "materiaux": "basic-materials",
    "communication": "communication-services",
    "consumer cyclical": "consumer-cyclical",
    "consommation cyclique": "consumer-cyclical",
    "consumer defensive": "consumer-defensive",
    "consommation defensive": "consumer-defensive",
    "energy": "energy",
    "energie": "energy",
    "financial": "financial-services",
    "finance": "financial-services",
    "healthcare": "healthcare",
    "sante": "healthcare",
    "industrials": "industrials",
    "industriel": "industrials",
    "real estate": "real-estate",
    "immobilier": "real-estate",
    "technology": "technology",
    "tech": "technology",
    "technologie": "technology",
    "utilities": "utilities",
    "services publics": "utilities",
}


# --- Fallback si yfinance echoue ---
_FALLBACK_SECTEUR = {
    "technology": ["QQQ", "VGT", "ARTY"],
    "energy": ["XLE", "XOP", "USO"],
    "healthcare": ["XLV", "IBB", "XBI"],
    "financial-services": ["XLF", "KBE", "KRE"],
    "industrials": ["XLI", "XAR", "ITA"],
    "consumer-cyclical": ["XLY", "XRT"],
    "consumer-defensive": ["XLP"],
    "utilities": ["XLU"],
    "real-estate": ["XLRE"],
    "basic-materials": ["XLB"],
    "communication-services": ["XLC", "VOX"],
}


def resoudre_ticker(texte):
    """Cherche un ETF a partir d'un texte libre. Retourne (ticker, nom) ou (None, None)."""
    if not texte or not texte.strip():
        return None, None
    bas = texte.lower().strip()

    # 1. Tickers explicites prioritaires
    for t in ["cw8", "iwda", "swda", "qqq", "spy", "amundi"]:
        if t in bas:
            return _CORRESPONDANCES[t]

    # 2. Noms generiques (par longueur decroissante)
    for cle in sorted(_CORRESPONDANCES, key=len, reverse=True):
        if cle in bas:
            return _CORRESPONDANCES[cle]

    # 3. Secours : yf.Lookup borne dans le temps
    try:
        import concurrent.futures
        def _lookup():
            return yf.Lookup(texte).get_etf(count=5)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            etfs = ex.submit(_lookup).result(timeout=5)
        if etfs is not None and not etfs.empty:
            symbol = etfs.index[0]
            return str(symbol), ""
    except Exception:
        pass

    return None, None


def resoudre_theme(texte):
    """Retourne une liste de tickers pour un theme specifique, ou None."""
    bas = texte.lower()
    for theme, tickers in _THEMES.items():
        if theme in bas:
            return tickers
    return None


def resoudre_secteur(texte):
    """Detecte un secteur Yahoo (tech, energie, sante...). Retourne le nom ou None."""
    bas = texte.lower()
    for cle, secteur in _SECTEURS_YAHOO.items():
        if cle in bas:
            return secteur
    return None


def top_etfs_secteur(secteur):
    """Recupere les top ETF d'un secteur Yahoo. Retourne une liste de tickers."""
    try:
        s = yf.Sector(secteur)
        top = s.top_etfs
        if top is not None and not top.empty:
            return list(top.index)[:5]
    except Exception:
        pass
    return _FALLBACK_SECTEUR.get(secteur, [])
