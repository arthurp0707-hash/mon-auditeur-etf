# Session 4 - Barriere anti-hallucination (brique 3)

## Fait
- src/barrier.py : extraction nombres, whitelist, tolerance arrondi.
- tests/test_barrier.py : 8 tests dont blocage chiffre invente.

## Note carnet de bord
- **Garde tel quel** : regex d'extraction.
- **Corrige a la main** : _est_couvert comparait a l'egalite stricte ; ajoute
  tolerance arrondi (0 a 3 decimales).
- **Reecrit** : barrier.py corrompu par heredoc ; reecrit via PYEOF.

## Compris
- Whitelist necessaire (sinon "il y a 3 ETF" rejete).
- Tolerance arrondi necessaire (sinon reponses justes rejetees).
