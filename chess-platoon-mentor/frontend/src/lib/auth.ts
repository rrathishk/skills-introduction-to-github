/**
 * auth.ts — tiny client-side auth helper for the web app.
 *
 * Stores the JWT in localStorage and exposes helpers to attach it to API
 * calls. When a token is present, the backend ties all actions to the logged
 * in account, so progress follows the user across devices.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const TOKEN_KEY = "cc_token";

export interface AuthUser {
  id: string;
  email: string;
  display_name?: string;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

/** Authorization header (empty object when anonymous). */
export function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function post(path: string, body: unknown) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((data as any).detail ?? "Request failed");
  return data;
}

export async function register(email: string, password: string, displayName?: string) {
  const data = await post("/api/auth/register", {
    email,
    password,
    display_name: displayName,
  });
  setToken(data.token);
  return data.user as AuthUser;
}

export async function login(email: string, password: string) {
  const data = await post("/api/auth/login", { email, password });
  setToken(data.token);
  return data.user as AuthUser;
}

export async function fetchMe(): Promise<AuthUser | null> {
  const t = getToken();
  if (!t) return null;
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, { headers: authHeaders() });
    if (!res.ok) {
      if (res.status === 401) setToken(null); // expired/invalid → drop it
      return null;
    }
    return (await res.json()).user as AuthUser;
  } catch {
    return null;
  }
}

export function logout() {
  setToken(null);
}
