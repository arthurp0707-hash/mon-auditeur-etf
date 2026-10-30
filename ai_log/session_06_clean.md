# Session 6 - Donnees sales + regle metier (brique 6)

## Fait
- src/clean.py : journal de nettoyage + regle SFDR.
- tests/test_clean.py : 5 tests dont CSV fabrique sale.

## Note carnet de bord
- **Garde tel quel** : structure du journal.
- **Corrige a la main** : journal QQQ affiche 0 retiree (cache propre). Pas un
  bug. Ajoute un test avec CSV fabrique sale pour prouver le nettoyage.
- **Reecrit** : regle metier remplacee par AMF/SFDR (un label ne garantit pas
  l'absence de fossiles), sourcee dans le code.

## Compris
- Une regle metier vient d'une source externe, pas du fichier.
- "0 retire" est une preuve, pas un echec.
