# EVIDENCE - MonAuditeur ETF

Une section par brique. Pour chaque brique : ce que je montre, les fichiers,
la commande qui reproduit, et la sortie attendue.

Briques retenues : 1, 3, 5, 6, 9.
Exigences : R1 (clone neuf), R2 (tests), R3 (journal IA dans ai_log/).

---

## Brique 1 - Mon outil (compute_metric, classer_etfs, meilleur_secteur)

**Ce que je montre.** Des fonctions que j'ai ecrites, qui lisent le cache CSV
et calculent un rendement annualise, une volatilite, un prix, ou classent
plusieurs ETF. Le LLM ne calcule jamais : il appelle ces outils.

**Fichiers.** `src/tools.py`, `tests/test_tools.py` (7 tests).

**Commande qui reproduit.**

    python -c "from src.tools import compute_metric; print(compute_metric('QQQ','rendement_annualise'))"

**Sortie attendue.** Un nombre proche de 13.11 (rendement annualise de QQQ sur
5 ans, selon la date du cache).

**Avec periode.**

    python -c "from src.tools import compute_metric; print(compute_metric('QQQ','rendement_annualise', annees=3))"

**Sortie attendue.** Un nombre different (le rendement sur 3 ans, pas 5).

**Classement.**

    python -c "from src.tools import classer_etfs; print(classer_etfs(['QQQ','SPY','VGT'], 'rendement_annualise'))"

**Sortie attendue.** Une liste triee du meilleur au moins bon.

---

## Brique 3 - Une regle imposee par le code (barriere)

**Ce que je montre.** Aucun chiffre dans la reponse finale ne peut exister
s'il n'a pas ete produit par un outil. C'est du code (`src/barrier.py`), pas
un prompt. La barriere extrait tous les nombres, verifie qu'ils sont traces
par un outil (ou dans une whitelist), et rejette sinon.

**Fichiers.** `src/barrier.py`, `tests/test_barrier.py` (8 tests).

**Commande qui reproduit.**

    python -c "from src.barrier import verifier_reponse; print(verifier_reponse('QQQ a fait +45% cette annee.', [12.34]))"

**Sortie attendue.**
`Verdict(ok=False, raison='1 chiffre(s) non tracé(s) : [45.0]', chiffres_inventes=[45.0])`

**Test qui essaie d'enfreindre la regle et se fait bloquer.**
`tests/test_barrier.py::test_chiffre_invente_est_bloque`.

**Tolerance d'arrondi.**
`tests/test_barrier.py::test_chiffre_arrondi_est_accepte` : l'outil calcule
12.3456, le LLM ecrit 12.3, la barriere accepte (sinon des reponses justes
seraient rejetees).

**Tickers ignores.**
`tests/test_barrier.py` verifie que "CW8.PA a fait 10.83%" n'est pas bloque
par le 8 de CW8 (les tickers sont retires avant l'extraction des nombres).

---

## Brique 5 - Memoire persistante (profil investisseur)

**Ce que je montre.** Un fichier `profil.json` relu a chaque session : le
systeme se souvient du profil (risque, horizon, exclusions) d'une session a
l'autre, et **filtre** les recommandations en consequence.

**Fichiers.** `src/memoire.py`, `tests/test_memoire.py` (7 tests),
`profil.json` (non versionne).

**Commande (test apres redemarrage).**

    python -c "from src.memoire import charger_profil, sauver_profil; p=charger_profil(); p['risque']='moyen'; p['exclusions']=['fossiles']; sauver_profil(p); print(charger_profil())"

**Sortie attendue.** Profil relu avec `risque: moyen` et `exclusions: ['fossiles']`.

**Test apres redemarrage.** `tests/test_memoire.py::test_profil_survit_a_un_redemarrage`.

**Memoire active (filtre).** Si le profil exclut `fossiles`, le systeme exclut
XLE, XOP, USO des classements. Si `risque: faible`, il exclut les ETF de
volatilite > 20 %. C'est la difference entre une memoire passive (un fichier)
et une memoire active (qui change les reponses).

**Cout en tokens.** Profil < 100 tokens, negligeable face aux 8192 du contexte.

---

## Brique 6 - Donnees sales, decisions ecrites (nettoyage + regle metier)

**Ce que je montre.** Un journal de nettoyage trace (lignes retirees, valeurs
converties) et une regle metier absente du fichier, sourcee AMF.

**Fichiers.** `src/clean.py`, `tests/test_clean.py` (5 tests).

**Journal de nettoyage.**

    python -c "from src.clean import nettoyer_ticker; df,j=nettoyer_ticker('QQQ'); print(j.resume()); [print(' -',d) for d in j.details]"

**Sortie attendue.** `lues=1255, retirees=0, converties=0` (cache Yahoo propre :
le journal le prouve honnetement).

**Preuve que le nettoyage marche.** `tests/test_clean.py::test_nettoyage_supprime_close_manquant`
fabrique un CSV avec un Close manquant et verifie que la ligne est retiree et tracee.

**La regle metier (de qui).** Source : AMF, guide finance durable / SFDR.
Un label SFDR Article 8/9 ne garantit pas l'absence de fossiles ; il faut
verifier les exclusions reelles du fonds.

    python -c "from src.clean import produit_respecte_exclusions; print(produit_respecte_exclusions({'label':'Article 9','secteurs':['tech','fossiles']}))"

**Sortie attendue.** `(False, ...)` : un produit Article 9 expose aux fossiles
est rejete malgre son label.

---

## Brique 9 - Une comparaison mesuree

**Ce que je montre.** 10 taches a verite connue (6 calculees, 2 fausses, 2
ambigues). Systeme complet (A) vs modele seul (B), 3 runs, moyenne + dispersion,
un echec analyse depuis sa trace.

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

## R1 - Tourne sur un clone neuf

    cd ~ && rm -rf /tmp/clone-test
    git clone ~/mon-auditeur-etf /tmp/clone-test
    cd /tmp/clone-test
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python data/download.py
    pytest -q

**Sortie attendue.** `35 passed`.

**Note.** Le clone neuf ne contient pas le cache CSV (gitignore). `data/download.py`
le recree. Le clone ne contient pas `profil.json` (gitignore). `memoire.py`
le cree par defaut.

---

## R2 - Tests automatiques

    pytest -q

**Sortie attendue.** `35 passed`.

Couverture : download (4), memoire (7), barrier (8), tools (7), clean (5),
agent (4).

---

## R3 - Journal d'usage de l'IA

Voir `ai_log/` : `HISTOIRE.md` (recit complet du projet avec decisions et bugs)
et une fiche par session (README + 12 sessions).

---

## Ce qui a change depuis la premiere version

- **Resolution de ticker** (`src/resolver.py`) : trouve un ticker depuis
  "QQQ", "ETF monde", "Amundi MSCI World", meme mal ecrit.
- **Resolution de theme** (`yf.Lookup`) : trouve des ETF par theme (crypto,
  semi-conducteurs, gaz...). Pas de dictionnaire comme source principale.
- **ETFQuery** : combine pays + secteur (chine tech -> CQQQ/KWEB) via le
  screener natif de yfinance.
- **Parseur d'intention LLM** (`src/llm_parser.py`) : comprend les questions
  mal ecrites via structured output (JSON force).
- **Interface Streamlit** (`app.py`) : theme sombre finance, graphiques
  Plotly, detail du calcul, profil personnalisable.
- **Filtre ETF a levier** : USD, SOXL, TQQQ... exclus des classements.
- **Priorite "pas risque"** : si la question dit "pas risque", le systeme
  trie par volatilite croissante, pas par rendement.

---

## Nouvelles fonctions (au-dela des 5 briques)

- **`top_etfs_marche`** (`src/tools.py`) : interroge tout l'univers Yahoo
  via ETFQuery, trie par rendement 5 ans, retourne le vrai top.
- **`parser_intention`** (`src/llm_parser.py`) : comprend les questions mal
  ecrites via structured output.
- **`resoudre_theme`** (`src/resolver.py`) : trouve des ETF par theme via
  yf.Search + traduction LLM, sans dictionnaire.
- **`app.py`** : interface Streamlit avec graphiques, fiches ETF, profil
  personnalisable, benchmark A vs B en direct.

## Limites connues

- **Combinaison pays + secteur partielle** : "ETF japonais tech" renvoie VGT
  (pas japonais) car Yahoo ne couvre pas tous les pays.
- **Themes Yahoo absents** : "gaz russe" renvoie un refus car les ETF Russie
  sont suspendus depuis 2022.
- **ETF a levier exclus** : USD (2x semi) est exclu des classements.
- **Traduction imparfaite** : "gaze" -> "oil gas" (pas "natural gas"), le
  fallback corrige.
- **Couverture limitee** : 27 tickers pre-telecharges au demarrage.
- **Pas de conseil en investissement** : le systeme verifie des faits, il ne
  recommande pas d'acheter.
