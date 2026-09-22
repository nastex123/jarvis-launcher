"""Suite A — Tools contra FS temporal (TEST-agente.md, casos A1–A10)."""

import os
import tempfile
import unittest

from core.agent.tools import MAX_FILE_BYTES, TOOLS, execute_tool, ollama_tools


def _ctx(root):
    return {"repo_root": root, "model": "test-model"}


class TestReadFile(unittest.TestCase):
    def test_a1_ok_y_recorte(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "a.txt")
            with open(p, "w") as fh:
                fh.write("0123456789")
            r = execute_tool("read_file", {"path": "a.txt", "max_chars": 4}, _ctx(tmp))
            self.assertEqual(r["status"], "ok")
            self.assertEqual(r["output"], "0123")
            self.assertTrue(r["truncated"])

    def test_a2_errores(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                execute_tool("read_file", {"path": "no.txt"}, _ctx(tmp))["error_code"],
                "FILE_NOT_FOUND",
            )
            os.mkdir(os.path.join(tmp, "d"))
            self.assertEqual(
                execute_tool("read_file", {"path": "d"}, _ctx(tmp))["error_code"],
                "NOT_A_FILE",
            )
            bp = os.path.join(tmp, "b.bin")
            with open(bp, "wb") as fh:
                fh.write(b"\x00\x01\x02")
            self.assertEqual(
                execute_tool("read_file", {"path": "b.bin"}, _ctx(tmp))["error_code"],
                "BINARY_FILE",
            )


class TestListDir(unittest.TestCase):
    def test_a3_orden_y_glob(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.mkdir(os.path.join(tmp, "sub"))
            open(os.path.join(tmp, "z.py"), "w").close()
            open(os.path.join(tmp, "a.txt"), "w").close()
            r = execute_tool("list_dir", {"path": "."}, _ctx(tmp))
            self.assertEqual(r["status"], "ok")
            self.assertEqual(r["output"][0]["name"], "sub")
            r2 = execute_tool("list_dir", {"path": ".", "glob": "*.py"}, _ctx(tmp))
            self.assertEqual([e["name"] for e in r2["output"]], ["z.py"])
            self.assertEqual(
                execute_tool("list_dir", {"path": "no"}, _ctx(tmp))["error_code"],
                "DIR_NOT_FOUND",
            )


class TestSearch(unittest.TestCase):
    def test_a4_hits_y_regex_mala(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "m.py"), "w") as fh:
                fh.write("hola mundo\notra linea\n")
            r = execute_tool("search", {"pattern": "mundo"}, _ctx(tmp))
            self.assertEqual(r["status"], "ok")
            self.assertEqual(len(r["output"]), 1)
            self.assertEqual(r["output"][0]["line"], 1)
            bad = execute_tool("search", {"pattern": "(["}, _ctx(tmp))
            self.assertEqual(bad["error_code"], "BAD_REGEX")


class TestWriteEdit(unittest.TestCase):
    def test_a5_write_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = execute_tool(
                "write_file", {"path": "nuevo/x.txt", "content": "hola\n"}, _ctx(tmp))
            self.assertEqual(r["status"], "ok")
            self.assertTrue(r["created"])
            r2 = execute_tool(
                "write_file", {"path": "nuevo/x.txt", "content": "adios\n"}, _ctx(tmp))
            self.assertFalse(r2["created"])
            with open(os.path.join(tmp, "nuevo", "x.txt.bak")) as fh:
                self.assertEqual(fh.read(), "hola\n")

    def test_a6_contenido_grande(self):
        with tempfile.TemporaryDirectory() as tmp:
            big = "x" * (MAX_FILE_BYTES + 1)
            # write_file usa tope 1 MB (más estricto que lectura 10 MB)
            r = execute_tool("write_file", {"path": "b.txt", "content": big}, _ctx(tmp))
            self.assertEqual(r["error_code"], "CONTENT_TOO_LARGE")
            self.assertFalse(os.path.exists(os.path.join(tmp, "b.txt")))

    def test_a7_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "e.txt")
            with open(p, "w") as fh:
                fh.write("uno\ndos\n")
            ok = execute_tool(
                "edit_file", {"path": "e.txt", "old": "dos", "new": "DOS"}, _ctx(tmp))
            self.assertEqual(ok["status"], "ok")
            with open(p) as fh:
                self.assertIn("DOS", fh.read())
            missing = execute_tool(
                "edit_file", {"path": "e.txt", "old": "zzz", "new": "q"}, _ctx(tmp))
            self.assertEqual(missing["error_code"], "OLD_NOT_FOUND")
            with open(p, "w") as fh:
                fh.write("a a a")
            dup = execute_tool(
                "edit_file", {"path": "e.txt", "old": "a", "new": "b"}, _ctx(tmp))
            self.assertEqual(dup["error_code"], "OLD_NOT_UNIQUE")


class TestShell(unittest.TestCase):
    def test_a8_ok_error_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok = execute_tool("run_shell", {"cmd": "echo hola"}, _ctx(tmp))
            self.assertEqual(ok["status"], "ok")
            self.assertIn("hola", ok["output"])
            bad = execute_tool("run_shell", {"cmd": "exit 3"}, _ctx(tmp))
            self.assertEqual(bad["error_code"], "NONZERO_EXIT")
            slow = execute_tool(
                "run_shell", {"cmd": "sleep 30", "timeout_s": 1}, _ctx(tmp))
            self.assertEqual(slow["error_code"], "TIMEOUT")


class TestAppsInfo(unittest.TestCase):
    def test_a9_app_inexistente(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = execute_tool("open_app", {"name": "app-que-no-existe-xyz"}, _ctx(tmp))
            self.assertEqual(r["error_code"], "APP_NOT_FOUND")
            self.assertIn("suggestions", r)

    def test_a10_system_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = execute_tool("get_system_info", {}, _ctx(tmp))
            self.assertEqual(r["status"], "ok")
            for key in ("os", "cpu_count", "ram_total", "ram_free",
                        "disk_free_repo", "ollama_model", "app_version"):
                self.assertIn(key, r["output"])


class TestCatalogo(unittest.TestCase):
    def test_nueve_tools_y_schemas_json(self):
        import json

        self.assertEqual(len(TOOLS), 9)
        json.dumps(ollama_tools())  # debe serializar
        names = [t.name for t in TOOLS]
        for expected in ("read_file", "list_dir", "search", "write_file",
                         "edit_file", "run_shell", "open_app", "list_apps",
                         "get_system_info"):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
