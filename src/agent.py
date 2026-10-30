"""
Agent MonAuditeur ETF (assemblage des briques).

Pipeline pour chaque question :
  1. charge le profil investisseur (brique 5)
  2. choisit un outil : heuristique de code d'abord, LLM en secours (brique 1)
  3. execute l'outil -> chiffre(s) trace(s)
  4. demande au LLM de rediger une reponse a partir de ce chiffre
  5. la barriere verifie que tous les chiffres cites sont traces (brique 3)
  6. retourne {question, reponse, chiffres, verdict, trace}
"""
import json
import re

import requests

from src.barrier import verifier_reponse
from src.config import OLLAMA_MODEL, OLLAMA_NUM_CTX, OLLAMA_URL
from src.memoire import charger_profil
from src.tools import compute_metric, classer_etfs, meilleur_secteur
from src.resolver import (
    resoudre_ticker, resoudre_theme, resoudre_secteur, top_etfs_secteur,
)

NUM_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def _ask(prompt):
    """Appel brut au LLM, sans thinking, court."""
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_ctx": OLLAMA_NUM_CTX, "num_predict": 120},
            "think": False,
        }, timeout=60)
        return r.json().get("response", "").strip()
    except Exception as e:
        return "[modele muet: %s]" % e


def _choisir_outil(question):
    """
    Choisit l'outil. Regle de code d'abord, LLM en secours.

    1. Resoudre le ticker (QQQ, SPY, IWDA.AS, CW8.PA... meme mal ecrit).
    2. Detecter la metrique dans la question.
    3. Cas special "meilleur ETF monde" -> classement.
    4. Si ticker + metrique -> compute_metric (heuristique).
    Sinon -> demander au LLM (peu fiable sur un 4B, mais on garde la trace).
    """
    q = question.lower()

    # 1. Ticker : cas connus en dur, puis resoudre_ticker
    ticker = None
    for t in ("qqq", "spy"):
        if t in q:
            ticker = t.upper()
            break
    if ticker is None:
        t_resolu, _ = resoudre_ticker(question)
        if t_resolu:
            ticker = t_resolu

    # 2. Metrique
    metric = None
    if any(w in q for w in ("rendement", "performance", "cagr", "annualise",
                            "fait +", "fait -", "a fait", "gagne", "perdu")):
        metric = "rendement_annualise"
    elif "rendem" in q or "rendemen" in q:
        metric = "rendement_annualise"
    elif any(w in q for w in ("volatil", "risque", "variation")):
        metric = "volatilite"
    elif any(w in q for w in ("prix", "cours", "cloture")) or "dernier prix" in q:
        metric = "prix_dernier"
    if metric is None and "%" in q:
        metric = "rendement_annualise"

    # 3. Cas speciaux : classement, secteur, panier
    intention_classement = (
        "meilleur" in q or "top " in q or "performant" in q
        or "performe" in q or "quel etf" in q or "quelle etf" in q
    )
    if intention_classement and ("etf" in q or "investir" in q):
        annees = _extraire_annees(q)
        # 3a. Question sur le SECTEUR (pas le ticker)
        if "secteur" in q:
            return {"outil": "meilleur_secteur", "annees": annees,
                    "source": "heuristique-secteur-global"}
        # 3b. Secteur Yahoo ? (tech, energie, sante...)
        secteur = resoudre_secteur(q)
        if secteur:
            tickers = top_etfs_secteur(secteur)
            if tickers:
                return {"outil": "classer_etfs",
                        "tickers": tickers,
                        "metric": metric or "rendement_annualise",
                        "annees": annees,
                        "top_n": _extraire_top_n(q),
                        "source": "heuristique-secteur",
                        "secteur": secteur}
        # 3c. Theme specifique ? (chine, petrole, semi...)
        tickers_theme = resoudre_theme(q)
        if tickers_theme:
            return {"outil": "classer_etfs",
                    "tickers": tickers_theme,
                    "metric": metric or "rendement_annualise",
                    "annees": annees,
                    "top_n": _extraire_top_n(q),
                    "source": "heuristique-theme"}
        # 3d. Pas de theme -> panier par defaut
        panier_defaut = ["QQQ", "SPY", "IWDA.AS", "CW8.PA", "VGT", "XLE", "XLV", "XLF", "XLI", "XLY", "XLU", "XLRE"]
        return {"outil": "classer_etfs",
                "tickers": panier_defaut,
                "metric": metric or "rendement_annualise",
                "annees": annees,
                "top_n": _extraire_top_n(q),
                "source": "heuristique-panier"}


    # 4. Ticker + metrique -> compute_metric
    if ticker and metric:
        return {"outil": "compute_metric", "ticker": ticker, "metric": metric,
                "source": "heuristique"}

    # 5. Secours : LLM
    prompt = (
        "Tu es un agent qui ne calcule jamais. Choisis UN outil parmi : "
        "compute_metric(ticker, metric) avec metric parmi "
        "rendement_annualise, volatilite, prix_dernier ; "
        "ou aucun si la question n'est pas calculable. "
        "Tickers disponibles : QQQ, SPY, IWDA.AS, CW8.PA. "
        "Question : " + question + " "
        "Reponds UNIQUEMENT par un JSON."
    )
    raw = _ask(prompt)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {"outil": "aucun", "raison": "heuristique et LLM muets"}
    try:
        choix = json.loads(m.group(0))
        if "outil" not in choix:
            choix = {"outil": "aucun", "raison": "cle 'outil' absente",
                     "brut": choix}
        choix["source"] = "llm"
        return choix
    except json.JSONDecodeError:
        return {"outil": "aucun", "raison": "JSON invalide"}


def _extraire_top_n(texte):
    """Extrait N de 'top N' (defaut: 5)."""
    m = re.search(r"top\s*(\d+)", texte.lower())
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return 5


def _extraire_annees(texte):
    """Extrait une periode en annees (ex: '3 ans', '2 dernieres annees')."""
    t = texte.lower()
    m = re.search(r"(\d+)\s*(?:ans?|annees?)", t)
    if not m:
        m = re.search(r"(\d+)\s*(?:derniere?s?|derniers?)", t)
    if not m:
        return None
    try:
        n = int(m.group(1))
        if 1 <= n <= 20:
            return n
    except ValueError:
        pass
    return None


def _extraire_pourcentage(texte):
    """Extrait un pourcentage explicite (ex: '+45%' -> 45.0)."""
    m = re.search(r"([-+]?\d+(?:[.,]\d+)?)\s*%", texte)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _rediger(question, chiffre, metric, ticker):
    """Demande au LLM de rediger une phrase qui cite UNIQUEMENT ce chiffre."""
    prompt = (
        "Redige une phrase courte en francais qui repond a la question en "
        "citant exactement le chiffre %.2f. " % chiffre
        + "N'invente AUCUN autre chiffre. "
        + "Question : " + question
    )
    return _ask(prompt)


def repondre(question):
    """Pipeline complet. Retourne la reponse + la trace pour la soutenance."""
    trace = []
    profil = charger_profil()
    trace.append("profil charge: risque=%s, exclusions=%s"
                 % (profil["risque"], profil["exclusions"]))

    choix = _choisir_outil(question)
    trace.append("choix LLM: %s" % choix)

    # --- Cas classement ---
    if choix.get("outil") == "classer_etfs":
        try:
            classement = classer_etfs(choix["tickers"], choix["metric"],
                                      annees=choix.get("annees"))
            trace.append("outil classer_etfs: %s" % classement)
        except Exception as e:
            trace.append("classer_etfs en erreur: %s" % e)
            return {"question": question,
                    "reponse": "Impossible de classer: %s" % e,
                    "chiffres": [], "verdict": False, "trace": trace}
        if not classement:
            return {"question": question,
                    "reponse": "Aucun ETF n'a pu etre evalue.",
                    "chiffres": [], "verdict": False, "trace": trace}
        # Limiter a top_n si demande
        top_n = choix.get("top_n")
        if top_n and top_n < len(classement):
            classement = classement[:top_n]
            trace.append("limite a top %d" % top_n)
        best_t, best_v = classement[0]
        period = choix.get("annees")
        suffix = ("sur %d ans" % period) if period else "sur 5 ans"
        metric_choisie = choix.get("metric", "rendement_annualise")
        if metric_choisie == "volatilite":
            reponse_finale = (
                "Le moins volatil est %s avec %.2f%% de volatilite %s."
                % (best_t, best_v, suffix)
            )
        else:
            reponse_finale = (
                "Le meilleur est %s avec %.2f%% de rendement annualise %s."
                % (best_t, best_v, suffix)
            )
        verdict = verifier_reponse(reponse_finale, [v for _, v in classement])
        trace.append("barriere: ok=%s raison=%s" % (verdict.ok, verdict.raison))
        return {"question": question, "reponse": reponse_finale,
                "chiffres": [v for _, v in classement],
                "verdict": verdict.ok, "trace": trace}

    # --- Cas meilleur_secteur ---
    if choix.get("outil") == "meilleur_secteur":
        try:
            classement = meilleur_secteur(annees=choix.get("annees"))
            trace.append("outil meilleur_secteur: %s" % classement[:3])
        except Exception as e:
            trace.append("meilleur_secteur en erreur: %s" % e)
            return {"question": question,
                    "reponse": "Impossible de classer les secteurs: %s" % e,
                    "chiffres": [], "verdict": False, "trace": trace}
        if not classement:
            return {"question": question,
                    "reponse": "Aucun secteur n'a pu etre evalue.",
                    "chiffres": [], "verdict": False, "trace": trace}
        best_s, best_t, best_v = classement[0]
        period = choix.get("annees")
        suffix = ("sur %d ans" % period) if period else "sur 5 ans"
        reponse_finale = (
            "Le meilleur secteur est %s (via %s) avec %.2f%% de rendement %s."
            % (best_s, best_t, best_v, suffix)
        )
        verdict = verifier_reponse(reponse_finale, [v for _, _, v in classement])
        trace.append("barriere: ok=%s raison=%s" % (verdict.ok, verdict.raison))
        return {"question": question, "reponse": reponse_finale,
                "chiffres": [v for _, _, v in classement],
                "verdict": verdict.ok, "trace": trace}

    # --- Cas pas d'outil ---
    if choix.get("outil") != "compute_metric":
        reponse = "Je ne peux pas conclure sans calcul sur les donnees."
        verdict = verifier_reponse(reponse, [])
        trace.append("barriere: %s" % verdict.raison)
        return {"question": question, "reponse": reponse, "chiffres": [],
                "verdict": verdict.ok, "trace": trace}

    # --- Cas compute_metric ---
    ticker = choix.get("ticker", "QQQ")
    metric = choix.get("metric", "rendement_annualise")

    try:
        chiffre = compute_metric(ticker, metric)
        trace.append("outil compute_metric(%s,%s) = %.4f"
                     % (ticker, metric, chiffre))
    except Exception as e:
        trace.append("outil en erreur: %s" % e)
        return {"question": question,
                "reponse": "Impossible de calculer: %s" % e,
                "chiffres": [], "verdict": False, "trace": trace}

    # Comparaison en code si un pourcentage est propose
    pct_propose = _extraire_pourcentage(question)
    if pct_propose is not None:
        ecart = abs(chiffre - pct_propose)
        if ecart <= 0.5:
            reponse_finale = (
                "Oui : le chiffre propose (%.2f%%) correspond au calcul (%.2f%%)."
                % (pct_propose, chiffre)
            )
        else:
            reponse_finale = (
                "Non : la question propose %.2f%%, mais le calcul donne %.2f%%."
                % (pct_propose, chiffre)
            )
        trace.append("comparaison construite en code: propose=%.2f calcule=%.2f"
                     % (pct_propose, chiffre))
        verdict = verifier_reponse(reponse_finale, [chiffre, pct_propose])
        trace.append("barriere: ok=%s raison=%s" % (verdict.ok, verdict.raison))
        return {"question": question, "reponse": reponse_finale,
                "chiffres": [chiffre], "verdict": verdict.ok, "trace": trace}

    # Sinon, redaction par le LLM
    reponse_llm = _rediger(question, chiffre, metric, ticker)
    trace.append("redaction LLM: %s" % reponse_llm[:150])

    verdict = verifier_reponse(reponse_llm, [chiffre])
    trace.append("barriere: ok=%s raison=%s" % (verdict.ok, verdict.raison))

    if not verdict.ok:
        reponse_finale = "Le resultat est %.2f." % chiffre
        verdict = verifier_reponse(reponse_finale, [chiffre])
        trace.append("repli honnete: %s" % verdict.raison)
    else:
        reponse_finale = reponse_llm

    return {"question": question, "reponse": reponse_finale,
            "chiffres": [chiffre], "verdict": verdict.ok, "trace": trace}
