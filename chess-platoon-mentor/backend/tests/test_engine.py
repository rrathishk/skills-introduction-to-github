"""Unit tests for the chess engine, scenarios, and the Behavioral Flaw Engine."""

import chess

from app.engine import (
    SCENARIOS,
    TacticalEngine,
    analyse_flaws,
    asset_name,
)


def test_all_scenarios_are_legal_white_to_move():
    assert set(SCENARIOS.keys()) == {1, 2, 3, 4}
    for level, sc in SCENARIOS.items():
        board = chess.Board(sc.fen)
        assert board.turn == chess.WHITE, f"level {level} should be white to move"
        assert board.is_valid()
        assert len(list(board.legal_moves)) > 0


def test_legal_move_applies_and_enemy_replies():
    eng = TacticalEngine(SCENARIOS[1].fen)
    out = eng.apply_user_move("g1f3")
    assert out.ok
    assert out.moved_asset == "Spy"          # knight
    assert out.user_san == "Nf3"
    assert out.enemy_san                       # enemy responded
    assert out.fen


def test_illegal_move_is_rejected():
    eng = TacticalEngine(SCENARIOS[1].fen)
    out = eng.apply_user_move("e2e5")          # pawn can't jump 3
    assert not out.ok
    assert "Illegal" in out.reason


def test_malformed_uci_is_rejected():
    eng = TacticalEngine(SCENARIOS[1].fen)
    out = eng.apply_user_move("zzzz")
    assert not out.ok


def test_lone_ranger_flaw_detected():
    # White knight on e4 jumps to d6 — deep, attacked by the c7 pawn, unsupported.
    fen = "3k4/2p5/8/8/4N3/8/8/3K4 w - - 0 1"
    flaws = analyse_flaws(fen, "e4d6")
    assert "lone_ranger" in flaws


def test_clean_developing_move_has_no_flaws():
    flaws = analyse_flaws(SCENARIOS[1].fen, "g1f3")
    assert flaws == []


def test_asset_names_use_military_lexicon():
    assert asset_name(chess.KNIGHT) == "Spy"
    assert asset_name(chess.ROOK) == "Heavy Armor"
    assert asset_name(chess.QUEEN) == "Strike Commander"
