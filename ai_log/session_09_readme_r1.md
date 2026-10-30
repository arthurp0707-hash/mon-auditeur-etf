# Session 9 - README et verification R1

## Fait
- README.md : titre, description, prerequis, installation, lancement.
- Verification R1 : clone neuf /tmp/clone-test, venv, pip install,
  data/download.py, pytest.

## Note carnet de bord
- **Garde tel quel** : structure du README.
- **Corrige a la main** : README corrompu deux fois par heredocs bash
  (backticks, triples backticks). Reecrit via python - << 'PYEOF'.
- **Reecrit** : commandes de lancement simplifiees en python -c d'une ligne.

## Resultat R1
- Clone neuf : 36 passed.
- Un test a d'abord echoue (prix exact), corrige par tolerance (session 5).

## Compris
- R1 se prouve en re-clonant, pas en reutilisant son venv.
- Ne jamais patcher dans un clone : patch dans le projet, commit, re-clone.
