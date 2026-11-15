"""Testes do servidor HTTP: sobe o servidor numa porta livre e chama cada rota."""
from __future__ import annotations

import gzip
import http.client
import json
import os
import shutil
import socket
import tempfile
import threading
import unittest
from urllib.parse import quote

import server

DANIELL_TOP10 = ["LFI3BGEE", "HF1GSBT4", "9DY57A6F", "HP9TUR60", "XZKZYO55", "IDKBZCAF", "YPSXMDRH", "D3HUUVPL",
                 "S53EVWFC", "5J7T0GZU"]


class ServerCase(unittest.TestCase):
    web_files = {"index.html": "<!doctype html><title>App</title>", "app.js": "console.log('ok');",
                 "style.css": "body{}" * 200}

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.web = os.path.join(cls.tmp, "web")
        os.mkdir(cls.web)
        for name, text in cls.web_files.items():
            with open(os.path.join(cls.web, name), "w", encoding="utf-8") as f:
                f.write(text)
        with open(os.path.join(cls.tmp, "secret.txt"), "w") as f:
            f.write("SEGREDO")
        with open(os.path.join(cls.web, ".hidden"), "w") as f:
            f.write("OCULTO")
        cls.server = server.LeadScorerServer(("127.0.0.1", 0), web_dir=cls.web, quiet=True)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.tmp)

    def request(self, path, method="GET", headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        try:
            conn.request(method, path, headers=headers or {})
            resp = conn.getresponse()
            return resp.status, {k.lower(): v for k, v in resp.getheaders()}, resp.read()
        finally:
            conn.close()

    def raw(self, data: bytes) -> bytes:
        """Manda bytes crus numa conexão e lê tudo até o servidor fechar."""
        with socket.create_connection(("127.0.0.1", self.port), timeout=10) as sock:
            sock.sendall(data)
            chunks = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        return b"".join(chunks)

    def get_json(self, path, status=200):
        code, headers, body = self.request(path)
        self.assertEqual(code, status, body[:300])
        self.assertEqual(headers["content-type"], "application/json; charset=utf-8")
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertEqual(headers["x-content-type-options"], "nosniff")
        self.assertEqual(headers["referrer-policy"], "no-referrer")
        return json.loads(body.decode("utf-8"))


class TestRoutes(ServerCase):
    def test_health(self):
        self.assertEqual(self.get_json("/health"), {"status": "ok"})

    def test_meta(self):
        data = self.get_json("/api/meta")
        self.assertEqual(data["dataset"]["deals"], 8800)
        self.assertEqual(len(data["dates"]), 26)
        self.assertEqual(data["default_date"], "2017-12-04")
        self.assertEqual(data["dataset"]["sellers_with_deals"], 30)

    def test_login(self):
        panel = self.get_json("/api/login")["panel"]
        self.assertEqual((panel["declared_value"], panel["live_value"]), (5006104, 2945683))
        self.assertEqual((panel["open_count"], panel["stale_count"]), (2078, 779))
        self.assertEqual(panel["headline_1"], "US$ 5,0 milhões em negociação.")
        self.assertEqual(panel["headline_2"], "US$ 2,9 milhões vivos.")

    def test_seller_daniell(self):
        data = self.get_json("/api/seller?name=Daniell%20Hammack&date=2017-12-04")
        s = data["summary"]
        self.assertEqual((s["open_count"], s["live_count"], s["stale_count"]), (85, 38, 47))
        self.assertEqual((s["declared_value"], s["live_value"], s["stale_value"]), (253368, 106459, 146909))
        self.assertEqual(round(s["expected_30d"]), 42162)
        self.assertEqual([x["id"] for x in data["deals"][:10]], DANIELL_TOP10)
        self.assertEqual([x["score"] for x in data["deals"][:3]], [98, 97, 96])
        self.assertEqual((data["rates"]["won"], data["rates"]["lost"]), (103, 70))
        self.assertAlmostEqual(data["rates"]["official"], 103 / 173)
        self.assertEqual(data["date"]["iso"], "2017-12-04")

    def test_seller_name_is_forgiving(self):
        data = self.get_json("/api/seller?name=" + quote("  daniell   HAMMACK "))
        self.assertEqual(data["seller"]["name"], "Daniell Hammack")

    def test_pipeline(self):
        data = self.get_json("/api/pipeline?name=Darcel%20Schlecht")
        cols = {c["key"]: c for c in data["columns"]}
        self.assertEqual(cols["prospecting"]["count"], 111)
        self.assertEqual(cols["engaging"]["count"], 118)
        self.assertEqual(cols["stale"]["count"], 0)
        for key in ("won", "lost"):
            for deal in cols[key]["deals"]:
                self.assertLess(deal["close_date"], "2017-12-04")

    def test_team(self):
        s = self.get_json("/api/team?manager=Rocco%20Neubert")["summary"]
        self.assertEqual((s["open_count"], s["live_count"], s["stale_count"], s["hot_count"]), (307, 169, 138, 55))
        self.assertEqual((s["declared_value"], s["live_value"], s["stale_value"]), (824840, 438104, 386736))
        self.assertEqual(round(s["expected_30d"]), 153815)  # soma crua; as linhas arredondadas somam 153.814
        east = self.get_json("/api/team?region=Leste")["summary"]
        self.assertEqual((east["open_count"], east["stale_count"]), (579, 291))
        company = self.get_json("/api/team")["summary"]
        self.assertEqual((company["open_count"], company["live_count"], company["stale_count"]), (2078, 1299, 779))
        self.assertEqual(round(company["expected_30d"]), 929174)

    def test_accounts(self):
        data = self.get_json("/api/accounts?region=East")
        self.assertEqual(data["count"], 27)
        first = data["accounts"][0]
        self.assertEqual((first["name"], first["closed_count"], first["won_value"]), ("Mathtouch", 75, 152556))
        self.assertEqual(self.get_json("/api/accounts")["count"], 85)

    def test_account(self):
        data = self.get_json("/api/account?name=Mathtouch&viewer=Daniell%20Hammack")
        self.assertEqual(data["account"]["revenue_label"], "US$ 3,03 bilhões")
        h = data["history"]
        self.assertEqual((h["closed_count"], h["won_count"], h["lost_count"], h["won_value"]), (75, 50, 25, 152556))
        o = data["open"]
        self.assertEqual((o["count"], o["live_count"], o["stale_count"]), (13, 10, 3))
        self.assertTrue(any(x["is_viewer"] for x in o["live"]))
        for deal in data["closed"]["deals"]:
            self.assertLess(deal["close_date"], "2017-12-04")

    def test_account_with_manager_viewer(self):
        data = self.get_json("/api/account?name=Acme%20Corporation&viewer=Rocco%20Neubert")
        managers = {m["name"]: m["team"] for m in self.get_json("/api/meta")["managers"]}
        team = set(managers["Rocco Neubert"])
        opened = data["open"]["live"] + data["open"]["stale"]
        self.assertEqual([x["is_viewer"] for x in opened], [x["seller"] in team for x in opened])
        self.assertEqual([x["is_viewer"] for x in data["closed"]["deals"]],
                         [x["seller"] in team for x in data["closed"]["deals"]])
        self.assertTrue(any(x["is_viewer"] for x in data["closed"]["deals"]))

    def test_time_machine(self):
        data = self.get_json("/api/time-machine?name=Daniell%20Hammack&date=2017-12-04")
        score = data["lists"]["score"]
        self.assertEqual([r["id"] for r in score["rows"]], DANIELL_TOP10)
        self.assertEqual((score["wins"], score["revenue"]), (5, 25687))
        self.assertEqual(data["lists"]["value_only"]["wins"], 0)
        self.assertEqual(data["window"]["days"], 27)

    def test_proof(self):
        data = self.get_json("/api/proof")
        self.assertEqual((data["n_dates"], data["n_lists"]), (22, 659))
        self.assertAlmostEqual(data["auc"]["chance"], 0.780, places=3)
        self.assertAlmostEqual(data["auc"]["expected_value"], 0.706, places=3)
        self.assertNotIn("score", data["auc"])
        self.assertAlmostEqual(data["rules"]["score"]["revenue"] / data["rules"]["value_only"]["revenue"], 1.42,
                               places=2)
        self.assertEqual(data["dates_won"]["vs_value_only"]["won"], 22)
        self.assertEqual(data["dates_won"]["vs_value_no_stale"]["won"], 20)

    def test_score_model(self):
        data = self.get_json("/api/score-model?viewer=Daniell%20Hammack")
        row = next(r for r in data["table"] if r["label"] == "61–75")
        self.assertEqual((row["y"], row["n"], row["level"]), (196, 391, "semana"))
        self.assertEqual([m["iso"] for m in data["training"]["mondays"]], ["2017-03-06", "2017-06-05", "2017-09-04"])
        self.assertEqual(data["example"]["id"], "LFI3BGEE")
        self.assertEqual(data["max_cycle"], 138)

    def test_data_quality_and_sources(self):
        data = self.get_json("/api/data-quality?date=2017-12-04")
        self.assertEqual(len(data["items"]), 5)
        self.assertEqual({r["region"]: r["stale_count"] for r in data["regions"]["rows"]},
                         {"Central": 0, "East": 291, "West": 488})
        self.assertEqual(len(self.get_json("/api/sources")["active"]["files"]), 4)

    def test_other_dates(self):
        for iso in ("2017-07-03", "2017-12-25"):
            self.assertEqual(self.get_json("/api/seller?name=Reed%20Clapper&date=" + iso)["date"]["iso"], iso)


class TestErrors(ServerCase):
    def test_bad_params(self):
        for path in ("/api/seller?name=Daniell%20Hammack&date=2017-12-05", "/api/seller?date=abc&name=Reed%20Clapper",
                     "/api/seller?name=Fulano", "/api/seller", "/api/account?name=Nada",
                     "/api/team?region=Norte", "/api/team?manager=Rocco%20Neubert&region=West",
                     "/api/time-machine?name=Rocco%20Neubert", "/api/accounts?region=xx"):
            data = self.get_json(path, status=400)
            self.assertIsInstance(data["error"], str)
            self.assertTrue(data["error"])
        self.assertIn("Data", self.get_json("/api/seller?name=Reed%20Clapper&date=2017-12-05", status=400)["error"])

    def test_dates_only_in_strict_iso(self):
        # o Python 3.11+ aceita estes formatos em date.fromisoformat; a API não
        for text in ("20171204", "2017-W49-1", "2017-12-4"):
            data = self.get_json("/api/seller?name=Reed%20Clapper&date=" + text, status=400)
            self.assertTrue(data["error"].startswith("Data inválida"), text)

    def test_seller_only_in_registry(self):
        for path in ("/api/seller?name=Carl%20Lin", "/api/pipeline?name=Carl%20Lin", "/api/team?seller=Carl%20Lin",
                     "/api/time-machine?name=Carl%20Lin", "/api/score-model?viewer=Carl%20Lin"):
            self.assertIn("só está no cadastro", self.get_json(path, status=400)["error"], path)

    def test_error_does_not_echo_huge_input(self):
        data = self.get_json("/api/seller?name=" + "A" * 20000, status=400)
        self.assertLess(len(data["error"]), 120)
        data = self.get_json("/api/" + "x" * 5000, status=404)
        self.assertLess(len(data["error"]), 120)

    def test_repeated_parameter_uses_the_last(self):
        data = self.get_json("/api/seller?name=Fulano&name=Reed%20Clapper")
        self.assertEqual(data["seller"]["name"], "Reed Clapper")

    def test_unknown_api_route(self):
        self.assertIn("error", self.get_json("/api/nada", status=404))
        self.assertIn("error", self.get_json("/api", status=404))

    def test_method_not_allowed(self):
        for method in ("POST", "PUT", "DELETE", "PATCH", "TRACE", "INVENTADO"):
            code, headers, body = self.request("/api/meta", method=method)
            self.assertEqual(code, 405, method)
            self.assertEqual(headers["allow"], "GET, HEAD")
            self.assertEqual(headers["content-type"], "application/json; charset=utf-8")
            self.assertIn("error", json.loads(body))

    def test_body_of_refused_request_does_not_leak_into_the_next(self):
        reply = self.raw(b"POST /api/meta HTTP/1.1\r\nHost: x\r\nContent-Length: 20\r\n\r\n" + b"x" * 20 +
                         b"GET /health HTTP/1.1\r\nHost: x\r\n\r\n").decode("utf-8", "replace")
        self.assertTrue(reply.startswith("HTTP/1.1 405"), reply[:80])
        self.assertIn("Connection: close", reply)
        self.assertNotIn("501", reply)
        self.assertNotIn("Unsupported", reply)

    def test_library_errors_are_json_in_portuguese(self):
        reply = self.raw(b"GET /" + b"a" * 70000 + b" HTTP/1.1\r\nHost: x\r\n\r\n").decode("utf-8", "replace")
        self.assertTrue(reply.startswith("HTTP/1.1 414"), reply[:80])
        self.assertIn('{"error":"Endereço longo demais."}', reply)
        reply = self.raw(b"GET / HTTP/9.9\r\nHost: x\r\n\r\n").decode("utf-8", "replace")
        self.assertIn('"error"', reply)
        self.assertNotIn("<html", reply.lower())

    def test_server_header_hides_python(self):
        _, headers, _ = self.request("/health")
        self.assertEqual(headers["server"], "LeadScorer/1.0")
        self.assertEqual(server.Handler.timeout, server.IDLE_TIMEOUT)

    def test_internal_value_error_is_500(self):
        original = server.ROUTES["/api/sources"]
        server.ROUTES["/api/sources"] = ((), lambda ds, p: max([]))
        try:
            import io
            import sys
            saved, sys.stderr = sys.stderr, io.StringIO()
            try:
                data = self.get_json("/api/sources", status=500)
            finally:
                sys.stderr = saved
        finally:
            server.ROUTES["/api/sources"] = original
        self.assertNotIn("max()", data["error"])

    def test_unexpected_error_is_generic(self):
        original = server.ROUTES["/api/sources"]

        def boom(ds, p):
            raise KeyError("detalhe interno")

        server.ROUTES["/api/sources"] = ((), boom)
        try:
            import io
            import sys
            saved, sys.stderr = sys.stderr, io.StringIO()
            try:
                data = self.get_json("/api/sources", status=500)
            finally:
                sys.stderr = saved
        finally:
            server.ROUTES["/api/sources"] = original
        self.assertNotIn("detalhe", data["error"])
        self.assertNotIn("Traceback", data["error"])


class TestStaticAndTransport(ServerCase):
    def test_index_and_files(self):
        code, headers, body = self.request("/")
        self.assertEqual(code, 200)
        self.assertEqual(headers["content-type"], "text/html; charset=utf-8")
        self.assertEqual(headers["cache-control"], "no-cache")
        self.assertIn(b"<title>App</title>", body)
        code, headers, body = self.request("/app.js")
        self.assertEqual(headers["content-type"], "text/javascript; charset=utf-8")
        self.assertEqual(body, b"console.log('ok');")

    def test_spa_fallback(self):
        code, headers, body = self.request("/vendedor/foco?x=1")
        self.assertEqual(code, 200)
        self.assertIn(b"<title>App</title>", body)

    def test_missing_asset_is_404(self):
        for path in ("/nao-existe.js", "/favicon.ico", "/img/logo.png"):
            code, headers, body = self.request(path)
            self.assertEqual(code, 404, path)
            self.assertNotIn(b"<title>App</title>", body)
        code, _, body = self.request("/app.js/")
        self.assertNotEqual(body, b"console.log('ok');")

    def test_traversal_is_blocked(self):
        for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/..%2fsecret.txt", "/static/../../secret.txt",
                     "/.hidden", "/%2ehidden", "/" + quote(os.path.join(self.tmp, "secret.txt"))):
            code, _, body = self.request(path)
            self.assertNotIn(b"SEGREDO", body, path)
            self.assertNotIn(b"OCULTO", body, path)

    def test_head(self):
        code, headers, body = self.request("/api/meta", method="HEAD")
        self.assertEqual(code, 200)
        self.assertEqual(body, b"")
        self.assertGreater(int(headers["content-length"]), 0)

    def test_gzip(self):
        code, headers, body = self.request("/api/meta", headers={"Accept-Encoding": "gzip, deflate"})
        self.assertEqual(headers.get("content-encoding"), "gzip")
        self.assertEqual(int(headers["content-length"]), len(body))
        self.assertEqual(json.loads(gzip.decompress(body))["dataset"]["deals"], 8800)
        code, headers, body = self.request("/api/meta", headers={"Accept-Encoding": "gzip;q=0"})
        self.assertNotIn("content-encoding", headers)
        code, headers, body = self.request("/style.css", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(headers.get("content-encoding"), "gzip")
        self.assertEqual(gzip.decompress(body).decode(), self.web_files["style.css"])
        code, headers, body = self.request("/health", headers={"Accept-Encoding": "gzip"})
        self.assertNotIn("content-encoding", headers)  # corpo pequeno vai sem compressão

    def test_utf8_without_escapes(self):
        _, _, body = self.request("/api/sources")
        self.assertIn("Integrações".encode("utf-8"), body)
        self.assertNotIn(b"\\u00", body)


class TestMissingInterface(unittest.TestCase):
    def test_missing_index_page(self):
        tmp = tempfile.mkdtemp()
        srv = server.LeadScorerServer(("127.0.0.1", 0), web_dir=tmp, quiet=True)
        thread = threading.Thread(target=srv.serve_forever, daemon=True)
        thread.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
            conn.request("GET", "/")
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            conn.close()
            self.assertEqual(resp.status, 404)
            self.assertIn("Interface não encontrada", body)
        finally:
            srv.shutdown()
            srv.server_close()
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
