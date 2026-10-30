# Session 5 - Outils de calcul (brique 1)

## Fait
- src/tools.py : compute_metric (rendement, volatilite, prix), get_price.
- tests/test_tools.py : 7 tests.

## Note carnet de bord
- **Garde tel quel** : formules (CAGR, volatilite annualisee).
- **Corrige a la main** : test du prix connu figeait 376.02166748046875.
  Sur clone neuf, yfinance a renvoye 376.0216979980469 (ecart 0.00003,
  floating point). Tolerance relachee a 0.01, code inchange.
- **Reecrit** : rien.

## Compris
- Un test trop precis casse sur clone neuf pour du bruit numerique.
- Les outils sont la seule source autorisee de chiffres.
