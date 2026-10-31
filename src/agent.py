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


def _choisir_outil(question, profil=None):
    """
    Comprend la question via le LLM (structured output), puis resout le
    theme/secteur en tickers. Fallback heuristique si le LLM echoue.
    """
    from src.llm_parser import parser_intention
    from src.resolver import (resoudre_secteur, top_etfs_secteur,
                               resoudre_theme, resoudre_ticker)

    intent = parser_intention(question, profil)
    outil = intent.get("outil", "aucun")

    if outil == "aucun":
        return {"outil": "aucun", "raison": "intention non calculable",
                "source": "llm-parser", "intent": intent}

    if outil == "meilleur_secteur":
        annees = intent.get("annees") or None
        return {"outil": "meilleur_secteur", "annees": annees,
                "source": "llm-parser", "intent": intent}

    if outil == "compute_metric":
        # Resoudre le ticker depuis la question
        ticker, _ = resoudre_ticker(question)
        if not ticker:
            # Essayer avec le theme
            theme = intent.get("theme", "")
            if theme:
                tickers = resoudre_theme(theme)
                if tickers:
                    ticker = tickers[0]
        if not ticker:
            return {"outil": "aucun", "raison": "ticker introuvable",
                    "source": "llm-parser", "intent": intent}
        metric = intent.get("metric", "rendement_annualise")
        annees = intent.get("annees") or None
        return {"outil": "compute_metric", "ticker": ticker,
                "metric": metric, "annees": annees,
                "source": "llm-parser", "intent": intent}

    if outil == "classer_etfs":
        theme = intent.get("theme", "")
        # 1. Secteur Yahoo ?
        secteur = resoudre_secteur(theme) if theme else None
        if secteur:
            tickers = top_etfs_secteur(secteur)
            if tickers:
                return {"outil": "classer_etfs", "tickers": tickers,
                        "metric": intent.get("metric", "rendement_annualise"),
                        "annees": intent.get("annees") or None,
                        "top_n": intent.get("top_n") or 5,
                        "filtre_min": intent.get("filtre_min") or 0,
                        "sens": intent.get("sens", "max"),
                        "source": "llm-parser-secteur", "secteur": secteur,
                        "intent": intent}
        # 2. Theme specifique ?
        if theme:
            tickers = resoudre_theme(theme)
            if tickers:
                return {"outil": "classer_etfs", "tickers": tickers,
                        "metric": intent.get("metric", "rendement_annualise"),
                        "annees": intent.get("annees") or None,
                        "top_n": intent.get("top_n") or 5,
                        "filtre_min": intent.get("filtre_min") or 0,
                        "sens": intent.get("sens", "max"),
                        "source": "llm-parser-theme", "intent": intent}
        # 3. Panier par defaut
        panier = ["QQQ", "SPY", "IWDA.AS", "CW8.PA", "VGT",
                  "XLE", "XLV", "XLF", "XLI", "XLY", "XLU", "XLRE"]
        return {"outil": "classer_etfs", "tickers": panier,
                "metric": intent.get("metric", "rendement_annualise"),
                "annees": intent.get("annees") or None,
                "top_n": intent.get("top_n") or 5,
                "filtre_min": intent.get("filtre_min") or 0,
                "sens": intent.get("sens", "max"),
                "source": "llm-parser-panier", "intent": intent}

    return {"outil": "aucun", "raison": "outil inconnu", "source": "llm-parser"}


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


def _rediger(question, chiffre, metric, ticker, profil=None):
    """Demande au LLM de rediger une phrase qui cite UNIQUEMENT ce chiffre.
    Injecte le profil utilisateur pour personnaliser la reponse."""
    profil_txt = ""
    if profil:
        profil_txt = (
            "Profil de l'utilisateur : risque=%s, horizon=%s ans, "
            "exclusions=%s. "
            % (profil.get("risque", "moyen"),
               profil.get("horizon_annees", 5),
               profil.get("exclusions", []))
        )
    prompt = (
        "Redige une phrase courte en francais qui repond a la question en "
        "citant exactement le chiffre %.2f. " % chiffre
        + profil_txt
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

    choix = _choisir_outil(question, profil=profil)
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
        # Appliquer le filtre minimum si demande
        filtre_min = choix.get("filtre_min", 0)
        if filtre_min and filtre_min > 0:
            avant = len(classement)
            classement = [(t, v) for t, v in classement if v >= filtre_min]
            trace.append("filtre >= %.1f : %d -> %d" % (filtre_min, avant, len(classement)))

        # Limiter a top_n si demande
        top_n = choix.get("top_n")
        if top_n and top_n < len(classement):
            classement = classement[:top_n]
            trace.append("limite a top %d" % top_n)
        best_t, best_v = classement[0]
        period = choix.get("annees")
        suffix = ("sur %d ans" % period) if period else "sur 5 ans"
        metric_choisie = choix.get("metric", "rendement_annualise")
        sens = choix.get("sens", "max")
        if metric_choisie == "volatilite":
            label = "Le moins volatil" if sens == "min" else "Le plus volatil"
            reponse_finale = (
                "%s est %s avec %.2f%% de volatilite %s."
                % (label, best_t, best_v, suffix)
            )
        else:
            label = "Le meilleur" if sens == "max" else "Le moins performant"
            # Si top_n > 1, citer le classement complet
            if len(classement) > 1:
                details = ", ".join("%s (%.2f%%)" % (t, v) for t, v in classement)
                reponse_finale = (
                    "%s est %s avec %.2f%% de rendement annualise %s. "
                    "Classement : %s."
                    % (label, best_t, best_v, suffix, details)
                )
            else:
                reponse_finale = (
                    "%s est %s avec %.2f%% de rendement annualise %s."
                    % (label, best_t, best_v, suffix)
                )
        verdict = verifier_reponse(reponse_finale, [v for _, v in classement])
        trace.append("barriere: ok=%s raison=%s" % (verdict.ok, verdict.raison))
        return {"question": question, "reponse": reponse_finale,
                "chiffres": [v for _, v in classement],
                "verdict": verdict.ok, "trace": trace,
                "meta": {"outil": "classer_etfs",
                         "classement": classement,
                         "metric": choix.get("metric"),
                         "annees": choix.get("annees"),
                         "source": choix.get("source"),
                         "tickers": choix.get("tickers")}}

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
                "verdict": verdict.ok, "trace": trace,
                "meta": {"outil": "meilleur_secteur",
                         "classement_secteurs": classement,
                         "annees": choix.get("annees")}}

    # --- Cas pas d'outil ---
    if choix.get("outil") != "compute_metric":
        reponse = "Je ne peux pas conclure sans calcul sur les donnees."
        verdict = verifier_reponse(reponse, [])
        trace.append("barriere: %s" % verdict.raison)
        return {"question": question, "reponse": reponse, "chiffres": [],
                "verdict": verdict.ok, "trace": trace, "meta": {}}

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
    reponse_llm = _rediger(question, chiffre, metric, ticker, profil=profil)
    trace.append("redaction LLM: %s" % reponse_llm[:150])

    verdict = verifier_reponse(reponse_llm, [chiffre])
    trace.append("barriere: ok=%s raison=%s" % (verdict.ok, verdict.raison))

    if not verdict.ok:
        reponse_finale = "Le resultat est %.2f." % chiffre
        verdict = verifier_reponse(reponse_finale, [chiffre])
        trace.append("repli honnete: %s" % verdict.raison)
    else:
        reponse_finale = reponse_llm

    # Recuperer les prix pour le graphique
    try:
        from src.tools import _load
        df = _load(ticker)
        if annees := choix.get("annees"):
            import pandas as pd
            fin = df.index.max()
            df = df[df.index >= (fin - pd.DateOffset(years=annees))]
        prix = {"dates": [str(d.date()) for d in df.index[-250:]],
                "close": [float(c) for c in df["Close"].iloc[-250:]]}
    except Exception:
        prix = None

    return {"question": question, "reponse": reponse_finale,
            "chiffres": [chiffre], "verdict": verdict.ok, "trace": trace,
            "meta": {"outil": "compute_metric", "ticker": ticker,
                     "metric": metric, "annees": choix.get("annees"),
                     "prix": prix}}
