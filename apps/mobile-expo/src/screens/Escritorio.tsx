import React, { useState } from "react";
import { Button, Text, View } from "react-native";
import { api } from "../api/client";

/* Tab Escritorio: handoff al RustDesk Server propio (Fase 3 levanta hbbs/hbbr).
   Gestos tap=click drag=move pinch=scroll se cablean al viewer en Fase 3. */
export function Escritorio({ base, jwt }: { base: string; jwt: string }) {
  const [info, setInfo] = useState("");
  const load = async () => {
    const r = await api(base, jwt).rustdesk();
    setInfo(`${r.device_id} ${r.hbbs} ${r.hbbr}`);
  };
  return (
    <View>
      <Text>Control PC tipo RustDesk</Text>
      <Button title="Ver datos de conexion" onPress={load} />
      <Text>{info}</Text>
    </View>
  );
}
