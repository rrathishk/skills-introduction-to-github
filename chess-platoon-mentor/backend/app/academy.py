"""
academy.py
==========
The Academy — the teaching layer that comes BEFORE the player ever makes a
move. Its job is not to train chess tactics directly; it is to *rewire how the
player sees the board*. Once a player stops seeing "pieces" and starts seeing a
platoon of assets with strengths, weaknesses, and ideal deployment zones, the
tactics follow naturally.

The curriculum is delivered as structured "doctrine cards" the front-ends
render as an onboarding flow / academy screen. Each card teaches one mental
shift: the asset's identity, its strength, where it belongs, and the
psychology of using it.

This module is pure data + helpers — no chess logic, no LLM.
"""

from __future__ import annotations

from typing import Dict, List

# ---------------------------------------------------------------------------
# Asset doctrine — one card per piece class. The "shift" field is the core
# mental reframing we want the player to internalise.
# ---------------------------------------------------------------------------

ASSET_DOCTRINE: List[Dict] = [
    {
        "key": "pawn",
        "asset": "Infantry",
        "piece": "Pawn",
        "strength": "Numbers, terrain control, and sacrifice value.",
        "deploy": "Hold the centre and form defensive perimeters. Never advance "
                  "a lone soldier without the line behind it.",
        "shift": "Stop seeing pawns as weak. Infantry WINS WARS — they take and "
                 "hold ground. A wall of Infantry is a fortress; a scattered "
                 "one is a graveyard.",
        "psychology": "Every soldier you advance is terrain you can never "
                      "un-commit. Move with intent, not impulse.",
    },
    {
        "key": "knight",
        "asset": "Spy / Recon",
        "piece": "Knight",
        "strength": "Infiltration. Jumps lines, strikes from unexpected angles.",
        "deploy": "Push into enemy territory ONLY with support behind it. A Spy "
                  "deep in enemy lines with no backup is a captured Spy.",
        "shift": "A Spy is not a brawler — it is a scalpel. Its power is fear and "
                 "position, not brute force.",
        "psychology": "Lone infiltration feels brave. It is usually just lost "
                      "intelligence. Support first, infiltrate second.",
    },
    {
        "key": "bishop",
        "asset": "Diagonal Sniper",
        "piece": "Bishop",
        "strength": "Long-range crossfire down open diagonals.",
        "deploy": "Open the diagonals and let it dominate from distance. Useless "
                  "when boxed in by your own Infantry.",
        "shift": "A Sniper rules the lanes you can't see coming. Watch every "
                 "open diagonal — yours AND the enemy's.",
        "psychology": "Death on a chessboard most often arrives from a diagonal "
                      "nobody was watching. Sweep the lanes before you move.",
    },
    {
        "key": "rook",
        "asset": "Heavy Armor",
        "piece": "Rook",
        "strength": "Devastating straight-line blitz down files and ranks.",
        "deploy": "Save it for open columns. Doubled Heavy Armor on an open file "
                  "is a battering ram nothing survives.",
        "shift": "Heavy Armor is patient. It does nothing for ten turns, then "
                 "ends the war in two. Don't waste it early.",
        "psychology": "Power held in reserve is power doubled. Deploy when the "
                      "lane opens, not before.",
    },
    {
        "key": "queen",
        "asset": "Strike Commander",
        "piece": "Queen",
        "strength": "Highest impact asset on the field — total mobility.",
        "deploy": "Bring it out LATE. Early deployment paints a target; the "
                  "enemy will chase it and develop their whole army for free.",
        "shift": "Your Strike Commander is precious, not invincible. Respect it "
                 "the way the enemy fears it.",
        "psychology": "Spending your highest asset on impulse is panic. Spending "
                      "it on a calculated 2-3 move payoff is strategy.",
    },
    {
        "key": "king",
        "asset": "Commander-in-Chief",
        "piece": "King",
        "strength": "The objective. In the endgame, an active combatant.",
        "deploy": "Fortify it EARLY (castle). In the endgame, march it forward — "
                  "it becomes a weapon.",
        "shift": "Early game: the Commander hides. Endgame: the Commander "
                 "fights. Knowing when to switch is mastery.",
        "psychology": "Lose the Commander, lose the war. Every other decision is "
                      "subordinate to keeping it alive until it's time to fight.",
    },
]

# ---------------------------------------------------------------------------
# Strategic doctrine — the psychology of decision-making. These are the four
# hardest mental lessons: position early, when to sacrifice, when to accept
# defeat, and when to simply hold.
# ---------------------------------------------------------------------------

STRATEGIC_DOCTRINE: List[Dict] = [
    {
        "key": "position_early",
        "title": "Take Position Early",
        "lesson": "Wars are won in the opening, not the endgame. Claim the "
                  "centre, develop your assets, and fortify your Commander "
                  "before the first shot is exchanged. Ground taken early is "
                  "ground you don't bleed for later.",
    },
    {
        "key": "when_to_sacrifice",
        "title": "When to Sacrifice",
        "lesson": "A sacrifice is an INVESTMENT, never a loss. Give up an asset "
                  "only when you can name the payoff — an open lane, a trapped "
                  "enemy Commander, a winning position 2-3 moves later. If you "
                  "can't name the return, it isn't a sacrifice, it's a blunder.",
    },
    {
        "key": "when_to_accept_defeat",
        "title": "When to Accept Defeat",
        "lesson": "A lost position drained of assets is intelligence, not shame. "
                  "Recognising a hopeless line early saves the morale and the "
                  "time you'd waste defending it. Concede the battle, study the "
                  "loss, and redeploy for the next one.",
    },
    {
        "key": "when_to_hold",
        "title": "When to Hold",
        "lesson": "Not every turn demands aggression. Sometimes the strongest "
                  "move is to consolidate, support an exposed asset, and force "
                  "the enemy to overcommit first. Patience baits mistakes.",
    },
]

# ---------------------------------------------------------------------------
# Mission ladder — how the 4 scenarios map onto the doctrine, so the academy
# can tell the player what each level will drill.
# ---------------------------------------------------------------------------

MISSION_MAP: List[Dict] = [
    {"level": 1, "teaches": "Basic Cohesion — protect your Spies with Infantry."},
    {"level": 2, "teaches": "Delayed Sacrifice — give up an asset now, win a lane later."},
    {"level": 3, "teaches": "Reading the Bait — refuse the obvious trap."},
    {"level": 4, "teaches": "Ruthless Prioritisation — cold sacrifices to win."},
]


def academy_payload(rank_names: Dict[str, str] | None = None) -> Dict:
    """
    Return the full academy curriculum. If a faction's ``rank_names`` map is
    supplied, each asset doctrine card is decorated with that faction's
    nation-specific name so the lesson speaks in the player's chosen flavour.
    """
    cards = []
    for card in ASSET_DOCTRINE:
        decorated = dict(card)
        if rank_names and card["key"] in rank_names:
            decorated["faction_name"] = rank_names[card["key"]]
        cards.append(decorated)

    return {
        "intro": (
            "Welcome, Commander. This board is not a game of chess — it is a "
            "platoon under your command. Before you fight, learn to SEE. Every "
            "square is terrain. Every piece is an asset with a strength, a "
            "weakness, and a place it belongs. Master how you look at the board, "
            "and victory becomes inevitable."
        ),
        "asset_doctrine": cards,
        "strategic_doctrine": STRATEGIC_DOCTRINE,
        "mission_map": MISSION_MAP,
    }
