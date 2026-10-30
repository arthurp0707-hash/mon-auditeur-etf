# Session 7 - Comparaison mesuree (brique 9)

## Fait
- benchmark/tasks.json : 10 taches (6 calculees, 2 fausses, 2 ambigues).
- benchmark/run.py : A (systeme) vs B (modele seul), 3 runs, moyenne + ecart.

## Note carnet de bord
- **Garde tel quel** : structure du benchmark.
- **Corrige a la main** : modele seul timeoutait a 180 s car Qwen3.5 pense.
  Ajoute "think": False, timeout baisse a 60 s. 37 s -> 0.6 s.
- **Reecrit** : evaluer comptait un refus comme echec. Corrige : sur tache
  fausse/ambigue, refuser de conclure est CORRECT.

## Resultats
- A : moyenne 1.00, ecart-type 0.00.
- B : moyenne 0.00, ecart-type 0.00.
- T01 : A repond 13.11 trois fois ; B repond 5, -100, 5.

## Compris
- Le modele seul ne calcule pas, il genere du texte plausible.
- Un benchmark honnete compte aussi les refus corrects.
