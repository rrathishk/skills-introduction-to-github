"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import TacticalBoard from "@/components/TacticalBoard";
import CommsSidebar, { CommsEntry } from "@/components/CommsSidebar";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

// Stable per-browser commander id so progress persists across reloads.
function getUserId(): string {
  if (typeof window === "undefined") return "commander";
  let id = window.localStorage.getItem("cc_user_id");
  if (!id) {
    id = `cmdr_${Math.random().toString(36).slice(2, 10)}`;
    window.localStorage.setItem("cc_user_id", id);
  }
  return id;
}

interface Scenario {
  level: number;
  codename: string;
  difficulty: string;
  objective: string;
  briefing: string;
}

interface Progress {
  elo: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  flaw_counts: Record<string, number>;
  dominant_flaw: string | null;
  difficulty_bias: number;
}

const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

let entryCounter = 0;
function newEntry(e: Omit<CommsEntry, "id">): CommsEntry {
  entryCounter += 1;
  return { id: `e${entryCounter}_${Date.now()}`, ...e };
}

export default function WarRoom() {
  const [userId, setUserId] = useState("commander");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [activeLevel, setActiveLevel] = useState<number>(1);
  const [fen, setFen] = useState<string>(START_FEN);
  const [entries, setEntries] = useState<CommsEntry[]>([]);
  const [pending, setPending] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [liveAgent, setLiveAgent] = useState(false);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [connected, setConnected] = useState<boolean | null>(null);
  const startedRef = useRef(false);

  const pushEntry = useCallback((e: Omit<CommsEntry, "id">) => {
    setEntries((prev) => [...prev, newEntry(e)]);
  }, []);

  const loadProgress = useCallback(
    async (uid: string) => {
      try {
        const res = await fetch(`${API_BASE}/api/progress/${uid}`);
        if (res.ok) setProgress(await res.json());
      } catch {
        /* non-fatal */
      }
    },
    [],
  );

  // -- bootstrap: health, scenarios, first game ---------------------------
  useEffect(() => {
    const uid = getUserId();
    setUserId(uid);

    (async () => {
      try {
        const health = await fetch(`${API_BASE}/api/health`);
        const hjson = await health.json();
        setConnected(true);
        setLiveAgent(Boolean(hjson.live_agent));
      } catch {
        setConnected(false);
      }

      try {
        const res = await fetch(`${API_BASE}/api/scenarios`);
        const data = await res.json();
        setScenarios(data.scenarios ?? []);
      } catch {
        /* non-fatal */
      }

      if (!startedRef.current) {
        startedRef.current = true;
        await startGame(1, uid);
        await loadProgress(uid);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function startGame(level: number, uid: string) {
    setPending(true);
    setGameOver(false);
    try {
      const res = await fetch(`${API_BASE}/api/new-game`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: uid, level }),
      });
      const data = await res.json();
      setActiveLevel(data.level);
      setFen(data.fen);
      setEntries([
        newEntry({
          kind: "system",
          text: `MISSION ${data.level} — ${data.codename} [${data.difficulty}]\nOBJECTIVE: ${data.objective}`,
        }),
        newEntry({ kind: "agent", text: data.transmission }),
      ]);
      if (data.eased) {
        pushEntry({
          kind: "system",
          text: "ADAPTIVE GUIDANCE: difficulty scaled down to rebuild fundamentals.",
        });
      }
    } catch {
      setConnected(false);
      pushEntry({
        kind: "system",
        text: "LINK FAILURE — cannot reach command gateway on port 8000.",
      });
    } finally {
      setPending(false);
    }
  }

  const handleAttemptMove = useCallback(
    async (uci: string) => {
      if (gameOver || pending) return;
      setPending(true);
      try {
        const res = await fetch(`${API_BASE}/api/move`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, move: uci }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          pushEntry({
            kind: "system",
            text: `Move rejected: ${err.detail ?? "illegal manoeuvre."}`,
          });
          return;
        }

        const data = await res.json();
        setFen(data.fen);

        if (data.flaws && data.flaws.length > 0) {
          pushEntry({
            kind: "flaw",
            text: "Structural vulnerability detected in your manoeuvre.",
            flaws: data.flaws,
          });
        }

        pushEntry({ kind: "agent", text: data.transmission });

        if (data.game_over) {
          setGameOver(true);
          const label =
            data.result === "win"
              ? "VICTORY — objective secured."
              : data.result === "loss"
              ? "DEFEAT — Commander-in-Chief lost."
              : "DRAW — stalemate on the field.";
          pushEntry({ kind: "result", text: label });
        }

        await loadProgress(userId);
      } catch {
        pushEntry({ kind: "system", text: "Transmission lost. Check the gateway link." });
      } finally {
        setPending(false);
      }
    },
    [gameOver, pending, userId, pushEntry, loadProgress],
  );

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8">
      {/* Header */}
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-warroom-border pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-[0.2em] text-warroom-accent">
            ◆ PLATOON COMMAND CENTER
          </h1>
          <p className="text-xs uppercase tracking-[0.3em] text-warroom-muted">
            Psychological Warfare Chess Trainer
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`pulse-dot h-2.5 w-2.5 rounded-full ${
              connected ? "bg-warroom-accent" : "bg-warroom-danger"
            }`}
          />
          <span className={connected ? "text-warroom-accent" : "text-warroom-danger"}>
            {connected === null
              ? "LINKING…"
              : connected
              ? "GATEWAY ONLINE :8000"
              : "GATEWAY OFFLINE"}
          </span>
        </div>
      </header>

      {/* Mission selector */}
      <nav className="flex flex-wrap gap-2">
        {scenarios.map((s) => (
          <button
            key={s.level}
            onClick={() => startGame(s.level, userId)}
            disabled={pending}
            className={`rounded-md border px-3 py-2 text-left text-xs transition ${
              activeLevel === s.level
                ? "border-warroom-accent bg-warroom-accent/10 text-warroom-accent"
                : "border-warroom-border bg-warroom-panel text-warroom-muted hover:border-warroom-accent/50"
            } disabled:opacity-40`}
          >
            <span className="block font-bold">LVL {s.level} · {s.codename}</span>
            <span className="block opacity-70">{s.difficulty}</span>
          </button>
        ))}
      </nav>

      {/* Battlefield + comms */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[auto_1fr]">
        <div className="flex flex-col gap-4">
          <TacticalBoard
            fen={fen}
            disabled={pending || gameOver}
            onAttemptMove={handleAttemptMove}
          />

          {/* Diagnostics dossier */}
          <div className="rounded-lg border border-warroom-border bg-warroom-panel p-4 text-xs">
            <p className="mb-2 text-[10px] uppercase tracking-[0.3em] text-warroom-muted">
              Commander Dossier
            </p>
            {progress ? (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat label="Elo" value={String(progress.elo)} />
                <Stat
                  label="W / L / D"
                  value={`${progress.wins}/${progress.losses}/${progress.draws}`}
                />
                <Stat label="Win Rate" value={`${Math.round(progress.win_rate * 100)}%`} />
                <Stat
                  label="Focus Flaw"
                  value={
                    progress.dominant_flaw
                      ? progress.dominant_flaw.replace(/_/g, " ")
                      : "none"
                  }
                  danger={Boolean(progress.dominant_flaw)}
                />
              </div>
            ) : (
              <p className="text-warroom-muted">Calibrating capability profile…</p>
            )}
          </div>
        </div>

        <div className="h-[640px]">
          <CommsSidebar entries={entries} liveAgent={liveAgent} pending={pending} />
        </div>
      </section>

      <footer className="border-t border-warroom-border pt-3 text-center text-[10px] uppercase tracking-[0.3em] text-warroom-muted">
        Commander ID: {userId} · {liveAgent ? "VOSS LIVE" : "VOSS OFFLINE RELAY"}
      </footer>
    </main>
  );
}

function Stat({
  label,
  value,
  danger = false,
}: {
  label: string;
  value: string;
  danger?: boolean;
}) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wide text-warroom-muted">{label}</p>
      <p className={`text-sm font-bold ${danger ? "text-warroom-danger" : "text-warroom-accent"}`}>
        {value}
      </p>
    </div>
  );
}
