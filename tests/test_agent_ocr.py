"""Suite OCR — read_image + see_screen con motor mockeado (sin RapidOCR real)."""

import os
import tempfile
import unittest
from unittest import mock

from core.agent import tools as tools_mod
from core.agent.tools import TOOLS, execute_tool, ollama_tools


def _ctx(root):
    return {"repo_root": root, "model": "llama3.2:1b"}


class TestOcrCatalog(unittest.TestCase):
    def test_catalogo_12_tools(self):
        names = [t.name for t in TOOLS]
        self.assertIn("read_image", names)
        self.assertIn("see_screen", names)
        self.assertIn("query_ocr", names)
        self.assertEqual(len(TOOLS), 12)
        wire = {f["function"]["name"] for f in ollama_tools()}
        self.assertIn("read_image", wire)
        self.assertIn("see_screen", wire)
        self.assertIn("query_ocr", wire)


class TestReadImage(unittest.TestCase):
    def test_no_existe(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = execute_tool("read_image", {"path": "no.png"}, _ctx(tmp))
            self.assertEqual(r["error_code"], "FILE_NOT_FOUND")

    def test_extension_no_imagen(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "a.txt")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("hola")
            r = execute_tool("read_image", {"path": "a.txt"}, _ctx(tmp))
            self.assertEqual(r["error_code"], "NOT_AN_IMAGE")

    def test_ok_mock(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "f.png")
            with open(p, "wb") as fh:
                fh.write(b"\x89PNG\r\n\x1a\n" + b"0" * 100)
            fake = {"status": "ok", "output": "FACTURA 123", "path": p,
                    "engine": "mock", "lines": 1}
            with mock.patch("core.agent.vision_ocr.ocr_image_file", return_value=fake):
                r = execute_tool("read_image", {"path": "f.png"}, _ctx(tmp))
            self.assertEqual(r["status"], "ok")
            self.assertIn("FACTURA", r["output"])

    def test_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "f.png")
            with open(p, "wb") as fh:
                fh.write(b"\x89PNG\r\n\x1a\n")
            fake = {"status": "error", "error_code": "OCR_UNAVAILABLE",
                    "error_detail": "pip install rapidocr-onnxruntime pillow"}
            with mock.patch("core.agent.vision_ocr.ocr_image_file", return_value=fake):
                r = execute_tool("read_image", {"path": "f.png"}, _ctx(tmp))
            self.assertEqual(r["error_code"], "OCR_UNAVAILABLE")

    def test_schema_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = execute_tool("read_image", {}, _ctx(tmp))
            self.assertEqual(r["error_code"], "INVALID_ARGS")


class TestSeeScreen(unittest.TestCase):
    def test_ok_mock(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = {"status": "ok", "output": "Ventana: Editor",
                    "screenshot_path": os.path.join(tmp, "s.png"),
                    "engine": "mock", "lines": 1}
            with mock.patch("core.agent.vision_ocr.capture_screen", return_value=fake):
                r = execute_tool("see_screen", {}, _ctx(tmp))
            self.assertEqual(r["status"], "ok")
            self.assertIn("Ventana", r["output"])


class TestVisionModule(unittest.TestCase):
    def test_ocr_available_no_crashea(self):
        from core.agent import vision_ocr

        ok, info = vision_ocr.ocr_available()
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(info, str)
        self.assertTrue(len(info) > 0)


class TestOcrStore(unittest.TestCase):
    def _save(self, tmp, text="TOTAL 12.50", **kw):
        from core.agent import ocr_store

        base = {"status": "ok", "output": text, "path": os.path.join(tmp, "f.png"),
                "engine": "mock", "lines": 1}
        base.update(kw)
        return ocr_store.save_ocr(base, repo_root=tmp)

    def test_save_last_recent(self):
        from core.agent import ocr_store

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ocr_store.load_recent(tmp), [])
            self.assertEqual(ocr_store.load_last(tmp), {})
            e1 = self._save(tmp, "FACTURA A")
            e2 = self._save(tmp, "FACTURA B")
            self.assertTrue(e1["id"] and e2["id"] and e1["id"] != e2["id"])
            last = ocr_store.load_last(tmp)
            self.assertEqual(last["id"], e2["id"])
            recent = ocr_store.load_recent(tmp, 2)
            self.assertEqual([e["id"] for e in recent], [e1["id"], e2["id"]])
            self.assertTrue(os.path.exists(os.path.join(tmp, "agent_ocr.jsonl")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "ocr_last.json")))

    def test_get_by_id_y_context(self):
        from core.agent import ocr_store

        with tempfile.TemporaryDirectory() as tmp:
            e1 = self._save(tmp, "TOTAL 12.50")
            block = ocr_store.context_block(tmp, 2)
            self.assertIn("[OCR reciente", block)
            self.assertIn("TOTAL 12.50", block)
            got = ocr_store.get_by_id(e1["id"][:6], repo_root=tmp)
            self.assertEqual(got["id"], e1["id"])
            self.assertEqual(ocr_store.get_by_id("zzzz", repo_root=tmp), {})
            self.assertEqual(ocr_store.context_block(tmp, 0), "")

    def test_no_guarda_error_ni_vacio(self):
        from core.agent import ocr_store

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ocr_store.save_ocr({"status": "error"}, repo_root=tmp), {})
            self.assertEqual(ocr_store.save_ocr(
                {"status": "ok", "output": "(sin texto detectable en la imagen)"},
                repo_root=tmp), {})


class TestQueryOcr(unittest.TestCase):
    def test_por_id_y_ultima(self):
        from core.agent import ocr_store

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                execute_tool("query_ocr", {}, _ctx(tmp))["error_code"], "OCR_EMPTY")
            e1 = ocr_store.save_ocr(
                {"status": "ok", "output": "TOTAL 99", "path": "a.png",
                 "engine": "mock", "lines": 1}, repo_root=tmp)
            r = execute_tool("query_ocr", {}, _ctx(tmp))
            self.assertEqual(r["status"], "ok")
            self.assertIn("TOTAL 99", r["output"])
            r2 = execute_tool("query_ocr", {"ocr_id": e1["id"]}, _ctx(tmp))
            self.assertEqual(r2["ocr_id"], e1["id"])
            self.assertEqual(
                execute_tool("query_ocr", {"ocr_id": "abcd1234"}, _ctx(tmp))["error_code"],
                "OCR_NOT_FOUND")

    def test_last_n(self):
        from core.agent import ocr_store

        with tempfile.TemporaryDirectory() as tmp:
            for t in ("UNO", "DOS"):
                ocr_store.save_ocr(
                    {"status": "ok", "output": t, "path": "a.png",
                     "engine": "mock", "lines": 1}, repo_root=tmp)
            r = execute_tool("query_ocr", {"last_n": 2}, _ctx(tmp))
            self.assertEqual(r["status"], "ok")
            self.assertEqual(r["total"], 2)


class TestOcrContextInjection(unittest.TestCase):
    def test_run_turn_inyecta_bloque(self):
        import sys as _sys
        import types as _types

        qtcore = _types.ModuleType("PyQt6.QtCore")
        qtcore.QThread = object
        qtcore.pyqtSignal = lambda *a, **k: object()
        qt = _types.ModuleType("PyQt6")
        qt.QtCore = qtcore
        _sys.modules.setdefault("PyQt6", qt)
        _sys.modules.setdefault("PyQt6.QtCore", qtcore)
        from core.agent import ocr_store
        from core.agent.loop import run_turn

        class FakeOllama:
            def __init__(self):
                self.timeout_s = 120
                self.seen = None

            def chat(self, messages, tools):
                self.seen = list(messages)
                return {"role": "assistant", "content": "ok"}

        with tempfile.TemporaryDirectory() as tmp:
            ocr_store.save_ocr(
                {"status": "ok", "output": "TOTAL 12.50", "path": "f.png",
                 "engine": "mock", "lines": 1}, repo_root=tmp)
            fake = FakeOllama()
            reply, _ = run_turn("cuanto es el total?",
                                [], fake, {"repo_root": tmp, "model": "t"},
                                decide=lambda p: ("approve", None))
            self.assertEqual(reply, "ok")
            systems = [m for m in fake.seen if m.get("role") == "system"]
            self.assertTrue(any("[OCR reciente" in m.get("content", "") for m in systems))
            self.assertTrue(any("TOTAL 12.50" in m.get("content", "") for m in systems))


if __name__ == "__main__":
    unittest.main()
