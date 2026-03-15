# model.py  v1.1
from __future__ import annotations
"""
model.py — Logique du jeu (pure Python, sans Tkinter).
v1.1 : is_won utilise Counter (comparaison non-ordonnée des couleurs
       dans chaque colonne) pour supporter les états finaux généraux
       (pas uniquement le cas mono-couleur par colonne).
"""
VERSION = ('model.py', '1.1')

from collections import Counter
from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    import logger
    logger.register(VERSION)
except ImportError:
    pass


@dataclass
class MoveRecord:
    type: str   # 'simple' | 'bloc'
    src:  int
    dst:  int

    def label(self) -> str:
        tag = ' [B]' if self.type == 'bloc' else ''
        return f"C{self.src+1}\u2192C{self.dst+1}{tag}"

    def to_dict(self) -> dict:
        return {'type': self.type, 'from': self.src + 1, 'to': self.dst + 1}

    @classmethod
    def from_dict(cls, d: dict) -> 'MoveRecord':
        return cls(d['type'], d['from'] - 1, d['to'] - 1)


_StackEntry = Tuple[List[List[str]], MoveRecord]


class GameState:
    """
    columns[c] : liste de pions, index 0 = bas, -1 = sommet.
    is_won utilise Counter → l'ordre dans la colonne n'a pas d'importance.
    """

    def __init__(self, cfg, initial: List[List[str]], final: List[List[str]]):
        self.g          = cfg.game
        self.initial    = [list(c) for c in initial]
        self.final      = [list(c) for c in final]
        self.columns    = [list(c) for c in initial]
        self.move_count = 0
        self.undo_stack: List[_StackEntry] = []
        self.redo_stack: List[_StackEntry] = []

    def top(self, col: int) -> Optional[str]:
        return self.columns[col][-1] if self.columns[col] else None

    def second(self, col: int) -> Optional[str]:
        return self.columns[col][-2] if len(self.columns[col]) >= 2 else None

    def height(self, col: int) -> int:
        return len(self.columns[col])

    def free(self, col: int) -> int:
        return self.g.nb_rows - len(self.columns[col])

    def snapshot(self) -> List[List[str]]:
        return [list(c) for c in self.columns]

    def can_move(self, src: int, dst: int) -> bool:
        if src == dst:             return False
        if not self.columns[src]: return False
        return self.free(dst) >= 1

    def can_bloc(self, src: int, dst: int) -> bool:
        """Bloc valide : couple identique au sommet de src,
        dst a ≥2 cases libres ET sommet de dst == même couleur."""
        if src == dst:                        return False
        if len(self.columns[src]) < 2:        return False
        if self.top(src) != self.second(src): return False
        if self.free(dst) < 2:                return False
        if not self.columns[dst]:             return False
        return self.top(dst) == self.top(src)

    def has_bloc_candidate(self, col: int) -> bool:
        return (len(self.columns[col]) >= 2 and
                self.columns[col][-1] == self.columns[col][-2])

    def valid_dests(self, src: int, bloc: bool) -> List[int]:
        fn = self.can_bloc if bloc else self.can_move
        return [c for c in range(self.g.nb_columns) if fn(src, c)]

    def do_move(self, src: int, dst: int, bloc: bool = False) -> MoveRecord:
        snap = self.snapshot()
        if bloc:
            p1 = self.columns[src].pop()
            p2 = self.columns[src].pop()
            self.columns[dst].append(p2)
            self.columns[dst].append(p1)
        else:
            self.columns[dst].append(self.columns[src].pop())
        rec = MoveRecord('bloc' if bloc else 'simple', src, dst)
        self.undo_stack.append((snap, rec))
        self.redo_stack.clear()
        self.move_count += 1
        return rec

    def undo(self) -> Optional[MoveRecord]:
        if not self.undo_stack: return None
        snap, rec = self.undo_stack.pop()
        self.redo_stack.append((self.snapshot(), rec))
        self.columns    = snap
        self.move_count -= 1
        return rec

    def redo(self) -> Optional[MoveRecord]:
        if not self.redo_stack: return None
        snap, rec = self.redo_stack.pop()
        self.undo_stack.append((self.snapshot(), rec))
        self.columns    = snap
        self.move_count += 1
        return rec

    def reset(self) -> None:
        self.columns    = [list(c) for c in self.initial]
        self.move_count = 0
        self.undo_stack.clear()
        self.redo_stack.clear()

    def is_won(self) -> bool:
        """
        Victoire si chaque colonne contient EXACTEMENT les mêmes couleurs
        que la colonne finale correspondante (Counter, ordre indifférent).
        Exemple : ['O','O','R','R','O'] == ['R','R','O','O','O'] → True
        """
        return all(Counter(self.columns[c]) == Counter(self.final[c])
                   for c in range(self.g.nb_columns))

    def __repr__(self) -> str:
        lines = []
        for row in range(self.g.nb_rows - 1, -1, -1):
            line = '|'
            for col in range(self.g.nb_columns):
                c = self.columns[col]
                line += c[row] if row < len(c) else '.'
            lines.append(line + '|')
        return '\n'.join(lines)

# end model.py  v1.1
