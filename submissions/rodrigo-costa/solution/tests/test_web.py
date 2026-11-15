"""Testes da interface: o servidor entrega o index.html e todo arquivo que ele puxa, seguindo os imports dos
módulos JS (estáticos e dinâmicos). Quando o jsc do macOS existe, confere também a sintaxe de cada módulo."""
from __future__ import annotations

import http.client
import json
import os
import posixpath
import re
import shutil
import subprocess
import threading
import unittest
from html.parser import HTMLParser
from urllib.parse import urlparse

import server

WEB_DIR = server.WEB_DIR
JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
EXPECTED_TYPES = {".js": "text/javascript", ".css": "text/css", ".html": "text/html"}

STATIC_IMPORT = re.compile(r"""^\s*(?:import|export)\b[^'"`;(=]*?\bfrom\s*['"]([^'"]+)['"]|^\s*import\s*['"]([^'"]+)['"]""", re.M)
DYNAMIC_IMPORT = re.compile(r"""\bimport\(\s*(['"`])(.+?)\1""")
ROUTE_MODULE = re.compile(r"""\bmodule:\s*['"]([\w-]+)['"]""")


class _IndexRefs(HTMLParser):
    """Coleta os arquivos locais que o index.html carrega (folhas de estilo, módulos e pré-carga)."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "link" and a.get("rel") in ("stylesheet", "modulepreload"):
            self.refs.append(a.get("href") or "")
        elif tag == "script" and a.get("src"):
            self.refs.append(a["src"])


def _is_local(ref: str) -> bool:
    parsed = urlparse(ref)
    return not parsed.scheme and not parsed.netloc and not ref.startswith("data:")


def _join(base_path: str, ref: str) -> str:
    """Resolve `ref` relativo ao caminho publicado `base_path` ("/assets/js/app.js")."""
    if ref.startswith("/"):
        return posixpath.normpath(ref)
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_path), ref))


def _js_refs(path: str, source: str) -> list[str]:
    """Imports de um módulo. Import dinâmico com template (`./views/${nome}.js`) vira um caminho por nome
    de módulo declarado no próprio arquivo (as rotas: `module: 'foco'`)."""
    refs = [a or b for a, b in STATIC_IMPORT.findall(source)]
    for quote, spec in DYNAMIC_IMPORT.findall(source):
        if quote != "`" or "${" not in spec:
            refs.append(spec)
            continue
        prefix = spec.split("${", 1)[0]
        suffix = re.match(r"\.\w+", spec.split("}", 1)[1]).group(0)
        names = ROUTE_MODULE.findall(source)
        if not names:
            raise AssertionError(f"{path}: import dinâmico {spec!r} sem nomes de módulo para resolver")
        refs.extend(f"{prefix}{name}{suffix}" for name in names)
    return [_join(path, ref) for ref in refs]


class WebCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = server.LeadScorerServer(("127.0.0.1", 0), web_dir=WEB_DIR, quiet=True)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path: str):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        try:
            conn.request("GET", path)
            resp = conn.getresponse()
            return resp.status, (resp.getheader("Content-Type") or ""), resp.read()
        finally:
            conn.close()

    def crawl(self) -> dict[str, bytes]:
        """Baixa o index.html e segue tudo o que ele puxa. Devolve {caminho publicado: corpo}."""
        status, _, body = self.get("/")
        self.assertEqual(status, 200)
        parser = _IndexRefs()
        parser.feed(body.decode("utf-8"))
        queue = [_join("/index.html", ref) for ref in parser.refs if _is_local(ref)]
        seen: dict[str, bytes] = {}
        while queue:
            path = queue.pop()
            if path in seen:
                continue
            status, ctype, content = self.get(path)
            with self.subTest(arquivo=path):
                self.assertEqual(status, 200, f"{path} respondeu {status}")
                expected = EXPECTED_TYPES.get(posixpath.splitext(path)[1])
                if expected:
                    self.assertTrue(ctype.startswith(expected), f"{path} veio como {ctype!r}")
            seen[path] = content
            if status == 200 and path.endswith(".js"):
                queue.extend(_js_refs(path, content.decode("utf-8")))
        return seen

    def test_root_serves_index(self):
        status, ctype, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertTrue(ctype.startswith("text/html"))
        with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
            self.assertEqual(body, f.read())

    def test_every_referenced_file_is_served(self):
        files = self.crawl()
        self.assertIn("/assets/js/app.js", files)
        self.assertTrue(any(path.endswith(".css") for path in files))
        # Toda tela em views/ é alcançável pelas rotas do app.js (nenhum módulo esquecido).
        views_dir = os.path.join(WEB_DIR, "assets", "js", "views")
        for name in sorted(os.listdir(views_dir)):
            if name.endswith(".js"):
                self.assertIn(f"/assets/js/views/{name}", files, f"views/{name} não é carregada por nenhuma rota")

    def test_every_web_file_is_reachable(self):
        files = self.crawl()
        for folder, _, names in os.walk(os.path.join(WEB_DIR, "assets")):
            for name in names:
                if name.endswith((".js", ".css")):
                    published = "/" + os.path.relpath(os.path.join(folder, name), WEB_DIR).replace(os.sep, "/")
                    self.assertIn(published, files, f"{published} existe, mas nada o carrega")

    def test_no_leftovers_in_source(self):
        for folder, _, names in os.walk(os.path.join(WEB_DIR, "assets")):
            for name in names:
                path = os.path.join(folder, name)
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                with self.subTest(arquivo=name):
                    self.assertNotRegex(text, r"\bconsole\.(log|debug|info)\(|\bdebugger\b|\bTODO\b|\bFIXME\b")
                    if name.endswith(".css") and name != "tokens.css":
                        self.assertNotRegex(text, r"#[0-9a-fA-F]{3,8}\b|\brgba?\(", "cor fora dos tokens")

    @unittest.skipUnless(os.access(JSC, os.X_OK) or shutil.which("jsc"), "jsc não existe nesta máquina")
    def test_js_syntax(self):
        jsc = JSC if os.access(JSC, os.X_OK) else shutil.which("jsc")
        for folder, _, names in os.walk(os.path.join(WEB_DIR, "assets", "js")):
            for name in sorted(names):
                if not name.endswith(".js"):
                    continue
                path = os.path.abspath(os.path.join(folder, name))
                script = f"try {{ checkModuleSyntax(readFile({json.dumps(path)})); print('ok') }} catch (e) {{ print(String(e)) }}"
                out = subprocess.run([jsc, "-e", script], capture_output=True, text=True, timeout=60)
                with self.subTest(arquivo=name):
                    self.assertEqual(out.stdout.strip(), "ok", out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
