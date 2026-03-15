# view.py  v1.3
from __future__ import annotations
"""
view.py — Composants visuels Tkinter.
v1.3 :
  • Séparation propre clic / drag via DRAG_THRESHOLD (8px).
    <ButtonPress> ne déclenche PLUS de logique jeu → fin du bug
    "press réécrase la source avant que click exécute".
  • canvas_to_row_from_bottom(y) pour détecter quel pion a été cliqué.
  • start_drag_ghost(col, height, count, drag_x, drag_y) appelé par le
    contrôleur depuis _on_drag_start.
  • draw_static_background utilise sorted(final[col]) : couleurs
    identiques aux pions quelle que soit la configuration de fin.
"""
VERSION = ('view.py', '1.3')

import tkinter as tk
from tkinter import scrolledtext
from typing import List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from model  import GameState
    from config import Config

try:
    import logger
    logger.register(VERSION)
    _log = logger.get('view')
except ImportError:
    import logging
    _log = logging.getLogger('view')


# ─────────────────────────────────────────────────────────────────────────────
def blend_hex(fg: str, alpha: float, bg: str) -> str:
    def ch(h, i): return int(h[i:i+2], 16)
    r = int(ch(fg, 1) * alpha + ch(bg, 1) * (1 - alpha))
    g = int(ch(fg, 3) * alpha + ch(bg, 3) * (1 - alpha))
    b = int(ch(fg, 5) * alpha + ch(bg, 5) * (1 - alpha))
    return f'#{r:02x}{g:02x}{b:02x}'


def ease(t: float, mode: str) -> float:
    t = max(0.0, min(1.0, t))
    if mode == 'linear':   return t
    if mode == 'ease_in':  return t * t
    if mode == 'ease_out': return 2 * t - t * t
    return t * t * (3 - 2 * t)


# ─────────────────────────────────────────────────────────────────────────────
#  BoardView
# ─────────────────────────────────────────────────────────────────────────────
class BoardView:
    """
    Couches de dessin (bas → haut) :
      bg · grid (statiques) · bg_tint · piece · hl_border · guide · ghost
    """
    DRAG_THRESHOLD: int = 8

    def __init__(self, parent: tk.Widget, cfg):
        self.cfg     = cfg
        self.g       = cfg.game
        self.gr      = cfg.grid
        self.cs      = cfg.grid.cell_size
        self.nb_cols = cfg.game.nb_columns
        self.nb_rows = cfg.game.nb_rows
        self._debug  = cfg.debug.enabled

        W = self.nb_cols * self.cs
        H = self.nb_rows * self.cs

        self.canvas = tk.Canvas(parent, width=W, height=H,
                                bg=self.gr.grid_bg,
                                highlightthickness=0, bd=0)
        self.piece_ids: dict     = {}
        self.animating: bool     = False

        # état drag interne
        self._press_x:    float     = 0.0
        self._press_y:    float     = 0.0
        self._press_col:  int       = -1
        self._press_row:  int       = -1
        self._drag_on:    bool      = False
        self._drag_lx:    float     = 0.0
        self._drag_ly:    float     = 0.0
        self._ghost_ids:  List[int] = []

        # callbacks contrôleur
        self._click_cb:      Optional[Callable] = None  # (col, row_from_bottom)
        self._drag_start_cb: Optional[Callable] = None  # (col, row_from_bottom)
        self._drag_end_cb:   Optional[Callable] = None  # (dst_col)

        self.canvas.bind('<ButtonPress-1>',   self._evt_press)
        self.canvas.bind('<B1-Motion>',       self._evt_motion)
        self.canvas.bind('<ButtonRelease-1>', self._evt_release)
        if self._debug:
            self.canvas.bind('<Motion>', self._evt_hover)

    # ── API callbacks ─────────────────────────────────────────────────────
    def bind_click(self, cb):      self._click_cb      = cb
    def bind_drag_start(self, cb): self._drag_start_cb = cb
    def bind_drag_end(self, cb):   self._drag_end_cb   = cb

    # ── Événements ────────────────────────────────────────────────────────
    def _evt_press(self, event) -> None:
        if self.animating: return
        self._press_x   = float(event.x)
        self._press_y   = float(event.y)
        self._press_col = self.canvas_to_col(event.x)
        self._press_row = self.canvas_to_row_from_bottom(event.y)
        self._drag_on   = False
        if self._debug:
            _log.debug("PRESS (%d,%d) col=%d row=%d",
                       event.x, event.y, self._press_col, self._press_row)

    def _evt_motion(self, event) -> None:
        if self.animating: return
        if not self._drag_on:
            dx = event.x - self._press_x
            dy = event.y - self._press_y
            if abs(dx) > self.DRAG_THRESHOLD or abs(dy) > self.DRAG_THRESHOLD:
                self._drag_on = True
                if self._debug:
                    _log.debug("DRAG_START col=%d row=%d", self._press_col, self._press_row)
                if self._drag_start_cb:
                    # Le contrôleur appelle start_drag_ghost() → _drag_lx/ly initialisés
                    self._drag_start_cb(self._press_col, self._press_row)
        if self._drag_on and self._ghost_ids:
            mx, my = float(event.x), float(event.y)
            self.move_ghost(self._ghost_ids, mx - self._drag_lx, my - self._drag_ly)
            self._drag_lx, self._drag_ly = mx, my

    def _evt_release(self, event) -> None:
        if self.animating: return
        if self._drag_on:
            self.delete_ghost()
            self._ghost_ids = []
            self._drag_on   = False
            dst = self.canvas_to_col(event.x)
            if self._debug:
                _log.debug("DRAG_END dst=%d", dst)
            if self._drag_end_cb:
                self._drag_end_cb(dst)
        else:
            col = self.canvas_to_col(event.x)
            row = self.canvas_to_row_from_bottom(event.y)
            if self._debug:
                _log.debug("CLICK (%d,%d) col=%d row=%d", event.x, event.y, col, row)
            if self._click_cb:
                self._click_cb(col, row)

    def _evt_hover(self, event) -> None:
        _log.debug("HOVER (%d,%d) col=%d row=%d",
                   event.x, event.y,
                   self.canvas_to_col(event.x),
                   self.canvas_to_row_from_bottom(event.y))

    # ── API ghost (appelée par le contrôleur) ─────────────────────────────
    def start_drag_ghost(self, col: int, col_height: int,
                         count: int, drag_x: float, drag_y: float) -> None:
        self._ghost_ids = self.create_ghost(col, col_height, count)
        self._drag_lx   = drag_x
        self._drag_ly   = drag_y

    # ── Coordonnées ──────────────────────────────────────────────────────
    def col_x_center(self, col: int) -> int:
        return col * self.cs + self.cs // 2

    def piece_y_center(self, row_from_bottom: int) -> int:
        return (self.nb_rows - 1 - row_from_bottom) * self.cs + self.cs // 2

    def canvas_to_col(self, x: float) -> int:
        col = int(x) // self.cs
        return col if 0 <= col < self.nb_cols else -1

    def canvas_to_row_from_bottom(self, y: float) -> int:
        row_from_top = int(y) // self.cs
        return self.nb_rows - 1 - row_from_top

    # ── Fond statique ────────────────────────────────────────────────────
    def draw_static_background(self, final: List[List[str]]) -> None:
        """
        sorted(final[col]) garantit que les couleurs affichées
        sont regroupées (bandes) et identiques à celles des pions.
        Cas mono-couleur : sorted(['O','O','O','O','O']) = idem → tout orange.
        """
        self.canvas.delete('bg')
        self.canvas.delete('grid')
        gr       = self.gr
        nb_final = self.g.nb_rows_initial

        for col in range(self.nb_cols):
            display = sorted(final[col])
            for row in range(self.nb_rows):
                x1 = col * self.cs
                y1 = (self.nb_rows - 1 - row) * self.cs
                x2, y2 = x1 + self.cs, y1 + self.cs
                if row < nb_final and row < len(display):
                    ci   = self.cfg.get_color(display[row])
                    fill = blend_hex(ci.fill, gr.target_alpha, gr.grid_bg)
                else:
                    fill = gr.empty_cell_color
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill, outline='', tags='bg')

        W = self.nb_cols * self.cs
        H = self.nb_rows * self.cs
        if gr.inner_v_width > 0:
            for col in range(1, self.nb_cols):
                x = col * self.cs
                self.canvas.create_line(x, 0, x, H,
                    fill=gr.inner_v_color, width=gr.inner_v_width, tags='grid')
        if gr.inner_h_width > 0:
            for row in range(1, self.nb_rows):
                y = row * self.cs
                self.canvas.create_line(0, y, W, y,
                    fill=gr.inner_h_color, width=gr.inner_h_width, tags='grid')
        bw = gr.outer_border_width
        if bw > 0:
            hw = bw // 2
            self.canvas.create_rectangle(hw, hw, W - hw, H - hw,
                fill='', outline=gr.outer_border_color, width=bw, tags='grid')
        self.canvas.tag_lower('bg')
        self.canvas.tag_raise('grid')

    # ── Rafraîchissement ──────────────────────────────────────────────────
    def refresh(self, state, selected: int = -1,
                bloc_mode: bool = False,
                valid_dests: Optional[List[int]] = None) -> None:
        self.canvas.delete('bg_tint')
        self.canvas.delete('piece')
        self.canvas.delete('hl_border')
        gr = self.gr

        # 1. Teintes AVANT les pions
        if selected >= 0:
            alpha = 0.40 if bloc_mode else 0.30
            self._draw_col_fill(selected, gr.highlight_color, alpha, 'bg_tint')
        if valid_dests:
            for col in valid_dests:
                self._draw_col_fill(col, gr.valid_color, 0.22, 'bg_tint')

        # 2. Pions
        for col in range(self.nb_cols):
            for pos, ck in enumerate(state.columns[col]):
                self._draw_piece(col, pos, ck)

        # 3. Contours (fill='')
        if selected >= 0:
            w = gr.highlight_width + (2 if bloc_mode else 0)
            self._draw_col_border(selected, gr.highlight_color, w, 'hl_border')
            if bloc_mode:
                self._draw_col_border(selected, '#FFFFFF', 1, 'hl_border')
        if valid_dests:
            for col in valid_dests:
                self._draw_col_border(col, gr.valid_color,
                                      gr.highlight_width, 'hl_border')

        self.canvas.tag_raise('grid')
        self.canvas.tag_raise('bg_tint')
        self.canvas.tag_raise('piece')
        self.canvas.tag_raise('hl_border')

    def _draw_col_fill(self, col, color, alpha, tag):
        t = blend_hex(color, alpha, self.gr.grid_bg)
        self.canvas.create_rectangle(
            col * self.cs + 1, 1,
            (col + 1) * self.cs - 1, self.nb_rows * self.cs - 1,
            fill=t, outline='', tags=tag)

    def _draw_piece(self, col, pos, color_key):
        ci = self.cfg.get_color(color_key)
        r  = self.cfg.pieces.radius
        cx = self.col_x_center(col)
        cy = self.piece_y_center(pos)
        oid = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=ci.fill, outline=ci.outline,
            width=self.cfg.pieces.outline_width, tags='piece')
        tid = None
        if self.cfg.pieces.show_label:
            bold = 'bold' if self.cfg.pieces.label_font_bold else ''
            tid = self.canvas.create_text(
                cx, cy, text=color_key, fill=ci.text,
                font=(self.cfg.pieces.label_font,
                      self.cfg.pieces.label_font_size, bold),
                tags='piece')
        self.piece_ids[(col, pos)] = (oid, tid)

    def _draw_col_border(self, col, color, width, tag):
        hw = max(1, width // 2)
        self.canvas.create_rectangle(
            col * self.cs + hw, hw,
            (col + 1) * self.cs - hw, self.nb_rows * self.cs - hw,
            fill='', outline=color, width=width, tags=tag)

    # ── Guide & animation ─────────────────────────────────────────────────
    def draw_guide(self, x0, y0, x1, y1):
        gl = self.cfg.animation.guide_line
        if not gl.enabled: return
        dash = tuple(gl.dash) if gl.dash else ()
        self.canvas.create_line(x0, y0, x1, y1,
            fill=gl.color, width=gl.width, dash=dash, tags='guide')

    def erase_guide(self):
        self.canvas.delete('guide')

    def animate_move(self, item_ids, total_dx, total_dy, on_done,
                     x0=0, y0=0, x1=0, y1=0):
        anim = self.cfg.animation
        if not anim.enabled:
            for iid in item_ids:
                self.canvas.move(iid, total_dx, total_dy)
            on_done()
            return
        self.animating  = True
        total_frames    = max(1, int(anim.fps * anim.duration_ms / 1000))
        frame_ms        = max(1, 1000 // anim.fps)
        mode            = anim.easing
        frame, prev_et  = [0], [0.0]
        self.draw_guide(x0, y0, x1, y1)
        def tick():
            f = frame[0]
            if f >= total_frames:
                rem = 1.0 - prev_et[0]
                for iid in item_ids:
                    self.canvas.move(iid, rem * total_dx, rem * total_dy)
                self.erase_guide()
                self.animating = False
                on_done()
                return
            t  = (f + 1) / total_frames
            et = ease(t, mode)
            d  = et - prev_et[0]
            for iid in item_ids:
                self.canvas.move(iid, d * total_dx, d * total_dy)
            prev_et[0] = et
            frame[0]  += 1
            self.canvas.after(frame_ms, tick)
        self.canvas.after(16, tick)

    def get_top_item_ids(self, col, col_height, count=1):
        ids = []
        for pos in range(col_height - count, col_height):
            key = (col, pos)
            if key in self.piece_ids:
                oid, tid = self.piece_ids[key]
                ids.append(oid)
                if tid is not None:
                    ids.append(tid)
        return ids

    # ── Ghost ─────────────────────────────────────────────────────────────
    def create_ghost(self, col, col_height, count=1):
        ids = []
        for i in range(count):
            pos = col_height - 1 - i
            if pos < 0: break
            fill = '#888888'
            if (col, pos) in self.piece_ids:
                oid, _ = self.piece_ids[(col, pos)]
                fill = self.canvas.itemcget(oid, 'fill')
            cx = self.col_x_center(col)
            cy = self.piece_y_center(pos)
            r  = self.cfg.pieces.radius
            gid = self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=fill, outline='white', width=2,
                stipple='gray50', tags='ghost')
            ids.append(gid)
        self.canvas.tag_raise('ghost')
        return ids

    def move_ghost(self, ids, dx, dy):
        for gid in ids: self.canvas.move(gid, dx, dy)

    def delete_ghost(self):
        self.canvas.delete('ghost')

    def pack(self, **kw): self.canvas.pack(**kw)


# ─────────────────────────────────────────────────────────────────────────────
#  SpecialPanel
# ─────────────────────────────────────────────────────────────────────────────
class SpecialPanel:
    CELL_NAMES = ['escape', 'bloc', 'undo', 'redo', 'aide']

    def __init__(self, parent, cfg, board_height: int):
        from types import SimpleNamespace as NS
        sp   = cfg.special_cells
        self.cfg  = cfg
        self.btns = {}
        size   = sp.size
        margin = sp.margin
        bold   = 'bold' if sp.font_bold else ''
        font   = (sp.font, sp.font_size, bold)
        self.frame = tk.Frame(parent, bg=cfg.window.bg,
                              width=size + margin * 2)
        self.frame.pack_propagate(False)
        n   = len(self.CELL_NAMES)
        pad = max(0, (board_height - n * (size + margin)) // 2)
        tk.Frame(self.frame, height=pad, bg=cfg.window.bg).pack()
        aide_cell = NS(label='? Aide', bg='#001A00', fg='#52B788', bg_hover='#003300')
        cells = {'escape': sp.escape, 'bloc': sp.bloc,
                 'undo': sp.undo, 'redo': sp.redo, 'aide': aide_cell}
        for name in self.CELL_NAMES:
            cc  = cells[name]
            btn = tk.Button(self.frame, text=cc.label,
                            bg=cc.bg, fg=cc.fg,
                            activebackground=cc.bg_hover, activeforeground=cc.fg,
                            relief=tk.FLAT, bd=0, font=font,
                            width=int(size / 7), height=2, cursor='hand2')
            btn.pack(pady=(margin // 2, margin // 2), padx=margin)
            btn.bind('<Enter>', lambda e, b=btn, c=cc: b.config(bg=c.bg_hover))
            btn.bind('<Leave>', lambda e, b=btn, c=cc: b.config(bg=c.bg))
            self.btns[name] = btn

    def bind(self, name, cb):
        if name in self.btns: self.btns[name].config(command=cb)

    def set_active(self, name, active):
        if name not in self.btns: return
        sp = self.cfg.special_cells
        if not hasattr(sp, name): return
        cc = getattr(sp, name)
        self.btns[name].config(bg=cc.bg_hover if active else cc.bg)

    def pack(self, **kw): self.frame.pack(**kw)


# ─────────────────────────────────────────────────────────────────────────────
#  TapePanel
# ─────────────────────────────────────────────────────────────────────────────
class TapePanel:
    def __init__(self, parent, cfg, on_raz=None, on_save=None, on_load=None):
        sp   = cfg.side_panel
        self.cfg = cfg
        self.frame = tk.Frame(parent, bg=sp.bg, width=sp.width,
                              highlightthickness=sp.border_width,
                              highlightbackground=sp.border_color)
        self.frame.pack_propagate(False)
        cnt  = sp.counter
        bold = 'bold' if cnt.font_bold else ''
        tk.Label(self.frame, text=cnt.label, bg=sp.bg, fg=cnt.label_color,
                 font=(cnt.font, cnt.label_size)).pack(pady=(10, 0))
        self.lbl_count = tk.Label(self.frame, text='0', bg=sp.bg, fg=cnt.color,
                                  font=(cnt.font, cnt.font_size, bold))
        self.lbl_count.pack()
        tk.Frame(self.frame, height=1, bg=sp.border_color).pack(fill='x', padx=6)
        tape    = sp.tape
        t_frame = tk.Frame(self.frame, bg=sp.bg)
        t_frame.pack(fill='both', expand=True, padx=4, pady=4)
        self.text = tk.Text(t_frame, bg=tape.bg, fg=tape.fg,
                            font=(tape.font, tape.font_size),
                            relief=tk.FLAT, bd=0, state='disabled',
                            wrap='none', cursor='arrow',
                            selectbackground=tape.bg)
        sb = tk.Scrollbar(t_frame, orient='vertical', command=self.text.yview)
        self.text.config(yscrollcommand=sb.set)
        self.text.pack(side='left', fill='both', expand=True)
        if tape.scrollbar: sb.pack(side='right', fill='y')
        self.text.tag_config('normal',  foreground=tape.fg)
        self.text.tag_config('bloc',    foreground=tape.fg_bloc)
        self.text.tag_config('current', foreground=tape.fg_current,
                             font=(tape.font, tape.font_size, 'bold'))
        self.text.tag_config('annule',  foreground=tape.fg_undo)
        self.text.tag_config('sep',     foreground='#CCBBAA')
        btns = sp.buttons
        for lk, cb in [('raz', on_raz), ('save', on_save), ('load', on_load)]:
            bc  = getattr(btns, lk)
            btn = tk.Button(self.frame, text=bc.label,
                            bg=bc.bg, fg=bc.fg,
                            activebackground=bc.bg_hover, activeforeground=bc.fg,
                            relief=tk.FLAT, bd=0,
                            font=(btns.font, btns.font_size, 'bold'),
                            height=1, cursor='hand2', command=cb or (lambda: None))
            btn.pack(fill='x', padx=6, pady=2)
            btn.bind('<Enter>', lambda e, b=btn, bc_=bc: b.config(bg=bc_.bg_hover))
            btn.bind('<Leave>', lambda e, b=btn, bc_=bc: b.config(bg=bc_.bg))

    def update(self, undo_stack, redo_stack, move_count):
        tape = self.cfg.side_panel.tape
        self.lbl_count.config(text=str(move_count))
        self.text.config(state='normal')
        self.text.delete('1.0', 'end')
        n = len(undo_stack)
        for i, (_, rec) in enumerate(undo_stack):
            tag = 'current' if i == n - 1 else ('bloc' if rec.type == 'bloc' else 'normal')
            t   = tape.tag_bloc if rec.type == 'bloc' else tape.tag_simple
            self.text.insert('end', f"{i+1:>3}. C{rec.src+1}\u2192C{rec.dst+1}{t}\n", tag)
        if redo_stack:
            self.text.insert('end', tape.separator_char * 14 + '\n', 'sep')
            for j, (_, rec) in enumerate(reversed(redo_stack)):
                t = tape.tag_bloc if rec.type == 'bloc' else tape.tag_simple
                self.text.insert('end',
                    f"{n+1+j:>3}. C{rec.dst+1}\u2192C{rec.src+1}{t} \u21a9\n", 'annule')
        self.text.config(state='disabled')
        self.text.see('end')

    def pack(self, **kw): self.frame.pack(**kw)


# ─────────────────────────────────────────────────────────────────────────────
#  CommandBar
# ─────────────────────────────────────────────────────────────────────────────
class CommandBar:
    def __init__(self, parent, cfg, on_command):
        cb   = cfg.command_bar
        self.cfg = cfg
        self.frame = tk.Frame(parent, bg=cb.bg,
                              highlightthickness=1,
                              highlightbackground=cb.border_top)
        tk.Label(self.frame, text=cb.prompt, bg=cb.bg, fg=cb.prompt_color,
                 font=(cb.font, cb.font_size, 'bold')).pack(side='left', padx=(6, 0))
        self.var   = tk.StringVar()
        self.entry = tk.Entry(self.frame, textvariable=self.var,
                              bg=cb.bg, fg=cb.fg,
                              insertbackground=cb.cursor_color,
                              relief=tk.FLAT, bd=0,
                              font=(cb.font, cb.font_size))
        self.entry.pack(side='left', fill='x', expand=True, ipady=6)
        self.entry.bind('<Return>',   lambda e: self._submit())
        self.entry.bind('<FocusIn>',  self._clear_ph)
        self.entry.bind('<FocusOut>', self._set_ph)
        self.lbl_msg = tk.Label(self.frame, text='', bg=cb.bg, fg='#FF6B6B',
                                font=(cb.font, cb.font_size - 1))
        self.lbl_msg.pack(side='right', padx=8)
        self._on_command = on_command
        self._ph         = cb.placeholder
        self._set_ph(None)

    def _set_ph(self, _):
        if not self.var.get():
            self.entry.config(fg='#444466')
            self.var.set(self._ph)

    def _clear_ph(self, _):
        if self.var.get() == self._ph:
            self.var.set('')
            self.entry.config(fg=self.cfg.command_bar.fg)

    def _submit(self):
        t = self.var.get().strip()
        if t and t != self._ph:
            self.var.set('')
            self.show_message('')
            self._on_command(t)

    def show_message(self, msg, error=True):
        self.lbl_msg.config(text=msg, fg='#FF6B6B' if error else '#52B788')

    def focus(self):      self.entry.focus_set()
    def pack(self, **kw): self.frame.pack(**kw)


# ─────────────────────────────────────────────────────────────────────────────
#  Dialogs
# ─────────────────────────────────────────────────────────────────────────────
def show_win_dialog(root, cfg, move_count, on_replay):
    wd  = cfg.win_dialog
    dlg = tk.Toplevel(root)
    dlg.title('')
    dlg.configure(bg=wd.bg, highlightthickness=wd.border_width,
                  highlightbackground=wd.border_color)
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.transient(root)
    tk.Label(dlg, text='\U0001f3c6', bg=wd.bg,
             font=('Helvetica', 36)).pack(pady=(20, 4))
    tk.Label(dlg, text='F\u00e9licitations !', bg=wd.bg, fg=wd.title_color,
             font=('Helvetica', wd.title_font_size, 'bold')).pack()
    tk.Label(dlg, text=str(move_count), bg=wd.bg, fg=wd.score_color,
             font=('Helvetica', wd.score_font_size, 'bold')).pack(pady=4)
    tk.Label(dlg, text='d\u00e9placements', bg=wd.bg, fg=wd.text_color,
             font=('Helvetica', 13)).pack()
    def _r(): dlg.destroy(); on_replay()
    tk.Button(dlg, text=wd.button_label, bg=wd.border_color, fg=wd.bg,
              activebackground='#B8860B', relief=tk.FLAT, bd=0,
              font=('Helvetica', 13, 'bold'),
              padx=24, pady=8, cursor='hand2', command=_r).pack(pady=20)
    dlg.update_idletasks()
    x = root.winfo_x() + (root.winfo_width()  - dlg.winfo_width())  // 2
    y = root.winfo_y() + (root.winfo_height() - dlg.winfo_height()) // 2
    dlg.geometry(f'+{x}+{y}')


AIDE_TEXTE = """\
\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
\u2551       PUZZLE DES COULEURS \u2014 Aide          \u2551
\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d

OBJECTIF
  Distribuer les pions pour que chaque
  colonne contienne exactement les couleurs
  indiquées en fond (peu importe l'ordre).

R\u00c8GLES
  D\u00e9placement SIMPLE (1 coup) :
    Cliquer sur le pion DU HAUT d'une colonne
    (ou sur la zone vide au-dessus) puis sur
    la colonne de destination.

  D\u00e9placement BLOC (1 coup) :
    Conditions requises :
      \u2022 2 pions identiques au sommet de la source
      \u2022 Destination : \u22652 cases libres
        ET pion de m\u00eame couleur au sommet
    Comment l'activer :
      \u2022 Cliquer sur le 2\u00e9 pion depuis le haut
      \u2022 OU bouton \u2263 Bloc apr\u00e8s s\u00e9lection
    D\u00e9faire le mode BLOC :
      \u2022 Bouton \u2715 Esc ou touche Echap

SOURIS
  Clic sur col. vide ou pion du haut
                   \u2192 SIMPLE (contour dor\u00e9)
  Clic sur le 2\u00e9 pion (couple identique)
                   \u2192 BLOC   (contour bleu+blanc)
  Re-clic source sans couple \u2192 rien
  Re-clic source avec couple \u2192 BLOC
  Clic col. destination \u2192 exécute
  Drag depuis n'importe quel pion \u2192 drag simple
  Drag depuis 2\u00e9 pion d'un couple \u2192 drag bloc
  Clic hors de la grille \u2192 annule s\u00e9lection

BOUTONS
  \u2715 Esc  Annule s\u00e9lection  (ou Echap)
  \u2263 Bloc Activer/d\u00e9sactiver mode bloc
  \u21a9 Undo  Annuler coup  (ou Ctrl+Z)
  \u21aa Redo  Rejouer coup  (ou Ctrl+Y)
  ? Aide  Cette fen\u00eatre      (ou F1)

COMMANDES
  deplace C1 C2 / bloc C1 C2 / efface / rejoue
  raz / lire <f> / enregistre <f> / aide / ?

RACCOURCIS
  Ctrl+Z/Y  Undo/Redo    Ctrl+S/O  Save/Load
  Echap  Annuler          F1  Aide
"""


def show_help_dialog(root, cfg):
    bg  = cfg.window.bg
    fg  = '#C0C0D8'
    dlg = tk.Toplevel(root)
    dlg.title('Aide \u2014 Puzzle des Couleurs')
    dlg.configure(bg=bg)
    dlg.resizable(True, True)
    dlg.transient(root)
    txt = scrolledtext.ScrolledText(
        dlg, bg='#0A0A1A', fg=fg, font=('Courier', 11),
        relief=tk.FLAT, bd=0, wrap='word', width=52, height=38)
    txt.pack(fill='both', expand=True, padx=8, pady=8)
    txt.insert('end', AIDE_TEXTE)
    txt.config(state='disabled')
    tk.Button(dlg, text='Fermer', bg='#1A1A2E', fg=fg,
              activebackground='#2A2A4E', relief=tk.FLAT, bd=0,
              font=('Helvetica', 11), padx=20, pady=6,
              cursor='hand2', command=dlg.destroy).pack(pady=(0, 8))
    dlg.update_idletasks()
    x = root.winfo_x() + (root.winfo_width()  - dlg.winfo_width())  // 2
    y = root.winfo_y() + (root.winfo_height() - dlg.winfo_height()) // 2
    dlg.geometry(f'+{x}+{y}')

# end view.py  v1.3
