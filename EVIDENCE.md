# EVIDENCE - MonAuditeur ETF

Une section par brique. Pour chaque brique : ce que je montre, les fichiers,
la commande qui reproduit, et la sortie attendue.

Briques retenues : 1, 3, 5, 6, 9.

---

## Brique 1 - Mon outil (compute_metric)

**Ce que je montre.** Une fonction que j'ai ecrite, `compute_metric(ticker,
metric)`, qui lit le cache CSV et calcule un rendement annualise, une
volatilite ou un prix. Le LLM ne calcule jamais : il appelle cet outil.

**Fichiers.** `src/tools.py`, `tests/test_tools.py`.

**Commande qui reproduit.**

    python -c "from src.tools import compute_metric; print(compute_metric('QQQ','rendement_annualise'))"

**Sortie attendue.** Un nombre proche de 13.11.

**Trace d'un vrai appel.** Dans `src/agent.py` : `outil compute_metric(QQQ,rendement_annualise) = 13.1107`.

---

## Brique 3 - Une regle imposee par le code (barriere)

**Ce que je montre.** Aucun chiffre dans la reponse finale ne peut exister
s'il n'a pas ete produit par un outil. C'est du code (`src/barrier.py`), pas
un prompt.

**Fichiers.** `src/barrier.py`, `tests/test_barrier.py` (8 tests).

**Commande qui reproduit.**

    python -c "from src.barrier import verifier_reponse; print(verifier_reponse('QQQ a fait +45% cette annee.', [12.34]))"

**Sortie attendue.** `Verdict(ok=False, raison='1 chiffre(s) non tracé(s) : [45.0]', chiffres_inventes=[45.0])`

**Test qui essaie d'enfreindre la regle et se fait bloquer.**
`tests/test_barrier.py::test_chiffre_invente_est_bloque`.

---

## Brique 5 - Memoire persistante (profil investisseur)

**Ce que je montre.** Un fichier `profil.json` relu a chaque session : le
systeme se souvient du profil (risque, horizon, exclusions) d'une session a
l'autre, et refuse un produit incompatible.

**Fichiers.** `src/memoire.py`, `tests/test_memoire.py` (7 tests).

**Commande (test apres redemarrage).**

    python -c "from src.memoire import charger_profil, sauver_profil; p=charger_profil(); p['risque']='moyen'; p['exclusions']=['fossiles']; sauver_profil(p); print(charger_profil())"

**Sortie attendue.** Profil relu avec `risque: moyen` et `exclusions: ['fossiles']`.

**Test apres redemarrage.** `tests/test_memoire.py::test_profil_survit_a_un_redemarrage`.

**Cout en tokens.** Profil < 100 tokens, negligeable face aux 8192 du contexte.

---

## Brique 6 - Donnees sales, decisions ecrites

**Ce que je montre.** Journal de nettoyage trace + regle metier absente du
fichier, sourcee AMF.

**Fichiers.** `src/clean.py`, `tests/test_clean.py` (5 tests).

**Journal de nettoyage.**

    python -c "from src.clean import nettoyer_ticker; df,j=nettoyer_ticker('QQQ'); print(j.resume()); [print(' -',d) for d in j.details]"

**Sortie attendue.** `lues=1255, retirees=0, converties=0` (cache Yahoo propre : le journal le prouve honnetement).

**Preuve que le nettoyage marche.** `tests/test_clean.py::test_nettoyage_supprime_close_manquant` fabrique un CSV sale.

**La regle metier (de qui).** Source : AMF, guide finance durable / SFDR.
Un label SFDR Article 8/9 ne garantit pas l'absence de fossiles ; il faut
verifier les exclusions reelles.

    python -c "from src.clean import produit_respecte_exclusions; print(produit_respecte_exclusions({'label':'Article 9','secteurs':['tech','fossiles']}))"

**Sortie attendue.** `(False, ...)` : un produit Article 9 expose aux fossiles est rejete.

---

## Brique 9 - Une comparaison mesuree

**Ce que je montre.** 10 taches a verite connue (6 calculees, 2 fausses, 2
ambigues). Systeme complet (A) vs modele seul (B), 3 runs, moyenne et
dispersion, un echec analyse depuis sa trace.

**Fichiers.** `benchmark/tasks.json`, `benchmark/run.py`, `benchmark/results.json`.

**Commande qui reproduit.**

    python -m benchmark.run

**Sortie attendue.**

    T01 [calculee]: A=3/3 B=0/3
    ...
    A: moyenne=1.00 ecart-type=0.00
    B: moyenne=0.00 ecart-type=0.00

**Un echec explique depuis sa trace (T01).** Question : rendement annualise
de QQQ sur 5 ans ? Bonne reponse : 13.11 %.

- A : outil calcule 13.1107, reponse cite 13.11, barriere accepte. 3/3.
- B : premier chiffre extrait = 5 (run 1), -100 (run 2), 5 (run 3). Aucun
  proche de 13.11. Le modele ne calcule pas, il genere du texte plausible.

**Ce que les donnees ne permettent pas de conclure.** Le benchmark mesure la
fiabilite sur 10 taches et 3 runs. Il ne prouve pas que le systeme est fiable
sur toute question financiere ; il prouve qu'il est fiable sur les taches
calculables et qu'il refuse honnetement les taches fausses ou ambigues.

---

## R2 - Tests automatiques

    pytest -q

**Sortie attendue.** `36 passed`.

Couverture : download (4), memoire (7), barrier (8), tools (7), clean (5),
agent (4), smoke (1).

---

## R1 - Tourne sur un clone neuf

    cd ~ && rm -rf /tmp/clone-test
    git clone ~/mon-auditeur-etf /tmp/clone-test
    cd /tmp/clone-test
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python data/download.py
    pytest -q

**Sortie attendue.** `36 passed`.
