"""
ui/chat_panel.py - Panel de chat del asistente IA local (Fase 1).

Burbujas terminal-HUD + tarjetas de aprobación (ESPEC §3.6, ADR-014 §2).
Sin paint custom (stylesheets con colores del ThemeManager activo).
La decisión del usuario sale por la señal decisionMade (la conecta el
controlador al AgentWorker); este widget nunca ejecuta tools.
"""

from __future__ import annotations

import json
import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence, QTextDocument
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger("jarvis.chat")


def _risk_badge(risk: str) -> str:
    return {"read": "🟢", "write": "🟡", "shell": "🔴"}.get(risk, "🟢")


class ChatPanel(QWidget):
    """Panel lateral de conversación con el agente."""

    messageSent = pyqtSignal(str)
    decisionMade = pyqtSignal(str, str, object)  # proposal_id, decision, new_args|None

    _FIRST_USE_HINT = (
        "Cada acción se ejecuta solo si la apruebas. "
        "Revisa los argumentos antes de Aprobar."
    )

    def __init__(self, settings, theme, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._theme = theme
        self._suggested = False

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        self._status = QLabel("● listo")
        self._status.setStyleSheet("background: transparent; border: none; font-size: 10px;")
        root.addWidget(self._status)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        self._stream = QWidget()
        self._stream_layout = QVBoxLayout(self._stream)
        self._stream_layout.setContentsMargins(2, 2, 2, 2)
        self._stream_layout.setSpacing(8)
        self._stream_layout.addStretch()
        self._scroll.setWidget(self._stream)
        root.addWidget(self._scroll, 1)

        self._suggest_row = QHBoxLayout()
        self._suggest_row.setSpacing(6)
        for text in ("¿Qué proyectos tengo aquí?", "Abre VS Code", "¿RAM libre?"):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, t=text: self._send(t))
            self._suggest_row.addWidget(btn)
        self._suggest_box = QWidget()
        self._suggest_box.setLayout(self._suggest_row)
        root.addWidget(self._suggest_box)

        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        self._input = QLineEdit(self)
        self._input.setPlaceholderText("Pregunta o pide algo a J.A.R.V.I.S. …")
        self._input.returnPressed.connect(self._send_from_input)
        input_row.addWidget(self._input, 1)
        self._send_btn = QPushButton("➤")
        self._send_btn.setFixedSize(36, 32)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.clicked.connect(self._send_from_input)
        input_row.addWidget(self._send_btn)
        root.addLayout(input_row)

        self._hint = QLabel(self._FIRST_USE_HINT)
        self._hint.setWordWrap(True)
        root.addWidget(self._hint)

        self.refresh_theme()

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------

    def refresh_theme(self) -> None:
        them = self._theme.theme
        self.setStyleSheet(f"ChatPanel {{ background: {them.bg_alt}; }}")
        self._status.setStyleSheet(
            f"background: transparent; border: none; color: {them.accent}; font-size: 10px;"
        )
        self._input.setStyleSheet(
            f"background: {them.bg}; color: {them.text}; border: 1px solid {them.card_border};"
            f"border-radius: 8px; padding: 6px 10px; font-size: 12px;"
        )
        self._send_btn.setStyleSheet(
            f"QPushButton {{ background: {them.accent_soft}; color: {them.accent};"
            f"border: 1px solid {them.accent}; border-radius: 8px; font-size: 14px; }}"
            f"QPushButton:hover {{ background: {them.accent}; color: {them.bg}; }}"
        )
        for i in range(self._suggest_row.count()):
            btn = self._suggest_row.itemAt(i).widget()
            if isinstance(btn, QPushButton):
                btn.setStyleSheet(
                    f"background: transparent; color: {them.text_dim}; font-size: 10px;"
                    f"border: 1px solid {them.card_border}; border-radius: 6px; padding: 4px;"
                )
        self._hint.setStyleSheet(
            f"background: transparent; border: none; color: {them.text_dim}; font-size: 9px;"
        )
        self._accent = them.accent
        self._bubble_user = them.accent_soft
        self._bubble_agent = them.bg
        self._text = them.text
        self._text_dim = them.text_dim
        self._border = them.card_border

    # ------------------------------------------------------------------
    # Entrada
    # ------------------------------------------------------------------

    def _send_from_input(self) -> None:
        text = self._input.text().strip()
        if text:
            self._send(text)

    def _send(self, text: str) -> None:
        self._input.clear()
        if not self._suggested:
            self._suggested = True
            self._suggest_box.hide()
        self._add_bubble(text, who="user")
        self.messageSent.emit(text)

    def set_busy(self, busy: bool) -> None:
        self._input.setEnabled(not busy)
        self._send_btn.setEnabled(not busy)

    def clear(self) -> None:
        while self._stream_layout.count() > 1:  # conserva el stretch final
            item = self._stream_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    # ------------------------------------------------------------------
    # Slots del worker
    # ------------------------------------------------------------------

    def agentReply(self, text: str) -> None:
        self._add_bubble(text, who="agent")
        self.set_busy(False)

    def agentError(self, text: str) -> None:
        lbl = QLabel(f"⚠ {text}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"background: transparent; border: none; color: #FF6B6B; font-size: 11px;"
        )
        self._push(lbl)
        self.set_busy(False)

    def set_status(self, text: str) -> None:
        dot = {"pensando": "● pensando", "listo": "● listo",
               "offline": "● offline", "ejecutando": "● ejecutando"}.get(text, f"● {text}")
        self._status.setText(dot)
        if text == "pensando":
            self.set_busy(True)

    # ------------------------------------------------------------------
    # Tarjetas de aprobación
    # ------------------------------------------------------------------

    def show_proposal(self, proposal) -> None:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(
            f"QFrame {{ background: {self._bubble_agent}; border: 1px solid {self._accent};"
            f"border-radius: 10px; }}"
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        head = QLabel(f"{_risk_badge(proposal.risk)} <b>{proposal.tool}</b>")
        head.setStyleSheet(f"background: transparent; border: none; color: {self._text};")
        layout.addWidget(head)

        summary = QLabel(proposal.summary)
        summary.setWordWrap(True)
        summary.setStyleSheet(
            f"background: transparent; border: none; color: {self._text}; font-size: 12px;"
        )
        layout.addWidget(summary)

        args_view = QTextEdit(json.dumps(proposal.args, indent=2, ensure_ascii=False))
        args_view.setReadOnly(True)
        args_view.setFixedHeight(90)
        args_view.setStyleSheet(
            f"background: {self._bubble_user}; color: {self._text}; font-size: 10px;"
            f"border: 1px solid {self._border}; border-radius: 6px;"
        )
        args_view.hide()
        toggle_args = QPushButton("ver argumentos ▾")
        toggle_args.setStyleSheet(
            f"background: transparent; border: none; color: {self._text_dim}; font-size: 10px;"
        )
        toggle_args.clicked.connect(
            lambda: (args_view.setVisible(not args_view.isVisible()),
                     toggle_args.setText("ver argumentos ▴" if args_view.isVisible()
                                         else "ver argumentos ▾")))
        layout.addWidget(toggle_args)
        layout.addWidget(args_view)

        if proposal.diff:
            diff_view = QTextEdit(proposal.diff[:6000])
            diff_view.setReadOnly(True)
            diff_view.setFixedHeight(120)
            diff_view.setStyleSheet(
                f"background: {self._bubble_user}; color: {self._text}; font-size: 10px;"
                f"font-family: monospace; border: 1px solid {self._border}; border-radius: 6px;"
            )
            diff_view.hide()
            toggle_diff = QPushButton("ver diff ▾")
            toggle_diff.setStyleSheet(toggle_args.styleSheet())
            toggle_diff.clicked.connect(
                lambda: (diff_view.setVisible(not diff_view.isVisible()),
                         toggle_diff.setText("ver diff ▴" if diff_view.isVisible()
                                             else "ver diff ▾")))
            layout.addWidget(toggle_diff)
            layout.addWidget(diff_view)

        btn_row = QHBoxLayout()
        approve = QPushButton("Aprobar ⏎")
        reject = QPushButton("Rechazar ⌫")
        edit = QPushButton("Editar")
        for b in (approve, reject, edit):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_row.addWidget(b)
        approve.setStyleSheet(
            f"background: {self._accent}; color: {self._bubble_agent}; border-radius: 6px;"
            f"padding: 6px; font-weight: bold;"
        )
        reject.setStyleSheet(
            f"background: transparent; color: #FF6B6B; border: 1px solid #FF6B6B;"
            f"border-radius: 6px; padding: 6px;"
        )
        edit.setStyleSheet(
            f"background: transparent; color: {self._text_dim};"
            f"border: 1px solid {self._border}; border-radius: 6px; padding: 6px;"
        )
        layout.addLayout(btn_row)

        def _done(decision: str, new_args=None):
            for b in (approve, reject, edit):
                b.setEnabled(False)
            head.setText(f"{_risk_badge(proposal.risk)} <b>{proposal.tool}</b> — {decision}")
            self.decisionMade.emit(proposal.id, decision, new_args)

        approve.clicked.connect(lambda: _done("approve"))
        reject.clicked.connect(lambda: _done("reject"))
        edit.clicked.connect(lambda: self._edit_args(card, layout, proposal, _done))

        QShortcut(QKeySequence(Qt.Key.Key_Return), card,
                  activated=lambda: approve.click() if approve.isEnabled() else None,
                  context=Qt.ShortcutContext.WidgetWithChildrenShortcut)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), card,
                  activated=lambda: reject.click() if reject.isEnabled() else None,
                  context=Qt.ShortcutContext.WidgetWithChildrenShortcut)

        self._push(card)

    def _edit_args(self, card, layout, proposal, done) -> None:
        editor = QTextEdit(json.dumps(proposal.args, indent=2, ensure_ascii=False))
        editor.setFixedHeight(110)
        layout.addWidget(editor)
        save = QPushButton("Guardar y aprobar")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(save)

        def _save():
            try:
                new_args = json.loads(editor.toPlainText())
            except json.JSONDecodeError as exc:
                editor.setStyleSheet(editor.styleSheet() + "border: 2px solid #FF6B6B;")
                editor.setPlaceholderText(f"JSON inválido: {exc}")
                return
            if not isinstance(new_args, dict):
                editor.setPlaceholderText("Debe ser un objeto JSON")
                return
            editor.deleteLater()
            save.deleteLater()
            done("edit", new_args)

        save.clicked.connect(_save)

    def show_blocked(self, info: dict) -> None:
        proposal = info.get("proposal", {})
        motivo = info.get("motivo", "")
        lbl = QLabel(
            f"⛔ <b>{proposal.get('tool', '?')}</b> bloqueada por política:<br/>{motivo}"
        )
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"background: {self._bubble_user}; color: {self._text}; font-size: 11px;"
            f"border: 1px dashed #FF6B6B; border-radius: 8px; padding: 8px;"
        )
        self._push(lbl)

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _render_markdown(self, text: str) -> str:
        """Convierte Markdown a HTML estilizado con soporte de tablas comparativas."""
        doc = QTextDocument()
        doc.setMarkdown(text)
        raw_html = doc.toHtml()

        # Inyectar estilos CSS para tablas comparativas elegantes y legibles
        accent = getattr(self, "_accent", "#00FFFF")
        border = getattr(self, "_border", "#2A3546")
        text_color = getattr(self, "_text", "#FFFFFF")
        table_style = f"""
<style type="text/css">
table {{
    border-collapse: collapse;
    margin: 6px 0;
    width: 100%;
}}
th, td {{
    border: 1px solid {border};
    padding: 5px 8px;
    font-size: 11px;
    color: {text_color};
}}
tr:first-child td {{
    background-color: rgba(0, 255, 255, 0.12);
    color: {accent};
    font-weight: bold;
}}
code {{
    background-color: rgba(255, 255, 255, 0.1);
    padding: 1px 4px;
    border-radius: 3px;
    font-family: monospace;
}}
pre {{
    background-color: rgba(0, 0, 0, 0.35);
    border: 1px solid {border};
    border-radius: 6px;
    padding: 6px;
    font-family: monospace;
}}
</style>
"""
        return raw_html.replace("<style type=\"text/css\">", table_style)

    def _add_bubble(self, text: str, who: str) -> None:
        bg = self._bubble_user if who == "user" else "transparent"
        border = f"border: 1px solid {self._border};" if who == "agent" else "border: none;"
        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # Usar renderizador Markdown enriquecido con soporte de tablas
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setText(self._render_markdown(text))

        lbl.setStyleSheet(
            f"background: {bg}; color: {self._text}; font-size: 12px;"
            f"{border} border-radius: 8px; padding: 8px;"
        )
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._push(lbl)

    def _push(self, widget: QWidget) -> None:
        self._stream_layout.insertWidget(self._stream_layout.count() - 1, widget)
        bar = self._scroll.verticalScrollBar()
        if bar is not None:
            bar.setValue(bar.maximum())
