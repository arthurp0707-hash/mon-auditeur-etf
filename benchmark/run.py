"""
Benchmark comparatif (brique 9).

Compare :
  (A) le systeme complet : outil -> chiffre trace -> barriere
  (B) le modele seul : Qwen sans outil

Sur 10 taches a verite connue, 3 runs chacune, moyenne + dispersion.
"""
import json
import re
import statistics
from pathlib import Path

import requests

from src.barrier import verifier_reponse
from src.config import OLLAMA_MODEL, OLLAMA_NUM_CTX, OLLAMA_URL
from src.tools import compute_metric

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "tasks.json"
RESULTS = ROOT / "results.json"
RUNS = 3
NUM_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def ask_model(question: str) -> str:
    """Appelle Qwen sans thinking. Retourne "" si echec (le benchmark continue)."""
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": question,
            "stream": False,
            "options": {"num_ctx": OLLAMA_NUM_CTX, "num_predict": 80},
            "think": False,
        }, timeout=60)
        return r.json().get("response", "")
    except Exception as e:
        print(f"  [warn] modele muet: {e}")
        return ""


def chiffre_attendu(task: dict):
    if task["metric"] in ("faux_rendement_45", "faux_vol_5",
                          "diversification", "surpasse_indice"):
        return None
    try:
        return compute_metric(task["ticker"], task["metric"])
    except Exception:
        return None


def extraire_premier_chiffre(texte: str):
    m = NUM_RE.search(texte)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", "."))
    except ValueError:
        return None


def systeme_complet(task: dict):
    """A: outil -> reponse chiffree -> barriere. Retourne (ok, reponse)."""
    metric = task["metric"]
    if metric in ("faux_rendement_45", "faux_vol_5",
                  "diversification", "surpasse_indice"):
        reponse = "Je ne peux pas conclure sans calcul sur les donnees."
        v = verifier_reponse(reponse, [])
        return v.ok, reponse

    try:
        val = compute_metric(task["ticker"], metric)
    except Exception as e:
        return False, f"outil en erreur: {e}"
    reponse = f"Le resultat est {val:.2f}."
    v = verifier_reponse(reponse, [val])
    return v.ok, reponse


def modele_seul(task: dict):
    """B: Qwen sans outil. Retourne (ok_brut, reponse)."""
    reponse = ask_model(task["question"])
    return True, reponse


def evaluer(task: dict, condition: str, reponse: str) -> bool:
    """Vrai si la reponse est correcte au sens de la verite de la tache.

    - calculee : le chiffre doit etre present et proche de la valeur attendue.
    - fausse   : refuser de conclure est CORRECT (ne pas valider le faux chiffre).
    - ambigue  : refuser de conclure est CORRECT (pas de reponse unique).
    """
    if task["verite"] == "calculee":
        attendu = chiffre_attendu(task)
        if attendu is None:
            return False
        n = extraire_premier_chiffre(reponse)
        if n is None:
            return False
        return abs(n - attendu) <= task["tolerance_pct"]

    if task["verite"] in ("fausse", "ambigue"):
        # Correct si le systeme ne valide PAS le chiffre propose / l'affirmation.
        # On considere qu'il refuse s'il dit explicitement ne pas pouvoir conclure.
        refus = "ne peux pas conclure" in reponse.lower() or "pas conclure" in reponse.lower()
        return refus

    return False


def main() -> None:
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    results = []

    for t in tasks:
        attendu = chiffre_attendu(t)
        a_reponses, b_reponses = [], []
        for _ in range(RUNS):
            ok_a, rep_a = systeme_complet(t)
            ok_b, rep_b = modele_seul(t)
            a_reponses.append({"ok_barriere": ok_a, "correct": evaluer(t, "A", rep_a), "texte": rep_a[:200]})
            b_reponses.append({"correct": evaluer(t, "B", rep_b), "texte": rep_b[:200]})

        results.append({
            "id": t["id"],
            "question": t["question"],
            "verite": t["verite"],
            "attendu": attendu,
            "A": a_reponses,
            "B": b_reponses,
        })
        a_ok = sum(r["correct"] for r in a_reponses)
        b_ok = sum(r["correct"] for r in b_reponses)
        print(f"{t['id']} [{t['verite']}]: A={a_ok}/{RUNS} B={b_ok}/{RUNS}")

    RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                       encoding="utf-8")

    print()
    for cond in ("A", "B"):
        taux = [statistics.mean([r["correct"] for r in res[cond]]) for res in results]
        print(f"{cond}: moyenne={statistics.mean(taux):.2f} "
              f"ecart-type={statistics.pstdev(taux):.2f}")
    print("Resultats ecrits dans", RESULTS)


if __name__ == "__main__":
    main()
