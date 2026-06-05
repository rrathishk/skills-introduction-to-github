"""Active-game session persistence (no longer in process memory)."""

import chess

from app import database as db

from .conftest import unique_user


def test_active_session_is_persisted_in_db(client):
    uid = unique_user()
    client.post("/api/new-game", json={"user_id": uid, "level": 1})
    saved = db.get_active_session(uid)
    assert saved is not None
    assert saved["level"] == 1
    assert saved["history"] == []


def test_move_survives_a_fresh_client(client):
    """Simulate a server restart / second instance: a brand-new TestClient
    (new process-level state) can continue the game because the session lives
    in the database, not an in-memory dict."""
    uid = unique_user()
    ng = client.post("/api/new-game", json={"user_id": uid, "level": 1}).json()
    first = list(chess.Board(ng["fen"]).legal_moves)[0].uci()

    from fastapi.testclient import TestClient
    from app import main

    with TestClient(main.app) as fresh:
        mv = fresh.post("/api/move", json={"user_id": uid, "move": first})
        assert mv.status_code == 200
        assert mv.json()["ok"]

    # The persisted session advanced (history now has the move recorded).
    saved = db.get_active_session(uid)
    assert len(saved["history"]) >= 1
