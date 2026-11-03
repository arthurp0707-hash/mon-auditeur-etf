# Session 11 - Parseur d'intention LLM (structured output)

## Fait
- src/llm_parser.py : parser_intention, traduire_theme.
- Schema JSON force via Ollama format (outil, theme, metric, annees, top_n,
  filtre_min, sens).
- Priorite "pas risque" -> metric=volatilite, sens=min.
- Traduction francais -> anglais pour yf.Lookup.

## Note carnet de bord
- **Garde tel quel** : le schema JSON et l'appel Ollama avec format.
- **Corrige a la main** : le LLM repondait "growth energy" pour "gaze".
  Ajout d'une normalisation des fautes + dictionnaire de traductions verifiees.
- **Reecrit** : le parseur a regles (if "meilleur" in q) a ete remplace par un
  parseur LLM avec structured output, car il ne comprenait pas les questions
  mal ecrites ("kel et le meilleur etf tech sur 3 an").

## Compris
- Un 4B ne produit pas de JSON valide sans contrainte. Le parametre format
  d'Ollama force la structure.
- Le LLM comprend mieux les questions mal ecrites qu'un parseur a regles.
