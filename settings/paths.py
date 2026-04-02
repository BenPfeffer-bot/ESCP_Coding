from pathlib import Path
import os
from dotenv import load_dotenv

# On crée une constante avec le path de notre projet
ROOT = Path.cwd()

# Dans la meme mesure, on va crée des constantes pour chacun des paths que nous allons utiliser tout au long du projet

load_dotenv()


#API
FRED_API_KEY = os.getenv("fred_api_key")

TICKERS_YFINANCE = {
    "^IRX": 0.25,   # 13-week T-Bill
    "^FVX": 5.0,    # 5Y Note
    "^TNX": 10.0,   # 10Y Note
    "^TYX": 30.0,   # 30Y Bond
}
POLL_INTERVAL = 30  # secondes

FREDAPI_SERIES = {
    0.5:  "DGS6MO",
    1.0:  "DGS1",
    2.0:  "DGS2",
    3.0:  "DGS3",
    7.0:  "DGS7",
    20.0: "DGS20",
}


# Support
SETTINGS = ROOT / "settings"
DB = ROOT / "db"
LOGS = ROOT / "logs"

# Projet
SRC = ROOT / "src"
UTILS = SRC / "utils"
API = SRC / "api"
CURVES = SRC / "curves"
INSTRUMENTS = SRC / "instruments"
RISKS = SRC / "risks"
VISUALISATION = SRC / "plots"


# Ici, j'ai rassemblé les folders essentielles pour le bon fonctionnement du projet
# afin de plus bas faire une if-conditions dans le cas de figures ou les folders n'existerai pas afin d'assurer qu'il se crée
projet_folder = [SETTINGS,
                DB,
                LOGS,
                SRC,
                UTILS,
                API,
                CURVES,
                INSTRUMENTS,
                RISKS,
                VISUALISATION


]
# petite boucle pour s'assurer que les folders sont bien présent dans le projet
# ça nous permets d'éviter les problèmes basiques liées à l'infrastructure
try:
    for i in projet_folder:
        if not os.path.exists(i):
                os.makedirs(i)
except FileExistsError:
    print("Folder already exists")
    raise 
