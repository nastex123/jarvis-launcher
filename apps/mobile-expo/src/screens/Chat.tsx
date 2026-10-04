import React, { useState } from "react";
import { Button, Text, TextInput, View } from "react-native";
import { api } from "../api/client";
import { HudLite } from "../ui/HudLite";

/* Tab Chat: streaming via POST /api/chat/turn (WS en Fase 3). */
export function Chat({ base, jwt }: { base: string; jwt: string }) {
  const [text, setText] = useState("");
  const [reply, setReply] = useState("");
  const [thinking, setThinking] = useState(false);
  const send = async () => {
    setThinking(true);
    try {
      const r = await api(base, jwt).chatTurn(text);
      setReply(String(r.reply ?? ""));
    } catch (e) {
      setReply(`[ERROR] ${String(e)}`);
    } finally {
      setThinking(false);
    }
  };
  return (
    <View>
      <HudLite thinking={thinking} />
      <TextInput value={text} onChangeText={setText} placeholder="Habla con Jarvis" accessibilityLabel="Mensaje a Jarvis" />
      <Button title="Enviar" onPress={send} />
      <Text>{reply}</Text>
    </View>
  );
}
