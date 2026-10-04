# Jarvis Mobile Expo (Base Fase 3)

> [!NOTE] Estructura elegida 4 tabs base: Chat / Modos / Escritorio / Aprobar. Animacion HUD Lite adaptativo. Estilo Tailwind via NativeWind + shadcn movil. Responsive 360+ y a11y tactil 44px.

## Stack

* Base movil: Expo RN + TS strict. Web desktop sigue Next.js + TS.
* UI: NativeWind Tailwind + shadcn movil, dark OLED `#000000`.
* Anim: Motion 150-300ms + `HudLite.tsx` 30fps con reduced-motion. PixiJS completo solo desktop `src-web`; en movil expo-gl/skia opcional Fase 3.
* Contrato: `src/api/client.ts` tipado contra `docs/ESPEC-remoto.md` v1.

## Correr

```bash
cd apps/mobile-expo
npm install
npm run typecheck
npx expo start
```

> [!WARNING] Configura `base` LAN del gateway y `jwt` de `/api/pairing/exchange`. Nunca exponer sin Tailscale/TLS.
