"""Constantes partagées du projet MonAuditeur ETF."""
from pathlib import Path

# Racine du projet = dossier parent de src/
ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

# ETF suivis par défaut (tickers Yahoo Finance)
DEFAULT_TICKERS = ["QQQ", "SPY"]

# Période de téléchargement par défaut
DEFAULT_PERIOD = "5y"      # 5 ans d'historique
DEFAULT_INTERVAL = "1d"    # bougies journalières

# Modèle Ollama (section 2 du sujet)
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3.5:4b-q4_K_M"
OLLAMA_NUM_CTX = 8192
