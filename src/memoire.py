"""
Mémoire persistante du profil investisseur (brique 5).

Le profil est stocké dans un JSON à la racine du projet. Il est relu à chaque
démarrage : c'est ce qui fait qu'une session n'oublie pas la précédente.
"""
import json
from pathlib import Path
from typing import Any

from src.config import ROOT

PROFILE_PATH = ROOT / "profil.json"

# Profil par défaut : prudent, pas de produit exotique.
DEFAULT_PROFILE: dict[str, Any] = {
    "risque": "faible",              # "faible" | "moyen" | "eleve"
    "horizon_annees": 5,
    "frais_max_pct": 0.30,           # frais annuels max acceptés (%)
    "exclusions": [],                # secteurs exclus (ex: ["fossiles"])
    "devise": "EUR",
}


def charger_profil(path: Path = PROFILE_PATH) -> dict[str, Any]:
    """Lit le profil sur disque. Crée le fichier par défaut s'il n'existe pas."""
    if not path.exists():
        sauver_profil(DEFAULT_PROFILE, path)
        return dict(DEFAULT_PROFILE)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Fusion avec les défauts : si un champ manque, on le complète.
    merged = dict(DEFAULT_PROFILE)
    merged.update(data)
    return merged


def sauver_profil(profil: dict[str, Any], path: Path = PROFILE_PATH) -> None:
    """Écrit le profil sur disque (UTF-8, indenté pour lecture humaine)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=2)


def profil_compatible(profil: dict[str, Any], produit: dict[str, Any]) -> tuple[bool, str]:
    """
    Vérifie qu'un produit est compatible avec le profil.
    Retourne (compatible, raison). C'est la règle métier de la brique 5.
    """
    # Règle 1 : le risque du produit ne doit pas dépasser celui du profil.
    ordre = {"faible": 0, "moyen": 1, "eleve": 2}
    if ordre.get(produit.get("risque", "eleve"), 2) > ordre.get(profil.get("risque", "faible"), 0):
        return False, f"risque {produit.get('risque')} > profil {profil.get('risque')}"

    # Règle 2 : frais du produit <= plafond du profil.
    if produit.get("frais_pct", 0) > profil.get("frais_max_pct", 0):
        return False, f"frais {produit.get('frais_pct')}% > plafond {profil.get('frais_max_pct')}%"

    # Règle 3 : aucune exclusion du profil ne doit apparaître dans le produit.
    for exclu in profil.get("exclusions", []):
        if exclu in produit.get("secteurs", []):
            return False, f"secteur exclu présent : {exclu}"

    return True, "compatible"
