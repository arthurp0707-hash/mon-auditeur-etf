# MonAuditeur ETF

Un petit systeme d'IA qui verifie des affirmations sur des ETF (QQQ, SPY) a
partir de donnees reelles, sans jamais laisser le modele de langage inventer
un chiffre. Le LLM propose et redige ; le code calcule, trace et verifie.

> **Ce projet ne donne pas de conseil en investissement.** Il verifie des
> affirmations factuelles contre des donnees publiques. La decision reste
> humaine.

---

## Ce que fait le systeme

1. **Tu poses une question** sur un ETF (rendement, volatilite, prix, ou une
   affirmation chiffree comme "QQQ a fait +45% par an").
2. **Le code choisit l'outil** (heuristique deterministe : ticker + metrique).
3. **L'outil calcule** le vrai chiffre a partir du cache CSV.
4. **Le LLM redige** une reponse a partir de ce chiffre.
5. **La barriere verifie** que tous les chiffres cites sont traces ; sinon,
   rejet et repli honnete.
6. **La memoire** (profil investisseur) est chargee a chaque session.

Les 5 briques du sujet couvertes : 1 (outil), 3 (barriere), 5 (memoire),
6 (donnees sales + regle metier), 9 (comparaison mesuree).

---

## Prerequis

- Python 3.10+
- Ollama installe et lance
- Le modele qwen3.5:4b-q4_K_M

Pour telecharger le modele :

    ollama pull qwen3.5:4b-q4_K_M

Si ta machine ne fait pas tourner le 4B, utilise Qwen 3.8 27B via Cerebras
(cle CEREBRAS_API_KEY) et remplace OLLAMA_MODEL dans src/config.py.

---

## Installation (clone neuf)

    git clone <ton-depot> mon-auditeur-etf
    cd mon-auditeur-etf
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python data/download.py

---

## Lancement

### 1. Agent sur une question

    python -c "from src.agent import repondre; r=repondre('Quel est le rendement annualise de QQQ sur 5 ans ?'); print(r['reponse']); [print(' -', t) for t in r['trace']]"

### 2. Tests (R2)

    pytest -q

Attendu : 36 passed.

### 3. Benchmark comparatif (brique 9)

    python -m benchmark.run

Attendu : A=1.00 vs B=0.00 (systeme vs modele seul).

### 4. Memoire persistante (brique 5)

    python -c "from src.memoire import charger_profil, sauver_profil; p=charger_profil(); p['risque']='moyen'; sauver_profil(p); print(charger_profil())"

Puis relance : le profil est relu depuis profil.json.

---

## Structure du depot

    mon-auditeur-etf/
      README.md              # ce fichier (R1)
      EVIDENCE.md            # une section par brique
      requirements.txt
      pytest.ini
      profil.json            # memoire persistante (non versionne)
      ai_log/                # journal d'usage de l'IA (R3)
      data/
        download.py          # telechargement yfinance + cache CSV
        cache/               # CSV en cache (non versionnes)
      src/
        config.py            # constantes partagees
        tools.py             # brique 1 : outils de calcul
        barrier.py           # brique 3 : blocage des chiffres non traces
        memoire.py           # brique 5 : profil investisseur persistant
        clean.py             # brique 6 : nettoyage + regle metier SFDR
        agent.py             # pipeline complet
      benchmark/
        tasks.json           # 10 taches a verite connue
        run.py               # brique 9 : comparaison mesuree
      tests/                 # R2 : tests automatiques

---

## Regles du projet

- Aucune cle API ni donnee personnelle dans le depot.
- Le modele ne calcule jamais : il propose un outil et redige.
- Tous les chiffres affiches proviennent d'un outil et sont verifies par la
  barriere.
- Les donnees sont publiques (Yahoo Finance, cache CSV).

---

## Journal d'usage de l'IA (R3)

Voir ai_log/. Chaque session de travail avec un outil d'IA y est tracee.

---

## Licence et limites

Projet pedagogique (Coding for AI & Data Science, 2026-27). Les donnees
proviennent de Yahoo Finance et peuvent etre incompletes. Les resultats ne
constituent pas une recommandation d'investissement.
