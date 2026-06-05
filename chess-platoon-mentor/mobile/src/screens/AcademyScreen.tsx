import React from "react";
import { ScrollView, Text, TouchableOpacity, View, StyleSheet } from "react-native";

/** The teaching screen — rewires how the player sees the board. */
export default function AcademyScreen({
  data,
  accent = "#5ef38c",
  onContinue,
}: {
  data: any;
  accent?: string;
  onContinue: () => void;
}) {
  if (!data) {
    return (
      <View style={[s.root, { padding: 16 }]}>
        <Text style={s.sub}>Loading doctrine…</Text>
      </View>
    );
  }

  return (
    <ScrollView style={s.root} contentContainerStyle={{ padding: 16 }}>
      <Text style={[s.title, { color: accent }]}>◆ THE ACADEMY</Text>
      <Text style={s.intro}>{data.intro}</Text>

      <Text style={s.section}>KNOW YOUR ASSETS</Text>
      {data.asset_doctrine?.map((c: any) => (
        <View key={c.key} style={s.card}>
          <Text style={[s.cardTitle, { color: accent }]}>
            {c.faction_name ?? c.asset} <Text style={s.piece}>({c.piece})</Text>
          </Text>
          <Text style={s.line}>
            <Text style={s.label}>Strength: </Text>
            {c.strength}
          </Text>
          <Text style={s.line}>
            <Text style={s.label}>Deploy: </Text>
            {c.deploy}
          </Text>
          <Text style={[s.shift, { color: accent }]}>{c.shift}</Text>
          <Text style={s.psych}>{c.psychology}</Text>
        </View>
      ))}

      <Text style={s.section}>THE PSYCHOLOGY OF COMMAND</Text>
      {data.strategic_doctrine?.map((d: any) => (
        <View key={d.key} style={s.card}>
          <Text style={[s.cardTitle, { color: accent }]}>{d.title}</Text>
          <Text style={s.line}>{d.lesson}</Text>
        </View>
      ))}

      <TouchableOpacity style={s.continue} onPress={onContinue}>
        <Text style={[s.continueText, { color: accent }]}>ENTER THE WAR ROOM →</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#0a0e0a" },
  title: { fontSize: 20, fontWeight: "700", letterSpacing: 3, marginBottom: 8 },
  intro: { color: "#cdeccf", fontSize: 13, lineHeight: 20, marginBottom: 16 },
  section: {
    color: "#7d8b78",
    fontSize: 11,
    letterSpacing: 3,
    marginTop: 8,
    marginBottom: 8,
  },
  card: {
    borderWidth: 1,
    borderColor: "#1f2b1a",
    backgroundColor: "#11160f",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
  },
  cardTitle: { fontSize: 14, fontWeight: "700" },
  piece: { color: "#7d8b78", fontSize: 11, fontWeight: "400" },
  line: { color: "#cdeccf", fontSize: 12, marginTop: 4, lineHeight: 18 },
  label: { color: "#7d8b78" },
  shift: { fontSize: 12, fontStyle: "italic", marginTop: 6 },
  psych: { color: "#7d8b78", fontSize: 11, marginTop: 2 },
  continue: {
    marginTop: 8,
    marginBottom: 24,
    backgroundColor: "#1f2b1a",
    borderRadius: 10,
    padding: 16,
    alignItems: "center",
  },
  continueText: { fontWeight: "700", letterSpacing: 2 },
});
