# logger.py  v1.0
"""
logger.py — Journalisation centralisée du Puzzle des Couleurs.
Chaque module s'enregistre avec son VERSION ; main.py affiche le tableau
complet au démarrage et l'écrit dans le fichier log.
"""
VERSION = ('logger.py', '1.0')

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Registre des versions de tous les modules chargés
_registry: dict[str, str] = {}


def register(version_tuple: tuple) -> None:
    """Appelé par chaque module : register(VERSION)."""
    name, ver = version_tuple
    _registry[name] = ver


def setup(cfg) -> logging.Logger:
    """
    Configure le logger racine d'après cfg.logging.
    Retourne le logger principal 'puzzle'.
    """
    lc  = cfg.logging
    lvl = getattr(logging, str(lc.level).upper(), logging.INFO)

    logger  = logging.getLogger('puzzle')
    if logger.handlers:          # déjà configuré
        return logger
    logger.setLevel(lvl)

    fmt = logging.Formatter(
        fmt='%(asctime)s [%(levelname)-7s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    if lc.log_to_console:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    if lc.log_to_file:
        log_dir = cfg.paths.log_dir
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, lc.filename)
        fh = RotatingFileHandler(
            log_path,
            maxBytes=lc.max_file_size_kb * 1024,
            backupCount=lc.max_backup_files,
            encoding='utf-8')
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


def log_banner(logger: logging.Logger, app_name: str) -> None:
    """Affiche / journalise le bandeau de démarrage avec toutes les versions."""
    sep  = '─' * 52
    logger.info(sep)
    logger.info(f'{app_name} — Démarrage')
    logger.info(sep)
    for name, ver in sorted(_registry.items()):
        logger.info(f'  {name:<22}  v{ver}')
    logger.info(sep)


def get(name: str = 'puzzle') -> logging.Logger:
    """Retourne un logger enfant."""
    return logging.getLogger(f'puzzle.{name}')

# ── Auto-enregistrement ──────────────────────────────────────────────
register(VERSION)
# end logger.py  v1.0
