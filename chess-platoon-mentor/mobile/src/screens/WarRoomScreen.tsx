import React, { useEffect, useRef, useState } from "react";
import {
  ScrollView,
  Text,
  TouchableOpacity,
  View,
  StyleSheet,
  ActivityIndicator,
  useWindowDimensions,
} from "react-native";
import Chessboard, { ChessboardRef } from "react-native-chessboard";
import { api, Faction, Scenario } from "../api";

interface Msg {
  kind: "agent" | "system" | "flaw" | "result";
  text: string;
}

/**
 * The mobile War Room: board on top, scrolling comms feed below, mission
 * selector, and the live dossier. Talks to the same backend as the web app.
 */
export default function WarRoomScreen({
  userId,
  faction,
  scenarios,
  onOpenAcademy,
}: {
  userId: string;
  faction: Faction | null;
  scenarios: Scenario[];
  onOpenAcademy: () => void;
}) {
  const { width } = useWindowDimensions();
  const boardSize = Math.min(width - 24, 380);
  const boardRef = useRef<ChessboardRef>(null);

  const [fen, setFen] = useState<string | undefined>(undefined);
  const [level, setLevel] = useState(1);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [pending, setPending] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [progress, setProgress] = useState<any>(null);

  const accent = faction?.colors.accent ?? "#5ef38c";

  useEffect(() => {
    startGame(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refreshProgress() {
    try {
      setProgress(await api.progress(userId));
    } catch {
      /* non-fatal */
    }
  }

  async function startGame(lvl: number) {
    setPending(true);
    setGameOver(false);
    try {
      const data = await api.newGame(userId, lvl, faction?.id);
      setLevel(data.level);
      setFen(data.fen);
      setMessages([
        { kind: "system", text: `MISSION ${data.level} — ${data.codename} [${data.difficulty}]\n${data.objective}` },
        { kind: "agent", text: data.transmission },
      ]);
      await refreshProgress();
    } catch (e: any) {
      setMessages([{ kind: "system", text: `LINK FAILURE: ${e.message}` }]);
    } finally {
      setPending(false);
    }
  }

  async function onMove(state: { move?: { from: string; to: string } }) {
    const mv = state?.move;
    if (!mv || pending || gameOver) return;
    const uci = `${mv.from}${mv.to}`;
    setPending(true);
    try {
      const data = await api.move(userId, uci);
      setFen(data.fen);
      const next: Msg[] = [];
      if (data.flaws?.length) {
        next.push({ kind: "flaw", text: `FLAW: ${data.flaws.join(", ").replace(/_/g, " ")}` });
      }
      next.push({ kind: "agent", text: data.transmission });
      if (data.game_over) {
        setGameOver(true);
        next.push({
          kind: "result",
          text:
            data.result === "win"
              ? "VICTORY — objective secured."
              : data.result === "loss"
              ? "DEFEAT — Commander-in-Chief lost."
              : "DRAW.",
        });
      }
      setMessages((prev) => [...prev, ...next]);
      await refreshProgress();
    } catch (e: any) {
      setMessages((prev) => [...prev, { kind: "system", text: `Move rejected: ${e.message}` }]);
    } finally {
      setPending(false);
    }
  }

  return (
    <View style={s.root}>
      {/* Header */}
      <View style={s.header}>
        <Text style={[s.title, { color: accent }]} numberOfLines={1}>
          {faction ? `${faction.flag} ${faction.general}` : "◆ COMMAND CENTER"}
        </Text>
        <TouchableOpacity onPress={onOpenAcademy} style={s.academyBtn}>
          <Text style={s.academyText}>📖</Text>
        </TouchableOpacity>
      </View>

      {/* Board */}
      <View style={[s.boardWrap, { borderColor: accent }]}>
        {fen ? (
          <Chessboard
            ref={boardRef}
            fen={fen}
            boardSize={boardSize}
            onMove={onMove}
            colors={{ black: faction?.colors.dark, white: faction?.colors.light }}
          />
        ) : (
          <ActivityIndicator color={accent} />
        )}
      </View>

      {/* Mission selector */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.missions}>
        {scenarios.map((sc) => (
          <TouchableOpacity
            key={sc.level}
            onPress={() => startGame(sc.level)}
            style={[
              s.missionBtn,
              { borderColor: level === sc.level ? accent : "#1f2b1a" },
            ]}
          >
            <Text style={[s.missionText, { color: level === sc.level ? accent : "#7d8b78" }]}>
              L{sc.level} · {sc.codename}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Comms feed */}
      <ScrollView style={s.feed} contentContainerStyle={{ padding: 10 }}>
        {messages.map((m, i) => (
          <View
            key={i}
            style={[
              s.msg,
              m.kind === "flaw" && { borderColor: "#ff5b5b", backgroundColor: "#ff5b5b1a" },
              m.kind === "result" && { borderColor: "#ffb347", backgroundColor: "#ffb3471a" },
              m.kind === "agent" && { borderColor: `${accent}66` },
            ]}
          >
            <Text style={s.msgLabel}>
              {m.kind === "agent" ? "VOSS // TRANSMISSION" : m.kind.toUpperCase()}
            </Text>
            <Text style={s.msgText}>{m.text}</Text>
          </View>
        ))}
        {pending && <ActivityIndicator color={accent} style={{ marginTop: 8 }} />}
      </ScrollView>

      {/* Dossier */}
      {progress && (
        <View style={s.dossier}>
          <Text style={s.stat}>Elo <Text style={{ color: accent }}>{progress.elo}</Text></Text>
          <Text style={s.stat}>
            W/L/D <Text style={{ color: accent }}>{progress.wins}/{progress.losses}/{progress.draws}</Text>
          </Text>
          <Text style={s.stat}>
            Flaw{" "}
            <Text style={{ color: progress.dominant_flaw ? "#ff5b5b" : accent }}>
              {progress.dominant_flaw ? progress.dominant_flaw.replace(/_/g, " ") : "none"}
            </Text>
          </Text>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#0a0e0a" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 12,
    paddingTop: 8,
  },
  title: { fontSize: 14, fontWeight: "700", letterSpacing: 1, flex: 1 },
  academyBtn: { padding: 8 },
  academyText: { fontSize: 18 },
  boardWrap: {
    alignItems: "center",
    justifyContent: "center",
    margin: 12,
    borderWidth: 1,
    borderRadius: 8,
    padding: 6,
    minHeight: 120,
  },
  missions: { maxHeight: 44, paddingHorizontal: 8 },
  missionBtn: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    marginHorizontal: 4,
  },
  missionText: { fontSize: 11, fontWeight: "700" },
  feed: { flex: 1 },
  msg: {
    borderWidth: 1,
    borderColor: "#1f2b1a",
    backgroundColor: "#11160f",
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
  },
  msgLabel: { color: "#7d8b78", fontSize: 9, letterSpacing: 1, marginBottom: 3 },
  msgText: { color: "#cdeccf", fontSize: 13, lineHeight: 19 },
  dossier: {
    flexDirection: "row",
    justifyContent: "space-around",
    borderTopWidth: 1,
    borderTopColor: "#1f2b1a",
    paddingVertical: 10,
  },
  stat: { color: "#7d8b78", fontSize: 12 },
});
