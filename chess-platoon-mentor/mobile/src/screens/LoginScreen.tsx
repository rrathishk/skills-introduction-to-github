import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { api, AuthUser } from "../api";

/**
 * Optional login/sign-up. Logging in ties progress to the account so it
 * follows the player across devices. "Continue as guest" skips it (progress
 * stays local to this install).
 */
export default function LoginScreen({
  onAuthed,
  onGuest,
}: {
  onAuthed: (user: AuthUser) => void;
  onGuest: () => void;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const user =
        mode === "login"
          ? await api.login(email.trim(), password)
          : await api.register(email.trim(), password);
      onAuthed(user);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={s.root}>
      <Text style={s.title}>◆ COMMAND ACCESS</Text>
      <Text style={s.sub}>Log in so your progress follows you across devices.</Text>

      <View style={s.tabs}>
        {(["login", "register"] as const).map((m) => (
          <TouchableOpacity key={m} onPress={() => setMode(m)}>
            <Text style={[s.tab, mode === m && s.tabActive]}>
              {m === "login" ? "Log in" : "Sign up"}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <TextInput
        style={s.input}
        placeholder="email"
        placeholderTextColor="#5a6657"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={s.input}
        placeholder="password (min 8 chars)"
        placeholderTextColor="#5a6657"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />
      {error && <Text style={s.error}>{error}</Text>}

      <TouchableOpacity style={s.primary} onPress={submit} disabled={busy}>
        {busy ? (
          <ActivityIndicator color="#5ef38c" />
        ) : (
          <Text style={s.primaryText}>
            {mode === "login" ? "LOG IN" : "CREATE ACCOUNT"}
          </Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity onPress={onGuest}>
        <Text style={s.guest}>Continue as guest →</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#0a0e0a", padding: 20, justifyContent: "center" },
  title: { color: "#5ef38c", fontSize: 22, fontWeight: "700", letterSpacing: 3, marginBottom: 6 },
  sub: { color: "#7d8b78", fontSize: 13, marginBottom: 24 },
  tabs: { flexDirection: "row", gap: 16, marginBottom: 12 },
  tab: { color: "#7d8b78", fontSize: 14, paddingBottom: 4 },
  tabActive: { color: "#5ef38c", borderBottomWidth: 1, borderBottomColor: "#5ef38c" },
  input: {
    borderWidth: 1,
    borderColor: "#1f2b1a",
    backgroundColor: "#11160f",
    borderRadius: 8,
    padding: 12,
    color: "#cdeccf",
    marginBottom: 10,
  },
  error: { color: "#ff5b5b", fontSize: 12, marginBottom: 8 },
  primary: {
    backgroundColor: "#1f2b1a",
    borderRadius: 8,
    padding: 16,
    alignItems: "center",
    marginTop: 6,
  },
  primaryText: { color: "#5ef38c", fontWeight: "700", letterSpacing: 2 },
  guest: { color: "#7d8b78", textAlign: "center", marginTop: 18, fontSize: 13 },
});
