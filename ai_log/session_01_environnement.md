# Session 1 - Environnement (2026-10-30)

## Fait
- Python 3.10, venv, git sous WSL/Ubuntu 22.04.
- Projet cree dans ~/mon-auditeur-etf (pas sous /mnt/c).
- Git init, .gitignore, requirements.txt.
- Ollama + qwen3.5:4b-q4_K_M, test HTTP depuis Python.

## Note carnet de bord
- **Garde tel quel** : commandes d'installation (apt, venv, ollama pull).
- **Corrige a la main** : `ollama serve &` a echoue (address already in use)
  car le service etait deja lance. Pas grave, j'ai continue.
- **Reecrit** : premier test yfinance sans auto_adjust ; ajoute pour prix
  ajustes (dividendes/splits).

## Compris
- Travailler dans ~/ et pas /mnt/c (I/O, permissions).
- Fixer num_ctx (sinon Ollama reserve 256K tokens).
- Qwen3.5 pense avant de repondre : think=false divise le temps par 60.
