"""Tests for the persistence layer + adaptive-guidance logic.

These run against whatever DATABASE_URL/COMMAND_CENTER_DB the conftest set, so
the same assertions validate both the SQLite and Postgres code paths.
"""

from app import database as db

from .conftest import unique_user


def test_get_or_create_is_idempotent(client):
    uid = unique_user()
    a = db.get_or_create_commander(uid)
    b = db.get_or_create_commander(uid)
    assert a["user_id"] == b["user_id"] == uid
    assert a["elo"] == db.DEFAULT_ELO
    assert isinstance(a["flaw_counts"], dict)


def test_repeated_flaw_triggers_adaptive_scaling(client):
    uid = unique_user()
    commander = None
    for _ in range(3):
        commander = db.record_flaws(uid, ["lone_ranger"])
    assert commander["flaw_counts"]["lone_ranger"] == 3
    assert commander["difficulty_bias"] < 0          # difficulty eased
    assert db.dominant_flaw(uid) == "lone_ranger"


def test_single_flaw_does_not_ease_difficulty(client):
    uid = unique_user()
    commander = db.record_flaws(uid, ["tunnel_vision"])
    assert commander["difficulty_bias"] == 0
    assert db.dominant_flaw(uid) is None


def test_record_result_updates_elo_and_history(client):
    uid = unique_user()
    before = db.get_or_create_commander(uid)["elo"]
    after = db.record_result(uid, level=2, result="win")
    assert after["elo"] > before
    assert after["wins"] == 1
    history = db.get_match_history(uid)
    assert history[0]["result"] == "win"


def test_loss_lowers_elo_with_floor(client):
    uid = unique_user()
    for _ in range(100):
        db.record_result(uid, level=4, result="loss")
    assert db.get_or_create_commander(uid)["elo"] >= 100   # never below floor
