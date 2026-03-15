# main.py  v1.2
from __future__ import annotations
"""
main.py — Point d'entrée du Puzzle des Couleurs.
v1.2 :
  • Nouvel état final général : chaque colonne contient 2 couleurs
    différentes (3+2 pions), ce qui exige de mélanger les colonnes.
    Victoire par Counter (ordre non requis).
  • Bind clic sur le fond de fenêtre → échappement.
"""
VERSION = ('main.py', '1.2')

import os, sys, argparse, tkinter as tk

# ─────────────────────────────────────────────────────────────────────────────
#  État initial : configuration cyclique standard
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_INITIAL = [
    ['O', 'V', 'B', 'J', 'R'],   # col 0  (bas → haut)
    ['R', 'O', 'V', 'B', 'J'],   # col 1
    ['J', 'R', 'O', 'V', 'B'],   # col 2
    ['B', 'J', 'R', 'O', 'V'],   # col 3
    ['V', 'B', 'J', 'R', 'O'],   # col 4
]

# ─────────────────────────────────────────────────────────────────────────────
#  État final GÉNÉRAL (cas non trivial)
#  Chaque colonne contient exactement 3 pions d'une couleur + 2 d'une autre.
#  Validation : O=3+0+2+0+0=5  R=2+0+0+3+0=5  J=0+3+0+2+0=5
#               B=0+2+0+0+3=5  V=0+0+3+0+2=5  ✓ 25 pions
#
#  La victoire est évaluée par Counter (l'ordre dans la colonne n'importe
#  pas) : le fond coloré montre quelles couleurs doivent être présentes.
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_FINAL = [
    ['O', 'O', 'O', 'R', 'R'],   # col 0 → 3 Orange + 2 Rouge
    ['J', 'J', 'J', 'B', 'B'],   # col 1 → 3 Jaune  + 2 Bleu
    ['V', 'V', 'V', 'O', 'O'],   # col 2 → 3 Vert   + 2 Orange
    ['R', 'R', 'R', 'J', 'J'],   # col 3 → 3 Rouge  + 2 Jaune
    ['B', 'B', 'B', 'V', 'V'],   # col 4 → 3 Bleu   + 2 Vert
]

AIDE_CONSOLE = """\
usage : python main.py [options]

Options :
  --aide, -h   Affiche cette aide et quitte
  --debug      Force le mode debug (surcharge config.yaml)
  --check      Vérifie la configuration et quitte
  --init F     Charge le fichier d'initialisation F au démarrage
  --partie F   Charge la partie sauvegardée F au démarrage

Commandes dans l'interface :
  deplace C1 C2 / bloc C1 C2 / efface / rejoue / raz
  lire <f> / enregistre <f> / init <f> / aide / ?

Raccourcis : Ctrl+Z/Y  F1  Ctrl+S/O  Echap
"""


def parse_args():
    p = argparse.ArgumentParser(prog='main.py', add_help=False)
    p.add_argument('--aide', '-h', '--help', action='store_true')
    p.add_argument('--debug',  action='store_true')
    p.add_argument('--check',  action='store_true')
    p.add_argument('--init',   default=None, metavar='F')
    p.add_argument('--partie', default=None, metavar='F')
    return p.parse_args()


def main():
    args = parse_args()
    if args.aide:
        print(AIDE_CONSOLE); sys.exit(0)

    import logger
    logger.register(VERSION)

    from config import Config
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
    try:
        cfg = Config(cfg_path)
    except Exception as ex:
        print(f"[ERREUR config] {ex}"); sys.exit(1)

    if args.debug:
        cfg._ns.debug.enabled = True
    if args.check:
        print(f"[OK] {cfg.meta.app_name} v{cfg.meta.config_version}"); sys.exit(0)

    for d in [cfg.paths.saves_dir, cfg.paths.init_dir, cfg.paths.log_dir]:
        os.makedirs(d, exist_ok=True)

    log = logger.setup(cfg)

    if cfg.debug.enabled:
        import logging
        rl = logging.getLogger('puzzle')
        if not any(isinstance(h, logging.StreamHandler) and
                   h.stream is sys.stdout for h in rl.handlers):
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)-7s] %(name)s: %(message)s', '%H:%M:%S'))
            sh.setLevel(logging.DEBUG)
            rl.addHandler(sh)
            rl.setLevel(logging.DEBUG)
        log.debug("Mode DEBUG activé")

    from model      import GameState
    from view       import BoardView, SpecialPanel, TapePanel, CommandBar
    from controller import GameController
    import fileio

    logger.log_banner(log, cfg.meta.app_name)

    # ── Chargement état initial ───────────────────────────────────────────
    initial, final = DEFAULT_INITIAL, DEFAULT_FINAL

    init_path = args.init or os.path.join(cfg.paths.init_dir, 'exemple.init.yaml')
    if os.path.exists(init_path):
        try:
            initial, final = fileio.load_init(init_path)
            log.info("Init chargée : %s", init_path)
        except Exception as ex:
            log.warning("Init ignorée (%s) : %s", init_path, ex)

    state = GameState(cfg, initial, final)

    if args.partie and os.path.exists(args.partie):
        try:
            state = fileio.load_game(args.partie, cfg)
            log.info("Partie chargée : %s", args.partie)
        except Exception as ex:
            log.warning("Partie ignorée : %s", ex)

    # ── Fenêtre principale ────────────────────────────────────────────────
    root = tk.Tk()
    root.title(cfg.window.title)
    root.configure(bg=cfg.window.bg)
    root.resizable(cfg.window.resizable, cfg.window.resizable)
    root.minsize(cfg.window.min_width, cfg.window.min_height)

    bold = 'bold' if cfg.window.title_font_bold else ''
    tk.Label(root, text=cfg.window.title,
             bg=cfg.window.bg, fg=cfg.window.title_color,
             font=(cfg.window.title_font,
                   cfg.window.title_font_size, bold)).pack(pady=(10, 0))

    main_frame = tk.Frame(root, bg=cfg.window.bg)
    main_frame.pack(fill='both', expand=True, padx=10, pady=6)

    board_h = cfg.game.nb_rows * cfg.grid.cell_size

    board   = BoardView(main_frame, cfg)
    tape    = TapePanel(main_frame, cfg,
                        on_raz=None, on_save=None, on_load=None)
    cmd     = CommandBar(root, cfg,
                         on_command=lambda t: ctrl.on_command(t))
    special = SpecialPanel(main_frame, cfg, board_h)

    special.pack(side='left', fill='y', padx=(0, 4))
    board.pack(  side='left')
    tape.pack(   side='left', fill='y', padx=(6, 0))
    cmd.pack(fill='x', side='bottom', pady=4, padx=10)

    ctrl = GameController(root, state, board, special, tape, cmd, cfg)

    # Rebind boutons TapePanel sur le contrôleur
    for w in tape.frame.winfo_children():
        if not isinstance(w, tk.Button): continue
        lbl = w.cget('text')
        if 'RAZ' in lbl:               w.config(command=ctrl.do_reset)
        elif '\U0001f4be' in lbl or 'nregistrer' in lbl: w.config(command=ctrl.do_save)
        elif '\U0001f4c2' in lbl or 'harger'     in lbl: w.config(command=ctrl.do_load)

    # Raccourcis clavier
    root.bind('<Control-z>', lambda e: ctrl.do_undo())
    root.bind('<Control-Z>', lambda e: ctrl.do_undo())
    root.bind('<Control-y>', lambda e: ctrl.do_redo())
    root.bind('<Control-Y>', lambda e: ctrl.do_redo())
    root.bind('<Escape>',    lambda e: ctrl._on_escape())
    root.bind('<Control-s>', lambda e: ctrl.do_save())
    root.bind('<Control-S>', lambda e: ctrl.do_save())
    root.bind('<Control-o>', lambda e: ctrl.do_load())
    root.bind('<Control-O>', lambda e: ctrl.do_load())
    root.bind('<F1>',        lambda e: ctrl.show_aide())

    # Clic sur le fond de fenêtre → échappement
    # (ne se propage pas aux widgets enfants qui gèrent leurs propres clics)
    def _bg_click(event):
        if event.widget in (root, main_frame):
            ctrl._on_escape()
    root.bind('<Button-1>', _bg_click, add='+')

    log.info("Interface prête — boucle principale")
    cmd.focus()
    root.mainloop()
    log.info("Application fermée")


if __name__ == '__main__':
    main()

# end main.py  v1.2
