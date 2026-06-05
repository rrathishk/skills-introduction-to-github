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
│   ├── requirements.txt
│   └── .env
└── README.md                 # (this file)
```

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

---

## Notes

- **No OpenAI key required to run.** `agent.py` degrades gracefully to a
  deterministic, in-character offline generator, so local dev and CI stay green.
- The board's authoritative state lives in `engine.py` (python-chess); the
  frontend validates locally with `chess.js` only for instant UX feedback and
  always reconciles with the backend FEN.
- The enemy AI is an intentionally lightweight, deterministic 1-ply responder
  so curriculum scenarios behave predictably.
