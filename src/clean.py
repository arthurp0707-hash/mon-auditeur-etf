"""
Nettoyage des données + règles métier (brique 6).

Deux choses ici :
  1. Le nettoyage traçable du cache CSV (lignes retirées, valeurs converties).
  2. La règle métier ABSENTE du fichier, obtenue auprès d'une source externe
     (AMF / SFDR) : un label ESG ne suffit pas, il faut vérifier les exclusions.
"""
from dataclasses import dataclass, field

import pandas as pd

from src.config import CACHE_DIR


# --- Règle métier externe, citée et sourcée -------------------------------
# Source : AMF, Guide sur la finance durable / SFDR (documentation publique).
# "La classification SFDR Article 8 ou 9 ne garantit pas à elle seule
#  l'absence d'expositions aux energies fossiles."
REGLE_METIER_SFDR = (
    "Un label SFDR Article 8/9 ne garantit pas l'absence d'energies fossiles ; "
    "il faut verifier les exclusions reelles du fonds (source: AMF, guide SFDR)."
)


@dataclass
class JournalNettoyage:
    lignes_lues: int = 0
    lignes_retirees: int = 0
    valeurs_converties: int = 0
    details: list = field(default_factory=list)

    def ajouter(self, message: str) -> None:
        self.details.append(message)

    def resume(self) -> str:
        return (
            f"lues={self.lignes_lues}, retirees={self.lignes_retirees}, "
            f"converties={self.valeurs_converties}"
        )


def nettoyer_ticker(ticker: str):
    """
    Nettoie le cache d'un ticker et retourne (df_propre, journal).

    Nettoyages appliques :
      - lignes sans Close -> retirees
      - Close <= 0 -> retirees (prix invalides)
      - Volume manquant -> converti en 0
      - doublons de dates -> garde le dernier
    """
    path = CACHE_DIR / f"{ticker}_5y_1d.csv"
    if not path.exists():
        raise FileNotFoundError(f"Cache absent pour {ticker}")
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    journal = JournalNettoyage(lignes_lues=len(df))

    avant = len(df)
    df = df.dropna(subset=["Close"])
    retirees = avant - len(df)
    if retirees:
        journal.lignes_retirees += retirees
        journal.ajouter(f"{retirees} ligne(s) sans Close retiree(s)")

    avant = len(df)
    df = df[df["Close"] > 0]
    retirees = avant - len(df)
    if retirees:
        journal.lignes_retirees += retirees
        journal.ajouter(f"{retirees} ligne(s) avec Close <= 0 retiree(s)")

    manquants = int(df["Volume"].isna().sum())
    if manquants:
        df["Volume"] = df["Volume"].fillna(0)
        journal.valeurs_converties += manquants
        journal.ajouter(f"{manquants} Volume manquant(s) converti(s) en 0")

    avant = len(df)
    df = df[~df.index.duplicated(keep="last")]
    doublons = avant - len(df)
    if doublons:
        journal.lignes_retirees += doublons
        journal.ajouter(f"{doublons} date(s) dupliquee(s) retiree(s)")

    return df.sort_index(), journal


def produit_respecte_exclusions(produit: dict):
    """
    Applique la regle metier SFDR : un label ESG ne suffit pas.
    On regarde les exclusions reelles du produit, pas son label.
    """
    label = produit.get("label", "").lower()
    secteurs = [s.lower() for s in produit.get("secteurs", [])]

    if "fossiles" in secteurs:
        return False, (
            f"Produit labellise '{label}' mais expose aux fossiles -> "
            f"la regle AMF/SFDR s'applique : label != exclusion reelle."
        )
    return True, "pas d'exposition aux fossiles detectee dans les secteurs"
