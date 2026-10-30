"""Tests R2 : l'agent assemble correctement les briques."""
from src.agent import repondre


def test_q1_rendement_calcule_et_trace():
    """Question calculable : l'outil donne ~13.11, la barriere accepte."""
    res = repondre("Quel est le rendement annualise de QQQ sur 5 ans ?")
    assert res["verdict"] is True
    assert len(res["chiffres"]) == 1
    # Le chiffre doit etre proche de 13.11 (valeur constatee sur le cache)
    assert 5.0 < res["chiffres"][0] < 25.0
    assert "13" in res["reponse"] or "12" in res["reponse"] or "14" in res["reponse"]


def test_q2_pourcentage_propose_est_compare_en_code():
    """Question piege : 45% propose, calcul 13.11 -> reponse 'Non, ...'."""
    res = repondre("QQQ a-t-il fait +45% par an sur 5 ans ?")
    assert res["verdict"] is True
    assert "Non" in res["reponse"] or "non" in res["reponse"]
    assert "45" in res["reponse"]
    # La comparaison doit etre tracee
    assert any("comparaison construite en code" in t for t in res["trace"])


def test_q3_hors_sujet_refus_honnete():
    """Question non calculable : refus, aucun chiffre invente."""
    res = repondre("Quel temps fera-t-il demain a Paris ?")
    assert res["verdict"] is True  # pas de chiffre invente = barriere OK
    assert res["chiffres"] == []
    assert "conclure" in res["reponse"].lower() or "calcul" in res["reponse"].lower()


def test_trace_contient_etapes_pipeline():
    """La trace doit montrer profil, choix, outil, barriere."""
    res = repondre("Quel est le rendement annualise de SPY sur 5 ans ?")
    trace = " ".join(res["trace"])
    assert "profil charge" in trace
    assert "outil compute_metric" in trace
    assert "barriere" in trace
