"""
engine.py
=========
python-chess integration, curriculum scenarios, and the Behavioral Flaw
Engine.

This module is deliberately framework-agnostic: it knows nothing about
FastAPI or the database. It exposes:

* SCENARIOS         -- the 4-level curriculum (FEN + briefing metadata)
* TacticalEngine    -- a thin wrapper around ``chess.Board`` that validates
                       commander moves and replies with an opposing move.
* analyse_flaws()   -- inspects a move against the live position and the
                       historical timeline to flag structural flaws.

Military lexicon is used in all human-facing strings; raw chess terms are
confined to internal logic only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import chess

# ---------------------------------------------------------------------------
# Lexicon — military designation for each asset class
# ---------------------------------------------------------------------------

ASSET_NAMES: Dict[int, str] = {
    chess.PAWN: "Infantry",
    chess.KNIGHT: "Spy",
    chess.BISHOP: "Diagonal Sniper",
    chess.ROOK: "Heavy Armor",
    chess.QUEEN: "Strike Commander",
    chess.KING: "Commander-in-Chief",
}

# Material weight (in "supply points") used by ruthless-prioritization checks.
ASSET_VALUE: Dict[int, int] = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,  # priceless; never traded for material
}


def asset_name(piece_type: int) -> str:
    return ASSET_NAMES.get(piece_type, "Unknown Asset")


# ---------------------------------------------------------------------------
# Curriculum scenarios
# ---------------------------------------------------------------------------

@dataclass
class Scenario:
    level: int
    codename: str
    difficulty: str
    fen: str
    objective: str
    briefing: str
    teaches_flaw: str  # flaw key this mission is designed to drill


# NOTE: All FENs are legal positions with White (the commander) to move.
SCENARIOS: Dict[int, Scenario] = {
    1: Scenario(
        level=1,
        codename="BASIC COHESION",
        difficulty="Easy",
        # Standard opening structure: forces infantry/spy coordination.
        fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        objective="Advance your Spies (Knights) only with Infantry support behind them.",
        briefing=(
            "Commander, the front is quiet but green. Your task is COHESION. "
            "Do not let a single Spy slip into enemy territory without an "
            "Infantry column anchoring its retreat. Hold the line, move as a "
            "platoon."
        ),
        teaches_flaw="lone_ranger",
    ),
    2: Scenario(
        level=2,
        codename="DELAYED THUNDER",
        difficulty="Medium",
        # Open-ish middlegame where a sacrifice opens a file 3 moves later.
        fen="r2qkb1r/ppp2ppp/2n2n2/3pp3/3PP3/2N2N2/PPP2PPP/R1BQKB1R w KQkq - 0 6",
        objective="Sacrifice an asset now to seize a critical lane within 3 turns.",
        briefing=(
            "Intelligence confirms the enemy column will buckle — but not "
            "today. Drop an asset into the grinder NOW so the lane opens in "
            "three turns. Patience is a weapon. Calculate the delayed payoff."
        ),
        teaches_flaw="panic_abandonment",
    ),
    3: Scenario(
        level=3,
        codename="GLASS TRAP",
        difficulty="Complex",
        # A tempting capture that walks into a diagonal sniper / fork bait.
        fen="r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQ1RK1 w kq - 6 5",
        objective="Refuse the obvious bait; the textbook capture snaps a trap shut.",
        briefing=(
            "The enemy has left a juicy asset hanging in the open. It is BAIT. "
            "Every academy graduate takes it — and every one of them walks "
            "into a Diagonal Sniper's crossfire. Read the board, not the "
            "manual."
        ),
        teaches_flaw="tunnel_vision",
    ),
    4: Scenario(
        level=4,
        codename="COLD STEEL",
        difficulty="Deeply Complex",
        # Sharp endgame: must shed material to force the objective.
        fen="6k1/5ppp/8/8/8/8/3Q1PPP/6K1 w - - 0 1",
        objective="Trade high-value assets ruthlessly to complete the mission.",
        briefing=(
            "Endgame. No reinforcements are coming. Sentiment will get your "
            "platoon killed. If sacrificing the Strike Commander completes the "
            "objective, you sacrifice the Strike Commander. Total tactical "
            "coldness, Commander."
        ),
        teaches_flaw="panic_abandonment",
    ),
}


def get_scenario(level: int) -> Scenario:
    return SCENARIOS.get(level, SCENARIOS[1])


# ---------------------------------------------------------------------------
# Tactical engine
# ---------------------------------------------------------------------------

@dataclass
class MoveOutcome:
    ok: bool
    reason: str = ""
    user_san: str = ""
    enemy_san: str = ""
    enemy_uci: str = ""
    fen: str = ""
    is_capture: bool = False
    captured_asset: Optional[str] = None
    moved_asset: Optional[str] = None
    game_over: bool = False
    result: Optional[str] = None  # 'win' | 'loss' | 'draw'
    flaws: List[str] = field(default_factory=list)


class TacticalEngine:
    """Validates commander moves and produces a deterministic enemy reply."""

    def __init__(self, fen: str):
        self.board = chess.Board(fen)

    # -- enemy AI ----------------------------------------------------------
    def _enemy_reply(self) -> Optional[chess.Move]:
        """
        A lightweight 1-ply enemy: prefer the highest-value capture, else a
        central/developing move, else the first legal move. Deterministic so
        scenarios behave predictably for the curriculum.
        """
        legal = list(self.board.legal_moves)
        if not legal:
            return None

        best_move = None
        best_score = -1
        for mv in legal:
            score = 0
            if self.board.is_capture(mv):
                victim = self.board.piece_at(mv.to_square)
                if victim is not None:
                    score = ASSET_VALUE.get(victim.piece_type, 0) * 10
                else:  # en-passant
                    score = ASSET_VALUE[chess.PAWN] * 10
            # Mild central preference as a tie-breaker.
            to_file = chess.square_file(mv.to_square)
            to_rank = chess.square_rank(mv.to_square)
            score += 4 - (abs(3.5 - to_file) + abs(3.5 - to_rank))
            if score > best_score:
                best_score = score
                best_move = mv
        return best_move

    # -- public API --------------------------------------------------------
    def apply_user_move(self, move_uci: str) -> MoveOutcome:
        """Apply the commander's move (UCI) and return the full outcome."""
        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError:
            return MoveOutcome(ok=False, reason="Malformed transmission (bad UCI).")

        if move not in self.board.legal_moves:
            return MoveOutcome(ok=False, reason="Illegal manoeuvre — rejected by the field.")

        moved_piece = self.board.piece_at(move.from_square)
        is_capture = self.board.is_capture(move)
        captured_piece = self.board.piece_at(move.to_square)

        user_san = self.board.san(move)
        self.board.push(move)

        outcome = MoveOutcome(
            ok=True,
            user_san=user_san,
            is_capture=is_capture,
            captured_asset=asset_name(captured_piece.piece_type) if captured_piece else None,
            moved_asset=asset_name(moved_piece.piece_type) if moved_piece else None,
            fen=self.board.fen(),
        )

        # Did the commander just end the war?
        if self._check_terminal(outcome, commander_just_moved=True):
            return outcome

        # Enemy responds.
        reply = self._enemy_reply()
        if reply is not None:
            outcome.enemy_san = self.board.san(reply)
            outcome.enemy_uci = reply.uci()
            self.board.push(reply)
            outcome.fen = self.board.fen()
            self._check_terminal(outcome, commander_just_moved=False)

        return outcome

    def _check_terminal(self, outcome: MoveOutcome, commander_just_moved: bool) -> bool:
        if self.board.is_checkmate():
            outcome.game_over = True
            # If it is now Black's turn to move and they are mated, White won.
            outcome.result = "win" if commander_just_moved else "loss"
            return True
        if self.board.is_stalemate() or self.board.is_insufficient_material() or \
                self.board.can_claim_fifty_moves():
            outcome.game_over = True
            outcome.result = "draw"
            return True
        return False


# ---------------------------------------------------------------------------
# Behavioral Flaw Engine
# ---------------------------------------------------------------------------

def _is_deep_in_enemy_territory(square: int) -> bool:
    """True if the square sits on the enemy half of the board (ranks 5-8)."""
    return chess.square_rank(square) >= 4


def _square_is_supported(board: chess.Board, square: int, color: bool) -> bool:
    """True if ``color`` has at least one defender of ``square``."""
    return bool(board.attackers(color, square))


def analyse_flaws(
    pre_fen: str,
    move_uci: str,
    history_sans: Optional[List[str]] = None,
) -> List[str]:
    """
    Inspect a single commander move (UCI) made from the position ``pre_fen``
    and return a list of structural-flaw keys it exhibits.

    Parameters
    ----------
    pre_fen : FEN of the position *before* the commander's move.
    move_uci : the commander's move in UCI.
    history_sans : optional list of prior commander moves (SAN) for timeline
                   analysis (used by Panic Abandonment).
    """
    flaws: List[str] = []
    history_sans = history_sans or []

    try:
        board = chess.Board(pre_fen)
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        return flaws

    if move not in board.legal_moves:
        return flaws

    mover = board.piece_at(move.from_square)
    if mover is None:
        return flaws
    color = mover.color

    # We simulate the move to inspect the resulting threat landscape.
    board.push(move)
    dest = move.to_square

    # --- 1. Lone Ranger Syndrome -------------------------------------------
    # A Spy (Knight) pushed deep into enemy territory with no friendly support.
    if mover.piece_type == chess.KNIGHT and _is_deep_in_enemy_territory(dest):
        supported = _square_is_supported(board, dest, color)
        attacked = bool(board.attackers(not color, dest))
        if not supported and attacked:
            flaws.append("lone_ranger")

    # --- 2. Tunnel Vision ---------------------------------------------------
    # Advancing straight down a file (vertical lane) into an enemy diagonal
    # sniper's (bishop's) line of fire.
    from_file = chess.square_file(move.from_square)
    to_file = chess.square_file(dest)
    moved_vertically = from_file == to_file
    if moved_vertically:
        enemy_snipers = [
            sq for sq in board.pieces(chess.BISHOP, not color)
        ]
        for sniper_sq in enemy_snipers:
            if dest in board.attacks(sniper_sq):
                # Walked the asset directly into the crossfire.
                if not _square_is_supported(board, dest, color):
                    flaws.append("tunnel_vision")
                    break

    # --- 3. Panic Abandonment ----------------------------------------------
    # Sacrificing a high-value asset (Strike Commander / Heavy Armor) into an
    # immediate, unsupported capture without a calculable delayed payoff.
    board_before = chess.Board(pre_fen)
    if board_before.is_capture(move):
        # The commander captured something; check if they over-traded.
        victim = board_before.piece_at(move.to_square)
        attacker_value = ASSET_VALUE.get(mover.piece_type, 0)
        victim_value = ASSET_VALUE.get(victim.piece_type, 0) if victim else 0
        # Walking a 9/5-point asset into a square defended by the enemy for a
        # cheaper victim, with no recapture support, reads as panic.
        if attacker_value >= 5 and victim_value < attacker_value:
            if board.attackers(not color, dest) and not _square_is_supported(board, dest, color):
                flaws.append("panic_abandonment")
    else:
        # Non-capturing hang of the Strike Commander under pressure.
        if mover.piece_type == chess.QUEEN and \
                board.attackers(not color, dest) and \
                not _square_is_supported(board, dest, color):
            flaws.append("panic_abandonment")

    return flaws
