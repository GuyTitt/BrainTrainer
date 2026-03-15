# config.py  v1.1
"""
config.py — Chargement et validation de config.yaml.
Fournit un accès par attributs (cfg.grid.cell_size, cfg.pieces.radius…).
Toute clé absente prend sa valeur par défaut définie dans DEFAULTS.
v1.1 : ajout paramètres grille (lignes internes v/h, bordure extérieure),
       target_alpha par défaut = 1.0 (fond = couleur pleine des pièces).
"""
VERSION = ('config.py', '1.1')

import os
import copy
import yaml
from types import SimpleNamespace

# ─────────────────────────────────────────────────────────────────────────────
#  Valeurs par défaut
# ─────────────────────────────────────────────────────────────────────────────
DEFAULTS = {
    'meta': {
        'config_version': 1,
        'app_name': 'Puzzle des Couleurs',
    },
    'game': {
        'nb_columns': 5, 'nb_rows': 7, 'nb_rows_initial': 5,
        'nb_colors': 5, 'nb_pieces_per_color': 5,
    },
    'pieces': {
        'colors': {
            'R': {'label':'Rouge',  'fill':'#E63946','outline':'#9B1B24','text':'#FFFFFF'},
            'J': {'label':'Jaune',  'fill':'#F4C430','outline':'#A07800','text':'#333333'},
            'B': {'label':'Bleu',   'fill':'#4895EF','outline':'#1B4F9B','text':'#FFFFFF'},
            'V': {'label':'Vert',   'fill':'#52B788','outline':'#1E6E45','text':'#FFFFFF'},
            'O': {'label':'Orange', 'fill':'#FB8500','outline':'#A05000','text':'#FFFFFF'},
        },
        'radius': 28, 'outline_width': 2,
        'show_label': True, 'label_font': 'Helvetica',
        'label_font_size': 13, 'label_font_bold': True,
    },
    'grid': {
        'cell_size': 68,
        'cell_padding': 4,
        # Fond des cellules cibles : 1.0 = même couleur que les pièces
        'target_alpha': 1.0,
        # Couleur des cases libres (hors zone cible)
        'empty_cell_color': '#1E1E2E',
        # Fond général du canvas
        'grid_bg': '#12121F',

        # ── Traits internes verticaux (entre colonnes) ────────────────────────
        'inner_v_width': 1,
        'inner_v_color': '#3A3A3A',

        # ── Traits internes horizontaux (entre rangées) ───────────────────────
        'inner_h_width': 0,           # 0 = désactivé par défaut
        'inner_h_color': '#2A2A2A',

        # ── Bordure extérieure de la grille ───────────────────────────────────
        'outer_border_width': 2,
        'outer_border_color': '#5A5A7A',

        # ── Surbrillance colonne sélectionnée ────────────────────────────────
        'highlight_color': '#FFD700',
        'highlight_width': 3,

        # ── Surbrillance destinations valides / invalides ─────────────────────
        'valid_color':   '#52B788',
        'invalid_color': '#E63946',
    },
    'special_cells': {
        'size': 52, 'margin': 8,
        'font': 'Helvetica', 'font_size': 10, 'font_bold': True,
        'escape': {'label':'✕ Esc',  'bg':'#2D1B00','fg':'#FB8500','bg_hover':'#4A2E00'},
        'bloc':   {'label':'⣿ Bloc', 'bg':'#001B2D','fg':'#4895EF','bg_hover':'#002E4A'},
        'undo':   {'label':'↩ Undo', 'bg':'#1B001B','fg':'#C084FC','bg_hover':'#2E002E'},
        'redo':   {'label':'↪ Redo', 'bg':'#1B001B','fg':'#C084FC','bg_hover':'#2E002E'},
    },
    'animation': {
        'enabled': True, 'duration_ms': 300, 'fps': 60,
        'easing': 'ease_in_out',
        'guide_line': {'enabled':True,'color':'#FFFFFF','width':2,'dash':[6,4]},
    },
    'window': {
        'title': 'Puzzle des Couleurs', 'resizable': True,
        'min_width': 680, 'min_height': 560, 'bg': '#0D0D1A',
        'ui_font': 'Helvetica', 'ui_font_size': 12,
        'title_font': 'Helvetica', 'title_font_size': 18,
        'title_font_bold': True, 'title_color': '#E2C97E',
    },
    'side_panel': {
        'width': 170, 'bg': '#0A0A14',
        'border_color': '#2A2A40', 'border_width': 1,
        'counter': {
            'label':'COUPS','font':'Courier','font_size':30,
            'font_bold':True,'color':'#E2C97E',
            'label_color':'#555577','label_size':9,
        },
        'tape': {
            'font':'Courier','font_size':11,'line_height':18,
            'bg':'#F5F0E8','fg':'#1A1A1A','fg_undo':'#AAAAAA',
            'fg_bloc':'#0055AA','fg_current':'#CC2200',
            'scrollbar':True,'show_move_num':True,
            'format':'{num:>3}. C{src}\u2192C{dst}{tag}',
            'tag_simple':'','tag_bloc':' [B]',
            'separator_char':'\u2500',
        },
        'buttons': {
            'height':30,'font':'Helvetica','font_size':11,'radius':6,
            'raz':  {'label':'\u21ba  RAZ',          'bg':'#1A0000','fg':'#FF6B6B','bg_hover':'#330000'},
            'save': {'label':'\U0001f4be Enregistrer','bg':'#001A0D','fg':'#52B788','bg_hover':'#003318'},
            'load': {'label':'\U0001f4c2 Charger',    'bg':'#001020','fg':'#4895EF','bg_hover':'#002040'},
        },
    },
    'command_bar': {
        'height':34,'bg':'#0A0A14','fg':'#C0C0D8',
        'font':'Courier','font_size':12,
        'prompt':'\u203a ','prompt_color':'#E2C97E',
        'cursor_color':'#E2C97E','border_top':'#2A2A40',
        'placeholder':'deplace C1 C2  |  bloc C1 C2  |  efface  |  rejoue  |  raz  |  lire <f>  |  enregistre <f>',
    },
    'win_dialog': {
        'bg':'#0D0D1A','border_color':'#E2C97E','border_width':2,
        'title_color':'#E2C97E','title_font_size':22,
        'score_color':'#52B788','score_font_size':42,
        'text_color':'#C0C0D8','button_label':'Rejouer',
    },
    'paths': {
        'saves_dir':'./parties','init_dir':'./initialisations',
        'save_extension':'.partie.yaml','init_extension':'.init.yaml',
        'log_dir':'./logs',
    },
    'locale': {
        'language':'fr',
        'strings': {
            'win_msg':       'R\u00e9solu en {n} coups !',
            'error_invalid': 'D\u00e9placement impossible.',
            'error_full':    'Colonne pleine.',
            'error_empty':   'Colonne source vide.',
            'error_bloc':    'Conditions du bloc non remplies.',
            'cmd_unknown':   'Commande inconnue : {cmd}',
        },
    },
    'debug': {
        'enabled':False,'show_coords':False,
        'show_fps':False,'show_state':False,'highlight_valid':True,
    },
    'logging': {
        'enabled':True,'level':'INFO',
        'log_to_file':True,'log_to_console':False,
        'max_file_size_kb':512,'max_backup_files':3,
        'filename':'puzzle.log',
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  Classe Config
# ─────────────────────────────────────────────────────────────────────────────
class Config:
    def __init__(self, path: str = 'config.yaml'):
        data = copy.deepcopy(DEFAULTS)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                user = yaml.safe_load(f) or {}
            self._deep_merge(data, user)
        self._data = data
        self._ns   = self._to_ns(data)
        self._validate()
        try:
            import logger
            logger.register(VERSION)
        except ImportError:
            pass

    def __getattr__(self, name: str):
        try:
            return getattr(self._ns, name)
        except AttributeError:
            raise AttributeError(f"Config: section '{name}' introuvable")

    def get_color(self, key: str) -> SimpleNamespace:
        colors_ns = self._ns.pieces.colors
        return getattr(colors_ns, key,
                       SimpleNamespace(fill='#888888', outline='#555555',
                                       text='#FFFFFF', label=key))

    def font(self, family: str, size: int, bold: bool = False) -> tuple:
        return (family, size, 'bold') if bold else (family, size)

    def str(self, key: str, **kwargs) -> str:
        s = getattr(self._ns.locale.strings, key, key)
        return s.format(**kwargs) if kwargs else s

    def _deep_merge(self, base: dict, override: dict):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def _to_ns(self, obj):
        if isinstance(obj, dict):
            ns = SimpleNamespace()
            for k, v in obj.items():
                setattr(ns, k, self._to_ns(v))
            return ns
        return obj

    def _validate(self):
        g = self._ns.game
        expected = g.nb_colors * g.nb_pieces_per_color
        actual   = g.nb_columns * g.nb_rows_initial
        if expected != actual:
            raise ValueError(
                f"Config invalide : {g.nb_colors}\u00d7{g.nb_pieces_per_color}={expected}"
                f" \u2260 {g.nb_columns}\u00d7{g.nb_rows_initial}={actual}")
        if g.nb_rows_initial > g.nb_rows:
            raise ValueError("nb_rows_initial > nb_rows")
        r  = self._ns.pieces.radius
        cs = self._ns.grid.cell_size
        if r >= cs / 2:
            raise ValueError(f"Rayon pion ({r}) >= cell_size/2 ({cs/2})")

# end config.py  v1.1
