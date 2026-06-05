"""
database.py
===========
Persistence layer for the Command Center.

Portable across **SQLite** (local dev + tests — zero setup, a single file) and
**Postgres** (production — multi-instance safe). The same code runs on both
because it uses SQLAlchemy Core; only the connection URL changes.

Connection resolution (first match wins):
1. ``DATABASE_URL`` env var (e.g. ``postgresql+psycopg://user:pass@host/db``)
2. ``COMMAND_CENTER_DB`` env var → a SQLite file at that path
3. Default: ``command_center.db`` next to this module

Responsibilities:
* Track each commander's Elo, win/loss/draw history, and chosen faction.
* Persist structural-flaw flags (Lone Ranger, Tunnel Vision, Panic).
* Store a rolling diagnostic log of every agent transmission.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    insert,
    inspect,
    select,
    text,
    update,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FLAW_KEYS = ("lone_ranger", "tunnel_vision", "panic_abandonment")
DEFAULT_ELO = 800
DEFAULT_FACTION = "india"


def _resolve_url() -> str:
    """Build the SQLAlchemy connection URL from the environment."""
    url = os.environ.get("DATABASE_URL")
    if url:
        # Normalise the bare ``postgres://`` form some hosts hand out.
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        return url
    path = os.environ.get(
        "COMMAND_CENTER_DB",
        os.path.join(os.path.dirname(__file__), "command_center.db"),
    )
    return f"sqlite:///{path}"


# The engine is created lazily so tests can set env vars before first use.
_engine = None
_metadata = MetaData()

commanders = Table(
    "commanders",
    _metadata,
    Column("user_id", String(128), primary_key=True),
    Column("elo", Integer, nullable=False, default=DEFAULT_ELO),
    Column("wins", Integer, nullable=False, default=0),
    Column("losses", Integer, nullable=False, default=0),
    Column("draws", Integer, nullable=False, default=0),
    Column("flaw_counts", Text, nullable=False, default="{}"),
    Column("difficulty_bias", Integer, nullable=False, default=0),
    Column("faction", String(32), nullable=False, default=DEFAULT_FACTION),
    Column("created_at", Float, nullable=False),
    Column("updated_at", Float, nullable=False),
)

match_history = Table(
    "match_history",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(128), nullable=False, index=True),
    Column("level", Integer, nullable=False),
    Column("result", String(8), nullable=False),  # win | loss | draw
    Column("elo_delta", Integer, nullable=False),
    Column("created_at", Float, nullable=False),
)

diagnostics = Table(
    "diagnostics",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(128), nullable=False, index=True),
    Column("level", Integer),
    Column("move", String(16)),
    Column("fen", Text),
    Column("flaws", Text),          # JSON array
    Column("transmission", Text),
    Column("created_at", Float, nullable=False),
)

# Registered accounts (login). Anonymous play does not create a row here.
users = Table(
    "users",
    _metadata,
    Column("id", String(64), primary_key=True),
    Column("email", String(320), nullable=False, unique=True, index=True),
    Column("password_hash", Text, nullable=False),
    Column("display_name", String(120)),
    Column("created_at", Float, nullable=False),
)

# The player's CURRENT in-progress game. One active game per commander.
# Moving this out of process memory makes the backend multi-instance safe and
# survives restarts/redeploys.
active_sessions = Table(
    "active_sessions",
    _metadata,
    Column("user_id", String(128), primary_key=True),
    Column("level", Integer, nullable=False),
    Column("fen", Text, nullable=False),
    Column("history", Text, nullable=False, default="[]"),  # JSON array of SAN
    Column("updated_at", Float, nullable=False),
)


def get_engine():
    global _engine
    if _engine is None:
        url = _resolve_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)
    return _engine


def init_db() -> None:
    """Create tables if absent + apply the lightweight `faction` migration."""
    engine = get_engine()
    _metadata.create_all(engine)

    # Migration for databases created before `faction` existed.
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("commanders")}
    if "faction" not in cols:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE commanders ADD COLUMN faction VARCHAR(32) "
                    "NOT NULL DEFAULT 'india'"
                )
            )


# ---------------------------------------------------------------------------
# Commander records
# ---------------------------------------------------------------------------

def _row_to_commander(row) -> Dict[str, Any]:
    data = dict(row._mapping)
    data["flaw_counts"] = json.loads(data.get("flaw_counts") or "{}")
    return data


def get_or_create_commander(user_id: str) -> Dict[str, Any]:
    engine = get_engine()
    now = time.time()
    with engine.begin() as conn:
        row = conn.execute(
            select(commanders).where(commanders.c.user_id == user_id)
        ).first()
        if row is None:
            conn.execute(
                insert(commanders).values(
                    user_id=user_id,
                    elo=DEFAULT_ELO,
                    wins=0,
                    losses=0,
                    draws=0,
                    flaw_counts="{}",
                    difficulty_bias=0,
                    faction=DEFAULT_FACTION,
                    created_at=now,
                    updated_at=now,
                )
            )
            row = conn.execute(
                select(commanders).where(commanders.c.user_id == user_id)
            ).first()
        return _row_to_commander(row)


def set_faction(user_id: str, faction_id: str) -> Dict[str, Any]:
    commander = get_or_create_commander(user_id)
    with get_engine().begin() as conn:
        conn.execute(
            update(commanders)
            .where(commanders.c.user_id == user_id)
            .values(faction=faction_id, updated_at=time.time())
        )
    commander["faction"] = faction_id
    return commander


def record_flaws(user_id: str, flaw_keys: List[str]) -> Dict[str, Any]:
    """
    Increment observed flaw counters and return the updated commander. If any
    flaw reaches >= 3 observations, lower ``difficulty_bias`` (more negative ==
    easier) so adaptive guidance can scale the scenario down.
    """
    commander = get_or_create_commander(user_id)
    counts: Dict[str, int] = commander["flaw_counts"]
    for key in flaw_keys:
        if key in FLAW_KEYS:
            counts[key] = counts.get(key, 0) + 1

    bias = commander["difficulty_bias"]
    if any(v >= 3 for v in counts.values()):
        bias = max(bias - 1, -3)

    with get_engine().begin() as conn:
        conn.execute(
            update(commanders)
            .where(commanders.c.user_id == user_id)
            .values(flaw_counts=json.dumps(counts), difficulty_bias=bias, updated_at=time.time())
        )
    commander["flaw_counts"] = counts
    commander["difficulty_bias"] = bias
    return commander


def dominant_flaw(user_id: str) -> Optional[str]:
    """Return the most-observed flaw if seen >= 3 times, else None."""
    commander = get_or_create_commander(user_id)
    counts: Dict[str, int] = commander["flaw_counts"]
    if not counts:
        return None
    key, value = max(counts.items(), key=lambda kv: kv[1])
    return key if value >= 3 else None


def record_result(user_id: str, level: int, result: str) -> Dict[str, Any]:
    """Apply a win/loss/draw to the commander's Elo and append match history."""
    commander = get_or_create_commander(user_id)
    elo = commander["elo"]
    base = 12 + (level * 4)
    if result == "win":
        delta = base
        commander["wins"] += 1
    elif result == "loss":
        delta = -base
        commander["losses"] += 1
    else:
        delta = 0
        commander["draws"] += 1
    elo = max(100, elo + delta)
    now = time.time()

    with get_engine().begin() as conn:
        conn.execute(
            update(commanders)
            .where(commanders.c.user_id == user_id)
            .values(
                elo=elo,
                wins=commander["wins"],
                losses=commander["losses"],
                draws=commander["draws"],
                updated_at=now,
            )
        )
        conn.execute(
            insert(match_history).values(
                user_id=user_id, level=level, result=result, elo_delta=delta, created_at=now
            )
        )
    commander["elo"] = elo
    return commander


# ---------------------------------------------------------------------------
# Diagnostics log
# ---------------------------------------------------------------------------

def log_diagnostic(
    user_id: str,
    level: Optional[int],
    move: Optional[str],
    fen: Optional[str],
    flaws: List[str],
    transmission: str,
) -> None:
    with get_engine().begin() as conn:
        conn.execute(
            insert(diagnostics).values(
                user_id=user_id,
                level=level,
                move=move,
                fen=fen,
                flaws=json.dumps(flaws),
                transmission=transmission,
                created_at=time.time(),
            )
        )


def get_diagnostics(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    with get_engine().connect() as conn:
        rows = conn.execute(
            select(diagnostics)
            .where(diagnostics.c.user_id == user_id)
            .order_by(diagnostics.c.id.desc())
            .limit(limit)
        ).all()
    result = []
    for row in rows:
        item = dict(row._mapping)
        item["flaws"] = json.loads(item.get("flaws") or "[]")
        result.append(item)
    return result


def get_match_history(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    with get_engine().connect() as conn:
        rows = conn.execute(
            select(match_history)
            .where(match_history.c.user_id == user_id)
            .order_by(match_history.c.id.desc())
            .limit(limit)
        ).all()
    return [dict(r._mapping) for r in rows]


# ---------------------------------------------------------------------------
# Users (accounts)
# ---------------------------------------------------------------------------

def create_user(user_id: str, email: str, password_hash: str, display_name: str) -> Dict[str, Any]:
    with get_engine().begin() as conn:
        conn.execute(
            insert(users).values(
                id=user_id,
                email=email.lower().strip(),
                password_hash=password_hash,
                display_name=display_name,
                created_at=time.time(),
            )
        )
    return {"id": user_id, "email": email.lower().strip(), "display_name": display_name}


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with get_engine().connect() as conn:
        row = conn.execute(
            select(users).where(users.c.email == email.lower().strip())
        ).first()
    return dict(row._mapping) if row else None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    with get_engine().connect() as conn:
        row = conn.execute(select(users).where(users.c.id == user_id)).first()
    return dict(row._mapping) if row else None


# ---------------------------------------------------------------------------
# Active game session (persisted — replaces the old in-memory dict)
# ---------------------------------------------------------------------------

def save_active_session(user_id: str, level: int, fen: str, history: List[str]) -> None:
    """Upsert the commander's current in-progress game."""
    now = time.time()
    with get_engine().begin() as conn:
        existing = conn.execute(
            select(active_sessions.c.user_id).where(active_sessions.c.user_id == user_id)
        ).first()
        values = {
            "level": level,
            "fen": fen,
            "history": json.dumps(history),
            "updated_at": now,
        }
        if existing:
            conn.execute(
                update(active_sessions)
                .where(active_sessions.c.user_id == user_id)
                .values(**values)
            )
        else:
            conn.execute(insert(active_sessions).values(user_id=user_id, **values))


def get_active_session(user_id: str) -> Optional[Dict[str, Any]]:
    with get_engine().connect() as conn:
        row = conn.execute(
            select(active_sessions).where(active_sessions.c.user_id == user_id)
        ).first()
    if not row:
        return None
    data = dict(row._mapping)
    data["history"] = json.loads(data.get("history") or "[]")
    return data
