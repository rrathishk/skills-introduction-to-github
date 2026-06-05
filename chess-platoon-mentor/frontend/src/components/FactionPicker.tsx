"use client";

/**
 * FactionPicker
 * -------------
 * Lets the commander choose their army: India, USA, Russia, or China. Each
 * card shows the flag (or crest image if present), the commanding general, and
 * the faction motto. Selecting one re-themes the whole War Room.
 */

export interface Faction {
  id: string;
  name: string;
  country: string;
  flag: string;
  general: string;
  general_title: string;
  motto: string;
  colors: Record<string, string>;
  rank_names: Record<string, string>;
  assets: Record<string, string>;
}

export interface FactionPickerProps {
  factions: Faction[];
  selectedId?: string;
  onSelect: (id: string) => void;
}

export default function FactionPicker({
  factions,
  selectedId,
  onSelect,
}: FactionPickerProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {factions.map((f) => {
        const active = f.id === selectedId;
        return (
          <button
            key={f.id}
            onClick={() => onSelect(f.id)}
            className="rounded-lg border p-3 text-left transition"
            style={{
              borderColor: active ? f.colors.accent : "#1f2b1a",
              background: active ? `${f.colors.accent}1a` : "#11160f",
              boxShadow: active ? `0 0 24px ${f.colors.accent}33` : "none",
            }}
          >
            {/* Crest image with flag-emoji fallback */}
            <div className="mb-2 flex items-center gap-2">
              <CrestOrFlag faction={f} />
              <div>
                <p className="text-sm font-bold" style={{ color: f.colors.accent }}>
                  {f.country}
                </p>
                <p className="text-[10px] uppercase tracking-wide text-warroom-muted">
                  {f.name}
                </p>
              </div>
            </div>
            <p className="text-[11px] text-[#cdeccf]">{f.general}</p>
            <p className="mt-1 text-[10px] italic text-warroom-muted">“{f.motto}”</p>
          </button>
        );
      })}
    </div>
  );
}

function CrestOrFlag({ faction }: { faction: Faction }) {
  // Try the crest image; if it 404s, the flag emoji shows underneath.
  return (
    <span className="relative inline-flex h-9 w-9 items-center justify-center">
      <span
        className="absolute inset-0 flex items-center justify-center rounded text-2xl"
        aria-hidden
      >
        {faction.flag}
      </span>
      {faction.assets?.crest && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={faction.assets.crest}
          alt={`${faction.country} crest`}
          className="relative h-9 w-9 rounded object-contain"
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).style.display = "none";
          }}
        />
      )}
    </span>
  );
}
