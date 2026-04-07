"""
paths.py — Constantes de chemins du projet.

Toutes les constantes ROOT-relative passent par ce module.
Aucun path ne doit être hardcodé ailleurs dans le code.
"""

from pathlib import Path

# root
ROOT = Path(__file__).resolve().parent.parent

# top-level
SETTINGS = ROOT / "settings"
DB = ROOT / "db"
CACHE_DIR = DB / "cache"
LOGS = ROOT / "logs"
NOTEBOOKS = ROOT / "notebooks"

# Database file
DB_FILE = CACHE_DIR / "yields.db"

# Source code
SRC = ROOT / "src"
API = SRC / "api"
CURVES = SRC / "curves"
INSTRUMENTS = SRC / "instruments"
RISKS = SRC / "risks"
UTILS = SRC / "utils"
VISUALISATION = SRC / "plots"

# DB
DB_FILE = CACHE_DIR / "yields.db"

# Streamlit
APP = SRC / "app"

_PROJECT_FOLDERS = [
    SETTINGS,
    DB,
    CACHE_DIR,
    LOGS,
    NOTEBOOKS,
    SRC,
    API,
    CURVES,
    INSTRUMENTS,
    RISKS,
    UTILS,
    VISUALISATION,
    APP,
]

for folder in _PROJECT_FOLDERS:
    folder.mkdir(parents=True, exist_ok=True)
