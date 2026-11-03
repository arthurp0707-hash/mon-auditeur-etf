# Session 10 - Resolution de ticker, themes, secteurs

## Fait
- src/resolver.py : resoudre_ticker, resoudre_theme, resoudre_secteur,
  top_etfs_secteur, screener_etfs.
- data/download_all.py : panier de 27 tickers pre-telecharges.
- Correction : CW8.PA vs IWDA.AS (priorite Amundi).
- ETFQuery pour combiner pays + secteur (chine tech -> CQQQ/KWEB).
- Fallback verifie pour les themes ou Yahoo echoue (gaz, or, eau).

## Note carnet de bord
- **Garde tel quel** : la structure de resoudre_ticker (dictionnaire + yf.Lookup).
- **Corrige a la main** : "Amundi MSCI World" donnait IWDA.AS au lieu de CW8.PA.
  Ajout de "amundi" aux tickers explicites prioritaires.
- **Reecrit** : le dictionnaire de themes a ete remplace par yf.Lookup + ETFQuery,
  car il ne couvrait pas "crypto", "semi-conducteurs", etc.
- **Corrige a la main** : "gaze" etait traduit en "growth energy" au lieu de
  "natural gas". Ajout d'une normalisation (gaze -> gaz) et d'un dictionnaire
  de traductions verifiees.

## Compris
- Un dictionnaire de themes ne couvre jamais tout. yf.Lookup + ETFQuery sont
  des solutions natives, plus robustes.
- Le fallback ne sert que de filet de securite, pas de source principale.
