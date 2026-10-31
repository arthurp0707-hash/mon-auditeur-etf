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
    "ia": ['VGT', 'QQQ', 'ARTY', 'XAIX.DE', 'IART.L', 'XAIX.L', 'AIAI.L'],
    "intelligence": ['VGT', 'QQQ', 'ARTY', 'XAIX.DE', 'IART.L', 'XAIX.L', 'AIAI.L'],
    "technologie": ['QQQ', 'VGT', 'ARTY', 'XLK', 'SMH', 'SOXX', 'IGV', 'FTEC', 'XAIX.DE', 'IART.L'],
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


# Normalisation des fautes de frappe courantes (partagee avec llm_parser)
_NORMALISATION = {
    "gaze": "gaz",
    "petrol": "petrole",
    "santé": "sante",
    "medicall": "medical",
    "technologi": "technologie",
    "immobillier": "immobilier",
}


# Dictionnaire de secours verifie manuellement (dernier recours).
# Utilise en priorite pour les themes connus, car yf.Lookup renvoie parfois
# des actions au lieu d'ETF.
_FALLBACK_THEMES = {
    "gaz": ["UNG", "UNL", "FCG"],
    "gaze": ["UNG", "UNL", "FCG"],
    "natural gas": ["UNG", "UNL", "FCG"],
    "petrole": ["USO", "XLE", "XOP"],
    "petrol": ["USO", "XLE", "XOP"],
    "crude oil": ["USO", "XLE", "XOP"],
    "oil": ["USO", "XLE", "XOP"],
    "or": ["GLD", "IAU", "GDX"],
    "gold": ["GLD", "IAU", "GDX"],
    "eau": ["PHO", "FIW", "CGW"],
    "water": ["PHO", "FIW", "CGW"],
    "sante": ["XLV", "IBB", "XBI"],
    "medical": ["XLV", "IBB", "XBI"],
    "healthcare": ["XLV", "IBB", "XBI"],
    "technologie": ["QQQ", "VGT", "XLK"],
    "tech": ["QQQ", "VGT", "XLK"],
    "technology": ["QQQ", "VGT", "XLK"],
    "chine": ["ICHD.AS", "FXI", "MCHI"],
    "china": ["ICHD.AS", "FXI", "MCHI"],
    "foret": ["WOOD", "WOOE.AS", "WOOD.L"],
    "forest": ["WOOD", "WOOE.AS", "WOOD.L"],
    "immobilier": ["XLRE", "VNQ", "IYR"],
    "real estate": ["XLRE", "VNQ", "IYR"],
    "energie": ["XLE", "XOP", "USO"],
    "energy": ["XLE", "XOP", "USO"],
    "defense": ["ITA", "XAR", "PPA"],
    "cybersecurite": ["HACK", "CIBR", "BUG"],
    "robotique": ["BOTZ", "ROBO", "IRBO"],
    "china technology": ["CQQQ", "KWEB", "CHIK"],
    "chinese technology": ["CQQQ", "KWEB", "CHIK"],
    "chine technologie": ["CQQQ", "KWEB", "CHIK"],
    "chinois technologie": ["CQQQ", "KWEB", "CHIK"],
}


def screener_etfs(region=None, sector=None, category=None, limit=10):
    """
    Screener ETF natif via yfinance.ETFQuery (pas de dictionnaire).
    Combine region + sector + category avec AND.
    Ex: screener_etfs(region="cn", sector="Technology") -> ETF chinois tech.
    """
    try:
        from yfinance import ETFQuery, screen
        conditions = []
        if region:
            conditions.append(ETFQuery('eq', ['region', region.lower()]))
        if sector:
            conditions.append(ETFQuery('eq', ['sector', sector]))
        if category:
            conditions.append(ETFQuery('eq', ['category', category]))
        if not conditions:
            return None
        if len(conditions) == 1:
            q = conditions[0]
        else:
            q = ETFQuery('and', conditions)
        resultats = screen(q, size=limit)
        if resultats is not None and not resultats.empty:
            return list(resultats.index)
    except Exception:
        pass
    return None


def resoudre_theme(texte):
    """
    Cherche des ETF correspondant a un theme via yfinance Lookup.
    Traduit le theme francais en anglais, cherche, puis filtre les tickers
    valides (qui se telechargent et ont assez de lignes).
    Fallback sur un mini-dictionnaire uniquement si Yahoo ne trouve rien.
    """
    if not texte or not texte.strip():
        return None

    # 1. Normaliser les fautes de frappe
    bas = texte.lower().strip()
    if bas in _NORMALISATION:
        bas = _NORMALISATION[bas]

    # 2. Traduire en anglais
    try:
        from src.llm_parser import traduire_theme
        theme_en = traduire_theme(bas)
    except Exception:
        theme_en = bas

    # 3. Chercher sur Yahoo (20 resultats pour avoir de la marge)
    candidats = []
    for mot in (theme_en, bas):
        try:
            lookup = yf.Lookup(mot)
            etfs = lookup.get_etf(count=20)
            if etfs is not None and not etfs.empty:
                candidats = list(etfs.index)
                break
        except Exception:
            pass

    # 4. Filtrer : garder les tickers qui se telechargent et ont assez de lignes
    valides = []
    for t in candidats:
        try:
            from src.tools import _load
            df = _load(t)
            if len(df) >= 100:
                valides.append(t)
            if len(valides) >= 5:
                break
        except Exception:
            continue

    if valides:
        return valides

    # 5. Dernier recours : mini-dictionnaire verifie (themes tres courants)
    if bas in _FALLBACK_THEMES:
        return _FALLBACK_THEMES[bas]

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
