"""Auth: register, login, token identity, and cross-device progress."""

import chess

from .conftest import unique_user


def _email() -> str:
    return f"{unique_user('cmdr')}@example.com"


def test_register_returns_token_and_user(client):
    email = _email()
    res = client.post(
        "/api/auth/register",
        json={"email": email, "password": "longenough123", "display_name": "Ace"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["token"]
    assert body["user"]["email"] == email
    assert body["user"]["id"].startswith("usr_")


def test_duplicate_email_rejected(client):
    email = _email()
    client.post("/api/auth/register", json={"email": email, "password": "longenough123"})
    dup = client.post("/api/auth/register", json={"email": email, "password": "longenough123"})
    assert dup.status_code == 409


def test_short_password_rejected(client):
    res = client.post("/api/auth/register", json={"email": _email(), "password": "short"})
    assert res.status_code == 422


def test_login_success_and_failure(client):
    email = _email()
    client.post("/api/auth/register", json={"email": email, "password": "longenough123"})

    ok = client.post("/api/auth/login", json={"email": email, "password": "longenough123"})
    assert ok.status_code == 200
    assert ok.json()["token"]

    bad = client.post("/api/auth/login", json={"email": email, "password": "wrongpassword"})
    assert bad.status_code == 401


def test_me_requires_valid_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401

    email = _email()
    token = client.post(
        "/api/auth/register", json={"email": email, "password": "longenough123"}
    ).json()["token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == email


def test_progress_follows_the_token_not_the_body(client):
    """The whole point of login: progress is tied to the account, so it follows
    the user across devices regardless of any body/path user_id."""
    email = _email()
    token = client.post(
        "/api/auth/register", json={"email": email, "password": "longenough123"}
    ).json()["token"]
    hdr = {"Authorization": f"Bearer {token}"}

    # Play one move while authenticated, sending a DECOY user_id in the body.
    ng = client.post(
        "/api/new-game", json={"user_id": "decoy-device-A", "level": 1}, headers=hdr
    ).json()
    first = list(chess.Board(ng["fen"]).legal_moves)[0].uci()
    client.post("/api/move", json={"user_id": "decoy-device-B", "move": first}, headers=hdr)

    # From a "different device" (different decoy id) but same token → same diagnostics.
    diag = client.get("/api/diagnostics/decoy-device-C", headers=hdr).json()["diagnostics"]
    assert len(diag) >= 1  # the move we made is attributed to the account, not the decoy id
