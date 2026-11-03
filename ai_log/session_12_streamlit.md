# Session 12 - Interface Streamlit et profil personnalisable

## Fait
- app.py : interface sombre theme finance (bleu nuit / or / vert).
- Sidebar : profil investisseur + formulaire de modification.
- 3 onglets : Question / Benchmark / A propos.
- Graphiques Plotly : prix de l'ETF, classement en barres.
- Expander "Detail du calcul" : ticker, metrique, periode, valeur.
- Bouton "Verifier le benchmark en direct".

## Note carnet de bord
- **Garde tel quel** : la structure des onglets et le CSS sombre.
- **Corrige a la main** : les apostrophes francaises (d'affirmations) cassaient
  la syntaxe dans le heredoc. Remplacees par "de affirmations".
- **Reecrit** : l'interface initiale (cartoon, emoji) a ete refaite en theme
  finance sobre, sans emoji, avec badges texte.

## Compris
- Streamlit sous WSL doit ecouter sur 0.0.0.0 pour etre accessible depuis Windows.
- Un formulaire de profil rend la memoire (brique 5) visible et testable.
