"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import TacticalBoard from "@/components/TacticalBoard";
import CommsSidebar, { CommsEntry } from "@/components/CommsSidebar";
import FactionPicker, { Faction } from "@/components/FactionPicker";
import Academy, { AcademyData } from "@/components/Academy";
import AuthBar from "@/components/AuthBar";
import { authHeaders, fetchMe, AuthUser } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

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
  faction?: Faction;
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
  const [factions, setFactions] = useState<Faction[]>([]);
  const [faction, setFaction] = useState<Faction | null>(null);
  const [academyData, setAcademyData] = useState<AcademyData | null>(null);
  const [showAcademy, setShowAcademy] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const startedRef = useRef(false);

  const accent = faction?.colors.accent ?? "#5ef38c";
  const darkSq = faction?.colors.dark ?? "#2e3b27";
  const lightSq = faction?.colors.light ?? "#7d8b78";

  const pushEntry = useCallback((e: Omit<CommsEntry, "id">) => {
    setEntries((prev) => [...prev, newEntry(e)]);
  }, []);

  const loadProgress = useCallback(async (uid: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/progress/${uid}`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setProgress(data);
        if (data.faction) setFaction(data.faction);
      }
    } catch {
      /* non-fatal */
    }
  }, []);

  const loadAcademy = useCallback(async (uid: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/academy?user_id=${uid}`, { headers: authHeaders() });
      if (res.ok) setAcademyData(await res.json());
    } catch {
      /* non-fatal */
    }
  }, []);

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
        const [sc, fc] = await Promise.all([
          fetch(`${API_BASE}/api/scenarios`).then((r) => r.json()),
          fetch(`${API_BASE}/api/factions`).then((r) => r.json()),
        ]);
        setScenarios(sc.scenarios ?? []);
        setFactions(fc.factions ?? []);
      } catch {
        /* non-fatal */
      }

      // Restore a logged-in session if a token is stored.
      const me = await fetchMe();
      setAuthUser(me);

      await loadProgress(uid);
      await loadAcademy(uid);

      // First-time commanders start at the Academy.
      const seen = window.localStorage.getItem("cc_seen_academy");
      if (!seen) setShowAcademy(true);

      if (!startedRef.current) {
        startedRef.current = true;
        await startGame(1, uid);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function chooseFaction(id: string) {
    const f = factions.find((x) => x.id === id) ?? null;
    setFaction(f);
    try {
      await fetch(`${API_BASE}/api/set-faction`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ user_id: userId, faction: id }),
      });
      await loadAcademy(userId); // refresh academy with faction-flavoured names
    } catch {
      /* non-fatal */
    }
    await startGame(activeLevel, userId, id);
  }

  async function startGame(level: number, uid: string, factionId?: string) {
    setPending(true);
    setGameOver(false);
    try {
      const res = await fetch(`${API_BASE}/api/new-game`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ user_id: uid, level, faction: factionId }),
      });
      const data = await res.json();
      setActiveLevel(data.level);
      setFen(data.fen);
      if (data.faction) setFaction(data.faction);
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
          headers: { "Content-Type": "application/json", ...authHeaders() },
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

  function closeAcademy() {
    window.localStorage.setItem("cc_seen_academy", "1");
    setShowAcademy(false);
  }

  async function onAuthChange(u: AuthUser | null) {
    // Logging in/out switches the identity the backend keys off; reload state.
    setAuthUser(u);
    await loadProgress(userId);
    await loadAcademy(userId);
    await startGame(activeLevel, userId);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8">
      {showAcademy && academyData && (
        <Academy data={academyData} accent={accent} onClose={closeAcademy} />
      )}

      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-warroom-border pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-[0.2em]" style={{ color: accent }}>
            ◆ PLATOON COMMAND CENTER
          </h1>
          <p className="text-xs uppercase tracking-[0.3em] text-warroom-muted">
            {faction ? `${faction.flag} ${faction.name} — ${faction.general}` : "Psychological Warfare Chess Trainer"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <AuthBar user={authUser} accent={accent} onChange={onAuthChange} />
          <button
            onClick={() => setShowAcademy(true)}
            className="rounded border border-warroom-border px-3 py-2 text-warroom-muted hover:border-warroom-accent/60"
          >
            📖 ACADEMY
          </button>
          <span className="flex items-center gap-2">
            <span
              className={`pulse-dot h-2.5 w-2.5 rounded-full ${connected ? "bg-warroom-accent" : "bg-warroom-danger"}`}
            />
            <span className={connected ? "text-warroom-accent" : "text-warroom-danger"}>
              {connected === null ? "LINKING…" : connected ? "GATEWAY ONLINE" : "GATEWAY OFFLINE"}
            </span>
          </span>
        </div>
      </header>

      {/* Faction selection */}
      <section>
        <p className="mb-2 text-[10px] uppercase tracking-[0.3em] text-warroom-muted">
          Choose Your Army
        </p>
        <FactionPicker factions={factions} selectedId={faction?.id} onSelect={chooseFaction} />
      </section>

      {/* Mission selector */}
      <nav className="flex flex-wrap gap-2">
        {scenarios.map((s) => (
          <button
            key={s.level}
            onClick={() => startGame(s.level, userId)}
            disabled={pending}
            className="rounded-md border px-3 py-2 text-left text-xs transition disabled:opacity-40"
            style={{
              borderColor: activeLevel === s.level ? accent : "#1f2b1a",
              background: activeLevel === s.level ? `${accent}1a` : "#11160f",
              color: activeLevel === s.level ? accent : "#7d8b78",
            }}
          >
            <span className="block font-bold">
              LVL {s.level} · {s.codename}
            </span>
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
            darkColor={darkSq}
            lightColor={lightSq}
          />

          <div className="rounded-lg border border-warroom-border bg-warroom-panel p-4 text-xs">
            <p className="mb-2 text-[10px] uppercase tracking-[0.3em] text-warroom-muted">
              Commander Dossier
            </p>
            {progress ? (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat label="Elo" value={String(progress.elo)} accent={accent} />
                <Stat
                  label="W / L / D"
                  value={`${progress.wins}/${progress.losses}/${progress.draws}`}
                  accent={accent}
                />
                <Stat
                  label="Win Rate"
                  value={`${Math.round(progress.win_rate * 100)}%`}
                  accent={accent}
                />
                <Stat
                  label="Focus Flaw"
                  value={progress.dominant_flaw ? progress.dominant_flaw.replace(/_/g, " ") : "none"}
                  accent={accent}
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
        Commander ID: {userId} · {liveAgent ? "VOSS LIVE" : "OFFLINE RELAY"}
      </footer>
    </main>
  );
}

function Stat({
  label,
  value,
  accent,
  danger = false,
}: {
  label: string;
  value: string;
  accent: string;
  danger?: boolean;
}) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wide text-warroom-muted">{label}</p>
      <p className="text-sm font-bold" style={{ color: danger ? "#ff5b5b" : accent }}>
        {value}
      </p>
    </div>
  );
}
