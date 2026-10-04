import React, { useState } from "react";
import { Button, Text, View } from "react-native";
import { api, type ModeInfo } from "../api/client";

/* Tab Modos: lista modos y ejecuta con idempotency_key unico. */
export function Modos({ base, jwt }: { base: string; jwt: string }) {
  const [modes, setModes] = useState<ModeInfo[]>([]);
  const [log, setLog] = useState("");
  const load = async () => setModes((await api(base, jwt).modes()).modes);
  const run = async (id: string) => {
    const key = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const r = await api(base, jwt).runMode(id, key);
    setLog(`OK ${r.launched.length} FAIL ${r.failed.length}`);
  };
  return (
    <View>
      <Button title="Cargar modos" onPress={load} />
      {modes.map((m) => (
        <View key={m.id}>
          <Text>{m.name}</Text>
          <Button title={`Ejecutar ${m.name}`} onPress={() => run(m.id)} />
        </View>
      ))}
      <Text>{log}</Text>
    </View>
  );
}
