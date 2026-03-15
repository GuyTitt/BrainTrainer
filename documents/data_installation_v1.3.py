# data_installation_v1.3.py  v1.3
"""
data_installation_v1.3.py — Manifeste d'installation du Puzzle des Couleurs.
v1.3 : model v1.1, view v1.3, controller v1.3, main v1.2
"""
VERSION = ('data_installation_v1.3.py', '1.3')

from pathlib import Path

PROJET         = "Puzzle des Couleurs"
VERSION_PROJET = "1.3"

_ici = Path(__file__).parent
SRC  = _ici
DST  = _ici.parent / "prog"

SOUS_DOSSIERS = [DST / "initialisations", DST / "parties", DST / "logs"]

FICHIERS = [
    ("main_v1.2.py",               DST / "main.py",               True),
    ("config_v1.1.py",             DST / "config.py",             True),
    ("model_v1.1.py",              DST / "model.py",              True),
    ("view_v1.3.py",               DST / "view.py",               True),
    ("controller_v1.3.py",         DST / "controller.py",         True),
    ("fileio_v1.0.py",             DST / "fileio.py",             True),
    ("logger_v1.0.py",             DST / "logger.py",             True),
    ("config.yaml",                DST / "config.yaml",           True),
    ("exemple.init.yaml",
     DST / "initialisations" / "exemple.init.yaml",               True),
    ("installation.py",            DST / "installation.py",       False),
    ("data_installation_v1.3.py",  DST / "data_installation_v1.3.py", False),
]

SUPPRIMER = [
    DST / "data_installation_v1.0.py",
    DST / "data_installation_v1.1.py",
    DST / "data_installation_v1.2.py",
]

CONNUS      = {Path(c).name for _, c, _ in FICHIERS}
CONNUS     |= {"__init__.py", "lancer.cmd", "lancer.bat", "lancer.sh"}
IGNORER_EXT = {".pyc", ".pyo", ".log", ".partie.yaml", ".init.yaml"}
IGNORER_DIR = {"__pycache__", "parties", "logs", "initialisations"}

# end data_installation_v1.3.py  v1.3
