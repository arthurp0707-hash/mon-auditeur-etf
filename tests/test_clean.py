"""Tests R2 + preuve brique 6 : nettoyage trace + regle metier externe."""
import pandas as pd
import pytest

from src.clean import (
    REGLE_METIER_SFDR,
    nettoyer_ticker,
    produit_respecte_exclusions,
)


def test_nettoyage_qqq_retourne_df_et_journal():
    df, journal = nettoyer_ticker("QQQ")
    assert len(df) > 1000
    assert journal.lignes_lues >= len(df)
    assert isinstance(journal.resume(), str)


def test_nettoyage_supprime_close_manquant(tmp_path, monkeypatch):
    sale = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
        "Open": [1.0, 2.0, 3.0],
        "High": [1.0, 2.0, 3.0],
        "Low": [1.0, 2.0, 3.0],
        "Close": [10.0, None, 12.0],
        "Volume": [100, 200, 300],
    }).set_index("Date")
    path = tmp_path / "FAKE_5y_1d.csv"
    sale.to_csv(path)

    monkeypatch.setattr("src.clean.CACHE_DIR", tmp_path)
    df, journal = nettoyer_ticker("FAKE")
    assert len(df) == 2
    assert journal.lignes_retirees == 1
    assert any("Close" in d for d in journal.details)


def test_label_esg_ne_suffit_pas_si_fossiles_presents():
    produit = {"label": "Article 9", "secteurs": ["tech", "fossiles"]}
    ok, raison = produit_respecte_exclusions(produit)
    assert not ok
    assert "fossiles" in raison.lower()


def test_produit_sans_fossiles_est_accepte():
    produit = {"label": "Article 8", "secteurs": ["tech", "sante"]}
    ok, raison = produit_respecte_exclusions(produit)
    assert ok


def test_regle_metier_est_citee_et_sourcee():
    assert "SFDR" in REGLE_METIER_SFDR
    assert "AMF" in REGLE_METIER_SFDR
