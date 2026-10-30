# Session 8 - Agent (assemblage)

## Fait
- src/agent.py : pipeline LLM -> outil -> barriere -> reponse, avec trace.
- tests/test_agent.py : 4 tests.

## Note carnet de bord
- **Garde tel quel** : pipeline et trace.
- **Corrige a la main** : LLM seul repondait "aucun" (mauvais JSON sur 4B).
  Ajoute heuristique code (ticker + metrique) ; LLM en secours et pour rediger.
- **Reecrit** : question avec pourcentage propose ("+45%") : LLM formulait mal
  ("n'a pas atteint 13.11%" au lieu de "n'a pas fait 45%, il a fait 13.11%").
  Comparaison construite en CODE quand la question contient un pourcentage.

## Compris
- Un 4B ne suit pas bien une consigne de formatage JSON.
- Quand la formulation est critique, le code reprend la main.
