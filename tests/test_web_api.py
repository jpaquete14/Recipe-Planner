"""Testes de integração para a API do servidor web."""

import json
import threading
import time
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer
from app import RecipeHandler, iniciar_servidor


class TestWebApi(unittest.TestCase):
    servidor = None
    thread = None
    porta = 8899
    base_url = f"http://127.0.0.1:{porta}"

    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("127.0.0.1", cls.porta), RecipeHandler)
        cls.thread = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        if cls.servidor:
            cls.servidor.shutdown()
            cls.servidor.server_close()

    def test_get_index_html(self):
        req = urllib.request.urlopen(f"{self.base_url}/")
        self.assertEqual(req.status, 200)
        conteudo = req.read().decode("utf-8")
        self.assertIn("Recipe Planner", conteudo)

    def test_get_api_receitas(self):
        req = urllib.request.urlopen(f"{self.base_url}/api/receitas")
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertTrue(data.get("sucesso"))
        self.assertGreaterEqual(len(data.get("receitas", [])), 8)

    def test_get_api_receita_detalhes(self):
        req = urllib.request.urlopen(f"{self.base_url}/api/receitas/bacalhau_a_bras")
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertTrue(data.get("sucesso"))
        rec = data.get("receita")
        self.assertIn("Bacalhau", rec.get("titulo"))
        self.assertEqual(rec.get("doses"), 4)

    def test_post_planear_e_trocar(self):
        # 1. Planear para 2 dias, 2 pessoas com 1 prato (4 refeições)
        payload = json.dumps({
            "dias": 2,
            "pessoas": 2,
            "refeicoes_dia": 2,
            "escolhas": [{"receita_id": "bacalhau_a_bras", "refeicoes": 4}],
            "preencher_aleatorio": False
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/planear",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode("utf-8"))
        self.assertTrue(data.get("sucesso"))
        plano = data.get("plano")
        self.assertEqual(len(plano["itens"]), 1)
        self.assertEqual(plano["itens"][0]["doses_necessarias"], 8)

        # 2. Trocar prato
        payload_troca = json.dumps({
            "remover": "bacalhau_a_bras",
            "adicionar": "frango_com_caril"
        }).encode("utf-8")

        req_troca = urllib.request.Request(
            f"{self.base_url}/api/trocar",
            data=payload_troca,
            headers={"Content-Type": "application/json"}
        )
        res_troca = urllib.request.urlopen(req_troca)
        self.assertEqual(res_troca.status, 200)
        data_troca = json.loads(res_troca.read().decode("utf-8"))
        self.assertTrue(data_troca.get("sucesso"))
        self.assertEqual(data_troca["plano"]["itens"][0]["receita_id"], "frango_com_caril")


if __name__ == "__main__":
    unittest.main()
