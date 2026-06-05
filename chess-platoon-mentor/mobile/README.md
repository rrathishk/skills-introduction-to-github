# 📱 Chess Platoon — Mobile App (Expo / React Native)

The phone version of the War Room. It talks to the **same FastAPI backend** as
the web app — choose your army, learn at the Academy, and play, all on your
phone. Nothing is hosted twice: the backend is the shared brain.

## Screens
1. **Faction** — pick your army: 🇮🇳 India · 🇺🇸 USA · 🇷🇺 Russia · 🇨🇳 China
2. **Academy** — the teaching flow that rewires how you see the board
3. **War Room** — the live chess board (`react-native-chessboard`) + Field
   Marshal Voss's coaching, in your faction general's voice

## Setup

```bash
cd chess-platoon-mentor/mobile
npm install
npx expo start          # opens Expo Dev Tools; scan the QR with Expo Go
```

### Point the app at your backend (IMPORTANT)

On a real phone, `localhost` means the phone — not your computer. Set your
machine's LAN IP in `app.json`:

```json
"extra": { "apiBase": "http://<YOUR-COMPUTER-LAN-IP>:8000" }
```

Find your IP with `ipconfig` (Windows) / `ifconfig | grep inet` (macOS/Linux),
e.g. `http://192.168.1.42:8000`. Make sure the backend is running
(`uvicorn app.main:app --host 0.0.0.0 --port 8000`) and the phone is on the
same Wi-Fi. In production, set `apiBase` to your deployed backend URL.

## Building for the stores
- **Apple App Store** — requires an Apple Developer account ($99/yr)
- **Google Play** — requires a Play Console account ($25 one-time)

```bash
npm install -g eas-cli
eas build --platform ios       # or android
eas submit
```

## Faction artwork
Drop crest/general images into `mobile/assets/factions/<id>/` (mirrors the web
app's `frontend/public/factions/`). Until then the flag emoji + faction color
are used as the fallback.

> Note: `react-native-chessboard`'s exact prop names (`colors`, `onMove`) can
> vary by version — if a board prop errors after `npm install`, check the
> installed version's docs and adjust `WarRoomScreen.tsx` accordingly.
