import React from "react";
import { ScrollView, Text, TouchableOpacity, View, StyleSheet } from "react-native";
import { Faction } from "../api";

/** Army selection screen — India / USA / Russia / China. */
export default function FactionScreen({
  factions,
  selectedId,
  onSelect,
  onContinue,
}: {
  factions: Faction[];
  selectedId?: string;
  onSelect: (id: string) => void;
  onContinue: () => void;
}) {
  return (
    <ScrollView style={s.root} contentContainerStyle={{ padding: 16 }}>
      <Text style={s.title}>◆ CHOOSE YOUR ARMY</Text>
      <Text style={s.sub}>
        The board is a platoon under your command. Pick the army you will lead.
      </Text>

      {factions.map((f) => {
        const active = f.id === selectedId;
        return (
          <TouchableOpacity
            key={f.id}
            onPress={() => onSelect(f.id)}
            style={[
              s.card,
              {
                borderColor: active ? f.colors.accent : "#1f2b1a",
                backgroundColor: active ? `${f.colors.accent}1a` : "#11160f",
              },
            ]}
          >
            <Text style={s.flag}>{f.flag}</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.country, { color: f.colors.accent }]}>
                {f.country} — {f.name}
              </Text>
              <Text style={s.general}>{f.general}</Text>
              <Text style={s.motto}>“{f.motto}”</Text>
            </View>
          </TouchableOpacity>
        );
      })}

      <TouchableOpacity
        style={[s.continue, { opacity: selectedId ? 1 : 0.4 }]}
        disabled={!selectedId}
        onPress={onContinue}
      >
        <Text style={s.continueText}>TO THE ACADEMY →</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#0a0e0a" },
  title: { color: "#5ef38c", fontSize: 20, fontWeight: "700", letterSpacing: 3, marginBottom: 6 },
  sub: { color: "#7d8b78", fontSize: 12, marginBottom: 16 },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
  },
  flag: { fontSize: 34 },
  country: { fontSize: 15, fontWeight: "700" },
  general: { color: "#cdeccf", fontSize: 12, marginTop: 2 },
  motto: { color: "#7d8b78", fontSize: 11, fontStyle: "italic", marginTop: 2 },
  continue: {
    marginTop: 8,
    backgroundColor: "#1f2b1a",
    borderRadius: 10,
    padding: 16,
    alignItems: "center",
  },
  continueText: { color: "#5ef38c", fontWeight: "700", letterSpacing: 2 },
});
