"""
Telecharge le panier complet de tickers connus (une fois, a l'installation).

Usage : python data/download_all.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.download import download_one

# Panier : panier par defaut + themes IA + tech + chine + petrole + semi
TICKERS = [
    # Panier par defaut
    "QQQ", "SPY", "IWDA.AS", "CW8.PA", "VGT",
    "XLE", "XLV", "XLF", "XLI", "XLY", "XLU", "XLRE",
    # IA / tech
    "ARTY", "XAIX.DE", "IART.L", "XAIX.L", "AIAI.L",
    "XLK", "SMH", "SOXX", "IGV", "FTEC",
    # Chine
    "ICHD.AS", "FXI", "MCHI",
    # Petrole / energie
    "XOP", "USO",
]


def main():
    for i, t in enumerate(TICKERS, 1):
        try:
            download_one(t, force=False)
        except Exception as e:
            print(f"[skip] {t}: {str(e)[:60]}")
        if i < len(TICKERS):
            time.sleep(1)  # pause pour eviter le rate limiting Yahoo
    print(f"Termine : {len(TICKERS)} tickers traites.")


if __name__ == "__main__":
    main()
