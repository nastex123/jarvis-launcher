# Documentación técnica - J.A.R.V.I.S. Launcher

Fuente principal de documentación técnica y operativa para desarrolladores.
La documentación de usuario (qué es y cómo usarlo) vive en el
[README.md raíz](../README.md).

## Índice

| Documento | Contenido |
|-----------|-----------|
| [Arquitectura.md](./Arquitectura.md) | Componentes, módulos, responsabilidades, flujo de información, operaciones, TODOs y deuda técnica |
| [ADR-001-quitar-qgraphicseffect.md](./ADR-001-quitar-qgraphicseffect.md) | Decisión: eliminar `QGraphicsEffect` y pintar efectos manualmente (v1.2.0) |
| [ADR-002-resolucion-apps-por-nombre.md](./ADR-002-resolucion-apps-por-nombre.md) | Decisión: resolución de rutas de apps por nombre (v1.2.0) |
| [ADR-003-comando-global-jarvis.md](./ADR-003-comando-global-jarvis.md) | Decisión: comando global `jarvis` para lanzar la app desde CMD/PowerShell (v1.3.0) |
| [ADR-012-linux-port.md](./ADR-012-linux-port.md) | Decisión: port dual Windows+Linux + `install.py` (v2.0.3) |
| [ADR-013-motor-agentico-local.md](./ADR-013-motor-agentico-local.md) | Decisión: asistente IA local con Ollama `qwen2.5-coder:7b` (v3.0.0, Fase 1) |
| [ADR-014-politica-confirmacion.md](./ADR-014-politica-confirmacion.md) | Decisión: confirmar-todo + lista negra de shell (seguridad del agente) |
| [ADR-015-frontend-nextjs-pixi-tauri.md](./ADR-015-frontend-nextjs-pixi-tauri.md) | Decisión: Frontend Next.js 16, PixiJS v8, Esfera/Vórtice ASCII 3D, Doble Motor (Ollama + OpenCode) y Tauri v2 |
| [ESPEC-agente-fase1.md](./ESPEC-agente-fase1.md) | Especificación normativa Fase 1: tools, loop, system prompt, UX, settings, log, casos borde |
| [PLAN-fases.md](./PLAN-fases.md) | Roadmap Fases 1–4 (chat+sistema, visión, web, voz) |
| [TEST-agente.md](./TEST-agente.md) | Plan de pruebas del agente: suites A–D + checklist manual |

## Convenciones

- Tonos: formal, técnico y profesional en todos los `.md` de producción.
- Marcas de tiempo en zona horaria `America/Bogota`.
- Los ADRs se numeran de forma secuencial y no se modifican silenciosamente;
  si una decisión deja de ser válida, se registra un ADR nuevo o se actualiza
  su estado con justificación.
- Las decisiones arquitectónicas importantes SIEMPRE se documentan como ADR.