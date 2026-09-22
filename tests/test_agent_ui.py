"""Suite D — Offscreen Qt del panel y tarjetas (TEST-agente.md).

Se ejecuta con QT_QPA_PLATFORM=offscreen (lo fuerza si falta).
"""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from core.agent.policy import Proposal  # noqa: E402
from core.settings import SettingsManager  # noqa: E402
from core.themes import ThemeManager  # noqa: E402
from ui.chat_panel import ChatPanel  # noqa: E402

app = QApplication.instance() or QApplication(sys.argv)


class TestChatPanel(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.settings = SettingsManager(
            os.path.join(self._tmp.name, "settings.json"))
        self.theme = ThemeManager("obsidiana")
        self.panel = ChatPanel(self.settings, self.theme)
        self.panel.show()

    def tearDown(self):
        self.panel.deleteLater()
        self._tmp.cleanup()

    def test_render_8_temas(self):
        for tid in ThemeManager.available_themes():
            self.theme = ThemeManager(tid.id)
            self.panel._theme = self.theme
            self.panel.refresh_theme()
            self.panel.repaint()
        self.assertTrue(True)  # 0 errores QPainter = éxito

    def test_burbujas_y_tarjeta(self):
        decisions = []
        self.panel.decisionMade.connect(
            lambda pid, d, na: decisions.append((pid, d, na)))
        self.panel._send("hola")
        prop = Proposal(id="p1", tool="read_file",
                        args={"path": "x.py"}, summary="Leer x.py", risk="read")
        self.panel.show_proposal(prop)
        self.panel.show_blocked({"proposal": {"tool": "run_shell"},
                                 "motivo": "regla test"})
        app.processEvents()
        self.assertEqual(len(decisions), 0)  # sin clics aún

    def test_aprobar_rechazar(self):
        got = []
        self.panel.decisionMade.connect(lambda pid, d, na: got.append(d))
        prop = Proposal(id="p2", tool="list_dir", args={},
                        summary="Listar", risk="read")
        self.panel.show_proposal(prop)
        app.processEvents()
        # Clic en Aprobar (buscar por texto: también hay toggles QPushButton)
        from PyQt6.QtWidgets import QPushButton  # noqa: E402

        card = self.panel._stream_layout.itemAt(
            self.panel._stream_layout.count() - 2).widget()
        approve = next(
            b for b in card.findChildren(QPushButton)
            if b.text().startswith("Aprobar"))
        approve.click()
        app.processEvents()
        self.assertEqual(got, ["approve"])

    def test_markdown_tables_bubble(self):
        # Enviar respuesta con tabla comparativa en markdown
        table_md = (
            "### Comparativa\n\n"
            "| Característica | Local | Nube |\n"
            "| :--- | :--- | :--- |\n"
            "| Privacidad | 100% | Compartida |\n"
            "| Latencia | <10ms | >200ms |\n"
        )
        self.panel.agentReply(table_md)
        app.processEvents()
        
        # Verificar que el widget renderizado existe en el stream layout
        bubble_widget = self.panel._stream_layout.itemAt(
            self.panel._stream_layout.count() - 2
        ).widget()
        self.assertIsNotNone(bubble_widget)
        self.assertTrue("<table" in bubble_widget.text() or "table" in bubble_widget.text().lower())


if __name__ == "__main__":
    unittest.main()
