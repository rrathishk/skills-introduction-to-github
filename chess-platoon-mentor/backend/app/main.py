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

import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import auth
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables / run migrations once, when the server boots.
    db.init_db()
    yield


app = FastAPI(
    title="Psychological Chess Platoon Command Center",
    description="AI tactical mentor that models chess as psychological warfare.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: in dev allow everything; in production set CORS_ORIGINS to a
# comma-separated allowlist of your real front-end domains.
_origins_env = os.environ.get("CORS_ORIGINS", "*")
_allow_origins = ["*"] if _origins_env.strip() == "*" else [
    o.strip() for o in _origins_env.split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = CommandAgent()


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


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=8, max_length=200)
    display_name: Optional[str] = Field(None, max_length=120)


class LoginRequest(BaseModel):
    email: str
    password: str


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def optional_user_id(authorization: Optional[str] = Header(default=None)) -> Optional[str]:
    """Return the authenticated user id from a Bearer token, or None.

    When present it OVERRIDES any user_id in the request body/path, so a logged
    in player's progress is always tied to their account (and follows them
    across web + mobile). Absent → anonymous play with the body/path id.
    """
    if authorization and authorization.lower().startswith("bearer "):
        return auth.decode_token(authorization.split(" ", 1)[1].strip())
    return None


def require_user_id(authorization: Optional[str] = Header(default=None)) -> str:
    uid = optional_user_id(authorization)
    if not uid:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return uid


def _user_public(user: Dict) -> Dict:
    return {"id": user["id"], "email": user["email"], "display_name": user.get("display_name")}


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
    return {"status": "ok", "live_agent": agent.live, "auth": True}


# ---- Authentication -------------------------------------------------------

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    email = req.email.lower().strip()
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=422, detail="A valid email is required.")
    if db.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    user_id = auth.new_user_id()
    db.create_user(
        user_id=user_id,
        email=email,
        password_hash=auth.hash_password(req.password),
        display_name=req.display_name or email.split("@")[0],
    )
    db.get_or_create_commander(user_id)  # initialise their progress record
    return {
        "token": auth.create_token(user_id),
        "user": {"id": user_id, "email": email, "display_name": req.display_name or email.split("@")[0]},
    }


@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = db.get_user_by_email(req.email)
    if not user or not auth.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"token": auth.create_token(user["id"]), "user": _user_public(user)}


@app.get("/api/auth/me")
def me(user_id: str = Depends(require_user_id)):
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Account not found.")
    return {"user": _user_public(user)}


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
def set_faction(req: FactionRequest, auth_uid: Optional[str] = Depends(optional_user_id)):
    uid = auth_uid or req.user_id
    commander = db.set_faction(uid, req.faction)
    return {"user_id": uid, "faction": faction_public(get_faction(commander["faction"]))}


@app.get("/api/academy")
def academy(user_id: Optional[str] = None, auth_uid: Optional[str] = Depends(optional_user_id)):
    uid = auth_uid or user_id
    rank_names = None
    if uid:
        commander = db.get_or_create_commander(uid)
        rank_names = get_faction(commander["faction"]).rank_names
    return academy_payload(rank_names)


@app.post("/api/new-game")
def new_game(req: NewGameRequest, auth_uid: Optional[str] = Depends(optional_user_id)):
    uid = auth_uid or req.user_id
    scenario = get_scenario(req.level)
    db.get_or_create_commander(uid)
    if req.faction:
        db.set_faction(uid, req.faction)

    # Persist the fresh game so it survives restarts and is multi-instance safe.
    db.save_active_session(uid, scenario.level, scenario.fen, [])

    # Opening transmission sets the scene in-character, in the faction's voice.
    commander = db.get_or_create_commander(uid)
    faction = get_faction(commander["faction"])
    focus = db.dominant_flaw(uid)
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
def move(req: MoveRequest, auth_uid: Optional[str] = Depends(optional_user_id)):
    uid = auth_uid or req.user_id
    session = db.get_active_session(uid)
    if session is None:
        raise HTTPException(status_code=400, detail="No active engagement. Call /api/new-game first.")

    pre_fen = session["fen"]
    level = session["level"]
    history = session["history"]
    scenario = get_scenario(level)

    # --- Behavioral Flaw Engine (analyse against live + historical timeline)
    flaws: List[str] = analyse_flaws(pre_fen, req.move, history)

    # --- Apply the move on the tactical engine
    eng = TacticalEngine(pre_fen)
    outcome = eng.apply_user_move(req.move)
    if not outcome.ok:
        raise HTTPException(status_code=422, detail=outcome.reason)

    # Persist new board + commander move into the session timeline.
    history.append(outcome.user_san)
    db.save_active_session(uid, level, outcome.fen, history)
    outcome.flaws = flaws

    # --- Diagnostics persistence + adaptive scaling
    commander = db.get_or_create_commander(uid)
    if flaws:
        commander = db.record_flaws(uid, flaws)

    focus = db.dominant_flaw(uid)
    eased = commander["difficulty_bias"] < 0
    faction = get_faction(commander["faction"])

    # --- Record match result if the engagement ended
    if outcome.game_over and outcome.result:
        commander = db.record_result(uid, level, outcome.result)

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
        user_id=uid,
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
def progress(user_id: str, auth_uid: Optional[str] = Depends(optional_user_id)):
    uid = auth_uid or user_id
    commander = db.get_or_create_commander(uid)
    total = commander["wins"] + commander["losses"] + commander["draws"]
    win_rate = (commander["wins"] / total) if total else 0.0
    return {
        "user_id": uid,
        "elo": commander["elo"],
        "wins": commander["wins"],
        "losses": commander["losses"],
        "draws": commander["draws"],
        "win_rate": round(win_rate, 3),
        "flaw_counts": commander["flaw_counts"],
        "difficulty_bias": commander["difficulty_bias"],
        "dominant_flaw": db.dominant_flaw(uid),
        "faction": faction_public(get_faction(commander["faction"])),
        "match_history": db.get_match_history(uid, limit=20),
    }


@app.get("/api/diagnostics/{user_id}")
def diagnostics(user_id: str, limit: int = 50, auth_uid: Optional[str] = Depends(optional_user_id)):
    uid = auth_uid or user_id
    return {
        "user_id": uid,
        "diagnostics": db.get_diagnostics(uid, limit=limit),
    }
