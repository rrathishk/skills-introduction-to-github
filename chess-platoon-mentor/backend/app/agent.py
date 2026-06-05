"""
agent.py
========
The Command persona layer.

Wraps the OpenAI SDK to generate "transmissions" — terse, in-character
military analysis of the commander's last move. The persona NEVER uses
standard chess nomenclature; the lexicon below is injected into every prompt.

If no ``OPENAI_API_KEY`` is configured (or the SDK call fails) the module
falls back to a fully deterministic, offline transmission generator so the
Command Center remains operational without any external dependency. This
keeps local development and CI green even with no network access.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

# The OpenAI SDK is optional at runtime; import defensively.
try:  # pragma: no cover - import guard
    from openai import OpenAI  # type: ignore

    _OPENAI_AVAILABLE = True
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore
    _OPENAI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Hardcoded lexicon — the persona's entire vocabulary
# ---------------------------------------------------------------------------

LEXICON = """
ASSET DESIGNATION PROTOCOL (use these terms ONLY — never say pawn, knight,
bishop, rook, queen, king, check, castle, or any civilian chess word):
- Infantry            = the foot soldiers. Defensive perimeters, terrain
                        commitment, the backbone of any line.
- Spies / Recon       = infiltration units. Deep outposts, sowing chaos
                        behind enemy lines. Fragile if unsupported.
- Diagonal Snipers    = long-range crossfire specialists. Lethal on open
                        diagonals; useless when boxed in.
- Heavy Armor / Elephants = column blitz units. They roll down straight
                        vertical and horizontal lanes.
- Strike Commander    = your single highest-impact, highest-risk asset.
                        Devastating, but never spent on a whim.
- Commander-in-Chief  = the objective. Fortify early, then unleash as an
                        active combatant in the endgame.
""".strip()

PERSONA = """
You are "FIELD MARSHAL VOSS", the AI tactical mentor running a Psychological
Chess Platoon Command Center. You treat every match as psychological warfare,
not a board game. Your transmissions are:
- Terse, clipped, military radio cadence. 2-4 sentences. No fluff.
- Always in-character. Address the human as "Commander".
- Focused on PSYCHOLOGY: pressure, baiting, patience, coldness, morale.
- STRICTLY limited to the Asset Designation Protocol vocabulary.
You analyse the commander's last manoeuvre, name the structural risk if any,
and issue one concrete directive for the next move.
""".strip()


# ---------------------------------------------------------------------------
# Flaw coaching copy (used both to steer the LLM and for offline fallback)
# ---------------------------------------------------------------------------

FLAW_COACHING: Dict[str, Dict[str, str]] = {
    "lone_ranger": {
        "title": "LONE RANGER SYNDROME",
        "note": (
            "You pushed a Spy deep into hostile terrain with no Infantry "
            "anchoring its retreat. Isolated Recon gets captured and tells the "
            "enemy nothing. Bring support up before you infiltrate again."
        ),
    },
    "tunnel_vision": {
        "title": "TUNNEL VISION",
        "note": (
            "You tunneled straight down a vertical lane and walked your asset "
            "into a Diagonal Sniper's crossfire. Stop staring at the column. "
            "Sweep the diagonals before you advance."
        ),
    },
    "panic_abandonment": {
        "title": "PANIC ABANDONMENT",
        "note": (
            "You spent a high-value asset on impulse with no recapture and no "
            "delayed payoff. That is panic, not sacrifice. A real sacrifice is "
            "an investment that pays in two-to-three turns. Calculate, then "
            "commit."
        ),
    },
}


def _system_prompt(level_briefing: str, focus_flaw: Optional[str], eased: bool) -> str:
    parts = [PERSONA, "", LEXICON, "", f"CURRENT MISSION BRIEFING: {level_briefing}"]
    if focus_flaw and focus_flaw in FLAW_COACHING:
        coaching = FLAW_COACHING[focus_flaw]
        parts.append(
            "\nADAPTIVE DIRECTIVE: This commander repeatedly exhibits "
            f"'{coaching['title']}'. {coaching['note']} Dedicate this "
            "transmission to correcting that specific failure, and keep the "
            "tactical demands gentle."
        )
    if eased:
        parts.append(
            "\nDIFFICULTY HAS BEEN SCALED DOWN. Be encouraging but firm; "
            "rebuild the commander's fundamentals."
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Offline / fallback transmission generator
# ---------------------------------------------------------------------------

def _fallback_transmission(
    moved_asset: Optional[str],
    captured_asset: Optional[str],
    flaws: List[str],
    game_over: bool,
    result: Optional[str],
    focus_flaw: Optional[str],
) -> str:
    if game_over:
        if result == "win":
            return (
                "Transmission received. Objective secured, Commander — the "
                "enemy Commander-in-Chief has fallen. Cold, clean, decisive. "
                "Stand down and prep for the next theatre."
            )
        if result == "loss":
            return (
                "Our Commander-in-Chief is down. The line collapsed. Review "
                "the timeline, Commander — defeat is the cheapest intelligence "
                "you will ever buy. We redeploy."
            )
        return (
            "Stalemate on the field. No ground taken, no ground lost. A draw "
            "is a missed kill, Commander. Sharpen the next approach."
        )

    lead = "Manoeuvre logged"
    if moved_asset:
        lead = f"Your {moved_asset} advances"
    if captured_asset:
        lead += f", taking out enemy {captured_asset}"

    if flaws:
        key = flaws[0]
        coaching = FLAW_COACHING.get(key, {})
        return (
            f"{lead}. WARNING — {coaching.get('title', 'STRUCTURAL FLAW')}. "
            f"{coaching.get('note', '')} Tighten up before your next order, "
            "Commander."
        )

    directive = (
        "Hold formation and keep your assets in mutual support. Pressure the "
        "open lanes, but do not overextend."
    )
    if focus_flaw and focus_flaw in FLAW_COACHING:
        directive = (
            "Stay disciplined — remember the standing order: "
            f"{FLAW_COACHING[focus_flaw]['note']}"
        )
    return f"{lead}. Clean execution. {directive}"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

class CommandAgent:
    """Generates in-character transmissions for the War Room."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self._client = None
        if _OPENAI_AVAILABLE and self.api_key:
            try:  # pragma: no cover - network/SDK construction
                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                self._client = None

    @property
    def live(self) -> bool:
        """True when a real OpenAI client is configured."""
        return self._client is not None

    def transmit(
        self,
        *,
        level_briefing: str,
        moved_asset: Optional[str],
        captured_asset: Optional[str],
        flaws: List[str],
        game_over: bool = False,
        result: Optional[str] = None,
        focus_flaw: Optional[str] = None,
        eased: bool = False,
        fen: Optional[str] = None,
    ) -> str:
        """
        Produce a single transmission string. Uses the OpenAI SDK when
        available; otherwise the deterministic offline generator.
        """
        if not self.live:
            return _fallback_transmission(
                moved_asset, captured_asset, flaws, game_over, result, focus_flaw
            )

        # Build the user-context describing the latest field event.
        event_lines = []
        if moved_asset:
            event_lines.append(f"Commander moved a {moved_asset}.")
        if captured_asset:
            event_lines.append(f"It captured an enemy {captured_asset}.")
        if flaws:
            titles = ", ".join(FLAW_COACHING[f]["title"] for f in flaws if f in FLAW_COACHING)
            event_lines.append(f"Detected structural flaw(s): {titles}.")
        if game_over:
            event_lines.append(f"The engagement has ENDED. Result for the commander: {result}.")
        if fen:
            event_lines.append(f"(Internal board state, do not quote: {fen})")
        user_context = "\n".join(event_lines) or "Commander made a quiet developing move."

        try:  # pragma: no cover - network call
            resp = self._client.chat.completions.create(
                model=self.model,
                temperature=0.8,
                max_tokens=180,
                messages=[
                    {
                        "role": "system",
                        "content": _system_prompt(level_briefing, focus_flaw, eased),
                    },
                    {"role": "user", "content": user_context},
                ],
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            # Any SDK/network failure degrades gracefully to offline mode.
            return _fallback_transmission(
                moved_asset, captured_asset, flaws, game_over, result, focus_flaw
            )
