"use client";

import { useMemo } from "react";
import { Chessboard } from "react-chessboard";
import { Chess } from "chess.js";

/**
 * TacticalBoard
 * -------------
 * Thin wrapper around react-chessboard. It owns no game state of its own —
 * the parent War Room holds the authoritative FEN (mirrored from the backend
 * engine). This component only:
 *   1. Renders the current FEN.
 *   2. Validates a drag/drop locally with chess.js for instant UX feedback.
 *   3. Bubbles the attempted move up as UCI for the backend to adjudicate.
 *
 * The backend remains the source of truth; local validation just prevents
 * obviously-illegal drops from round-tripping.
 */

export interface TacticalBoardProps {
  fen: string;
  disabled?: boolean;
  onAttemptMove: (uci: string) => void;
}

export default function TacticalBoard({
  fen,
  disabled = false,
  onAttemptMove,
}: TacticalBoardProps) {
  // A fresh validator per render keyed on FEN.
  const validator = useMemo(() => {
    try {
      return new Chess(fen);
    } catch {
      return new Chess();
    }
  }, [fen]);

  function handleDrop(sourceSquare: string, targetSquare: string): boolean {
    if (disabled) return false;

    // Promotions auto-elevate Infantry to a Strike Commander (queen).
    const uci = `${sourceSquare}${targetSquare}`;

    // Local legality probe — does not mutate authoritative state.
    const probe = new Chess(validator.fen());
    let legal = false;
    try {
      const result = probe.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: "q",
      });
      legal = result !== null;
    } catch {
      legal = false;
    }

    if (!legal) return false;

    // Append promotion suffix when a pawn reaches the last rank.
    const movingPiece = validator.get(sourceSquare as any);
    const reachesLastRank =
      movingPiece?.type === "p" &&
      (targetSquare.endsWith("8") || targetSquare.endsWith("1"));
    onAttemptMove(reachesLastRank ? `${uci}q` : uci);

    // Return true so the board animates; the parent will reconcile with the
    // backend FEN on the next response.
    return true;
  }

  return (
    <div className="rounded-lg border border-warroom-border bg-warroom-panel p-3 shadow-[0_0_40px_rgba(94,243,140,0.08)]">
      <Chessboard
        position={fen}
        onPieceDrop={handleDrop}
        arePiecesDraggable={!disabled}
        animationDuration={200}
        customBoardStyle={{
          borderRadius: "6px",
          boxShadow: "inset 0 0 24px rgba(0,0,0,0.6)",
        }}
        customDarkSquareStyle={{ backgroundColor: "#2e3b27" }}
        customLightSquareStyle={{ backgroundColor: "#7d8b78" }}
        boardWidth={520}
      />
    </div>
  );
}
