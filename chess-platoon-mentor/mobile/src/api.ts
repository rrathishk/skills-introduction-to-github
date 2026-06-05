/**
 * api.ts — thin client for the shared FastAPI backend.
 *
 * The phone and the web app talk to the SAME backend. On a real device,
 * `localhost` points at the phone, not your dev machine — so set `apiBase`
 * in app.json (extra.apiBase) to your computer's LAN IP, e.g.
 * http://192.168.1.100:8000. In production, set it to your deployed URL.
 */

import Constants from "expo-constants";

const API_BASE: string =
  (Constants.expoConfig?.extra as any)?.apiBase ?? "http://localhost:8000";

async function jget<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json();
}

async function jpost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as any).detail ?? `POST ${path} -> ${res.status}`);
  }
  return res.json();
}

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

export interface Scenario {
  level: number;
  codename: string;
  difficulty: string;
  objective: string;
  briefing: string;
}

export const api = {
  base: API_BASE,
  health: () => jget<{ status: string; live_agent: boolean }>("/api/health"),
  scenarios: () => jget<{ scenarios: Scenario[] }>("/api/scenarios"),
  factions: () => jget<{ factions: Faction[] }>("/api/factions"),
  academy: (userId: string) => jget<any>(`/api/academy?user_id=${userId}`),
  progress: (userId: string) => jget<any>(`/api/progress/${userId}`),
  setFaction: (userId: string, faction: string) =>
    jpost<any>("/api/set-faction", { user_id: userId, faction }),
  newGame: (userId: string, level: number, faction?: string) =>
    jpost<any>("/api/new-game", { user_id: userId, level, faction }),
  move: (userId: string, move: string) =>
    jpost<any>("/api/move", { user_id: userId, move }),
};
