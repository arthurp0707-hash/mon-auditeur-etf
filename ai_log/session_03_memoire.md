# Session 3 - Memoire persistante (brique 5)

## Fait
- src/memoire.py : profil JSON, charger/sauver, compatibilite.
- tests/test_memoire.py : 7 tests dont preuve apres redemarrage.

## Note carnet de bord
- **Garde tel quel** : structure du profil et compatibilite.
- **Corrige a la main** : le test apres redemarrage recharge depuis le disque
  (charger_profil(path)) au lieu de reutiliser l'objet memoire.
- **Reecrit** : regle de compatibilite remplacee par table d'ordre
  {faible:0, moyen:1, eleve:2}.

## Compris
- Une memoire se prouve en relisant depuis le disque.
- profil.json ne doit pas etre versionne.
