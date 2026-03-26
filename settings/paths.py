import sqlite3
from pathlib import Path
import os

# On crée une constante avec le path de notre projet
ROOT = Path.cwd()

# Dans la meme mesure, on va crée des constantes pour chacun des paths que nous allons utiliser tout au long du projet

# Support
SETTINGS = ROOT / "settings"
DB = ROOT / "db"
LOGS = ROOT / "logs"

# Projet
SRC = ROOT / "src"
UTILS = SRC / "utils"

# Ici, j'ai rassemblé les folders essentielles pour le bon fonctionnement du projet
# afin de plus bas faire une if-conditions dans le cas de figures ou les folders n'existerai pas afin d'assurer qu'il se crée
projet_folder = [SETTINGS,
                DB,
                LOGS,
                SRC,
                UTILS,

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
