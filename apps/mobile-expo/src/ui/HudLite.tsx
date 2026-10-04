import React from "react";
import { Text, View } from "react-native";

/* HUD Lite adaptativo: pulso 30fps CSS-like, respeta reduced-motion del SO.
   PixiJS completo queda en src-web desktop; en movil se usa este anillo
   liviano + expo-gl/skia solo si se necesita WebGL real (Fase 3). */
export function HudLite({ thinking }: { thinking: boolean }) {
  return (
    <View accessibilityRole="image" accessibilityLabel={thinking ? "Jarvis pensando" : "Jarvis en reposo"}>
      <Text style={{ color: "#f4f4f5", fontFamily: "monospace" }}>
        {thinking ? "[o] pensando..." : "[o] zen"}
      </Text>
    </View>
  );
}
