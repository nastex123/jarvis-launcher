"""
ui/settings_dialog.py - Dialogo de ajustes del Jarvis Launcher (rueda).

Panel de control rediseñado como LISTA ESTRUCTURADA (modo workspace):
  1 · Apariencia ......... tema de color (swatches)
  2 · Comportamiento ..... atajo global, bandeja del sistema, auto-inicio
  3 · Noticias ........... activar, posicion, fuente RSS (presets / URL)
  4 · Cuenta de GitHub ... vinculacion con nombre real para el saludo
  5 · Próximamente ....... controles en desarrollo (editor de modos/paletas)
  6 · Asistente .......... IA local (Ollama): activar, URL, modelo, limites

Cada fila de la lista se compone de: etiqueta descriptiva a la izquierda y
control alineado a la derecha, separadas por lineas divisorias sutiles.

Contiene tambien ConnectDialog (conexion de fuentes RSS, usado tambien por
el launcher) y GithubDialog (vinculacion de cuenta GitHub).
"""

from __future__ import annotations

import threading

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QLineEdit,
    QMessageBox,
    QFrame,
    QRadioButton,
    QCheckBox,
)

from core.github_link import detect_gh_identity, verify_username
from core.news import NewsService, PRESET_SOURCES
from core.themes import ThemeManager

# ----------------------------------------------------------------------
# Utilidades de estilo
# ----------------------------------------------------------------------


def _mk_title(text: str, accent: str) -> QLabel:
    lbl = QLabel(text)
    f = QFont("Segoe UI", 10, QFont.Weight.Bold)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
    lbl.setFont(f)
    lbl.setStyleSheet(f"background: transparent; color: {accent};")
    return lbl


def _mk_btn(text: str, accent: str, bg_soft: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        f"""
        QPushButton {{
            background: {bg_soft};
            color: {accent};
            border: 1px solid {accent};
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{
            background: {accent};
            color: {bg_soft};
        }}
        QPushButton:disabled {{
            background: {bg_soft};
            color: #777777;
            border-color: #666666;
        }}
        """
    )
    return btn


def _mk_row_label(text: str, them) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"background: transparent; color: {them.text}; font-size: 12px;"
    )
    return lbl


def _mk_row_hint(text: str, them) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"background: transparent; color: {them.text_dim}; font-size: 10px;"
    )
    return lbl


def _mk_separator(them) -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {them.card_border}; background: {them.card_border};")
    line.setFixedHeight(1)
    return line


# ----------------------------------------------------------------------
# Swatch de tema
# ----------------------------------------------------------------------


class ThemeSwatch(QPushButton):
    """Boton de seleccion de tema con vista previa de color."""

    def __init__(self, theme, current: bool, parent=None) -> None:
        super().__init__(parent)
        self.theme_id = theme.id
        self.theme_name = theme.name
        self.accent = theme.accent
        self.bg = theme.bg
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(72, 56)
        self.setCheckable(True)
        self.setChecked(current)
        self.setToolTip(theme.name)
        self._paint()

    def _paint(self) -> None:
        accent = self.accent
        bg = self.bg
        border = "2px solid " + accent if self.isChecked() else f"1px solid {accent}55"
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {bg};
                border: {border};
                border-radius: 8px;
            }}
            QPushButton:hover {{ border: 2px solid {accent}; }}
            """
        )

    def paintEvent(self, event) -> None:
        # Dibuja una mini-vista previa (barra de acento + fondo)
        super().paintEvent(event)
        from PyQt6.QtGui import QPainter

        p = QPainter(self)
        w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self.accent))
        p.drawRect(4, h - 10, w - 8, 6)

    def update_checked(self, checked: bool) -> None:
        self.setChecked(checked)
        self._paint()


# ----------------------------------------------------------------------
# Dialogo de conexion de fuentes de noticias (presets + URL personal)
# ----------------------------------------------------------------------


class ConnectDialog(QDialog):
    """
    Modal para elegir fuentes de noticias.
    - Lista de fuentes predefinidas (presets).
    - Campo para pegar una URL RSS/Atom personalizada (con validacion).
    """

    # Resultado de la validacion de URL (emitida desde el hilo de trabajo)
    validationDone = pyqtSignal(bool, str)

    def __init__(
        self,
        settings,
        theme: ThemeManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._theme = theme
        self._service = NewsService()
        self.validationDone.connect(self._validated)
        self.setWindowTitle("Conectar fuente de noticias")
        self.setModal(True)
        self.setMinimumSize(520, 440)
        self._build()
        self._apply_theme()

    def _build(self) -> None:
        them = self._theme.theme
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 16)
        outer.setSpacing(12)

        title = _mk_title("CONECTAR FUENTE DE NOTICIAS", them.accent)
        outer.addWidget(title)

        subtitle = QLabel(
            "Elige una fuente predefinida o pega el enlace RSS/Atom de tu app favorita.",
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"background: transparent; color: {them.text_dim}; font-size: 11px;"
        )
        outer.addWidget(subtitle)

        # --- Presets en scroll ---
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        preset_container = QWidget()
        preset_layout = QVBoxLayout(preset_container)
        preset_layout.setContentsMargins(0, 0, 8, 0)
        preset_layout.setSpacing(6)

        for src in PRESET_SOURCES:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 4, 4, 4)
            row_layout.setSpacing(8)

            name_lbl = QLabel(src["name"])
            name_lbl.setStyleSheet(
                f"background: transparent; color: {them.text}; font-size: 12px;"
            )
            url_lbl = QLabel(src["url"])
            url_lbl.setStyleSheet(
                f"background: transparent; color: {them.text_dim}; font-size: 9px;"
            )
            url_lbl.setWordWrap(True)

            row_layout.addWidget(name_lbl, 1)
            url_col = QVBoxLayout()
            url_col.addWidget(url_lbl)
            row_layout.addLayout(url_col, 2)

            btn = _mk_btn("USAR", them.accent, them.accent_soft)
            btn.setFixedSize(64, 28)
            btn.clicked.connect(
                lambda _=False, n=src["name"], u=src["url"]: self._connect(n, u)
            )
            row_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)

            preset_layout.addWidget(row)

        preset_layout.addStretch()
        scroll.setWidget(preset_container)
        outer.addWidget(scroll, 1)

        # --- URL personalizada ---
        custom_row = QHBoxLayout()
        custom_row.setSpacing(8)
        self._url_edit = QLineEdit(self)
        self._url_edit.setPlaceholderText("https://ejemplo.com/feed.xml")
        self._url_edit.setStyleSheet(
            f"""
            QLineEdit {{
                background: {them.bg};
                color: {them.text};
                border: 1px solid {them.card_border};
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{ border-color: {them.accent}; }}
            """
        )
        custom_row.addWidget(self._url_edit, 1)

        connect_btn = _mk_btn("CONECTAR", them.accent, them.accent_soft)
        connect_btn.clicked.connect(self._connect_custom)
        custom_row.addWidget(connect_btn)

        outer.addLayout(custom_row)
        self._connect_btn = connect_btn
        self._status = QLabel("")
        self._status.setStyleSheet(
            f"background: transparent; color: {them.accent}; font-size: 10px;"
        )
        outer.addWidget(self._status)

        # Cerrar
        close_row = QHBoxLayout()
        close_row.addStretch()
        cancel_btn = _mk_btn("CERRAR", them.text_dim, them.bg_alt)
        cancel_btn.clicked.connect(self.reject)
        close_row.addWidget(cancel_btn)
        outer.addLayout(close_row)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"QDialog {{ background: {self._theme.theme.bg}; color: {self._theme.theme.text}; }}"
        )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _connect(self, name: str, url: str) -> None:
        
        self._settings.news_sources = [{"name": name, "url": url}]
        self._settings.news_enabled = True
        self._status.setText(f"Conectado a {name}")
        QMessageBox.information(
            self,
            "Conectado",
            f"Fuente conectada: {name}\nLas noticias se actualizaran automaticamente.",
        )
        self.accept()

    def _connect_custom(self) -> None:
        url = self._url_edit.text().strip()
        if not url:
            self._status.setText("Escribe una URL RSS/Atom primero.")
            return

        
        self._connect_btn.setEnabled(False)
        self._connect_btn.setText("VERIFICANDO...")
        self._status.setText("Comprobando enlace...")

        def _work() -> None:
            ok = self._service.validate_url(url)
            # Resultado al hilo principal (entrega segura via senal)
            self.validationDone.emit(ok, url)

        threading.Thread(target=_work, daemon=True).start()

    def _validated(self, __ok: bool = False, __url: str = "") -> None:
        self._connect_btn.setEnabled(True)
        self._connect_btn.setText("CONECTAR")
        if __ok:
            self._connect("Feed personalizado", __url)
        else:
            self._status.setText(
                "No se pudo leer el feed. Verifica el enlace (debe ser RSS/Atom)."
            )


# ----------------------------------------------------------------------
# Dialogo de vinculacion de la cuenta de GitHub
# ----------------------------------------------------------------------


class GithubDialog(QDialog):
    """
    Modal para vincular la cuenta de GitHub del usuario.

    - Intenta detectar la identidad con `gh` (si esta autenticado).
    - Si no, pide el username y lo verifica contra la API publica.
    - Guarda username + nombre real en SettingsManager (sin secretos).
    """

    linked = pyqtSignal(str, str)  # (login, name)

    def __init__(
        self,
        settings,
        theme: ThemeManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._theme = theme
        self.setWindowTitle("Vincular cuenta de GitHub")
        self.setModal(True)
        self.setMinimumSize(460, 260)
        self._build()
        self._apply_theme()

    def _build(self) -> None:
        them = self._theme.theme
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 16)
        outer.setSpacing(12)

        title = _mk_title("VINCULAR CUENTA DE GITHUB", them.accent)
        outer.addWidget(title)

        hint = QLabel(
            "Asi el launcher podra saludarte por tu nombre real.\n"
            "Se usa solo tu perfil publico: no se guardan claves ni tokens.",
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"background: transparent; color: {them.text_dim}; font-size: 11px;"
        )
        outer.addWidget(hint)

        self._status = QLabel("Comprobando si tienes el CLI `gh` instalado...")
        self._status.setWordWrap(True)
        self._status.setStyleSheet(
            f"background: transparent; color: {them.accent}; font-size: 10px;"
        )
        outer.addWidget(self._status)

        # Campo manual
        manual_row = QHBoxLayout()
        manual_row.setSpacing(8)
        self._username_edit = QLineEdit(self)
        self._username_edit.setPlaceholderText("tu-usuario-de-github")
        self._username_edit.setStyleSheet(
            f"""
            QLineEdit {{
                background: {them.bg};
                color: {them.text};
                border: 1px solid {them.card_border};
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{ border-color: {them.accent}; }}
            """
        )
        manual_row.addWidget(self._username_edit, 1)

        self._verify_btn = _mk_btn("VERIFICAR", them.accent, them.accent_soft)
        self._verify_btn.clicked.connect(self._verify_manual)
        manual_row.addWidget(self._verify_btn)
        outer.addLayout(manual_row)

        # Acciones
        actions = QHBoxLayout()
        actions.addStretch()
        self._link_btn = _mk_btn("VINCULAR AHORA", them.accent, them.accent_soft)
        self._link_btn.clicked.connect(self._link_now)
        self._link_btn.setVisible(False)
        actions.addWidget(self._link_btn)
        cancel_btn = _mk_btn("CANCELAR", them.text_dim, them.bg_alt)
        cancel_btn.clicked.connect(self.reject)
        actions.addWidget(cancel_btn)
        outer.addLayout(actions)

        # Deteccion automatica en hilo (gh puede tardar unos segundos)
        threading.Thread(target=self._auto_detect, daemon=True).start()

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"QDialog {{ background: {self._theme.theme.bg}; color: {self._theme.theme.text}; }}"
        )

    # ------------------------------------------------------------------
    # Deteccion automatica con gh
    # ------------------------------------------------------------------

    def _auto_detect(self) -> None:
        ident = detect_gh_identity()
        # Resultado al hilo principal a traves de una senal anonima
        self._status.setText(
            f"Identidad detectada: {ident[0]}" if ident else
            "`gh` no disponible o sin sesion. Escribe tu username debajo."
        )
        self._pending = ident or None

    def _pending_identity(self):
        return getattr(self, "_pending", None)

    # ------------------------------------------------------------------
    # Verificacion manual
    # ------------------------------------------------------------------

    def _verify_manual(self) -> None:
        username = self._username_edit.text().strip()
        if not username:
            self._status.setText("Escribe tu username de GitHub primero.")
            return
        
        self._verify_btn.setEnabled(False)
        self._verify_btn.setText("VERIFICANDO...")
        self._status.setText("Consultando perfil en GitHub...")

        def _work() -> None:
            ident = verify_username(username)
            # Resultado al hilo principal via senal anonima
            self._set_manual_result(ident)

        threading.Thread(target=_work, daemon=True).start()

    def _set_manual_result(self, ident) -> None:
        self._verify_btn.setEnabled(True)
        self._verify_btn.setText("VERIFICAR")
        if ident:
            self._pending = ident
            self._status.setText(
                f"Cuenta valida: {ident[0]}"
                + (f" ({ident[1]})" if ident[1] else "")
            )
            self._link_btn.setVisible(True)
        else:
            self._pending = None
            self._status.setText(
                "No se encontro ese username en GitHub. Revisa la ortografia."
            )
            self._link_btn.setVisible(False)

    # ------------------------------------------------------------------
    # Vincular
    # ------------------------------------------------------------------

    def _link_now(self) -> None:
        ident = self._pending_identity()
        if not ident:
            return
        login, name = ident
        self._settings.github_username = login
        self._settings.github_name = name or login
        
        QMessageBox.information(
            self,
            "Cuenta vinculada",
            f"Cuenta de GitHub vinculada: {login}"
            + (f"\nNombre real: {name}" if name else ""),
        )
        self.linked.emit(login, name or login)
        self.accept()


# ----------------------------------------------------------------------
# Dialogo principal de ajustes (lista estructurada)
# ----------------------------------------------------------------------


class SettingsDialog(QDialog):
    """Panel de control como lista estructurada con separadores."""

    def __init__(self, settings, theme: ThemeManager, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._theme = theme
        self.setWindowTitle("Panel de control")
        self.setModal(True)
        self.setMinimumSize(620, 600)
        self._build()
        self._apply_theme()

    # ------------------------------------------------------------------
    # Construccion
    # ------------------------------------------------------------------

    def _build(self) -> None:
        them = self._theme.theme
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 18)
        outer.setSpacing(12)

        title = _mk_title("PANEL DE CONTROL", them.accent)
        outer.addWidget(title)

        # ---- Scroll general ----
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: transparent; width: 10px; }"
        )

        container = QWidget(self)
        self._form = QVBoxLayout(container)
        self._form.setContentsMargins(0, 0, 10, 0)
        self._form.setSpacing(10)

        # ============ 1 · APARIENCIA ============
        self._form.addWidget(
            _mk_title("1 · APARIENCIA", them.accent)
        )
        self._build_theme_row()
        self._form.addWidget(_mk_separator(them))

        # ============ 2 · COMPORTAMIENTO ============
        self._form.addWidget(
            _mk_title("2 · COMPORTAMIENTO", them.accent)
        )
        self._build_behavior_rows()
        self._form.addWidget(_mk_separator(them))

        # ============ 3 · NOTICIAS ============
        self._form.addWidget(
            _mk_title("3 · PANEL DE NOTICIAS", them.accent)
        )
        self._build_news_rows()
        self._form.addWidget(_mk_separator(them))

        # ============ 4 · CUENTA DE GITHUB ============
        self._form.addWidget(
            _mk_title("4 · CUENTA DE GITHUB", them.accent)
        )
        self._build_github_row()
        self._form.addWidget(_mk_separator(them))

        # ============ 5 · PROXIMAMENTE ============
        self._form.addWidget(
            _mk_title("5 · PROXIMAMENTE", them.accent)
        )
        self._build_soon_rows()
        self._form.addWidget(_mk_separator(them))

        # ============ 6 · ASISTENTE ============
        self._form.addWidget(
            _mk_title("6 · ASISTENTE", them.accent)
        )
        self._build_agent_rows()

        self._form.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

        # ---- Acciones ----
        action_row = QHBoxLayout()
        action_row.addStretch()
        cancel_btn = _mk_btn("CANCELAR", them.text_dim, them.bg_alt)
        cancel_btn.clicked.connect(self.reject)
        action_row.addWidget(cancel_btn)

        apply_btn = _mk_btn("APLICAR", them.accent, them.accent_soft)
        apply_btn.clicked.connect(self._apply_and_close)
        action_row.addWidget(apply_btn)
        outer.addLayout(action_row)

    # ------------------------------------------------------------------
    # Fila: apariencia (tema)
    # ------------------------------------------------------------------

    def _build_theme_row(self) -> None:
        them = self._theme.theme
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Tema de color", them))
        text_col.addWidget(
            _mk_row_hint("Cambia la paleta completa del launcher al instante.", them)
        )
        row.addLayout(text_col, 1)

        theme_scroll = QScrollArea(self)
        theme_scroll.setWidgetResizable(True)
        theme_scroll.setFrameShape(QFrame.Shape.NoFrame)
        theme_scroll.setFixedWidth(300)
        theme_scroll.setFixedHeight(64)
        theme_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )

        theme_container = QWidget()
        theme_layout = QHBoxLayout(theme_container)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(8)

        self._swatches: dict[str, ThemeSwatch] = {}
        for t in ThemeManager.available_themes():
            swatch = ThemeSwatch(t, current=(t.id == self._theme.theme_id))
            swatch.clicked.connect(
                lambda _=False, tid=t.id: self._on_theme_selected(tid)
            )
            self._swatches[t.id] = swatch
            theme_layout.addWidget(swatch)
        theme_layout.addStretch()

        theme_scroll.setWidget(theme_container)
        row.addWidget(theme_scroll)
        self._form.addLayout(row)

    # ------------------------------------------------------------------
    # Filas: comportamiento
    # ------------------------------------------------------------------

    def _build_behavior_rows(self) -> None:
        them = self._theme.theme

        # Atajo global (informativo)
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Atajo global", them))
        text_col.addWidget(
            _mk_row_hint("Convocar/ocultar el launcher desde cualquier app.", them)
        )
        row.addLayout(text_col, 1)
        badge = QLabel("Ctrl + Shift + Espacio")
        badge.setStyleSheet(
            f"background: {them.accent_soft}; color: {them.accent};"
            f"border: 1px solid {them.accent}; border-radius: 6px;"
            f"padding: 6px 12px; font-size: 11px; font-weight: bold;"
        )
        row.addWidget(badge, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

        # Bandeja del sistema
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Bandeja del sistema", them))
        text_col.addWidget(
            _mk_row_hint(
                "Al cerrar con ✕ el launcher se oculta a la bandeja y sigue activo.",
                them,
            )
        )
        row.addLayout(text_col, 1)
        self._tray_check = QCheckBox("Activar bandeja")
        self._tray_check.setChecked(self._settings.tray_enabled)
        self._tray_check.setStyleSheet(
            f"background: transparent; color: {them.text}; font-size: 12px;"
        )
        row.addWidget(self._tray_check, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

        # Auto-inicio
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Arrancar con Windows", them))
        text_col.addWidget(
            _mk_row_hint(
                "Inicia el launcher en segundo plano junto al sistema.", them
            )
        )
        row.addLayout(text_col, 1)
        self._startup_btn = _mk_btn("CONFIGURAR", them.accent, them.accent_soft)
        self._startup_btn.clicked.connect(self._on_startup_toggle)
        row.addWidget(self._startup_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

    # ------------------------------------------------------------------
    # Filas: noticias
    # ------------------------------------------------------------------

    def _build_news_rows(self) -> None:
        them = self._theme.theme

        # Activar panel
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Panel de noticias", them))
        text_col.addWidget(
            _mk_row_hint(
                "Muestra las ultimas noticias en el lateral del launcher.", them
            )
        )
        row.addLayout(text_col, 1)
        self._news_check = QCheckBox("Activar panel")
        self._news_check.setChecked(self._settings.news_enabled)
        self._news_check.setStyleSheet(
            f"background: transparent; color: {them.text}; font-size: 12px;"
        )
        row.addWidget(self._news_check, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

        # Posicion
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Posicion del panel", them))
        row.addLayout(text_col, 1)
        pos_widget = QWidget()
        pos_layout = QHBoxLayout(pos_widget)
        pos_layout.setContentsMargins(0, 0, 0, 0)
        pos_layout.setSpacing(6)
        self._pos_left = QRadioButton("Izquierda")
        self._pos_right = QRadioButton("Derecha")
        self._pos_left.setChecked(self._settings.news_position == "left")
        self._pos_right.setChecked(self._settings.news_position == "right")
        for pos in (self._pos_left, self._pos_right):
            pos.setStyleSheet(
                f"background: transparent; color: {them.text}; font-size: 12px;"
            )
        pos_layout.addWidget(self._pos_left)
        pos_layout.addWidget(self._pos_right)
        row.addWidget(pos_widget, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

        # Fuente conectada
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Fuente conectada", them))
        self._sources_lbl = QLabel(self._current_sources_text())
        self._sources_lbl.setWordWrap(True)
        self._sources_lbl.setStyleSheet(
            f"background: transparent; color: {them.text_dim}; font-size: 10px;"
        )
        text_col.addWidget(self._sources_lbl)
        row.addLayout(text_col, 1)
        self._connect_btn = _mk_btn("CONECTAR / CAMBIAR", them.accent, them.accent_soft)
        self._connect_btn.clicked.connect(self._open_connect_dialog)
        row.addWidget(self._connect_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

    # ------------------------------------------------------------------
    # Fila: cuenta de GitHub
    # ------------------------------------------------------------------

    def _build_github_row(self) -> None:
        them = self._theme.theme
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Cuenta de GitHub", them))
        if self._settings.github_username:
            name_part = self._settings.github_name or self._settings.github_username
            status = f"Vinculada: {self._settings.github_username} ({name_part})"
        else:
            status = (
                "Sin vincular. El saludo usara un adjetivo generico; "
                "al vincular usara tu nombre real."
            )
        self._github_lbl = QLabel(status)
        self._github_lbl.setWordWrap(True)
        self._github_lbl.setStyleSheet(
            f"background: transparent; color: {them.text_dim}; font-size: 10px;"
        )
        text_col.addWidget(self._github_lbl)
        row.addLayout(text_col, 1)
        self._github_btn = _mk_btn(
            "VINCULAR", them.accent, them.accent_soft
        )
        self._github_btn.clicked.connect(self._open_github_dialog)
        row.addWidget(self._github_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

    # ------------------------------------------------------------------
    # Filas: proximamente
    # ------------------------------------------------------------------

    def _build_soon_rows(self) -> None:
        them = self._theme.theme
        for label, hint in (
            ("Editor visual de modos", "Personaliza colores e iconos de cada modo."),
            (
                "Editor de paletas de tema",
                "Crea tus propios esquemas de color partiendo de los existentes.",
            ),
            (
                "Lector de noticias a pantalla completa",
                "Lee articulos completos con tipografia comoda.",
            ),
        ):
            row = QHBoxLayout()
            row.setSpacing(12)
            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            text_col.addWidget(_mk_row_label(label, them))
            text_col.addWidget(_mk_row_hint(hint, them))
            row.addLayout(text_col, 1)
            soon = QLabel("PRÓXIMAMENTE")
            soon.setStyleSheet(
                f"background: transparent; color: {them.text_dim};"
                f"border: 1px solid {them.card_border}; border-radius: 6px;"
                f"padding: 6px 10px; font-size: 10px; letter-spacing: 1px;"
            )
            row.addWidget(soon, alignment=Qt.AlignmentFlag.AlignRight)
            self._form.addLayout(row)

    def _current_sources_text(self) -> str:
        srcs = self._settings.news_sources
        if not srcs:
            return "Sin conexion. Pulsa CONECTAR para elegir una fuente."
        return " • ".join(s.get("name", s.get("url", "?")) for s in srcs)

    # ------------------------------------------------------------------
    # Filas: asistente IA local (Fase 1)
    # ------------------------------------------------------------------

    def _build_agent_rows(self) -> None:
        them = self._theme.theme

        # Activar asistente
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Asistente IA local", them))
        text_col.addWidget(
            _mk_row_hint(
                "Chat con tu PC (archivos, comandos, apps). Cada acción pide aprobación.",
                them,
            )
        )
        row.addLayout(text_col, 1)
        self._agent_check = QCheckBox("Activar asistente")
        self._agent_check.setChecked(self._settings.agent_enabled)
        self._agent_check.setStyleSheet(
            f"background: transparent; color: {them.text}; font-size: 12px;"
        )
        row.addWidget(self._agent_check, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

        # URL de Ollama
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Servidor Ollama", them))
        row.addLayout(text_col, 1)
        self._agent_url = QLineEdit(self._settings.agent_url)
        self._agent_url.setFixedWidth(260)
        self._agent_url.setStyleSheet(
            f"background: {them.bg}; color: {them.text}; font-size: 12px;"
            f"border: 1px solid {them.card_border}; border-radius: 6px; padding: 6px;"
        )
        row.addWidget(self._agent_url, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

        # Modelo + probar conexión
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Modelo", them))
        self._agent_status = QLabel("Sin probar.")
        self._agent_status.setWordWrap(True)
        self._agent_status.setStyleSheet(
            f"background: transparent; color: {them.text_dim}; font-size: 10px;"
        )
        text_col.addWidget(self._agent_status)
        row.addLayout(text_col, 1)
        self._agent_model = QLineEdit(self._settings.agent_model)
        self._agent_model.setFixedWidth(200)
        self._agent_model.setStyleSheet(self._agent_url.styleSheet())
        row.addWidget(self._agent_model, alignment=Qt.AlignmentFlag.AlignRight)
        self._agent_test_btn = _mk_btn("PROBAR", them.accent, them.accent_soft)
        self._agent_test_btn.clicked.connect(self._on_agent_test)
        row.addWidget(self._agent_test_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

        # Límites (timeout / pasos)
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Límites", them))
        text_col.addWidget(
            _mk_row_hint("Timeout por llamada (s) y pasos máximos por turno.", them)
        )
        row.addLayout(text_col, 1)
        self._agent_timeout = QLineEdit(str(self._settings.agent_timeout_s))
        self._agent_timeout.setFixedWidth(70)
        self._agent_timeout.setStyleSheet(self._agent_url.styleSheet())
        row.addWidget(self._agent_timeout, alignment=Qt.AlignmentFlag.AlignRight)
        self._agent_steps = QLineEdit(str(self._settings.agent_max_steps))
        self._agent_steps.setFixedWidth(60)
        self._agent_steps.setStyleSheet(self._agent_url.styleSheet())
        row.addWidget(self._agent_steps, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

        # Log + vaciar chat
        row = QHBoxLayout()
        row.setSpacing(12)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(_mk_row_label("Auditoría", them))
        text_col.addWidget(
            _mk_row_hint("Registro append-only de propuestas y decisiones.", them)
        )
        row.addLayout(text_col, 1)
        self._agent_log_btn = _mk_btn("VER LOG", them.accent, them.accent_soft)
        self._agent_log_btn.clicked.connect(self._on_agent_log)
        row.addWidget(self._agent_log_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self._agent_clear_btn = _mk_btn("VACIAR CHAT", them.accent, them.accent_soft)
        self._agent_clear_btn.clicked.connect(self._on_agent_clear)
        row.addWidget(self._agent_clear_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self._form.addLayout(row)

    def _on_agent_test(self) -> None:
        """Prueba conexión contra Ollama (ping + lista de modelos)."""
        from core.agent import OllamaClient

        url = self._agent_url.text().strip() or "http://localhost:11434"
        model = self._agent_model.text().strip()
        client = OllamaClient(base_url=url, model=model, timeout_s=15, max_retries=1)
        try:
            if not client.ping():
                self._agent_status.setText("Sin conexión: ¿ollama serve en marcha?")
                return
            models = client.list_models()
            if model and not any(m.split(":")[0] == model.split(":")[0] for m in models):
                self._agent_status.setText(
                    f"En línea, pero falta el modelo. Ejecuta: ollama pull {model}"
                )
            else:
                self._agent_status.setText(f"En línea ({len(models)} modelos).")
        except Exception as exc:  # noqa: BLE001
            self._agent_status.setText(f"Error: {exc}")

    def _on_agent_log(self) -> None:
        import os as _os
        import webbrowser as _web

        path = self._settings.agent_log_path
        if not _os.path.isabs(path):
            import core.platform as _plat

            path = _os.path.join(_plat.repo_root(), path)
        if _os.path.exists(path):
            _web.open(f"file://{path}")
        else:
            self._agent_status.setText("Aún no hay log (usa el chat primero).")

    def _on_agent_clear(self) -> None:
        parent_ui = self.parent()
        if parent_ui is not None and hasattr(parent_ui, "clear_agent_chat"):
            parent_ui.clear_agent_chat()

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------

    def _on_theme_selected(self, theme_id: str) -> None:
        
        self._theme.set_theme(theme_id)
        self._apply_theme()
        for tid, swatch in self._swatches.items():
            swatch.update_checked(tid == theme_id)

    # ------------------------------------------------------------------
    # Noticias / conexion
    # ------------------------------------------------------------------

    def _open_connect_dialog(self) -> None:
        dlg = ConnectDialog(self._settings, self._theme, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._sources_lbl.setText(self._current_sources_text())
            self._news_check.setChecked(True)
            # Refrescar panel en vivo
            parent_ui = self.parent()
            if parent_ui is not None and hasattr(parent_ui, "refresh_news"):
                parent_ui.refresh_news()

    # ------------------------------------------------------------------
    # GitHub
    # ------------------------------------------------------------------

    def _open_github_dialog(self) -> None:
        dlg = GithubDialog(self._settings, self._theme, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            login = self._settings.github_username
            name = self._settings.github_name or login
            self._github_lbl.setText(f"Vinculada: {login} ({name})")
            # Actualizar saludo en vivo
            parent_ui = self.parent()
            if parent_ui is not None and hasattr(parent_ui, "refresh_greeting"):
                parent_ui.refresh_greeting()

    # ------------------------------------------------------------------
    # Auto-inicio
    # ------------------------------------------------------------------

    def _on_startup_toggle(self) -> None:
        
        parent_ui = self.parent()
        if parent_ui is not None and hasattr(parent_ui, "toggle_startup"):
            parent_ui.toggle_startup()

    # ------------------------------------------------------------------
    # Aplicar
    # ------------------------------------------------------------------

    def _apply_and_close(self) -> None:
        
        # Tema
        self._settings.theme = self._theme.theme_id
        # Bandeja
        self._settings.tray_enabled = self._tray_check.isChecked()
        # Noticias
        self._settings.news_enabled = self._news_check.isChecked()
        if self._pos_left.isChecked():
            self._settings.news_position = "left"
        else:
            self._settings.news_position = "right"
        # Asistente (Fase 1)
        self._settings.agent_enabled = self._agent_check.isChecked()
        self._settings.agent_url = self._agent_url.text()
        self._settings.agent_model = self._agent_model.text()
        try:
            self._settings.agent_timeout_s = int(self._agent_timeout.text())
        except ValueError:
            pass
        try:
            self._settings.agent_max_steps = int(self._agent_steps.text())
        except ValueError:
            pass
        # Aplicar en la UI padre
        parent_ui = self.parent()
        if parent_ui is not None:
            if hasattr(parent_ui, "apply_theme"):
                parent_ui.apply_theme()
            if hasattr(parent_ui, "apply_news_panel"):
                parent_ui.apply_news_panel()
            if hasattr(parent_ui, "apply_agent_settings"):
                parent_ui.apply_agent_settings()
            if hasattr(parent_ui, "refresh_news"):
                # Fix v2.0.2 (Bug G-003): refresca las noticias en vivo al
                # aplicar ajustes - antes el panel solo cambiaba al reiniciar
                parent_ui.refresh_news()
        self.accept()

    # ------------------------------------------------------------------
    # Theme painting
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        them = self._theme.theme
        self.setStyleSheet(f"QDialog {{ background: {them.bg}; color: {them.text}; }}")
        for swatch in self._swatches.values():
            swatch._paint()
        self._sources_lbl.setStyleSheet(
            f"background: transparent; color: {them.text_dim}; font-size: 10px;"
        )
        self._github_lbl.setStyleSheet(
            f"background: transparent; color: {them.text_dim}; font-size: 10px;"
        )
        if hasattr(self, "_agent_status"):
            self._agent_status.setStyleSheet(
                f"background: transparent; color: {them.text_dim}; font-size: 10px;"
            )