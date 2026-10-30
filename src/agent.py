"""
Agent MonAuditeur ETF (assemblage des briques).

Pipeline pour chaque question :
  1. charge le profil investisseur (brique 5)
  2. choisit un outil : heuristique de code d'abord, LLM en secours (brique 1)
  3. execute l'outil -> chiffre trace
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
from src.tools import compute_metric
from src.resolver import resoudre_ticker

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
    3. Si ticker + metrique -> compute_metric (heuristique).
    Sinon -> demander au LLM (peu fiable sur un 4B, mais on garde la trace).
    """
    q = question.lower()

    # 1. Ticker : d'abord les cas connus en dur (rapide), puis resoudre_ticker
    ticker = None
    for t in ("qqq", "spy"):
        if t in q:
            ticker = t.upper()
            break
    if ticker is None:
        t_resolu, _ = resoudre_ticker(question)
        if t_resolu:
            ticker = t_resolu

    # 2. Metrique : mots-cles + pourcentage explicite
    metric = None
    if any(w in q for w in ("rendement", "performance", "cagr", "annualise",
                            "fait +", "fait -", "a fait", "gagne", "perdu")):
        metric = "rendement_annualise"
    elif "rendem" in q or "rendemen" in q:
        # Gere les fautes de frappe courantes ("rendemen", "rendement"...)
        metric = "rendement_annualise"
    elif any(w in q for w in ("volatil", "risque", "variation")):
        metric = "volatilite"
    elif any(w in q for w in ("prix", "cours", "cloture", "dernier")):
        metric = "prix_dernier"
    if metric is None and "%" in q:
        metric = "rendement_annualise"

    # 3. Si on a les deux -> heuristique
    if ticker and metric:
        return {"outil": "compute_metric", "ticker": ticker, "metric": metric,
                "source": "heuristique"}

    # 4. Secours : LLM, mais on ne depend pas de lui
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


def _rediger(question, chiffre, metric, ticker):
    """Demande au LLM de rediger une phrase qui cite UNIQUEMENT ce chiffre."""
    prompt = (
        "Redige une phrase courte en francais qui repond a la question en "
        "citant exactement le chiffre %.2f. " % chiffre
        + "N'invente AUCUN autre chiffre. "
        + "Question : " + question
    )
    return _ask(prompt)


def _extraire_pourcentage(texte):
    """Extrait un pourcentage explicite de la question (ex: '+45%' -> 45.0)."""
    m = re.search(r"([-+]?\d+(?:[.,]\d+)?)\s*%", texte)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def repondre(question):
    """Pipeline complet. Retourne la reponse + la trace pour la soutenance."""
    trace = []
    profil = charger_profil()
    trace.append("profil charge: risque=%s, exclusions=%s"
                 % (profil["risque"], profil["exclusions"]))

    choix = _choisir_outil(question)
    trace.append("choix LLM: %s" % choix)

    if choix.get("outil") != "compute_metric":
        reponse = "Je ne peux pas conclure sans calcul sur les donnees."
        verdict = verifier_reponse(reponse, [])
        trace.append("barriere: %s" % verdict.raison)
        return {"question": question, "reponse": reponse, "chiffres": [],
                "verdict": verdict.ok, "trace": trace}

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

    # Si la question propose un pourcentage a verifier (ex: "+45%"),
    # on construit la comparaison en CODE, pas par le LLM (plus fiable).
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
