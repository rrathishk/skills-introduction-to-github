# ⚙️ CONFIGURATION — single source of truth

Everything that must be **set, decided, or provisioned** to run this project in
dev and in production lives here. Scan the **Status** column: `✅ done`,
`⚙️ set per-environment`, `🟡 decide`, `❌ TODO`.

> Rule of thumb: **code is committed; secrets are not.** Never commit real keys.
> Set them in your host's dashboard / a secrets manager.

---

## 1. Where are we hosting it? (the plan)

One backend (the "brain") serves both the web app and the mobile app — it is
**not** hosted twice.

| Piece | Recommended host | Free tier? | Status |
|---|---|---|---|
| **Backend** (FastAPI, Docker) | **Render** (or Railway / Fly.io) | Yes → ~$7/mo | 🟡 decide & create account |
| **Database** (Postgres) | **Neon** (or Supabase) | Yes (~0.5 GB) | 🟡 decide & create account |
| **Web frontend** (Next.js) | **Vercel** | Yes | 🟡 decide & create account |
| **Mobile app** (Expo) | **Expo EAS** build → App Store + Play | Build free | 🟡 decide |
| **Domain name** | Cloudflare / Namecheel | ~$12/yr | 🟡 optional |

> Why these: cheapest + simplest at our scale (~$0–7/mo to start). AWS is an
> option but more expensive/complex here — revisit at scale. See the chat
> "cheapest hosting" table.

---

## 2. Secrets & accounts to create

| Item | Needed for | Where to get it | Status |
|---|---|---|---|
| **OpenAI API key** | Live AI coaching (else offline mode) | platform.openai.com | ❌ TODO |
| **`JWT_SECRET_KEY`** | Signing login tokens | generate random 32+ chars | ❌ TODO (prod) |
| **Postgres `DATABASE_URL`** | Production database | from Neon/Supabase | ❌ TODO (prod) |
| **Apple Developer account** | Publish iOS app | developer.apple.com ($99/yr) | 🟡 when shipping mobile |
| **Google Play Console** | Publish Android app | play.google.com/console ($25 once) | 🟡 when shipping mobile |
| **Hosting accounts** | Render / Vercel / Neon | their signup pages | 🟡 when deploying |

Generate a JWT secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 3. Backend environment variables (`backend/.env` / host dashboard)

| Var | Purpose | Dev default | Production | Status |
|---|---|---|---|---|
| `OPENAI_API_KEY` | Live agent | *(blank = offline)* | your key | ⚙️ |
| `OPENAI_MODEL` | Which model | `gpt-4o-mini` | e.g. `gpt-4o-mini` | ✅ default ok |
| `DATABASE_URL` | Postgres URL | *(blank = SQLite file)* | `postgresql+psycopg://…` | ⚙️ |
| `COMMAND_CENTER_DB` | SQLite path (dev only) | `command_center.db` | unused | ✅ |
| `JWT_SECRET_KEY` | Token signing | dev fallback | **strong random** | ❌ set in prod |
| `JWT_TTL_SECONDS` | Login lifetime | 30 days | your choice | ✅ default ok |
| `CORS_ORIGINS` | Allowed front-end origins | `*` | `https://yourapp.com,…` | ❌ lock in prod |
| `PORT` | Bind port | 8000 | set by host | ✅ auto |

> ⚠️ If `JWT_SECRET_KEY` is left at the dev fallback in production, login is
> insecure. The backend logs/serves with the insecure default — set a real one.

---

## 4. Frontend (web) configuration (`frontend/.env.local`)

| Var | Purpose | Dev | Production | Status |
|---|---|---|---|---|
| `NEXT_PUBLIC_API_BASE` | Backend URL | `http://localhost:8000` | `https://api.yourapp.com` | ⚙️ |

---

## 5. Mobile configuration (`mobile/app.json` → `expo.extra`)

| Key | Purpose | Dev | Production | Status |
|---|---|---|---|---|
| `apiBase` | Backend URL | your LAN IP `http://192.168.x.x:8000` | `https://api.yourapp.com` | ⚙️ |

> On a phone, `localhost` is the phone — use your machine's LAN IP in dev.

---

## 6. Artwork & content to supply

| Item | Where it goes | Status |
|---|---|---|
| Faction crests (4) | `frontend/public/factions/<id>/crest.png` + `mobile/assets/...` | ❌ TODO |
| Faction general portraits (4) | `…/<id>/general.png` | ❌ TODO |
| App icon / splash | `mobile/assets/` (referenced in `app.json`) | ❌ TODO |

> Use only licensed/original art (national insignia & real portraits can be
> copyright/trademark). Until supplied, flag emoji + faction color is used.

---

## 7. Pre-production launch checklist

- [ ] Create hosting accounts (§1) and decide final hosts
- [ ] Provision Postgres; set `DATABASE_URL`
- [ ] Set a strong `JWT_SECRET_KEY`
- [ ] Set `OPENAI_API_KEY` (or stay offline intentionally)
- [ ] Set `CORS_ORIGINS` to real domains (not `*`)
- [ ] Point `NEXT_PUBLIC_API_BASE` (web) + `apiBase` (mobile) at prod backend
- [ ] Confirm CI is green (tests on SQLite + Postgres, frontend build, Docker)
- [ ] Deploy backend (Docker) → run DB migration (auto on boot via `init_db`)
- [ ] Deploy frontend (Vercel) → smoke test register / login / play
- [ ] (Mobile) `eas build` + submit to stores
- [ ] Add faction artwork
- [ ] Run full end-to-end test in staging before production

---

## 8. What is NOT yet built (known gaps)

| Gap | Impact | Plan |
|---|---|---|
| Password reset / email verification | Users can't recover accounts | add when needed |
| Rate limiting on auth endpoints | Brute-force exposure | add before public launch |
| Mobile token storage uses memory | Login doesn't persist across app restarts | add `expo-secure-store` |
| Observability (logging/metrics) | Harder to debug prod | add when traffic grows |

> ✅ Already done: auth (register/login/JWT), persisted active-game sessions
> (multi-instance safe), Postgres support, automated tests, CI/CD, Docker.
