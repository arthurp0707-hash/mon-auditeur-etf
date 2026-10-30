"""Tests R2 + preuve brique 5 : la mémoire survit à un redémarrage."""
import json

from src.memoire import (
    DEFAULT_PROFILE,
    charger_profil,
    profil_compatible,
    sauver_profil,
)


def test_profil_cree_par_defaut(tmp_path):
    path = tmp_path / "profil.json"
    profil = charger_profil(path)
    assert path.exists(), "le fichier doit être créé automatiquement"
    assert profil["risque"] == "faible"
    assert profil["horizon_annees"] == 5


def test_profil_survit_a_un_redemarrage(tmp_path):
    """Preuve brique 5 : on sauve, on 'redémarre' (recharge depuis disque),
    et le système se souvient."""
    path = tmp_path / "profil.json"

    # Session 1 : l'utilisateur dit qu'il accepte le risque moyen.
    profil = charger_profil(path)
    profil["risque"] = "moyen"
    profil["exclusions"] = ["fossiles"]
    sauver_profil(profil, path)

    # 'Redémarrage' : nouveau chargement depuis le disque.
    profil_relu = charger_profil(path)
    assert profil_relu["risque"] == "moyen"
    assert profil_relu["exclusions"] == ["fossiles"]


def test_profil_incomplet_est_complete(tmp_path):
    """Si un champ manque, on retombe sur les défauts."""
    path = tmp_path / "profil.json"
    path.write_text(json.dumps({"risque": "eleve"}), encoding="utf-8")
    profil = charger_profil(path)
    assert profil["risque"] == "eleve"
    assert profil["horizon_annees"] == DEFAULT_PROFILE["horizon_annees"]


def test_produit_refuse_si_risque_trop_eleve():
    profil = {"risque": "faible", "frais_max_pct": 0.30, "exclusions": []}
    produit = {"risque": "eleve", "frais_pct": 0.10, "secteurs": []}
    ok, raison = profil_compatible(profil, produit)
    assert not ok
    assert "risque" in raison


def test_produit_refuse_si_frais_trop_eleves():
    profil = {"risque": "eleve", "frais_max_pct": 0.20, "exclusions": []}
    produit = {"risque": "faible", "frais_pct": 0.50, "secteurs": []}
    ok, raison = profil_compatible(profil, produit)
    assert not ok
    assert "frais" in raison


def test_produit_refuse_si_secteur_exclu():
    profil = {"risque": "eleve", "frais_max_pct": 0.50, "exclusions": ["fossiles"]}
    produit = {"risque": "faible", "frais_pct": 0.10, "secteurs": ["energie", "fossiles"]}
    ok, raison = profil_compatible(profil, produit)
    assert not ok
    assert "fossiles" in raison


def test_produit_compatible_est_accepte():
    profil = {"risque": "moyen", "frais_max_pct": 0.30, "exclusions": ["fossiles"]}
    produit = {"risque": "faible", "frais_pct": 0.10, "secteurs": ["tech"]}
    ok, raison = profil_compatible(profil, produit)
    assert ok
    assert raison == "compatible"
