# Faction artwork

Drop each army's images here and they render automatically across the web app.
Until a file is present, the UI falls back to the flag emoji + the faction's
crest color (so nothing breaks if artwork is missing).

```
frontend/public/factions/
├── india/    crest.png   general.png
├── usa/      crest.png   general.png
├── russia/   crest.png   general.png
└── china/    crest.png   general.png
```

- **crest.png** — square emblem/insignia (recommended 256×256, transparent PNG).
- **general.png** — portrait of the commanding general (recommended 512×512).

The exact paths each faction expects are declared in
`backend/app/factions.py` under each faction's `assets` map. Keep the file
names in sync with that config.

> ⚠️ Use only artwork you have the rights to ship. Real general portraits and
> national insignia may be subject to copyright/trademark — commission or
> license originals, or use stylised, non-infringing crests.
