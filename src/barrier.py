"""
Barrière anti-hallucination (brique 3).

Règle imposée par le CODE (pas par le prompt) :
    aucun chiffre dans la réponse finale ne peut exister s'il n'a pas été
    produit par un outil (calcul, lecture de données, etc.).

Le LLM peut écrire ce qu'il veut ; s'il invente "QQQ a fait +45%", la barrière
voit que 45 n'est pas dans les résultats d'outils et rejette la réponse.
"""
import re
from dataclasses import dataclass, field
from typing import Iterable

# Un nombre : entier ou décimal, avec signe et séparateurs éventuels.
_NUMBER_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")

# Nombres "autorisés" même sans outil : constantes triviales.
_WHITELIST = {0, 1, 2, 3, 4, 5, 10, 100, 1000}


# Motif des tickers (ex: CW8.PA, QQQ, IWDA.AS) : on les retire avant
# d'extraire les nombres, sinon "CW8" donne le chiffre 8.
_TICKER_RE = re.compile(r"\b[A-Z]{2,}\d*(?:\.[A-Z]{2})?\b")


def _extract_numbers(text: str) -> list[float]:
    """Extrait tous les nombres d'un texte, en ignorant les tickers."""
    text = _TICKER_RE.sub(" ", text)
    out: list[float] = []
    for raw in _NUMBER_RE.findall(text):
        try:
            out.append(float(raw.replace(",", ".")))
        except ValueError:
            continue
    return out


@dataclass
class Verdict:
    ok: bool
    raison: str
    chiffres_inventes: list[float] = field(default_factory=list)


def verifier_reponse(reponse: str, chiffres_outils: Iterable[float]) -> Verdict:
    """
    Vérifie que chaque nombre de `reponse` provient de `chiffres_outils`.

    - `chiffres_outils` : nombres réellement calculés par les outils.
    - Les nombres de la whitelist sont tolérés.
    - Un nombre est "couvert" s'il est égal (à 1e-6 près) à un nombre d'outil,
      ou s'il est un arrondi raisonnable (0 à 3 décimales) de celui-ci.
    """
    outils = list(chiffres_outils)
    inventes: list[float] = []

    for n in _extract_numbers(reponse):
        if n in _WHITELIST:
            continue
        if _est_couvert(n, outils):
            continue
        inventes.append(n)

    if inventes:
        return Verdict(
            ok=False,
            raison=f"{len(inventes)} chiffre(s) non tracé(s) : {inventes}",
            chiffres_inventes=inventes,
        )
    return Verdict(ok=True, raison="tous les chiffres sont tracés")


def _est_couvert(n: float, outils: list[float], tol: float = 1e-6) -> bool:
    """Vrai si n correspond à un outil, ou à un arrondi (0 à 3 décimales)."""
    for o in outils:
        if abs(n - o) <= tol:
            return True
        for dec in (0, 1, 2, 3):
            if abs(n - round(o, dec)) <= tol:
                return True
    return False
