"""
main.py
=======
FastAPI gateway for the Psychological Chess Platoon Command Center.

Endpoints
---------
GET  /                        -> service banner / health
GET  /api/health             -> liveness + whether the live agent is wired
GET  /api/scenarios          -> the 4-level curriculum metadata
POST /api/new-game           -> start / reset a scenario, returns the FEN
POST /api/move               -> submit a commander move, get enemy reply +
                                diagnostics + agent transmission
GET  /api/progress/{user_id} -> commander Elo, record, and flaw flags
GET  /api/diagnostics/{user_id} -> recent diagnostic transmissions log

State note
----------
Active board positions are held in an in-memory session map keyed by
``user_id``. Long-term progress + diagnostics live in SQLite (database.py).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import database as db
from .academy import academy_payload
from .agent import CommandAgent
from .engine import (
    SCENARIOS,
    TacticalEngine,
    analyse_flaws,
    get_scenario,
)
from .factions import FACTIONS, faction_public, get_faction

app = FastAPI(
    title="Psychological Chess Platoon Command Center",
    description="AI tactical mentor that models chess as psychological warfare.",
    version="1.0.0",
)

# Allow the Next.js dev server (and any local front-end) to talk to us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = CommandAgent()

# ---------------------------------------------------------------------------
# In-memory session store: user_id -> {"level": int, "fen": str, "history": []}
# ---------------------------------------------------------------------------
_SESSIONS: Dict[str, Dict] = {}

# Ensure the schema exists as soon as the module loads (covers both ASGI
# startup and direct import in tests/tools).
db.init_db()


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class NewGameRequest(BaseModel):
    user_id: str = Field(..., description="Stable identifier for the commander.")
    level: int = Field(1, ge=1, le=4)
    faction: Optional[str] = Field(None, description="Army faction id (india/usa/russia/china).")


class MoveRequest(BaseModel):
    user_id: str
    move: str = Field(..., description="Commander move in UCI, e.g. 'e2e4'.")


class FactionRequest(BaseModel):
    user_id: str
    faction: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "Psychological Chess Platoon Command Center",
        "status": "OPERATIONAL",
        "live_agent": agent.live,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "live_agent": agent.live}


@app.get("/api/scenarios")
def scenarios():
    return {
        "scenarios": [
            {
                "level": s.level,
                "codename": s.codename,
                "difficulty": s.difficulty,
                "objective": s.objective,
                "briefing": s.briefing,
            }
            for s in SCENARIOS.values()
        ]
    }


@app.get("/api/factions")
def factions():
    return {"factions": [faction_public(f) for f in FACTIONS.values()]}


@app.post("/api/set-faction")
def set_faction(req: FactionRequest):
    commander = db.set_faction(req.user_id, req.faction)
    return {"user_id": req.user_id, "faction": faction_public(get_faction(commander["faction"]))}


@app.get("/api/academy")
def academy(user_id: Optional[str] = None):
    rank_names = None
    if user_id:
        commander = db.get_or_create_commander(user_id)
        rank_names = get_faction(commander["faction"]).rank_names
    return academy_payload(rank_names)


@app.post("/api/new-game")
def new_game(req: NewGameRequest):
    scenario = get_scenario(req.level)
    db.get_or_create_commander(req.user_id)
    if req.faction:
        db.set_faction(req.user_id, req.faction)

    _SESSIONS[req.user_id] = {
        "level": scenario.level,
        "fen": scenario.fen,
        "history": [],  # SAN of commander moves, for timeline analysis
    }

    # Opening transmission sets the scene in-character, in the faction's voice.
    commander = db.get_or_create_commander(req.user_id)
    faction = get_faction(commander["faction"])
    focus = db.dominant_flaw(req.user_id)
    eased = commander["difficulty_bias"] < 0
    transmission = agent.transmit(
        level_briefing=scenario.briefing,
        moved_asset=None,
        captured_asset=None,
        flaws=[],
        focus_flaw=focus,
        eased=eased,
        general=faction.general,
        general_title=faction.general_title,
        motto=faction.motto,
    )

    return {
        "level": scenario.level,
        "codename": scenario.codename,
        "difficulty": scenario.difficulty,
        "objective": scenario.objective,
        "briefing": scenario.briefing,
        "fen": scenario.fen,
        "transmission": transmission,
        "eased": eased,
        "faction": faction_public(faction),
    }


@app.post("/api/move")
def move(req: MoveRequest):
    session = _SESSIONS.get(req.user_id)
    if session is None:
        raise HTTPException(status_code=400, detail="No active engagement. Call /api/new-game first.")

    pre_fen = session["fen"]
    level = session["level"]
    scenario = get_scenario(level)

    # --- Behavioral Flaw Engine (analyse against live + historical timeline)
    flaws: List[str] = analyse_flaws(pre_fen, req.move, session["history"])

    # --- Apply the move on the tactical engine
    eng = TacticalEngine(pre_fen)
    outcome = eng.apply_user_move(req.move)
    if not outcome.ok:
        raise HTTPException(status_code=422, detail=outcome.reason)

    # Persist new board + commander move into the session timeline.
    session["fen"] = outcome.fen
    session["history"].append(outcome.user_san)
    outcome.flaws = flaws

    # --- Diagnostics persistence + adaptive scaling
    commander = db.get_or_create_commander(req.user_id)
    if flaws:
        commander = db.record_flaws(req.user_id, flaws)

    focus = db.dominant_flaw(req.user_id)
    eased = commander["difficulty_bias"] < 0
    faction = get_faction(commander["faction"])

    # --- Record match result if the engagement ended
    if outcome.game_over and outcome.result:
        commander = db.record_result(req.user_id, level, outcome.result)

    # --- Agent transmission (in the faction general's voice)
    transmission = agent.transmit(
        level_briefing=scenario.briefing,
        moved_asset=outcome.moved_asset,
        captured_asset=outcome.captured_asset,
        flaws=flaws,
        game_over=outcome.game_over,
        result=outcome.result,
        focus_flaw=focus,
        eased=eased,
        fen=outcome.fen,
        general=faction.general,
        general_title=faction.general_title,
        motto=faction.motto,
    )

    db.log_diagnostic(
        user_id=req.user_id,
        level=level,
        move=outcome.user_san,
        fen=outcome.fen,
        flaws=flaws,
        transmission=transmission,
    )

    return {
        "ok": True,
        "user_move_san": outcome.user_san,
        "enemy_move_san": outcome.enemy_san,
        "enemy_move_uci": outcome.enemy_uci,
        "fen": outcome.fen,
        "is_capture": outcome.is_capture,
        "captured_asset": outcome.captured_asset,
        "moved_asset": outcome.moved_asset,
        "flaws": flaws,
        "game_over": outcome.game_over,
        "result": outcome.result,
        "transmission": transmission,
        "eased": eased,
        "focus_flaw": focus,
    }


@app.get("/api/progress/{user_id}")
def progress(user_id: str):
    commander = db.get_or_create_commander(user_id)
    total = commander["wins"] + commander["losses"] + commander["draws"]
    win_rate = (commander["wins"] / total) if total else 0.0
    return {
        "user_id": user_id,
        "elo": commander["elo"],
        "wins": commander["wins"],
        "losses": commander["losses"],
        "draws": commander["draws"],
        "win_rate": round(win_rate, 3),
        "flaw_counts": commander["flaw_counts"],
        "difficulty_bias": commander["difficulty_bias"],
        "dominant_flaw": db.dominant_flaw(user_id),
        "faction": faction_public(get_faction(commander["faction"])),
        "match_history": db.get_match_history(user_id, limit=20),
    }


@app.get("/api/diagnostics/{user_id}")
def diagnostics(user_id: str, limit: int = 50):
    return {
        "user_id": user_id,
        "diagnostics": db.get_diagnostics(user_id, limit=limit),
    }
