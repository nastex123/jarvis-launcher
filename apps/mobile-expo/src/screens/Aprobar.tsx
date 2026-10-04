import React from "react";
import { Button, Text, View } from "react-native";
import { api, type ProposalCard } from "../api/client";

/* Tab Aprobar: espejo movil de ui/chat_panel.py. Rechazo auto 60s en gateway. */
export function Aprobar({ base, jwt, card }: { base: string; jwt: string; card: ProposalCard | null }) {
  if (!card) return <Text>Sin propuestas pendientes</Text>;
  const decide = (d: "approve" | "reject" | "edit") => api(base, jwt).decide(card.id, d, card.tool, card.args);
  return (
    <View>
      <Text>{card.summary}</Text>
      <Text>Riesgo: {card.risk}</Text>
      <Button title="Aprobar" onPress={() => decide("approve")} />
      <Button title="Rechazar" onPress={() => decide("reject")} />
    </View>
  );
}
