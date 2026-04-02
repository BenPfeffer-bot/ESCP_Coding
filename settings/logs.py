import logging
import sys
from .paths import LOGS


def get_logger(name: str = "escp", level: int = logging.DEBUG) -> logging.Logger:
    """
    Retourne un logger configuré avec un handler console et un format lisible 
    Facilite le debugging et signale les erreurs critiques dans les pipelines de traitement
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        # format classique du logger 
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Formattage 
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Pour m'assurer qu'ils seront bien enregistrées dans le folder dédiée
    file_handler = logging.FileHandler(LOGS / f"{name}.log", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger