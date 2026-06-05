import React, { useEffect, useState } from "react";
import { View, StyleSheet } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import "react-native-gesture-handler";

import { api, Faction, Scenario } from "./src/api";
import FactionScreen from "./src/screens/FactionScreen";
import AcademyScreen from "./src/screens/AcademyScreen";
import WarRoomScreen from "./src/screens/WarRoomScreen";

type Screen = "faction" | "academy" | "war";

// A stable per-install id. In production, replace with real auth (Supabase).
function makeUserId(): string {
  return `cmdr_${Math.random().toString(36).slice(2, 10)}`;
}

export default function App() {
  const [userId] = useState(makeUserId);
  const [screen, setScreen] = useState<Screen>("faction");
  const [factions, setFactions] = useState<Faction[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [faction, setFaction] = useState<Faction | null>(null);
  const [academy, setAcademy] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const [fc, sc] = await Promise.all([api.factions(), api.scenarios()]);
        setFactions(fc.factions);
        setScenarios(sc.scenarios);
      } catch {
        /* backend offline — screens show their loading/empty states */
      }
    })();
  }, []);

  async function selectFaction(id: string) {
    setSelectedId(id);
    setFaction(factions.find((f) => f.id === id) ?? null);
  }

  async function confirmFaction() {
    if (!selectedId) return;
    try {
      await api.setFaction(userId, selectedId);
      const ac = await api.academy(userId);
      setAcademy(ac);
    } catch {
      /* non-fatal */
    }
    setScreen("academy");
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <SafeAreaView style={s.root} edges={["top", "bottom"]}>
          <StatusBar style="light" />
          <View style={s.root}>
            {screen === "faction" && (
              <FactionScreen
                factions={factions}
                selectedId={selectedId}
                onSelect={selectFaction}
                onContinue={confirmFaction}
              />
            )}
            {screen === "academy" && (
              <AcademyScreen
                data={academy}
                accent={faction?.colors.accent}
                onContinue={() => setScreen("war")}
              />
            )}
            {screen === "war" && (
              <WarRoomScreen
                userId={userId}
                faction={faction}
                scenarios={scenarios}
                onOpenAcademy={() => setScreen("academy")}
              />
            )}
          </View>
        </SafeAreaView>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#0a0e0a" },
});
