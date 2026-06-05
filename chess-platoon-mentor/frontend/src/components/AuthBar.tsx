"use client";

import { useState } from "react";
import { AuthUser, login, register, logout } from "@/lib/auth";

/**
 * AuthBar — compact login/register control for the header. When logged in it
 * shows the account + a logout button; otherwise a small inline form. Calls
 * `onChange` after any auth transition so the War Room can reload progress.
 */
export default function AuthBar({
  user,
  accent = "#5ef38c",
  onChange,
}: {
  user: AuthUser | null;
  accent?: string;
  onChange: (user: AuthUser | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) {
    return (
      <div className="flex items-center gap-2 text-xs">
        <span className="text-warroom-muted">
          ✅ <span style={{ color: accent }}>{user.display_name ?? user.email}</span>
        </span>
        <button
          onClick={() => {
            logout();
            onChange(null);
          }}
          className="rounded border border-warroom-border px-2 py-1 text-warroom-muted hover:border-warroom-danger/60"
        >
          Logout
        </button>
      </div>
    );
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const u = mode === "login" ? await login(email, password) : await register(email, password);
      onChange(u);
      setOpen(false);
      setEmail("");
      setPassword("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="rounded border border-warroom-border px-3 py-2 text-xs text-warroom-muted hover:border-warroom-accent/60"
      >
        🔐 Login / Sign up
      </button>
    );
  }

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-warroom-border bg-warroom-panel p-3 text-xs">
      <div className="flex gap-2">
        {(["login", "register"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className="rounded px-2 py-1"
            style={{
              color: mode === m ? accent : "#7d8b78",
              borderBottom: mode === m ? `1px solid ${accent}` : "1px solid transparent",
            }}
          >
            {m === "login" ? "Log in" : "Sign up"}
          </button>
        ))}
      </div>
      <input
        type="email"
        placeholder="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="rounded border border-warroom-border bg-warroom-bg px-2 py-1 text-warroom-muted outline-none"
      />
      <input
        type="password"
        placeholder="password (min 8 chars)"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="rounded border border-warroom-border bg-warroom-bg px-2 py-1 text-warroom-muted outline-none"
      />
      {error && <p className="text-warroom-danger">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={submit}
          disabled={busy}
          className="rounded px-3 py-1 font-bold disabled:opacity-50"
          style={{ background: `${accent}22`, color: accent }}
        >
          {busy ? "…" : mode === "login" ? "Log in" : "Create account"}
        </button>
        <button onClick={() => setOpen(false)} className="text-warroom-muted">
          Cancel
        </button>
      </div>
    </div>
  );
}
