# fileio.py  v1.0
"""
fileio.py — Sauvegarde et chargement de parties au format YAML.
Stocke : méta, état initial, état final, historique des coups.
Le chargement rejoue l'historique pour reconstruire les piles undo/redo.
"""
VERSION = ('fileio.py', '1.0')

import os
import yaml
from datetime import datetime
from model import GameState, MoveRecord

try:
    import logger
    logger.register(VERSION)
    _log = logger.get('fileio')
except ImportError:
    import logging
    _log = logging.getLogger('fileio')


# ─────────────────────────────────────────────────────────────────────────────
#  Sauvegarde
# ─────────────────────────────────────────────────────────────────────────────
def save_game(state: GameState, path: str) -> None:
    """Sérialise l'état courant + historique complet dans un fichier YAML."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    history = [rec.to_dict() for (_, rec) in state.undo_stack]
    data = {
        'meta': {
            'version': 1,
            'date':    datetime.now().isoformat(timespec='seconds'),
            'moves':   state.move_count,
        },
        'initial':      [list(col) for col in state.initial],
        'final':        [list(col) for col in state.final],
        'current':      [list(col) for col in state.columns],
        'history':      history,
        'current_move': state.move_count,
    }
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True,
                  default_flow_style=None, sort_keys=False)
    _log.info(f"Partie sauvegardée : {path}  ({state.move_count} coups)")


# ─────────────────────────────────────────────────────────────────────────────
#  Chargement d'une partie
# ─────────────────────────────────────────────────────────────────────────────
def load_game(path: str, cfg) -> GameState:
    """Lit un fichier de partie YAML et reconstruit le GameState complet."""
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    initial = [list(col) for col in data['initial']]
    final   = [list(col) for col in data['final']]
    state   = GameState(cfg, initial, final)
    for entry in data.get('history', []):
        rec = MoveRecord.from_dict(entry)
        state.do_move(rec.src, rec.dst, rec.type == 'bloc')
    _log.info(f"Partie chargée : {path}  ({state.move_count} coups)")
    return state


# ─────────────────────────────────────────────────────────────────────────────
#  Chargement d'une initialisation
# ─────────────────────────────────────────────────────────────────────────────
def load_init(path: str) -> tuple:
    """Retourne (initial, final) depuis un fichier .init.yaml."""
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    initial = [list(col) for col in data['initial']]
    final   = [list(col) for col in data['final']]
    _log.info(f"Init chargée : {path}")
    return initial, final


# ─────────────────────────────────────────────────────────────────────────────
#  Utilitaire chemin
# ─────────────────────────────────────────────────────────────────────────────
def add_extension(path: str, ext: str) -> str:
    return path if path.endswith(ext) else path + ext

# end fileio.py  v1.0
