"use client";

import { useEffect, useRef } from "react";

/**
 * CommsSidebar
 * ------------
 * The fluid agent comms viewport. Renders the stream of transmissions from
 * FIELD MARSHAL VOSS plus inline flaw alerts. Auto-scrolls to the latest
 * transmission as the engagement unfolds.
 */

export type CommsEntryKind = "agent" | "system" | "flaw" | "result";

export interface CommsEntry {
  id: string;
  kind: CommsEntryKind;
  text: string;
  flaws?: string[];
}

const FLAW_LABELS: Record<string, string> = {
  lone_ranger: "LONE RANGER SYNDROME",
  tunnel_vision: "TUNNEL VISION",
  panic_abandonment: "PANIC ABANDONMENT",
};

function kindStyles(kind: CommsEntryKind): string {
  switch (kind) {
    case "agent":
      return "border-warroom-accent/40 bg-warroom-accent/5 text-[#cdeccf]";
    case "flaw":
      return "border-warroom-danger/50 bg-warroom-danger/10 text-warroom-danger";
    case "result":
      return "border-warroom-amber/50 bg-warroom-amber/10 text-warroom-amber";
    default:
      return "border-warroom-border bg-warroom-panel text-warroom-muted";
  }
}

function kindLabel(kind: CommsEntryKind): string {
  switch (kind) {
    case "agent":
      return "VOSS // TRANSMISSION";
    case "flaw":
      return "DIAGNOSTIC // FLAW DETECTED";
    case "result":
      return "ENGAGEMENT // RESULT";
    default:
      return "SYSTEM";
  }
}

export interface CommsSidebarProps {
  entries: CommsEntry[];
  liveAgent: boolean;
  pending?: boolean;
}

export default function CommsSidebar({
  entries,
  liveAgent,
  pending = false,
}: CommsSidebarProps) {
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = feedRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [entries, pending]);

  return (
    <aside className="flex h-full w-full flex-col rounded-lg border border-warroom-border bg-warroom-panel">
      {/* Header / link status */}
      <div className="flex items-center justify-between border-b border-warroom-border px-4 py-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-warroom-muted">
            Command Comms
          </p>
          <p className="text-sm font-semibold text-warroom-accent">
            FIELD MARSHAL VOSS
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`pulse-dot h-2.5 w-2.5 rounded-full ${
              liveAgent ? "bg-warroom-accent" : "bg-warroom-amber"
            }`}
          />
          <span className={liveAgent ? "text-warroom-accent" : "text-warroom-amber"}>
            {liveAgent ? "LIVE LINK" : "OFFLINE RELAY"}
          </span>
        </div>
      </div>

      {/* Feed */}
      <div ref={feedRef} className="comms-feed flex-1 space-y-3 overflow-y-auto p-4">
        {entries.length === 0 && (
          <p className="text-sm italic text-warroom-muted">
            Awaiting orders, Commander. Deploy a scenario to open the channel.
          </p>
        )}

        {entries.map((entry) => (
          <div
            key={entry.id}
            className={`rounded-md border px-3 py-2 text-sm leading-relaxed ${kindStyles(
              entry.kind,
            )}`}
          >
            <p className="mb-1 text-[10px] uppercase tracking-[0.2em] opacity-70">
              {kindLabel(entry.kind)}
            </p>
            <p className="whitespace-pre-wrap">{entry.text}</p>
            {entry.flaws && entry.flaws.length > 0 && (
              <ul className="mt-2 flex flex-wrap gap-2">
                {entry.flaws.map((f) => (
                  <li
                    key={f}
                    className="rounded bg-warroom-danger/20 px-2 py-0.5 text-[10px] font-bold tracking-wide text-warroom-danger"
                  >
                    {FLAW_LABELS[f] ?? f}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}

        {pending && (
          <div className="rounded-md border border-warroom-accent/30 bg-warroom-accent/5 px-3 py-2 text-sm text-warroom-accent">
            <span className="pulse-dot">VOSS is analysing the field…</span>
          </div>
        )}
      </div>
    </aside>
  );
}
