"""
Parseur d'intention par LLM avec structured output (Ollama format).

Le LLM comprend la question (meme mal ecrite) et retourne un JSON structure
qui decrit l'outil a appeler, le theme, la metrique, la periode, le top_n
et un eventuel filtre. Pas de liste de themes : le LLM decide.
"""
import json

import requests

from src.config import OLLAMA_MODEL, OLLAMA_NUM_CTX, OLLAMA_URL

# Schema JSON force : le LLM DOIT retourner exactement cette structure.
INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "outil": {
            "type": "string",
            "enum": ["classer_etfs", "compute_metric", "meilleur_secteur", "aucun"],
            "description": "L'outil a appeler."
        },
        "theme": {
            "type": "string",
            "description": "Theme ou secteur propose par l'utilisateur (ex: cuivre, semi-conducteurs, chine). Vide si aucun."
        },
        "theme_brut": {
            "type": "string",
            "description": "Mot exact de l'utilisateur pour le theme (ex: cuivre, or, gaz). Vide si aucun."
        },
        "metric": {
            "type": "string",
            "enum": ["rendement_annualise", "volatilite", "prix_dernier"],
            "description": "La metrique demandee."
        },
        "annees": {
            "type": "integer",
            "description": "Periode en annees (2, 3, 5...). 0 si non precise."
        },
        "top_n": {
            "type": "integer",
            "description": "Nombre de resultats demandes (ex: top 6 -> 6). 0 si non precise."
        },
        "filtre_min": {
            "type": "number",
            "description": "Filtre minimum en pourcentage (ex: rendement > 10 -> 10). 0 si aucun."
        },
        "sens": {
            "type": "string",
            "enum": ["max", "min"],
            "description": "max = le plus grand/performant ; min = le moins."
        }
    },
    "required": ["outil", "theme", "theme_brut", "metric", "annees", "top_n", "filtre_min", "sens"]
}


def _appel_llm_structure(prompt, schema):
    """Appelle Ollama avec format=schema. Retourne le JSON parse ou None."""
    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": schema,
            "options": {"num_ctx": OLLAMA_NUM_CTX, "temperature": 0},
            "think": False,
        }, timeout=60)
        content = r.json()["message"]["content"]
        return json.loads(content)
    except Exception:
        return None


def parser_intention(question, profil=None):
    """
    Comprend la question via le LLM (structured output).
    Retourne un dict {outil, theme, theme_brut, metric, annees, top_n, filtre_min, sens}.
    Fallback sur une heuristique minimale si le LLM echoue.
    """
    profil_txt = ""
    if profil:
        profil_txt = (
            f"Profil investisseur : risque={profil.get('risque', 'moyen')}, "
            f"horizon={profil.get('horizon_annees', 5)} ans, "
            f"exclusions={profil.get('exclusions', [])}. "
        )

    prompt = (
        "Tu es un parseur d'intention pour un systeme d'analyse d'ETF. "
        "Analyse la question et remplis le JSON. La question peut etre mal "
        "ecrite, avec des fautes, des synonymes. Comprends l'intention. "
        f"{profil_txt}"
        "Regles : "
        "- Si la question demande de comparer les 11 SECTEURS GLOBAUX Yahoo "
        "(quel secteur est le meilleur, quel secteur est le moins risque), "
        "outil=meilleur_secteur. "
        "- Si la question porte sur un THEME PRECIS (un metal, une matiere "
        "premiere, une technologie, un pays, un secteur specifique), "
        "outil=classer_etfs avec theme=ce theme. "
        "- Un theme precis est TOUT ce qui n'est pas un des 11 secteurs globaux "
        "Yahoo (Technology, Healthcare, Energy, Financial Services, etc.). "
        "- Exemples de themes precis : cuivre, lithium, uranium, "
        "semi-conducteurs, cyber, biotech, crypto, chine, gaz, or. "
        "- Attention : 'secteur des semi-conducteurs' est un THEME precis, "
        "pas un secteur global. "
        "- Si la question demande une metrique sur un ETF unique, "
        "outil=compute_metric. "
        "- Sinon, outil=aucun. "
        "- theme : extrais le theme/secteur. theme_brut : le mot exact. "
        "- metric : rendement_annualise (defaut), volatilite (si risque), "
        "prix_dernier (si prix/cours). "
        "- annees : extrais la periode (2, 3, 5). 0 si non precise. "
        "- top_n : extrais le nombre (top 6 -> 6). 0 si non precise. "
        "- filtre_min : extrais un filtre (rendement > 10 -> 10). 0 si aucun. "
        "- sens : max si 'meilleur/plus performant', min si 'le moins'. "
        f"Question : {question}"
    )

    resultat = _appel_llm_structure(prompt, INTENT_SCHEMA)
    if resultat:
        q = question.lower()
        # Priorite "pas risque" -> volatilite, sens min
        mots_risque = ("pas risque", "pas risqué", "faible risque",
                       "moins risque", "moins risqué", "peu risque",
                       "peu risqué", "securitaire", "prudent")
        if any(m in q for m in mots_risque):
            resultat["metric"] = "volatilite"
            resultat["sens"] = "min"
        return resultat

    # Retry une fois avec un prompt simplifie
    prompt_simple = f"Question : {question}. Reponds en JSON."
    resultat = _appel_llm_structure(prompt_simple, INTENT_SCHEMA)
    if resultat:
        return resultat

    # Fallback heuristique minimale
    q = question.lower()
    outil = "aucun"
    if any(w in q for w in ("meilleur", "top", "performant", "performe")):
        outil = "classer_etfs"
    elif "secteur" in q:
        outil = "meilleur_secteur"
    return {
        "outil": outil, "theme": "", "theme_brut": "",
        "metric": "rendement_annualise", "annees": 0, "top_n": 0,
        "filtre_min": 0, "sens": "max",
    }


# Traductions verifiees manuellement (prioritaires sur le LLM)
_TRADUCTIONS_VERIFIEES = {
    "gaz": "natural gas",
    "petrole": "oil",
    "or": "gold",
    "eau": "water",
    "foret": "forest",
    "sante": "healthcare",
    "medical": "healthcare",
    "technologie": "technology",
    "tech": "technology",
    "ia": "artificial intelligence",
    "chine": "china",
    "immobilier": "real estate",
    "energie": "energy",
    "cuivre": "copper",
    "lithium": "lithium",
    "uranium": "uranium",
    "argent": "silver",
    "platine": "platinum",
    "acier": "steel",
    "biotech": "biotech",
    "cyber": "cybersecurity",
    "crypto": "crypto",
    "space": "space",
}


def traduire_theme(theme_fr):
    """
    Traduit un theme francais en mot-cle anglais pour Yahoo Finance.
    Utilise d'abord le dictionnaire verifie, puis le LLM en secours.
    """
    if not theme_fr:
        return theme_fr
    bas = theme_fr.lower().strip()
    if bas in _TRADUCTIONS_VERIFIEES:
        return _TRADUCTIONS_VERIFIEES[bas]
    # LLM en secours
    prompt = (
        "Traduis ce theme financier francais en un mot-cle anglais court "
        "pour une recherche d'ETF Yahoo Finance. "
        "Reponds UNIQUEMENT par le mot-cle anglais, sans phrase. "
        f"Theme : {theme_fr}"
    )
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_ctx": OLLAMA_NUM_CTX, "num_predict": 20},
            "think": False,
        }, timeout=30)
        trad = r.json().get("response", "").strip().lower()
        trad = trad.strip('."\' ')
        if trad and len(trad) < 50:
            return trad
    except Exception:
        pass
    return theme_fr
