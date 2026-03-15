# controller.py  v1.3
from __future__ import annotations
"""
controller.py — Contrôleur du jeu.
Machine à 3 états : IDLE → SRC_SELECTED → [BLOC_PENDING] → IDLE

v1.3 :
  • Sélection basée sur la POSITION du clic (pas auto-détection) :
      - clic sur pion du haut ou zone vide → simple (1 pion)
      - clic sur le 2e pion (couple) → bloc (2 pions) directement
  • Échappement si clic hors grille (col < 0)
  • Architecture drag propre : drag_start_cb ne réécrase plus la source
    si on est en SRC_SELECTED et qu'on drag vers une destination
  • _drag_src conservé séparément pour l'exécution en fin de drag
"""
VERSION = ('controller.py', '1.3')

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config
    from model  import GameState
    from view   import BoardView, TapePanel, SpecialPanel, CommandBar

try:
    import logger
    logger.register(VERSION)
    _log = logger.get('controller')
except ImportError:
    import logging
    _log = logging.getLogger('controller')

IDLE         = 'IDLE'
SRC_SELECTED = 'SRC_SELECTED'
BLOC_PENDING = 'BLOC_PENDING'


class GameController:

    def __init__(self, root, state, board, special, tape, cmd_bar, cfg):
        self.root    = root
        self.state   = state
        self.board   = board
        self.special = special
        self.tape    = tape
        self.cmd_bar = cmd_bar
        self.cfg     = cfg
        self._debug  = cfg.debug.enabled

        self._ui_state:    str       = IDLE
        self._src_col:     int       = -1
        self._valid_dests: List[int] = []

        # état drag (géré séparément de la sélection)
        self._drag_src:  int   = -1

        board.bind_click(self._on_click)
        board.bind_drag_start(self._on_drag_start)
        board.bind_drag_end(self._on_drag_end)

        special.bind('escape', self._on_escape)
        special.bind('bloc',   self._on_bloc_btn)
        special.bind('undo',   self.do_undo)
        special.bind('redo',   self.do_redo)
        special.bind('aide',   self.show_aide)

        board.draw_static_background(state.final)
        self._refresh()
        _log.info("Contrôleur initialisé  état=%s", IDLE)

    # ── Debug ─────────────────────────────────────────────────────────────
    def _dbg(self, fn: str, **kw) -> None:
        if not self._debug: return
        params = '  '.join(f"{k}={v}" for k, v in kw.items())
        msg = f"DBG {fn}  état={self._ui_state}  src={self._src_col}  {params}"
        _log.debug(msg)
        print(msg)

    # ── Helpers ───────────────────────────────────────────────────────────
    def _is_pair_bottom(self, col: int, row: int) -> bool:
        """True si le clic est exactement sur le 2e pion depuis le haut
        ET que ce pion forme un couple identique avec le pion du haut."""
        col_data = self.state.columns[col]
        height   = len(col_data)
        if height < 2:
            return False
        second_row_from_bottom = height - 2
        return (row == second_row_from_bottom and
                col_data[-1] == col_data[-2])

    def _refresh(self, message: str = '', msg_error: bool = False) -> None:
        valid = (self._valid_dests
                 if self._ui_state in (SRC_SELECTED, BLOC_PENDING)
                 else [])
        self.board.refresh(
            self.state,
            selected=self._src_col,
            bloc_mode=(self._ui_state == BLOC_PENDING),
            valid_dests=valid)
        self.tape.update(self.state.undo_stack,
                         self.state.redo_stack,
                         self.state.move_count)
        if message:
            self.cmd_bar.show_message(message, error=msg_error)

    def _reset_selection(self) -> None:
        self._dbg('_reset_selection')
        self._ui_state    = IDLE
        self._src_col     = -1
        self._valid_dests = []
        self.special.set_active('escape', False)
        self.special.set_active('bloc',   False)

    def _select_col(self, col: int) -> None:
        """Sélectionne col comme source simple (1 pion)."""
        self._src_col     = col
        self._ui_state    = SRC_SELECTED
        self._valid_dests = self.state.valid_dests(col, bloc=False)
        self.special.set_active('escape', True)
        # Le bouton Bloc s'illumine si un couple est disponible
        # (l'utilisateur peut l'activer volontairement)
        self.special.set_active('bloc',
                                self.state.has_bloc_candidate(col))
        self._dbg('_select_col', col=col,
                  nb_dests=len(self._valid_dests),
                  has_bloc=self.state.has_bloc_candidate(col))

    def _activate_bloc_mode(self) -> None:
        """Passe en BLOC_PENDING depuis SRC_SELECTED."""
        dests = self.state.valid_dests(self._src_col, bloc=True)
        self._dbg('_activate_bloc_mode', src=self._src_col, nb_dests=len(dests))
        self._ui_state    = BLOC_PENDING
        self._valid_dests = dests
        self.special.set_active('bloc', True)
        self._refresh()

    def _deactivate_bloc_mode(self) -> None:
        """Retourne à SRC_SELECTED depuis BLOC_PENDING."""
        self._ui_state    = SRC_SELECTED
        self._valid_dests = self.state.valid_dests(self._src_col, bloc=False)
        self.special.set_active('bloc', False)
        self._refresh()

    # ── Échappement ───────────────────────────────────────────────────────
    def _on_escape(self) -> None:
        self._dbg('_on_escape')
        self._reset_selection()
        self._refresh()

    # ── Bouton Bloc ───────────────────────────────────────────────────────
    def _on_bloc_btn(self) -> None:
        self._dbg('_on_bloc_btn')
        if self._ui_state == IDLE:
            self._refresh('Sélectionnez d\'abord une colonne.', msg_error=True)
            return
        if self._ui_state == BLOC_PENDING:
            self._deactivate_bloc_mode()
            return
        # SRC_SELECTED
        if self.state.has_bloc_candidate(self._src_col):
            self._activate_bloc_mode()
        else:
            self._refresh('Pas de paire identique au sommet.', msg_error=True)

    # ── Clic sur la grille ────────────────────────────────────────────────
    def _on_click(self, col: int, row: int) -> None:
        """
        Clic simple (< DRAG_THRESHOLD mouvement).
        col = -1 si hors grille → escape.
        row = rangée cliquée depuis le bas (0 = bas).

        Règle de sélection :
          row == height-1  (pion du haut) → SIMPLE
          row == height-2 ET couple       → BLOC
          row > height-1  (zone vide)     → SIMPLE
          autre                           → SIMPLE (pion plus bas)
        """
        if self.board.animating:
            return

        # Clic hors grille → échappement
        if col < 0:
            self._dbg('_on_click hors grille → escape')
            if self._ui_state != IDLE:
                self._on_escape()
            return

        is_pair_bot = self._is_pair_bottom(col, row)
        self._dbg('_on_click', col=col, row=row, is_pair_bot=is_pair_bot)

        # ── IDLE ──────────────────────────────────────────────────────────
        if self._ui_state == IDLE:
            if not self.state.columns[col]:
                return   # colonne vide : rien
            self._select_col(col)
            if is_pair_bot:
                self._activate_bloc_mode()
            else:
                self._refresh()
            return

        # ── SRC_SELECTED ──────────────────────────────────────────────────
        if self._ui_state == SRC_SELECTED:
            if col == self._src_col:
                if is_pair_bot:
                    # Clic sur le 2e pion → activer BLOC
                    self._activate_bloc_mode()
                # else : re-clic sur le pion du haut → rien (sélection conservée)
            else:
                self._try_execute(col, bloc=False)
            return

        # ── BLOC_PENDING ──────────────────────────────────────────────────
        if self._ui_state == BLOC_PENDING:
            if col == self._src_col:
                # Re-clic source → désactiver le mode bloc (garder sélection)
                self._deactivate_bloc_mode()
            else:
                self._try_execute(col, bloc=True)

    # ── Drag ──────────────────────────────────────────────────────────────
    def _on_drag_start(self, col: int, row: int) -> None:
        """
        Début du drag (seuil dépassé).
        Règle : même logique de sélection que le clic.
        Si on était en SRC_SELECTED ou BLOC_PENDING avec une AUTRE colonne,
        on ne réécrase pas — le drag depuis une destination est ignoré.
        """
        self._dbg('_on_drag_start', col=col, row=row)
        if self.board.animating:
            return
        if col < 0 or not self.state.columns[col]:
            return

        is_pair_bot = self._is_pair_bottom(col, row)

        # Sélectionner seulement si : IDLE ou même colonne que src
        # (évite d'écraser la source quand l'utilisateur drag vers la destination)
        if self._ui_state == IDLE:
            self._select_col(col)
            if is_pair_bot:
                self._activate_bloc_mode()
            else:
                self._refresh()
        elif col == self._src_col:
            # Drag depuis la source déjà sélectionnée :
            # passage en bloc si is_pair_bot ET pas encore en BLOC_PENDING
            if is_pair_bot and self._ui_state == SRC_SELECTED:
                self._activate_bloc_mode()
        # Si col != src et état != IDLE : l'utilisateur a appuyé sur une
        # destination — on laisse l'état en place (drag ignoré logiquement)
        # mais on crée quand même un fantôme depuis cette col (visuel)

        # Le drag utilise la source ET l'état courant
        # Mais si on drag depuis une colonne autre que src → on re-sélectionne
        if col != self._src_col and self._ui_state != IDLE:
            # Cas : était en SRC_SELECTED(A), user drag depuis B
            # → on sélectionne B
            self._select_col(col)
            if is_pair_bot:
                self._activate_bloc_mode()
            else:
                self._refresh()

        drag_bloc = (self._ui_state == BLOC_PENDING)
        count     = 2 if drag_bloc else 1
        col_h     = self.state.height(col)
        drag_x    = float(self.board.col_x_center(col))
        drag_y    = float(self.board.piece_y_center(col_h - 1))
        self._drag_src = col
        self.board.start_drag_ghost(col, col_h, count, drag_x, drag_y)
        self._dbg('drag ghost', drag_bloc=drag_bloc, count=count)

    def _on_drag_end(self, dst_col: int) -> None:
        self._dbg('_on_drag_end', src=self._drag_src, dst=dst_col)
        src = self._drag_src
        self._drag_src = -1
        if src < 0 or dst_col < 0 or dst_col == src:
            return
        drag_bloc = (self._ui_state == BLOC_PENDING and self._src_col == src)
        self._src_col = src   # sécurité : s'assurer que src est correct
        self._try_execute(dst_col, bloc=drag_bloc)

    # ── Exécution d'un déplacement ────────────────────────────────────────
    def _try_execute(self, dst: int, bloc: bool) -> None:
        src = self._src_col
        self._dbg('_try_execute', src=src, dst=dst, bloc=bloc)
        if src < 0:
            return
        if bloc:
            if not self.state.can_bloc(src, dst):
                self._refresh(self.cfg.str('error_bloc'), msg_error=True)
                return
        else:
            if not self.state.can_move(src, dst):
                self._refresh(self.cfg.str('error_invalid'), msg_error=True)
                return
        self._execute_move(src, dst, bloc)

    def _execute_move(self, src: int, dst: int, bloc: bool) -> None:
        count  = 2 if bloc else 1
        col_h  = self.state.height(src)
        ids    = self.board.get_top_item_ids(src, col_h, count)
        cx_src = self.board.col_x_center(src)
        cy_src = self.board.piece_y_center(col_h - 1)
        cx_dst = self.board.col_x_center(dst)
        cy_dst = self.board.piece_y_center(self.state.height(dst))
        self._dbg('_execute_move', src=src, dst=dst, bloc=bloc, ids=ids)
        self._reset_selection()
        self.cmd_bar.show_message('')

        def on_done():
            rec = self.state.do_move(src, dst, bloc)
            _log.info("Coup %d : %s", self.state.move_count, rec.label())
            self._refresh()
            if self.state.is_won():
                _log.info("Victoire en %d coups !", self.state.move_count)
                from view import show_win_dialog
                show_win_dialog(self.root, self.cfg,
                                self.state.move_count,
                                on_replay=self._do_replay)

        self.board.animate_move(ids, cx_dst - cx_src, cy_dst - cy_src,
                                on_done,
                                x0=cx_src, y0=cy_src,
                                x1=cx_dst, y1=cy_dst)

    def _do_replay(self):
        self.state.reset()
        self.board.draw_static_background(self.state.final)
        self._refresh()

    # ── Undo / Redo / Reset ───────────────────────────────────────────────
    def do_undo(self):
        self._dbg('do_undo')
        if self.board.animating: return
        self._reset_selection()
        rec = self.state.undo()
        if rec: _log.info("Undo : %s  (coups=%d)", rec.label(), self.state.move_count)
        self._refresh()

    def do_redo(self):
        self._dbg('do_redo')
        if self.board.animating: return
        self._reset_selection()
        rec = self.state.redo()
        if rec: _log.info("Redo : %s  (coups=%d)", rec.label(), self.state.move_count)
        self._refresh()

    def do_reset(self):
        self._dbg('do_reset')
        if self.board.animating: return
        if messagebox.askyesno('RAZ', 'Recommencer depuis le début ?', default='yes'):
            self._reset_selection()
            self.state.reset()
            _log.info("RAZ")
            self._refresh()

    def show_aide(self):
        from view import show_help_dialog
        show_help_dialog(self.root, self.cfg)

    # ── Sauvegarde / chargement ───────────────────────────────────────────
    def do_save(self, path=None):
        import fileio
        if path is None:
            os.makedirs(self.cfg.paths.saves_dir, exist_ok=True)
            path = filedialog.asksaveasfilename(
                initialdir=self.cfg.paths.saves_dir,
                defaultextension=self.cfg.paths.save_extension,
                filetypes=[('Partie YAML', '*.yaml *.partie.yaml'), ('Tous', '*.*')])
        if not path: return
        try:
            fileio.save_game(self.state, path)
            self.cmd_bar.show_message(f"Sauvegardé : {os.path.basename(path)}", error=False)
        except Exception as ex:
            _log.error("Sauvegarde : %s", ex)
            messagebox.showerror('Erreur', f'Sauvegarde impossible :\n{ex}')

    def do_load(self, path=None):
        import fileio
        if path is None:
            path = filedialog.askopenfilename(
                initialdir=self.cfg.paths.saves_dir,
                filetypes=[('Partie YAML', '*.yaml *.partie.yaml'), ('Tous', '*.*')])
        if not path or not os.path.exists(path): return
        try:
            self.state = fileio.load_game(path, self.cfg)
            self._reset_selection()
            self.board.draw_static_background(self.state.final)
            self._refresh()
            self.cmd_bar.show_message(f"Chargé : {os.path.basename(path)}", error=False)
        except Exception as ex:
            _log.error("Chargement : %s", ex)
            messagebox.showerror('Erreur', f'Chargement impossible :\n{ex}')

    def do_load_init(self, path):
        import fileio
        from model import GameState
        try:
            initial, final = fileio.load_init(path)
            self.state = GameState(self.cfg, initial, final)
            self._reset_selection()
            self.board.draw_static_background(self.state.final)
            self._refresh()
        except Exception as ex:
            _log.error("Init : %s", ex)
            messagebox.showerror('Erreur', f'Init impossible :\n{ex}')

    # ── Commandes textuelles ──────────────────────────────────────────────
    def on_command(self, text: str) -> None:
        tokens = text.strip().split()
        if not tokens: return
        cmd = tokens[0].lower()
        self._dbg('on_command', cmd=cmd, args=tokens[1:])
        try:
            if   cmd == 'deplace' and len(tokens) >= 3:
                src, dst = int(tokens[1]) - 1, int(tokens[2]) - 1
                self._select_col(src); self._try_execute(dst, bloc=False)
            elif cmd == 'bloc' and len(tokens) >= 3:
                src, dst = int(tokens[1]) - 1, int(tokens[2]) - 1
                self._select_col(src); self._activate_bloc_mode()
                self._try_execute(dst, bloc=True)
            elif cmd == 'efface':   self.do_undo()
            elif cmd == 'rejoue':   self.do_redo()
            elif cmd == 'raz':      self.do_reset()
            elif cmd in ('aide', 'help', '?'): self.show_aide()
            elif cmd == 'lire' and len(tokens) >= 2:
                self.do_load(_build_path(tokens[1], self.cfg.paths.save_extension,
                                         self.cfg.paths.saves_dir))
            elif cmd == 'enregistre' and len(tokens) >= 2:
                self.do_save(_build_path(tokens[1], self.cfg.paths.save_extension,
                                         self.cfg.paths.saves_dir))
            elif cmd == 'init' and len(tokens) >= 2:
                self.do_load_init(_build_path(tokens[1], self.cfg.paths.init_extension,
                                               self.cfg.paths.init_dir))
            elif cmd == 'debug':
                info = str(self.state); print(info); _log.debug(info)
            else:
                self.cmd_bar.show_message(
                    self.cfg.str('cmd_unknown', cmd=tokens[0]), error=True)
        except (IndexError, ValueError) as ex:
            _log.warning("Commande '%s' : %s", text, ex)
            self.cmd_bar.show_message(f'Erreur : {ex}', error=True)


def _build_path(name, ext, default_dir):
    if os.sep in name or '/' in name: return name
    if not name.endswith(ext): name += ext
    return os.path.join(default_dir, name)

# end controller.py  v1.3
