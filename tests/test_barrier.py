"""Tests R2 + preuve brique 3 : la barrière bloque les chiffres inventés."""
from src.barrier import verifier_reponse


def test_chiffre_trace_est_accepte():
    v = verifier_reponse("Le rendement est de 12.34%.", [12.34])
    assert v.ok, v.raison


def test_chiffre_arrondi_est_accepte():
    v = verifier_reponse("Le rendement est de 12.3%.", [12.3456])
    assert v.ok, v.raison


def test_chiffre_invente_est_bloque():
    v = verifier_reponse("QQQ a fait +45% cette année.", [12.34])
    assert not v.ok
    assert 45.0 in v.chiffres_inventes


def test_plusieurs_chiffres_dont_un_invente():
    v = verifier_reponse("Prix 376.02, rendement 45%.", [376.0217])
    assert not v.ok
    assert 45.0 in v.chiffres_inventes
    assert 376.02 not in v.chiffres_inventes


def test_whitelist_toleree():
    v = verifier_reponse("Il y a 3 ETF et 2 catégories.", [])
    assert v.ok, v.raison


def test_pourcentage_avec_espace_est_detecte():
    v = verifier_reponse("Gain de 7.5 % sur la période.", [])
    assert not v.ok
    assert 7.5 in v.chiffres_inventes


def test_reponse_sans_chiffre_est_acceptee():
    v = verifier_reponse("Cet ETF est diversifié.", [])
    assert v.ok


def test_nombre_negatif_invente_est_bloque():
    v = verifier_reponse("Perte de -30% cette année.", [])
    assert not v.ok
    assert -30.0 in v.chiffres_inventes
