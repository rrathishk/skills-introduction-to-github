"""
database.py
===========
Local SQLite persistence layer for the Command Center.

Responsibilities
----------------
* Track each commander's (user's) Elo capability.
* Track win / loss / draw history.
* Persist structural-flaw flags that describe recurring weaknesses in a
  commander's playing style (Lone Ranger Syndrome, Tunnel Vision, Panic
  Abandonment).
* Store a rolling diagnostic log of every transmission the agent emits so
  the War Room can be replayed / audited.

The database file lives next to this module as ``command_center.db`` so the
backend is fully self-contained and requires no external services.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = os.environ.get(
    "COMMAND_CENTER_DB",
    os.path.join(os.path.dirname(__file__), "command_center.db"),
)

# Canonical list of the structural flaws the diagnostic engine can flag.
FLAW_KEYS = ("lone_ranger", "tunnel_vision", "panic_abandonment")

# Default Elo assigned to a brand-new commander.
DEFAULT_ELO = 800


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they do not already exist. Idempotent."""
    with _connect() as conn:
        cur = conn.cursor()

        # One row per commander. ``flaw_counts`` is a JSON blob mapping every
        # FLAW_KEY to the number of times it has been observed.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS commanders (
                user_id         TEXT PRIMARY KEY,
                elo             INTEGER NOT NULL DEFAULT 800,
                wins            INTEGER NOT NULL DEFAULT 0,
                losses          INTEGER NOT NULL DEFAULT 0,
                draws           INTEGER NOT NULL DEFAULT 0,
                flaw_counts     TEXT    NOT NULL DEFAULT '{}',
                difficulty_bias INTEGER NOT NULL DEFAULT 0,
                created_at      REAL    NOT NULL,
                updated_at      REAL    NOT NULL
            )
            """
        )

        # Append-only log of every match result.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS match_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT NOT NULL,
                level      INTEGER NOT NULL,
                result     TEXT NOT NULL,        -- 'win' | 'loss' | 'draw'
                elo_delta  INTEGER NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )

        # Append-only diagnostic transmission log.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnostics (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT NOT NULL,
                level      INTEGER,
                move       TEXT,
                fen        TEXT,
                flaws      TEXT,                 -- JSON array of flaw keys
                transmission TEXT,               -- the agent's spoken analysis
                created_at REAL NOT NULL
            )
            """
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Commander records
# ---------------------------------------------------------------------------

def _row_to_commander(row: sqlite3.Row) -> Dict[str, Any]:
    data = dict(row)
    data["flaw_counts"] = json.loads(data.get("flaw_counts") or "{}")
    return data


def get_or_create_commander(user_id: str) -> Dict[str, Any]:
    """Return the commander record, creating a default one if needed."""
    now = time.time()
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM commanders WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                """
                INSERT INTO commanders
                    (user_id, elo, wins, losses, draws, flaw_counts,
                     difficulty_bias, created_at, updated_at)
                VALUES (?, ?, 0, 0, 0, '{}', 0, ?, ?)
                """,
                (user_id, DEFAULT_ELO, now, now),
            )
            conn.commit()
            cur.execute("SELECT * FROM commanders WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
        return _row_to_commander(row)


def record_flaws(user_id: str, flaw_keys: List[str]) -> Dict[str, Any]:
    """
    Increment the observed counters for the supplied flaws and return the
    updated commander record.

    If any single flaw has now been observed >= 3 times the commander's
    ``difficulty_bias`` is lowered (more negative == easier) so the adaptive
    guidance layer can scale the scenario down.
    """
    commander = get_or_create_commander(user_id)
    counts: Dict[str, int] = commander["flaw_counts"]

    for key in flaw_keys:
        if key in FLAW_KEYS:
            counts[key] = counts.get(key, 0) + 1

    # Adaptive scaling: if the commander keeps repeating *any* flaw, ease off.
    bias = commander["difficulty_bias"]
    if any(v >= 3 for v in counts.values()):
        bias = max(bias - 1, -3)

    now = time.time()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE commanders
               SET flaw_counts = ?, difficulty_bias = ?, updated_at = ?
             WHERE user_id = ?
            """,
            (json.dumps(counts), bias, now, user_id),
        )
        conn.commit()

    commander["flaw_counts"] = counts
    commander["difficulty_bias"] = bias
    return commander


def dominant_flaw(user_id: str) -> Optional[str]:
    """
    Return the flaw key the commander struggles with most *if* it has been
    observed at least 3 times (the threshold at which adaptive guidance kicks
    in). Otherwise return None.
    """
    commander = get_or_create_commander(user_id)
    counts: Dict[str, int] = commander["flaw_counts"]
    if not counts:
        return None
    key, value = max(counts.items(), key=lambda kv: kv[1])
    return key if value >= 3 else None


def record_result(user_id: str, level: int, result: str) -> Dict[str, Any]:
    """
    Apply a win/loss/draw to the commander's Elo and history.

    A simplified fixed-K Elo update is used: wins move the rating up, losses
    move it down, scaled by the scenario level so harder missions matter more.
    """
    commander = get_or_create_commander(user_id)
    elo = commander["elo"]

    base = 12 + (level * 4)
    if result == "win":
        delta = base
        commander["wins"] += 1
    elif result == "loss":
        delta = -base
        commander["losses"] += 1
    else:  # draw
        delta = 0
        commander["draws"] += 1

    elo = max(100, elo + delta)
    now = time.time()

    with _connect() as conn:
        conn.execute(
            """
            UPDATE commanders
               SET elo = ?, wins = ?, losses = ?, draws = ?, updated_at = ?
             WHERE user_id = ?
            """,
            (
                elo,
                commander["wins"],
                commander["losses"],
                commander["draws"],
                now,
                user_id,
            ),
        )
        conn.execute(
            """
            INSERT INTO match_history (user_id, level, result, elo_delta, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, level, result, delta, now),
        )
        conn.commit()

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
    """Append a single diagnostic transmission to the audit log."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO diagnostics
                (user_id, level, move, fen, flaws, transmission, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                level,
                move,
                fen,
                json.dumps(flaws),
                transmission,
                time.time(),
            ),
        )
        conn.commit()


def get_diagnostics(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return the most recent diagnostic transmissions, newest first."""
    with _connect() as conn:
        cur = conn.execute(
            """
            SELECT * FROM diagnostics
             WHERE user_id = ?
             ORDER BY id DESC
             LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cur.fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["flaws"] = json.loads(item.get("flaws") or "[]")
        result.append(item)
    return result


def get_match_history(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return the commander's recent match results, newest first."""
    with _connect() as conn:
        cur = conn.execute(
            """
            SELECT * FROM match_history
             WHERE user_id = ?
             ORDER BY id DESC
             LIMIT ?
            """,
            (user_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]
