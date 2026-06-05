"use client";

/**
 * Academy
 * -------
 * The teaching screen shown before (and accessible during) play. It rewires
 * how the player sees the board: each piece becomes an army asset with a
 * strength, a deployment doctrine, and a psychological lesson. Plus the four
 * strategic doctrines: position early, when to sacrifice, when to accept
 * defeat, when to hold.
 */

export interface AcademyData {
  intro: string;
  asset_doctrine: Array<{
    key: string;
    asset: string;
    piece: string;
    strength: string;
    deploy: string;
    shift: string;
    psychology: string;
    faction_name?: string;
  }>;
  strategic_doctrine: Array<{ key: string; title: string; lesson: string }>;
  mission_map: Array<{ level: number; teaches: string }>;
}

export interface AcademyProps {
  data: AcademyData;
  accent?: string;
  onClose: () => void;
}

export default function Academy({ data, accent = "#5ef38c", onClose }: AcademyProps) {
  return (
    <div className="fixed inset-0 z-40 overflow-y-auto bg-warroom-bg/95 p-4 sm:p-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold tracking-[0.2em]" style={{ color: accent }}>
            ◆ THE ACADEMY
          </h2>
          <button
            onClick={onClose}
            className="rounded border border-warroom-border px-4 py-2 text-xs text-warroom-muted hover:border-warroom-accent/60"
          >
            ENTER THE WAR ROOM →
          </button>
        </div>

        <p className="mb-6 rounded-lg border border-warroom-border bg-warroom-panel p-4 text-sm leading-relaxed text-[#cdeccf]">
          {data.intro}
        </p>

        {/* Asset doctrine */}
        <h3 className="mb-2 text-xs uppercase tracking-[0.3em] text-warroom-muted">
          Know Your Assets
        </h3>
        <div className="mb-6 grid grid-cols-1 gap-3 md:grid-cols-2">
          {data.asset_doctrine.map((c) => (
            <div
              key={c.key}
              className="rounded-lg border border-warroom-border bg-warroom-panel p-4"
            >
              <p className="text-sm font-bold" style={{ color: accent }}>
                {c.faction_name ?? c.asset}{" "}
                <span className="text-[10px] font-normal text-warroom-muted">
                  ({c.piece})
                </span>
              </p>
              <p className="mt-2 text-xs text-[#cdeccf]">
                <span className="text-warroom-muted">Strength:</span> {c.strength}
              </p>
              <p className="mt-1 text-xs text-[#cdeccf]">
                <span className="text-warroom-muted">Deploy:</span> {c.deploy}
              </p>
              <p className="mt-2 text-xs italic" style={{ color: accent }}>
                {c.shift}
              </p>
              <p className="mt-1 text-[11px] text-warroom-muted">{c.psychology}</p>
            </div>
          ))}
        </div>

        {/* Strategic doctrine */}
        <h3 className="mb-2 text-xs uppercase tracking-[0.3em] text-warroom-muted">
          The Psychology of Command
        </h3>
        <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {data.strategic_doctrine.map((d) => (
            <div
              key={d.key}
              className="rounded-lg border border-warroom-border bg-warroom-panel p-4"
            >
              <p className="text-sm font-bold" style={{ color: accent }}>
                {d.title}
              </p>
              <p className="mt-1 text-xs leading-relaxed text-[#cdeccf]">{d.lesson}</p>
            </div>
          ))}
        </div>

        {/* Mission ladder */}
        <h3 className="mb-2 text-xs uppercase tracking-[0.3em] text-warroom-muted">
          Your Campaign
        </h3>
        <ul className="space-y-2">
          {data.mission_map.map((m) => (
            <li
              key={m.level}
              className="rounded border border-warroom-border bg-warroom-panel px-3 py-2 text-xs text-[#cdeccf]"
            >
              <span className="font-bold" style={{ color: accent }}>
                LVL {m.level}
              </span>{" "}
              — {m.teaches}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
