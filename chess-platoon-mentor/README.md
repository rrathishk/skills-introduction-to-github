# ◆ Psychological Chess Platoon Command Center

A full-stack "War Room" that reframes chess as **psychological warfare**. An
interactive board is wired to an AI tactical mentor — **FIELD MARSHAL VOSS** —
who treats every piece as a military asset, diagnoses the structural flaws in
your play, and adapts the curriculum to drill them out of you.

```
chess-platoon-mentor/
├── frontend/                 # Next.js (App Router) + Tailwind CSS
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx       # The War Room UI (Board + Fluid Agent Sidebar)
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   └── components/
│   │       ├── TacticalBoard.tsx   # react-chessboard wrapper for user moves
│   │       └── CommsSidebar.tsx    # Chat viewport streaming agent analysis
│   ├── package.json
│   └── tailwind.config.js
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # API endpoints (moves, progress, diagnostics)
│   │   ├── engine.py         # python-chess integration & scenario states
│   │   ├── agent.py          # OpenAI persona wrapper (offline fallback built-in)
│   │   └── database.py       # SQLite progress tracking & diagnostic logs
│   │   ├── factions.py       # 4 playable armies (India/USA/Russia/China)
│   │   └── academy.py        # teaching doctrine (rewires how you see the board)
│   ├── requirements.txt
│   └── .env
├── mobile/                   # Expo / React Native app (same backend)
│   ├── App.tsx
│   ├── src/api.ts            # shared-backend client
│   └── src/screens/          # Faction · Academy · War Room
└── README.md                 # (this file)
```

## Choose Your Army

Players pick a faction — **🇮🇳 India**, **🇺🇸 United States**, **🇷🇺 Russia**, or
**🇨🇳 China**. The choice re-themes the board colors, renames assets into that
nation's military flavour (e.g. Knight → *Spetsnaz* for Russia, *Para-Commando*
for India), and gives the AI mentor a named commanding general whose voice the
transmissions adopt. It is purely cosmetic/psychological — the chess rules are
identical. Add crest/general artwork under `frontend/public/factions/<id>/`
(see that folder's README); until then a flag emoji + faction color is used.

## The Academy (teaching layer)

Before the first move, the **Academy** rewires how the player sees the board:
each piece becomes an army asset with a strength, a deployment doctrine, and a
psychological lesson — plus the four strategic doctrines (*take position early,
when to sacrifice, when to accept defeat, when to hold*). Served from
`/api/academy` and flavoured by the player's faction.

---

## 1. The Command Lexicon

VOSS never speaks civilian chess. Every asset has a military designation:

| Chess piece | Designation              | Doctrine |
|-------------|--------------------------|----------|
| Pawn        | **Infantry**             | Defensive perimeters, terrain commitment |
| Knight      | **Spy / Recon**          | Infiltration, deep outposts, chaos behind enemy lines |
| Bishop      | **Diagonal Sniper**      | Long-range crossfire on open diagonals |
| Rook        | **Heavy Armor / Elephant** | Straight column blitz down rows/files |
| Queen       | **Strike Commander**     | High impact, high risk |
| King        | **Commander-in-Chief**   | Fortify early, fight in the endgame |

---

## 2. The Diagnostic & Flaw Engine

The backend analyses every move against the live position **and** your match
timeline, flagging three structural flaws:

- **Lone Ranger Syndrome** — pushing a Spy (Knight) deep into enemy lines with
  zero asset/Infantry support, where it can be captured.
- **Tunnel Vision** — tunneling down a vertical lane straight into a Diagonal
  Sniper's (Bishop's) line of fire.
- **Panic Abandonment** — spending a high-value asset on impulse with no
  recapture and no calculable 2–3 turn delayed payoff.

When you repeat a flaw **3+ times**, the database flags it, **scales the
difficulty down** (`difficulty_bias`), and forces VOSS to dedicate his
transmissions to correcting that specific error (Adaptive Guidance).

Progress (Elo capability, win/loss/draw history, flaw flags) and every agent
transmission are persisted in a local SQLite database (`command_center.db`).

---

## 3. Curriculum Scenarios

Four pre-configured board states (FENs) handled by `engine.py`:

| Level | Codename       | Difficulty       | Lesson |
|-------|----------------|------------------|--------|
| 1 | BASIC COHESION  | Easy             | Protect your Spies with Infantry |
| 2 | DELAYED THUNDER | Medium           | Sacrifice now to win a lane 3 turns later |
| 3 | GLASS TRAP      | Complex          | Refuse the textbook bait; it snaps a trap shut |
| 4 | COLD STEEL      | Deeply Complex   | Ruthless material prioritization in the endgame |

---

## 4. Deployment & Execution (Step-by-Step)

### Prerequisites
- Python **3.10+**
- Node.js **18+** and npm

### Step 1 — Backend environment setup

```bash
# From the repo root:
cd chess-platoon-mentor/backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Bring FIELD MARSHAL VOSS online with a real LLM (OPTIONAL).
# Without a key the agent runs in deterministic OFFLINE mode — fully playable.
export OPENAI_API_KEY="sk-...your-key..."     # Windows: set OPENAI_API_KEY=...
# (You may instead paste the key into backend/.env)
```

### Step 2 — Start the backend (API gateway on port 8000)

```bash
# From chess-platoon-mentor/backend, with the venv active:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's alive:
```bash
curl http://localhost:8000/api/health
# -> {"status":"ok","live_agent":true|false}
```
Interactive API docs: <http://localhost:8000/docs>

### Step 3 — Start the frontend

```bash
# In a NEW terminal, from the repo root:
cd chess-platoon-mentor/frontend

npm install
npm run dev
```

Open the War Room at <http://localhost:3000>.

> The frontend reads `NEXT_PUBLIC_API_BASE` (defaults to
> `http://localhost:8000`). Override it by creating `frontend/.env.local`:
> ```
> NEXT_PUBLIC_API_BASE=http://localhost:8000
> ```

### Step 4 — Mission Verification Checklist

Confirm the frontend is communicating cleanly with the backend:

- [ ] **Gateway link** — the header shows `GATEWAY ONLINE :8000` with a green dot.
- [ ] **Agent link** — the comms sidebar shows `LIVE LINK` (key set) or
      `OFFLINE RELAY` (no key). Both are valid operating modes.
- [ ] **Scenarios load** — four mission buttons (LVL 1–4) render across the top.
- [ ] **Opening transmission** — VOSS issues a briefing when a mission starts.
- [ ] **Moves round-trip** — drag a piece; the board updates, an enemy reply
      appears, and a new VOSS transmission streams into the sidebar.
- [ ] **Flaw detection** — push a lone Spy deep (e.g. an unsupported Knight to
      the 6th rank) and confirm a red **FLAW DETECTED** card appears.
- [ ] **Dossier updates** — the Commander Dossier shows Elo / W-L-D and, after
      repeated flaws, a highlighted **Focus Flaw**.
- [ ] **Persistence** — reload the page; your Commander ID and progress persist.

#### Quick non-UI smoke test (curl)

```bash
curl -X POST http://localhost:8000/api/new-game \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","level":1}'

curl -X POST http://localhost:8000/api/move \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","move":"g1f3"}'

curl http://localhost:8000/api/progress/demo
curl http://localhost:8000/api/diagnostics/demo
```

---

## API Reference

| Method | Path                         | Purpose |
|--------|------------------------------|---------|
| GET    | `/api/health`                | Liveness + whether the live agent is wired |
| GET    | `/api/scenarios`             | The 4-level curriculum metadata |
| POST   | `/api/new-game`              | Start/reset a scenario `{user_id, level}` |
| POST   | `/api/move`                  | Submit a move `{user_id, move}` (UCI) |
| GET    | `/api/progress/{user_id}`    | Elo, record, and flaw flags |
| GET    | `/api/diagnostics/{user_id}` | Recent diagnostic transmissions log |
| GET    | `/api/factions`              | The 4 playable armies + theming |
| POST   | `/api/set-faction`           | Choose an army `{user_id, faction}` |
| GET    | `/api/academy?user_id=...`   | Teaching doctrine (faction-flavoured) |
| POST   | `/api/auth/register`         | Create account `{email, password}` → JWT |
| POST   | `/api/auth/login`            | Log in `{email, password}` → JWT |
| GET    | `/api/auth/me`               | Current account (requires `Bearer` token) |

**Login:** send the JWT as `Authorization: Bearer <token>` on any call — the
backend then ties all progress to that account, so it follows the player across
web **and** mobile. Anonymous play still works without a token.

**Active games are persisted in the database** (not process memory), so the
backend is restart-safe and multi-instance ready.

> 📋 **All configuration — env vars, secrets, hosting decisions, and the launch
> checklist — lives in [`CONFIGURATION.md`](./CONFIGURATION.md).**

## Mobile app (Expo)

The phone app lives in `mobile/` and talks to the **same backend** — nothing is
hosted twice. Setup:

```bash
cd chess-platoon-mentor/mobile
npm install
npx expo start            # scan the QR code with Expo Go
```

Point it at your machine: set `extra.apiBase` in `mobile/app.json` to your
computer's LAN IP (e.g. `http://192.168.1.42:8000`) — on a phone `localhost`
means the phone, not your dev machine. Full details in `mobile/README.md`.

---

## Production status & deployment

**The brain is production-ready; a couple of infra items remain.**

| Capability | Status |
|---|---|
| Automated test suite (pytest, 22 tests) | ✅ `backend/tests/` |
| CI: tests on **SQLite + Postgres**, frontend build, Docker build | ✅ `.github/workflows/chess-platoon-ci.yml` |
| Containerized backend | ✅ `backend/Dockerfile` |
| Postgres support (same code as SQLite) | ✅ via `DATABASE_URL` |
| CORS lockdown via env | ✅ `CORS_ORIGINS` |
| Login / auth (cross-device memory) | ⏳ next |
| Active-game session store (currently in-memory, single-instance) | ⏳ move to DB/Redis for multi-instance |

### Run the tests

```bash
cd chess-platoon-mentor/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest                       # runs on a throwaway SQLite db
# against Postgres:
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/db pytest
```

### Production environment variables (backend)

| Var | Purpose |
|---|---|
| `OPENAI_API_KEY` | Brings the live agent online (blank = offline mode) |
| `DATABASE_URL` | Postgres URL for production (unset = SQLite file) |
| `CORS_ORIGINS` | Comma-separated allowlist of front-end domains |
| `PORT` | Port to bind (set automatically by most hosts) |

### Deploy the backend (Docker)

```bash
cd chess-platoon-mentor/backend
docker build -t chess-platoon-backend .
docker run -p 8000:8000 -e DATABASE_URL=... -e OPENAI_API_KEY=... chess-platoon-backend
```

Cheapest managed path: **Render / Railway / Fly.io** (backend container) +
**Vercel** (frontend) + **Neon / Supabase** (Postgres) — all have free tiers.

## Notes

- **No OpenAI key required to run.** `agent.py` degrades gracefully to a
  deterministic, in-character offline generator, so local dev and CI stay green.
- The board's authoritative state lives in `engine.py` (python-chess); the
  frontend validates locally with `chess.js` only for instant UX feedback and
  always reconciles with the backend FEN.
- The enemy AI is an intentionally lightweight, deterministic 1-ply responder
  so curriculum scenarios behave predictably.
