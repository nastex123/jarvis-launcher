# ROADMAP Movil — Jarvis telefono + control PC

> [!NOTE] Rama `chore/scalable-base`. Alcance Full Jarvis + Escritorio, Expo RN, HUD Lite, Tailwind+shadcn, RustDesk Server propio.

## Fase 0 Desacople — hecha en diseno
* Contrato `docs/ESPEC-remoto.md` v1. Gateway opcion 1 aprobada.

## Fase 1 Gateway MVP — en curso
* `apps/gateway/` FastAPI: health, pairing QR, modes/run idempotente, chat/turn, decide, rustdesk handoff, WS stream.
* Verificacion: `compileall` + `pytest tests/test_gateway_auth.py` + arranque `uvicorn` local.

## Fase 2 Expo base — siguiente
* Tabs Chat/Modos/Escritorio/Aprobar, NativeWind Tailwind, Motion 150-300ms, PixiJS Lite 30fps, `prefers-reduced-motion`, tactil 44px, AA.
* Reutiliza contratos TS de ESPEC-remoto. Stack Next.js+TS en web, Expo en movil.

## Fase 3 RustDesk propio — despues
* `docker-compose.rustdesk.yml` hbbs/hbbr, `device_id=jarvis-pc`, deep-link desde Expo, Tailscale fallback.
* DoD video LAN <200ms, reconexion auto, kill-switch.

## Fase 4 Hardening
* E2E, PIN/biometrico, audit, EAS Build APK/IPA, docs sync final + commit Conventional.

DoD global: codigo corre + 0 errores log, docs + TODO sync, callouts en .md, commit solo fin indicado, cierre con siguiente paso.
