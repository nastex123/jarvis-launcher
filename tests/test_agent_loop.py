"""Suite C — Loop con Ollama mockeado (TEST-agente.md, casos C1–C8)."""

import unittest

from core.agent import run_turn
from core.agent.ollama import ModelMissing, OllamaOffline


class FakeOllama:
    def __init__(self, script):
        self.script = list(script)
        self.timeout_s = 120
        self.calls = 0

    def chat(self, messages, tools):
        self.calls += 1
        return self.script.pop(0)


def _ctx():
    return {"repo_root": "/tmp", "model": "test"}


def _approve(_proposal):
    return ("approve", None)


def _call(name, args, cid="c1"):
    return {"id": cid, "function": {"name": name, "arguments": args}}


class TestLoop(unittest.TestCase):
    def test_c1_respuesta_directa(self):
        fake = FakeOllama([{"role": "assistant", "content": "hola"}])
        reply, hist = run_turn("hi", [], fake, _ctx(), decide=_approve)
        self.assertEqual(reply, "hola")
        self.assertEqual(fake.calls, 1)
        self.assertEqual(hist[0]["role"], "system")

    def test_c2_tool_aprobada(self):
        fake = FakeOllama([
            {"role": "assistant", "content": "",
             "tool_calls": [_call("run_shell", {"cmd": "echo ok"})]},
            {"role": "assistant", "content": "hecho"},
        ])
        events = []
        reply, hist = run_turn("x", [], fake, _ctx(), decide=_approve,
                               on_event=events.append)
        self.assertEqual(reply, "hecho")
        self.assertIn('"status": "ok"', hist[3]["content"])
        self.assertIn("[stdout]", hist[3]["content"])
        kinds = [e["evento"] for e in events]
        self.assertEqual(kinds, ["propuesta", "decision", "resultado"])

    def test_c3_rechazo_reformula(self):
        fake = FakeOllama([
            {"role": "assistant", "content": "",
             "tool_calls": [_call("run_shell", {"cmd": "ls"})]},
            {"role": "assistant", "content": "desisto con elegancia"},
        ])
        reply, hist = run_turn("x", [], fake, _ctx(),
                               decide=lambda p: ("reject", None))
        self.assertEqual(reply, "desisto con elegancia")
        self.assertIn("denied_by_user", hist[3]["content"])

    def test_c4_segunda_omitida(self):
        fake = FakeOllama([
            {"role": "assistant", "content": "", "tool_calls": [
                _call("run_shell", {"cmd": "ls"}, "c1"),
                _call("run_shell", {"cmd": "pwd"}, "c2")]},
            {"role": "assistant", "content": "fin"},
        ])
        reply, hist = run_turn("x", [], fake, _ctx(),
                               decide=lambda p: ("reject", None))
        tool_msgs = [m for m in hist if m.get("role") == "tool"]
        self.assertIn("denied_by_user", tool_msgs[0]["content"])
        self.assertIn("SKIPPED", tool_msgs[1]["content"])
        self.assertEqual(reply, "fin")

    def test_c5_schema_invalido(self):
        fake = FakeOllama([
            {"role": "assistant", "content": "",
             "tool_calls": [_call("read_file", {"mal": 1})]},
            {"role": "assistant", "content": "entendido"},
        ])
        reply, hist = run_turn("x", [], fake, _ctx(), decide=_approve)
        self.assertIn("INVALID_ARGS", hist[3]["content"])

    def test_c6_max_steps(self):
        script = [{"role": "assistant", "content": "",
                   "tool_calls": [_call("list_dir", {})]} for _ in range(12)]
        fake = FakeOllama(script)
        reply, _ = run_turn("x", [], fake, _ctx(), decide=_approve, max_steps=3)
        self.assertIn("límite de pasos", reply)
        self.assertEqual(fake.calls, 3)

    def test_c7_offline(self):
        class Down:
            timeout_s = 120

            def chat(self, messages, tools):
                raise OllamaOffline("caído")

        with self.assertRaises(OllamaOffline):
            run_turn("x", [], Down(), _ctx(), decide=_approve)

    def test_c8_bloqueo_politica(self):
        blocked = []
        fake = FakeOllama([
            {"role": "assistant", "content": "",
             "tool_calls": [_call("run_shell", {"cmd": "rm -rf /"})]},
            {"role": "assistant", "content": "ok"},
        ])
        reply, hist = run_turn("x", [], fake, _ctx(), decide=_approve,
                               on_blocked=blocked.append)
        self.assertEqual(len(blocked), 1)
        self.assertIn("DENIED_BY_POLICY", hist[3]["content"])
        self.assertEqual(reply, "ok")


    def test_c9_fallback_json_en_texto(self):
        from core.agent.loop import _extract_json_calls

        text = '{\n  "name": "list_dir",\n  "arguments": {"path": "."}\n}'
        calls = _extract_json_calls(text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["name"], "list_dir")
        self.assertEqual(_extract_json_calls("hola mundo"), [])
        fenced = 'claro:\n```json\n{"name": "search", "arguments": {"pattern": "x"}}\n```'
        self.assertEqual(_extract_json_calls(fenced)[0]["function"]["name"], "search")
        # Turno completo vía fallback
        fake = FakeOllama([
            {"role": "assistant", "content": text},
            {"role": "assistant", "content": "listo"},
        ])
        reply, hist = run_turn("x", [], fake, _ctx(), decide=_approve)
        self.assertEqual(reply, "listo")
        self.assertTrue(any(m.get("role") == "tool" for m in hist))


    def test_c10_fabricacion_se_corrige(self):
        from core.agent.loop import looks_fabricated

        self.assertTrue(looks_fabricated("<tool_result>\n{}\n</tool_result>"))
        self.assertFalse(looks_fabricated("Tienes 4 GB libres."))
        fake = FakeOllama([
            {"role": "assistant",
             "content": "<tool_result>\n{\"free_memory\": \"16 GB\"}\n</tool_result>"},
            {"role": "assistant", "content": "No tengo el dato aún."},
        ])
        events = []
        reply, hist = run_turn("ram?", [], fake, _ctx(), decide=_approve,
                               on_event=events.append)
        kinds = [e["evento"] for e in events]
        self.assertIn("fabricacion_detectada", kinds)
        self.assertEqual(reply, "No tengo el dato aún.")
        # El bloque fabricado nunca sale como respuesta final
        self.assertNotIn("<tool_result>", reply)

    def test_c12_json_embebido_en_disculpa(self):
        from core.agent.loop import _extract_json_calls

        mixed = ('Perdón, aquí va: {"name": "get_system_info", "arguments": {}} '
                 'espero que sirva.')
        calls = _extract_json_calls(mixed)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["name"], "get_system_info")
        # JSON con tool inexistente se ignora (no es llamada)
        self.assertEqual(
            _extract_json_calls('{"name": "hackear", "arguments": {}}'), [])
        # Turno: disculpa + JSON embebido → se ejecuta sin re-pregunta
        fake = FakeOllama([
            {"role": "assistant", "content": mixed},
            {"role": "assistant", "content": "listo con datos reales"},
        ])
        reply, hist = run_turn("ram?", [], fake, _ctx(), decide=_approve)
        self.assertEqual(reply, "listo con datos reales")
        self.assertTrue(any(m.get("role") == "tool" for m in hist))

    def test_c13_correccion_lleva_a_llamada(self):
        fab = {"role": "assistant",
               "content": "<tool_result>\n{\"x\": 1}\n</tool_result>"}
        good = {"role": "assistant",
                "content": '{"name": "list_dir", "arguments": {"path": "."}}'}
        done = {"role": "assistant", "content": "ahí van los archivos"}
        fake = FakeOllama([dict(fab), dict(good), dict(done)])
        reply, hist = run_turn("lista", [], fake, _ctx(), decide=_approve)
        self.assertEqual(reply, "ahí van los archivos")
        self.assertTrue(any(m.get("role") == "tool" for m in hist))

    def test_c11_fabricacion_agotada(self):
        fab = {"role": "assistant",
               "content": "<tool_result>\n{\"x\": 1}\n</tool_result>"}
        fake = FakeOllama([dict(fab) for _ in range(5)])
        reply, _ = run_turn("x", [], fake, _ctx(), decide=_approve)
        self.assertNotIn("<tool_result>", reply)
        self.assertIn("formato correcto", reply)


if __name__ == "__main__":
    unittest.main()
