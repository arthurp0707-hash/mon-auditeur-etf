"""Tests R2 + preuve brique 1 : les outils calculent des chiffres réels."""
import pytest

from src.tools import compute_metric, get_price


def test_rendement_annualise_est_un_nombre():
    r = compute_metric("QQQ", "rendement_annualise")
    assert isinstance(r, float)
    assert -100 < r < 100  # un rendement annualisé plausible


def test_volatilite_positive():
    v = compute_metric("QQQ", "volatilite")
    assert v > 0


def test_prix_dernier_positif():
    p = compute_metric("QQQ", "prix_dernier")
    assert p > 0


def test_prix_connu_a_une_date():
    # Le prix exact varie legerement selon le telechargement (floating point
    # yfinance). On verifie l'ordre de grandeur, pas la decimale exacte.
    p = get_price("QQQ", "2021-11-01")
    assert p > 0
    assert abs(p - 376.02) < 0.01


def test_ticker_inconnu_leve_erreur():
    with pytest.raises(FileNotFoundError):
        compute_metric("XXXX", "prix_dernier")


def test_metrique_inconnue_leve_erreur():
    with pytest.raises(ValueError):
        compute_metric("QQQ", "rendement_magique")


def test_date_sans_cotation_leve_erreur():
    with pytest.raises(ValueError):
        get_price("QQQ", "2021-11-06")  # un samedi
