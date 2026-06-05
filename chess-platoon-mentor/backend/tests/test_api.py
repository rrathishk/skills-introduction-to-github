"""End-to-end API tests via FastAPI TestClient (offline agent mode)."""

import chess

from .conftest import unique_user


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"


def test_scenarios_list(client):
    body = client.get("/api/scenarios").json()
    assert len(body["scenarios"]) == 4


def test_factions_list(client):
    factions = client.get("/api/factions").json()["factions"]
    countries = {f["country"] for f in factions}
    assert countries == {"India", "United States", "Russia", "China"}
    for f in factions:
        assert f["general"] and f["colors"]["accent"] and f["rank_names"]


def test_set_faction_and_persist(client):
    uid = unique_user()
    res = client.post("/api/set-faction", json={"user_id": uid, "faction": "russia"})
    assert res.json()["faction"]["general"] == "Marshal Viktor Orlov"
    prog = client.get(f"/api/progress/{uid}").json()
    assert prog["faction"]["country"] == "Russia"


def test_academy_is_faction_flavoured(client):
    uid = unique_user()
    client.post("/api/set-faction", json={"user_id": uid, "faction": "india"})
    ac = client.get(f"/api/academy?user_id={uid}").json()
    assert len(ac["asset_doctrine"]) == 6
    assert len(ac["strategic_doctrine"]) == 4
    pawn = next(c for c in ac["asset_doctrine"] if c["key"] == "pawn")
    assert "Jawan" in pawn["faction_name"]


def test_new_game_returns_faction_and_briefing(client):
    uid = unique_user()
    ng = client.post(
        "/api/new-game", json={"user_id": uid, "level": 2, "faction": "china"}
    ).json()
    assert ng["level"] == 2
    assert ng["faction"]["country"] == "China"
    assert ng["transmission"]
    assert ng["fen"]


def test_full_move_flow(client):
    uid = unique_user()
    ng = client.post("/api/new-game", json={"user_id": uid, "level": 1, "faction": "usa"}).json()
    first = list(chess.Board(ng["fen"]).legal_moves)[0].uci()
    mv = client.post("/api/move", json={"user_id": uid, "move": first}).json()
    assert mv["ok"]
    assert mv["transmission"]
    # diagnostics recorded
    diag = client.get(f"/api/diagnostics/{uid}").json()["diagnostics"]
    assert len(diag) >= 1


def test_move_without_game_is_400(client):
    res = client.post("/api/move", json={"user_id": unique_user(), "move": "e2e4"})
    assert res.status_code == 400


def test_illegal_move_is_422(client):
    uid = unique_user()
    client.post("/api/new-game", json={"user_id": uid, "level": 1})
    res = client.post("/api/move", json={"user_id": uid, "move": "e2e5"})
    assert res.status_code == 422


def test_progress_starts_at_default_elo(client):
    uid = unique_user()
    prog = client.get(f"/api/progress/{uid}").json()
    assert prog["elo"] == 800
    assert prog["wins"] == 0
