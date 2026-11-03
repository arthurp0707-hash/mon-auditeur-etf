# Histoire du projet MonAuditeur ETF

Ce document raconte comment le projet a ete construit, dans l'ordre, avec les
decisions prises, les bugs trouves et les corrections faites. Il sert de
carnet de bord pour R3 et de support pour R4.

---

## Phase 1 - Le choix du sujet (decision personnelle)

J'ai choisi le sujet "analyse de donnees avec arbitre" applique aux ETF.
Raison : je voulais un projet qui repond a un vrai besoin (verifier des
affirmations sur des ETF) et qui montre la philosophie du cours (le LLM ne
calcule pas, le code verifie).

J'ai refuse plusieurs propositions :
- **MCP (brique 2)** : refuse car une 6e brique ne rapporte pas de points et
  que je voulais d'abord comprendre mes 5 briques.
- **Un parseur a regles** (if "meilleur" in q) : refuse car je voulais que
  le systeme comprenne les questions mal ecrites, pas seulement les
  formulations exactes.
- **Un dictionnaire de themes** : refuse car il ne couvre jamais tout
  (crypto, semi-conducteurs, gaz russe...). J'ai impose yf.Lookup + ETFQuery.
- **Une interface avec emoji** : refuse car je voulais un theme finance sobre.

---

## Phase 2 - L'environnement (WSL, Python, Ollama)

- Python 3.10 sous WSL/Ubuntu 22.04.
- Projet dans ~/mon-auditeur-etf (pas sous /mnt/c, trop lent).
- venv, git, requirements.txt.
- Ollama + qwen3.5:4b-q4_K_M.

**Decision** : garder le 4B local (pas Cerebras), car c'est le modele impose
par le sujet et il tourne sur ma machine.

**Bug trouve** : Qwen3.5 "pense" avant de repondre (37 s). **Correction** :
`think: false` dans le payload, temps ramene a 0.6 s.

---

## Phase 3 - Les donnees (brique 1 et R1)

- data/download.py : telechargement yfinance + cache CSV.
- 27 tickers pre-telecharges via download_all.py.
- Pas de scraping, pas de cle API : donnees publiques Yahoo.

**Decision** : cache CSV plutot que telechargement a la volee, pour que la
demo soit reproductible meme si Yahoo est down (R1).

**Bug trouve** : la derniere ligne du CSV Yahoo a un Close a NaN, ce qui
faisait retourner nan a compute_metric. **Correction** : dropna(subset=["Close"])
dans _load.

---

## Phase 4 - L'outil (brique 1)

- src/tools.py : compute_metric, classer_etfs, get_price, meilleur_secteur.
- compute_metric accepte un parametre `annees` (2, 3, 5 ans).
- classer_etfs filtre les nan et exclut les ETF a levier (USD, SOXL...).

**Decision** : exclure les ETF a levier des classements, car un utilisateur
qui demande "le plus performant" ne veut pas un 2x qui peut perdre 80 %.

**Bug trouve** : "je veux un ETF pas risque" renvoyait HHIS.TO (ETF canadien
a haut rendement), car le tri se faisait par rendement et pas par volatilite.
**Correction** : tri croissant pour la volatilite, et priorite "pas risque"
dans le parseur.

---

## Phase 5 - La barriere (brique 3)

- src/barrier.py : verifier_reponse, _est_couvert, whitelist.
- 8 tests : chiffre trace accepte, chiffre invente bloque, arrondi tolere.

**Decision** : tolerer les arrondis (12.3456 -> 12.3), sinon des reponses
justes seraient rejetees.

**Bug trouve** : "CW8.PA a fait 10.83%" etait bloque car la barriere extrayait
le 8 de CW8. **Correction** : ignorer les tickers avant d'extraire les nombres.

---

## Phase 6 - La memoire (brique 5)

- src/memoire.py : charger_profil, sauver_profil, profil_compatible.
- profil.json : risque, horizon, frais max, exclusions.
- Preuve apres redemarrage : on sauve, on recharge, le systeme se souvient.

**Decision** : rendre la memoire ACTIVE, pas juste un affichage. Le profil
filtre les recommandations (si risque=faible, exclure volatilite > 20 % ;
si exclusions=fossiles, exclure XLE/XOP/USO).

**Bug trouve** : la memoire etait passive, elle ne changeait rien.
**Correction** : _filtrer_par_profil dans agent.py.

---

## Phase 7 - Les donnees sales (brique 6)

- src/clean.py : nettoyer_ticker (journal trace), REGLE_METIER_SFDR.
- Regle metier sourcee AMF : un label SFDR Article 8/9 ne garantit pas
  l'absence de fossiles, il faut verifier les exclusions reelles.

**Decision** : citer la source (AMF) dans le code, pas juste dire "c'est une
regle". Le prof veut savoir d'ou vient la regle.

**Honte assumee** : le journal de QQQ affiche "0 retiree" car le cache Yahoo
est propre. Ce n'est pas un bug, c'est une preuve honnete. Le test avec un
CSV fabrique sale prouve que le nettoyage marche.

---

## Phase 8 - Le benchmark (brique 9)

- benchmark/tasks.json : 10 taches (6 calculees, 2 fausses, 2 ambigues).
- benchmark/run.py : systeme complet (A) vs modele seul (B), 3 runs.
- Resultat : A=1.00, B=0.00.

**Preuve T01** : rendement QQQ sur 5 ans. A repond 13.11 trois fois. B repond
5, -100, 5 : il ne calcule pas, il genere du texte plausible.

**Decision** : compter un refus de conclure comme CORRECT sur une tache fausse
ou ambigue. Sinon le systeme serait penalise pour avoir bien refuse.

---

## Phase 9 - L'agent (assemblage)

- src/agent.py : pipeline LLM -> outil -> barriere -> reponse.
- Trace : profil, choix LLM, outil, calcul, barriere.
- Comparaison en code quand un pourcentage est propose (45 % vs 13.11 %).

**Decision** : quand la question propose un pourcentage, construire la
comparaison en CODE, pas par le LLM. Le 4B formulait mal ("n'a pas atteint
13.11 %" au lieu de "n'a pas fait 45 %, il a fait 13.11 %").

---

## Phase 10 - La resolution de ticker et de theme

- src/resolver.py : resoudre_ticker, resoudre_theme, resoudre_secteur,
  top_etfs_secteur, screener_etfs.
- yf.Lookup pour les themes simples (crypto -> BITO/GBTC).
- ETFQuery pour les combinaisons pays + secteur (chine tech -> CQQQ/KWEB).
- Fallback verifie uniquement pour les themes ou Yahoo echoue (gaz, or, eau).

**Decision** : refuser le dictionnaire de themes comme source principale.
yf.Lookup et ETFQuery sont des solutions natives, plus robustes.

**Bug trouve** : "gaze" etait traduit en "growth energy" au lieu de
"natural gas". **Correction** : normalisation (gaze -> gaz) + dictionnaire
de traductions verifiees prioritaires.

**Bug trouve** : "ETF chinois tech" renvoyait VGT (US tech) au lieu de CQQQ.
**Correction** : ETFQuery combine region=cn + sector=Technology.

---

## Phase 11 - Le parseur d'intention LLM

- src/llm_parser.py : parser_intention, traduire_theme.
- Schema JSON force via Ollama format : outil, theme, metric, annees, top_n,
  filtre_min, sens.

**Decision** : remplacer le parseur a regles (if "meilleur" in q) par un
parseur LLM avec structured output. Le 4B comprend mieux les questions mal
ecrites qu'un parseur a regles.

**Bug trouve** : le LLM repondait "growth energy" pour "gaze".
**Correction** : normalisation + dictionnaire de traductions verifiees.

---

## Phase 12 - L'interface Streamlit

- app.py : theme sombre finance (bleu nuit / or / vert), sans emoji.
- Sidebar : profil investisseur + formulaire de modification.
- 3 onglets : Question / Benchmark / A propos.
- Graphiques Plotly : prix de l'ETF, classement en barres.
- Expander "Detail du calcul" : ticker, metrique, periode, valeur.
- Bouton "Verifier le benchmark en direct".

**Decision** : refaire l'interface initiale (cartoon, emoji) en theme finance
sobre, sans emoji, avec badges texte. Je voulais que ca "en jette" sans faire
amateur.

**Bug trouve** : les apostrophes francaises (d'affirmations) cassaient la
syntaxe dans le heredoc. **Correction** : remplacer par "de affirmations".

---

## Phase 13 - R1 et R2 (clone neuf, tests)

- README.md : installation, lancement, structure.
- pytest.ini : pythonpath = .
- 35 tests dans tests/.

**Decision** : tester sur un clone neuf a chaque etape, pas seulement a la fin.
C'est ce qui a revele que data/download.py et src/config.py n'etaient pas
commites, et que le test du prix connu figeait une date qui variait.

**Bug trouve** : le test du prix connu figeait 2021-11-01, qui n'existe pas
dans le cache d'un clone neuf (Yahoo renvoie 2021-11-03). **Correction** :
date dynamique (premiere date du cache).

**Bug trouve** : le clone neuf utilisait l'ancien test car la correction
n'etait pas commitee. **Lecon** : git clone ne voit que les commits.

---

## Phase 14 - R3 (journal IA)

- ai_log/ : une fiche par session (README + 12 sessions).
- Chaque fiche : ce qui a ete fait, garde tel quel / corrige / reecrit,
  ce que j'ai compris.
- HISTOIRE.md (ce fichier) : la vue d'ensemble.

**Decision** : un resume par session plutot que les conversations brutes
(trop longues pour le depot). Le sujet accepte le resume avec la note du
carnet de bord.

---

## Ce que j'ai appris (bilan honnete)

1. **Un LLM ne calcule pas** : il genere du texte plausible. Le benchmark
   le prouve (B=0.00).
2. **Un parseur a regles ne couvre pas tout** : il faut un LLM pour
   comprendre les questions mal ecrites.
3. **Un dictionnaire ne couvre pas tout** : yf.Lookup + ETFQuery sont des
   solutions natives, plus robustes.
4. **La memoire doit etre active** : un profil qui ne filtre rien ne sert
   a rien.
5. **Un test trop precis est fragile** : il casse sur un clone neuf pour du
   bruit numerique.
6. **git clone ne voit que les commits** : un fichier modifie mais pas
   commite n'existe pas pour le clone.

---

## Ce que je ferais differemment

- Commiter plus souvent (j'ai perdu du temps avec des patches non commits).
- Tester sur clone neuf plus tot (j'ai decouvert les bugs R1 a la fin).
- Documenter les limites au fur et a mesure (Japon tech, gaz russe) plutot
  qu'a la fin.

---

## Les limites connues du systeme

- **Combinaison pays + secteur partielle** : "ETF japonais tech" renvoie
  VGT (pas japonais) car Yahoo ne couvre pas tous les pays.
- **Themes Yahoo absents** : "gaz russe" renvoie un refus car les ETF Russie
  sont suspendus depuis 2022.
- **ETF a levier exclus** : USD (2x semi) est exclu des classements.
- **Traduction imparfaite** : "gaze" -> "oil gas" (pas "natural gas"), le
  fallback corrige.
- **Couverture limitee** : 27 tickers pre-telecharges.

---

## Conclusion

Ce projet m'a appris a construire un systeme d'IA fiable autour d'un modele
faillible. Le modele ne calcule pas, le code calcule, la barriere verifie.
C'est la philosophie du cours, appliquee a un vrai cas : verifier des
affirmations sur des ETF.
