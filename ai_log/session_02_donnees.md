# Session 2 - Donnees et cache CSV

## Fait
- data/download.py : QQQ + SPY via yfinance, cache CSV.
- src/config.py : constantes partagees.
- tests/test_download.py : 4 tests.

## Note carnet de bord
- **Garde tel quel** : structure du script de telechargement.
- **Corrige a la main** : yfinance renvoie des colonnes MultiIndex ; ajoute
  df.columns = df.columns.get_level_values(0) pour aplatir.
- **Reecrit** : test_download.py corrompu par un collage ; reecrit via
  python - << 'PYEOF'.

## Compris
- Cache = demo reproductible meme si Yahoo est down.
- auto_adjust=True pour prix ajustes.
