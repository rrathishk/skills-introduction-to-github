"""
factions.py
===========
The four playable armies. Choosing a faction is cosmetic + psychological — it
does NOT change the chess rules. It re-skins the board colors, renames the
asset designations into that nation's military flavour, and gives the AI
mentor a named commanding general whose voice the transmissions adopt.

This is the layer that lets a player "pick a side" — India, the United States,
Russia, or China — and feel like they command that nation's platoon.

Real general portraits / crest artwork are NOT shipped in this repo (they are
licensed assets). Each faction declares the asset *paths* it expects; drop the
matching files into `frontend/public/factions/<id>/` (web) and
`mobile/assets/factions/<id>/` (app) and they render automatically. Until then
the UI falls back to the flag emoji + the faction's crest color.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Faction:
    id: str
    name: str               # e.g. "Bharat Command"
    country: str            # e.g. "India"
    flag: str               # emoji fallback
    general: str            # the AI mentor's in-character commander name
    general_title: str      # rank/title of that general
    motto: str
    # Board theming (hex). dark/light = the two square colors.
    colors: Dict[str, str]
    # Nation-flavoured names layered ON TOP of the universal lexicon.
    rank_names: Dict[str, str]
    # Asset paths the front-ends look for (crest + general portrait).
    assets: Dict[str, str] = field(default_factory=dict)


# Universal piece -> generic asset class is defined in engine.ASSET_NAMES.
# Here each faction gives those classes a nation-specific flavour name.

FACTIONS: Dict[str, Faction] = {
    "india": Faction(
        id="india",
        name="Bharat Command",
        country="India",
        flag="🇮🇳",
        general="Field Marshal Arjun Rana",
        general_title="Param Senapati (Supreme Commander)",
        motto="Veerta aur Vivek — Valour and Wisdom.",
        colors={
            "dark": "#1b3a1b",
            "light": "#e6d3a3",
            "accent": "#ff9933",   # saffron
            "panel": "#10160f",
        },
        rank_names={
            "pawn": "Jawan (Infantry)",
            "knight": "Para-Commando (Spy/Recon)",
            "bishop": "Marksman (Diagonal Sniper)",
            "rook": "Armoured Regiment (Heavy Armor)",
            "queen": "Strike Commander",
            "king": "Param Senapati (Commander-in-Chief)",
        },
        assets={
            "crest": "/factions/india/crest.png",
            "general": "/factions/india/general.png",
        },
    ),
    "usa": Faction(
        id="usa",
        name="Eagle Command",
        country="United States",
        flag="🇺🇸",
        general="General Marcus Hale",
        general_title="Chairman, Joint Command",
        motto="This We'll Defend.",
        colors={
            "dark": "#1e2a44",
            "light": "#dfe6f0",
            "accent": "#3c6df0",   # navy/electric blue
            "panel": "#0c111c",
        },
        rank_names={
            "pawn": "Rifleman (Infantry)",
            "knight": "Green Beret (Spy/Recon)",
            "bishop": "Designated Marksman (Diagonal Sniper)",
            "rook": "Abrams Armor (Heavy Armor)",
            "queen": "Strike Commander",
            "king": "Commander-in-Chief",
        },
        assets={
            "crest": "/factions/usa/crest.png",
            "general": "/factions/usa/general.png",
        },
    ),
    "russia": Faction(
        id="russia",
        name="Vostok Command",
        country="Russia",
        flag="🇷🇺",
        general="Marshal Viktor Orlov",
        general_title="Verkhovny (Supreme Commander)",
        motto="Strength in the Cold.",
        colors={
            "dark": "#3a1b1b",
            "light": "#e8d8c0",
            "accent": "#d32f2f",   # deep red
            "panel": "#160f0f",
        },
        rank_names={
            "pawn": "Motostrelok (Infantry)",
            "knight": "Spetsnaz (Spy/Recon)",
            "bishop": "Sniper (Diagonal Sniper)",
            "rook": "Armata Armor (Heavy Armor)",
            "queen": "Strike Commander",
            "king": "Verkhovny (Commander-in-Chief)",
        },
        assets={
            "crest": "/factions/russia/crest.png",
            "general": "/factions/russia/general.png",
        },
    ),
    "china": Faction(
        id="china",
        name="Dragon Command",
        country="China",
        flag="🇨🇳",
        general="General Li Wei",
        general_title="Supreme Field Commander",
        motto="Patience, then the Storm.",
        colors={
            "dark": "#3a2f12",
            "light": "#efe2b8",
            "accent": "#e6b422",   # imperial gold
            "panel": "#15120a",
        },
        rank_names={
            "pawn": "Bingshi (Infantry)",
            "knight": "Recon Operative (Spy/Recon)",
            "bishop": "Sharpshooter (Diagonal Sniper)",
            "rook": "Type-99 Armor (Heavy Armor)",
            "queen": "Strike Commander",
            "king": "Supreme Commander (Commander-in-Chief)",
        },
        assets={
            "crest": "/factions/china/crest.png",
            "general": "/factions/china/general.png",
        },
    ),
}

DEFAULT_FACTION = "india"


def get_faction(faction_id: str) -> Faction:
    return FACTIONS.get(faction_id, FACTIONS[DEFAULT_FACTION])


def faction_public(f: Faction) -> Dict:
    """Serialisable view for the API."""
    return {
        "id": f.id,
        "name": f.name,
        "country": f.country,
        "flag": f.flag,
        "general": f.general,
        "general_title": f.general_title,
        "motto": f.motto,
        "colors": f.colors,
        "rank_names": f.rank_names,
        "assets": f.assets,
    }
