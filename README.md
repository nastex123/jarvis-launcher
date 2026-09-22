# J.A.R.V.I.S. Launcher

Interfaz tipo JARVIS (Iron Man) que se ejecuta al iniciar Windows y permite lanzar conjuntos de aplicaciones segun el modo seleccionado: **Gaming**, **Trabajo** o **Estudio**.

## Caracteristicas

- **HUD Moderno Next.js 16 + PixiJS v8 + Tauri v2**: Fondo OLED negro puro (`#000000`), estética minimalista técnica anti-clichés de IA, renderizado acelerado por WebGL/WebGPU y empaquetado nativo de alto rendimiento.
- **Red Neuronal ASCII 3D y Morphing Continuo**: Esfera geodésica zen con 8 meridianos y 7 paralelos en reposo que transmuta suavemente en ~1.2s a un vórtice concéntrico de 14 anillos de tensores durante el razonamiento, con retorno fluido y continuo sin reinicios de canvas.
- **Lienzo 100% Responsivo y Recentrado Automático**: Canvas acoplado a `ResizeObserver` que recalcula su proyección matemática y recentra la esfera dinámicamente al ensanchar o reducir el panel de chat.
- **Logo J.A.R.V.I.S. SVG Estilizado**: Reactor Arc vectorial monocromático de triple anillo con animación reactiva al pensamiento y tipografía técnica monoespaciada en la esquina superior derecha.
- **Control Total de PC y Ejecución de Terminal**: Apertura de aplicaciones (`abre <app>`), ejecución de comandos de consola (`ejecuta: <cmd>`), conmutación nativa de aplicaciones por modo en el dock y captura detallada de stdout/stderr.
- **Política de Seguridad con Confirmación Destructiva**: Detección estricta de comandos críticos (`rm`, `kill`, `pkill`, `dd`, etc.) que exige confirmación explícita del usuario mediante un modal interactivo antes de proceder.
- **Doble Motor de Inferencia (Ollama + Agente Autónomo OpenCode)**: Conexión streaming directa con modelo local `qwen2.5-coder:7b`, selector manual en cabecera `[motor: ollama / opencode]` y conmutación automática de contingencia hacia OpenCode si el LLM local no responde.
- **Blindaje Estricto de Cero Emojis**: Filtrado en 3 capas (prompting inmutable, sanitizador Unicode `stripEmojis` en stream y purificación directa en renderizado) que elimina por completo cualquier emoji en ambos motores.
- **Estructuración HUD y Acordeón de Telemetría**: Respuestas técnicas organizadas con títulos nítidos, viñetas espaciadas (`—`), tablas comparativas Paper/Terminal con botón de copiado y logs de consola/búsqueda web aislados en un acordeón desplegable.
- **Búsqueda Web en Tiempo Real**: Búsqueda en vivo integrada con toggle `[web: on/off]` que inyecta automáticamente contexto web y citas en Markdown a las respuestas.
- **Historial de Conversaciones Persistente**: Drawer lateral de sesiones con almacenamiento local en `localStorage` y creación rápida de nuevas conversaciones.
- **Chatbot Redimensionable**: Manija táctil vertical para ajustar libremente el ancho del panel entre 300px y 850px mediante arrastre del mouse.
- **Panel lateral de noticias RSS**: posicion izquierda/derecha, ancho
  redimensionable arrastrando el borde, actualizacion automatica cada 10
  minutos y clic en una noticia para abrirla en tu navegador
- **Fuentes de noticias**: 10 presets (Google News, BBC Mundo, El Tiempo, El
  Espectador, CNN en Espanol, DW, RT, Hacker News, The Verge, Wired) o pega tu
  propia URL RSS/Atom (se valida antes de conectar)
- **Temas de color**: 8 paletas (obsidiana, nocturno, crimson, esmeralda,
  matriz, violeta, ambar, luz, nieve) selectables desde la rueda de ajustes ⚙
- **Siempre al frente + bandeja del sistema**: el launcher queda encima de todo
  y ocupa toda la pantalla; al pulsar ✕ se oculta a la bandeja y sigue activo
  (doble clic en el icono para volverlo a abrir)
- **Atajo global `Ctrl+Shift+Espacio`**: convoca u oculta el launcher desde
  cualquier aplicación
- **Saludo dinámico**: "Buenos días/tardes/noches" según la hora, con adjetivo
  profesional rotativo (Desarrollador, Ingeniero, Arquitecto, ...) o con tu
  **nombre real** si vinculas tu cuenta de GitHub
- **Vinculación de cuenta GitHub**: el launcher detecta tu cuenta automática­mente
  (si tienes el CLI `gh` autenticado) o puedes vincularla manualmente desde
  los ajustes para que el saludo use tu nombre real
- **Panel de control estructurado**: lista por secciones (Apariencia,
  Comportamiento, Noticias, Cuenta de GitHub, Próximamente) con auto-inicio y
  bandeja configurables
- **Lector de noticias con mini navegador**: haz clic en cualquier noticia del
  panel y se abre a pantalla completa un **navegador embebido con el artículo
  real** (imágenes, videos y todo el contenido del sitio). Cambia de artículo
  **al instante** (el resumen aparece de inmediato y la página completa salta
  cuando termina de cargar), botón **⟳** para recargar y **ABRIR ORIGINAL ↗**
  para verlo en tu navegador habitual.
  *El panel lateral se mantiene limpio: fuente, hora y título de cada noticia
  (sin textos apilados); lo completo se lee en el lector.*
- **Noticias rápidas**: las fuentes se descargan en paralelo (solo esperas a
  la más lenta) y la primera carga del panel llega en segundos

## Requisitos y Pila Tecnológica

### Entorno General:
- Windows 10/11 **o** Linux (Ubuntu/Debian/Fedora/Arch, GNOME/KDE, X11/Wayland)
- Python 3.10+ (para backend tradicional PyQt6 y scripts de sistema)
- Node.js 18+ y npm (para el frontend moderno Next.js 16 + PixiJS v8)
- Rust y Cargo (opcional, para compilar el binario nativo de escritorio Tauri v2)
- [Ollama](https://ollama.com) con modelo `qwen2.5-coder:7b` (para el asistente agéntico local)

---

## Instalación y Puesta en Marcha Rápida

### 🚀 Opción A: Frontend Moderno HUD (Next.js 15 + PixiJS v8 + Ollama) [RECOMENDADO]

1. **Asegurar el motor Ollama en ejecución**:
   ```bash
   # Descarga y arranca el modelo local (ejecutar en terminal o servicio background)
   ollama run qwen2.5-coder:7b
   ```

2. **Instalar dependencias del frontend**:
   ```bash
   cd src-web
   npm install
   ```

3. **Iniciar en modo desarrollo (Navegador local)**:
   ```bash
   npm run dev
   ```
   Abre [http://localhost:3000](http://localhost:3000) (o el puerto asignado) en tu navegador para interactuar con la esfera ASCII 3D, el chatbot y el dock de modos.

4. **Compilar para producción (Exportación estática)**:
   ```bash
   npm run build
   ```
   Genera los artefactos HTML/JS optimizados en `src-web/out/`.

5. **Lanzar como aplicación nativa de escritorio con Tauri v2** (Requiere Rust):
   ```bash
   cd src-web
   npm run tauri dev
   ```

---

### 🐍 Opción B: Launcher Python / PyQt6 Clásico

1. **Instalación de dependencias Python**:
   ```bash
   pip install -r requirements.txt   # instala PyQt6 y PyQt6-WebEngine
   ```

2. **Instalador guiado en Linux (crea venv, comando jarvis y autostart)**:
   ```bash
   python3 install.py                # instala todo (venv + comando jarvis + .desktop + autostart)
   python3 install.py --run          # instala (si falta) y lanza el launcher
   python3 install.py --check-only   # diagnostico del entorno
   python3 install.py --uninstall    # revierte bin/.desktop/autostart
   ```

   En Ubuntu/Debian puede requerir librerías del sistema para Qt6:
   ```bash
   sudo apt install -y python3-venv python3-pip libgl1 libxkbcommon-x11-0 libxcb-cursor0 libnss3 libasound2t64 libnotify-bin
   ```

Para detalles de arquitectura, decisiones técnicas (ADRs) y especificaciones normativas, consulta [`docs/`](./docs/).

## Comando global `jarvis` (Entorno clásico Windows)

Instala el comando `jarvis` en el PATH de usuario para abrir el launcher
desde **cualquier** CMD o PowerShell:

```bash
install_jarvis_cmd.bat
```

Despues de instalarlo (y abrir una ventana nueva), escribe `jarvis` desde
cualquier directorio:

```powershell
jarvis
```

Para desinstalarlo:

```bash
install_jarvis_cmd.bat --uninstall
```

El comando usa `pythonw.exe` (abre la GUI sin ventana de consola y devuelve
el prompt al instante).

## Configuracion de modos

Edita `config.json` para personalizar los modos y las aplicaciones que se abren en cada uno:

```json
{
    "modes": {
        "gaming": {
            "name": "Gaming",
            "icon": "\U0001f3ae",
            "color": "#FF2D55",
            "description": "Listo para la accion",
            "apps": [
                {
                    "name": "Steam",
                    "command": "C:\\Program Files (x86)\\Steam\\steam.exe"
                },
                {
                    "name": "Discord",
                    "command": "C:\\Users\\TU_USUARIO\\AppData\\Local\\Discord\\Update.exe",
                    "args": "--processStart Discord.exe"
                }
            ]
        }
    }
}
```

### Campos de cada app

| Campo | Tipo | Requerido | Descripcion |
|-------|------|-----------|-------------|
| `name` | string | Si | Nombre que se muestra en el log |
| `command` | string | Si | Ruta al ejecutable, URL o nombre corto de la app |
| `args` | string | No | Argumentos adicionales |

### Resolucion de apps por nombre

Si `command` no es una ruta existente ni una URL, el launcher busca la app
automaticamente en (en orden):

1. Variable de entorno `PATH`
2. Accesos directos del menu de inicio (usuario y sistema)
3. Registro de Windows `App Paths`

Esto permite usar nombres cortos como `"Discord"` o `"Spotify"` sin
depender de rutas fijas que cambian en cada instalacion.

### Como encontrar la ruta de una app

1. Busca el acceso directo en el Menu Inicio
2. Click derecho -> Propiedades
3. Copia el campo "Destino"

## Auto-inicio en Windows

Tienes dos formas:

### Opcion 1: Desde la interfaz
Haz click en el boton **"Configurar auto-inicio"** en la esquina superior derecha.

### Opcion 2: Script manual
Ejecuta como Administrador:
```bash
install_startup.bat
```

Para desactivar, ejecuta el mismo script nuevamente.

## Atajos de teclado

| Tecla | Accion |
|-------|--------|
| `Ctrl + Shift + Espacio` | Convocar/ocultar el launcher (desde cualquier app) |
| `Escape` | Ocultar el launcher |
| `F11` | Alternar pantalla completa |

## Noticias y temas

### Rueda de ajustes ⚙

Haz clic en la rueda **⚙** (esquina superior derecha) para abrir el panel de
control, organizado en secciones:

- **1 · Apariencia**: tema de color (swatches con vista previa).
- **2 · Comportamiento**: atajo global, bandeja del sistema y auto-inicio.
- **3 · Panel de noticias**: activar/desactivar, posición y fuente conectada.
- **4 · Cuenta de GitHub**: vincula tu cuenta para que el saludo use tu
  nombre real.
- **5 · Próximamente**: funciones en desarrollo (editor de modos, paletas,
  lector de noticias).

### Conectar una fuente de noticias

1. Abre la rueda ⚙ → **Fuentes**.
2. Elige un preset (Google News, BBC Mundo, El Tiempo, ...) y pulsa **USAR**,
   o pega una **URL RSS/Atom** propia y pulsa **CONECTAR** (se valida que el
   feed sea legible antes de conectar).
3. El panel mostrará las noticias con su antigüedad ("hace 5 min").

### Redimensionar el panel

Arrastra el **borde interior** del panel (cursor ⇔) para cambiar su ancho
(280–560 px). La posición y el ancho se guardan para la próxima sesión.

### Abrir una noticia

Haz clic en cualquier noticia del panel: se abre el **lector de noticias** a
pantalla completa dentro del launcher.

- A la **izquierda** tienes la lista de noticias: haz clic (o usa `←` / `→`)
  para cambiar de artículo al instante.
- A la **derecha** se carga la **noticia completa en un mini navegador
  embebido** (imágenes, videos, todo el sitio). Usa **⟳** para recargar.
- Usa **`Escape`** (o el botón **← VOLVER**) para regresar al launcher.
- Para abrir el artículo en tu navegador habitual, pulsa **ABRIR ORIGINAL ↗**.

> Sin `PyQt6-WebEngine` instalado, el lector muestra el resumen del artículo
> con tipografía de lectura larga en lugar del mini navegador (mismo flujo).

> Las noticias se actualizan automáticamente cada 10 minutos. Si el panel
> queda "Sin noticias disponibles", verifica tu conexión o cambia de fuente
> desde el conector.

## Estructura del proyecto

```
jarvis-launcher/
├── main.py              # Entry point
├── config.json          # Configuracion de modos Windows (edita aqui en Windows)
├── config.linux.example.json  # Plantilla de modos Linux (no editar)
├── config.linux.json    # Configuracion de modos Linux (generado por install.py)
├── settings.json        # Preferencias de interfaz (tema/noticias, generado automaticamente)
├── state.json           # Estado/historial (generado automaticamente)
├── requirements.txt     # Dependencias Python
├── install.py           # Instalador + inicializador Linux (venv, jarvis, .desktop, autostart)
├── install_startup.bat  # Instalar/desinstalar auto-inicio (Windows)
├── install_jarvis_cmd.bat  # Instalar/desinstalar comando global `jarvis` (Windows)
├── core/
│   ├── config.py        # Gestor de configuracion de modos (dual: config.linux.json)
│   ├── platform.py      # Helpers de plataforma (autostart, .desktop, distro)
│   ├── settings.py      # Preferencias de interfaz (tema, noticias, bandeja, GitHub)
│   ├── themes.py        # Paletas y gestor de temas de color
│   ├── news.py          # Servicio de noticias RSS/Atom (stdlib)
│   ├── hotkey.py        # Atajo Ctrl+Shift+Espacio (RegisterHotKey en Win, QShortcut en Linux)
│   ├── tray.py          # Bandeja del sistema
│   ├── greeting.py      # Saludo dinamico por hora + adjetivo rotativo
│   ├── github_link.py   # Vinculacion de cuenta GitHub (gh / API publica)
│   ├── launcher.py      # Motor de apertura de apps (PATH/.lnk/App Paths/.desktop)
│   ├── state.py         # Historial de modos recientes
│   └── notifier.py      # Notificaciones nativas (toast Win / notify-send Linux)
├── ui/
│   ├── jarvis_ui.py     # Ventana principal con efectos HUD
│   ├── mode_card.py     # Tarjetas workspace de modo (monograma)
│   ├── news_panel.py    # Panel lateral de noticias (limpio, sin previews)
│   ├── news_reader.py   # Lector fullscreen: mini navegador embebido + lista
│   └── settings_dialog.py  # Panel de control estructurado + GitHub/Connect
└── assets/
    ├── startup.vbs      # Script de auto-inicio Windows
    ├── jarvis.cmd       # Origen del comando global `jarvis` (Windows)
    └── jarvis-launcher.desktop.template  # Plantilla .desktop Linux (usa install.py)
└── docs/                # Documentacion tecnica (Arquitectura + ADRs)
```

Nota: `docs/` es la fuente principal de documentación técnica para
desarrolladores; el README está orientado a usuario final.
