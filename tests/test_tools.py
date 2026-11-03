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
    # On teste une date qui existe vraiment dans le cache (la premiere date
    # disponible), pas une date figee qui peut varier selon le telechargement.
    from src.tools import _load
    df = _load("QQQ")
    premiere_date = df.index[0].strftime("%Y-%m-%d")
    p = get_price("QQQ", premiere_date)
    assert p > 0
    attendu = float(df["Close"].iloc[0])
    assert abs(p - attendu) / attendu < 0.01


def test_ticker_inconnu_leve_erreur():
    with pytest.raises(FileNotFoundError):
        compute_metric("XXXX", "prix_dernier")


def test_metrique_inconnue_leve_erreur():
    with pytest.raises(ValueError):
        compute_metric("QQQ", "rendement_magique")


def test_date_sans_cotation_leve_erreur():
    with pytest.raises(ValueError):
        get_price("QQQ", "2021-11-06")  # un samedi
