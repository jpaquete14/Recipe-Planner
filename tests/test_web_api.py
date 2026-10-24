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

    def test_criar_e_editar_receita(self):
        from pathlib import Path
        pasta_rec = Path(__file__).parent.parent / "recipes"

        # 1. Criar receita de teste
        payload_nova = json.dumps({
            "titulo": "Omolete Especial de Ervas",
            "doses": 2,
            "tempo_preparacao": "5 min",
            "tempo_cozedura": "5 min",
            "categoria": "Rápido, Ovos",
            "dificuldade": "Muito Fácil",
            "ingredientes": "- 4 unidades de ovos [Lacticínios e Ovos]\n- 1 c. de sopa de azeite [Azeites e Óleos]",
            "instrucoes": "1. Bater os ovos.\n2. Cozinhar na frigideira com azeite.",
            "notas": "- Servir quente."
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/receitas",
            data=payload_nova,
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode("utf-8"))
        self.assertTrue(data.get("sucesso"))
        rec_id = data.get("id")
        ficheiro_criado = pasta_rec / f"{rec_id}.txt"

        try:
            # 2. Obter detalhes e verificar campos brutos
            req_get = urllib.request.urlopen(f"{self.base_url}/api/receitas/{rec_id}")
            self.assertEqual(req_get.status, 200)
            data_get = json.loads(req_get.read().decode("utf-8"))
            self.assertTrue(data_get.get("sucesso"))
            rec = data_get.get("receita")
            self.assertEqual(rec["doses"], 2)
            self.assertIn("ovos", rec["ingredientes_bruto"].lower())

            # 3. Editar receita via PUT (aumentar para 4 doses e mudar título)
            payload_edit = json.dumps({
                "titulo": "Omolete Especial de Queijo e Ervas",
                "doses": 4,
                "tempo_preparacao": "10 min",
                "tempo_cozedura": "8 min",
                "categoria": "Rápido, Ovos",
                "dificuldade": "Fácil",
                "ingredientes": "- 6 unidades de ovos [Lacticínios e Ovos]\n- 50 g de queijo ralado [Lacticínios e Ovos]\n- 1 c. de sopa de azeite [Azeites e Óleos]",
                "instrucoes": "1. Bater os ovos com o queijo.\n2. Cozinhar na frigideira com azeite.",
                "notas": "- Pode juntar orégãos."
            }).encode("utf-8")

            req_put = urllib.request.Request(
                f"{self.base_url}/api/receitas/{rec_id}",
                data=payload_edit,
                headers={"Content-Type": "application/json"},
                method="PUT"
            )
            res_put = urllib.request.urlopen(req_put)
            self.assertEqual(res_put.status, 200)
            data_put = json.loads(res_put.read().decode("utf-8"))
            self.assertTrue(data_put.get("sucesso"))

            novo_id = data_put.get("id")
            ficheiro_atualizado = pasta_rec / f"{novo_id}.txt"

            # 4. Verificar se a receita foi atualizada
            req_get_edit = urllib.request.urlopen(f"{self.base_url}/api/receitas/{novo_id}")
            self.assertEqual(req_get_edit.status, 200)
            data_get_edit = json.loads(req_get_edit.read().decode("utf-8"))
            rec_editada = data_get_edit.get("receita")
            self.assertEqual(rec_editada["titulo"], "Omolete Especial de Queijo e Ervas")
            self.assertEqual(rec_editada["doses"], 4)
            self.assertIn("queijo", rec_editada["ingredientes_bruto"].lower())

        finally:
            # Limpeza do ficheiro de teste
            if ficheiro_criado.exists():
                ficheiro_criado.unlink()
            ficheiro_atualizado = pasta_rec / "omolete_especial_de_queijo_e_ervas.txt"
            if ficheiro_atualizado.exists():
                ficheiro_atualizado.unlink()

    def test_editar_receita_atualiza_plano_ativo(self):
        from pathlib import Path
        pasta_rec = Path(__file__).parent.parent / "recipes"

        # 1. Criar receita temporária
        payload_nova = json.dumps({
            "titulo": "Sopa de Legumes da Aldeia",
            "doses": 4,
            "tempo_preparacao": "10 min",
            "tempo_cozedura": "25 min",
            "categoria": "Sopas, Saudável",
            "dificuldade": "Fácil",
            "ingredientes": "- 400 g de abóbora [Frutas e Legumes]\n- 1 unidade de cebola média [Frutas e Legumes]",
            "instrucoes": "1. Cozer legumes e triturar.",
            "notas": ""
        }).encode("utf-8")

        req = urllib.request.Request(f"{self.base_url}/api/receitas", data=payload_nova, headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode("utf-8"))
        rec_id = data.get("id")

        try:
            # 2. Criar plano usando esta receita
            payload_plano = json.dumps({
                "dias": 2,
                "pessoas": 2,
                "refeicoes_dia": 1,
                "escolhas": [{"receita_id": rec_id, "refeicoes": 2}],
                "preencher_aleatorio": False
            }).encode("utf-8")

            req_p = urllib.request.Request(f"{self.base_url}/api/planear", data=payload_plano, headers={"Content-Type": "application/json"})
            res_p = urllib.request.urlopen(req_p)
            data_p = json.loads(res_p.read().decode("utf-8"))
            # 2 pessoas * 2 refeições = 4 doses necessárias. Doses base: 4 -> fator escala: 1.0
            self.assertEqual(data_p["plano"]["itens"][0]["fator_escala"], 1.0)

            # 3. Editar a receita, alterando doses_base para 2 (duplica o fator de escala no plano para 2.0)
            payload_edit = json.dumps({
                "titulo": "Sopa de Legumes da Aldeia",
                "doses": 2,
                "tempo_preparacao": "10 min",
                "tempo_cozedura": "25 min",
                "categoria": "Sopas, Saudável",
                "dificuldade": "Fácil",
                "ingredientes": "- 400 g de abóbora [Frutas e Legumes]\n- 1 unidade de cebola média [Frutas e Legumes]",
                "instrucoes": "1. Cozer legumes e triturar.",
                "notas": ""
            }).encode("utf-8")

            req_edit = urllib.request.Request(f"{self.base_url}/api/receitas/{rec_id}", data=payload_edit, headers={"Content-Type": "application/json"}, method="PUT")
            res_edit = urllib.request.urlopen(req_edit)
            data_edit = json.loads(res_edit.read().decode("utf-8"))
            self.assertTrue(data_edit["sucesso"])

            # 4. Verificar se o endpoint GET /api/plano reflete a nova escala
            req_plano_atual = urllib.request.urlopen(f"{self.base_url}/api/plano")
            data_plano_atual = json.loads(req_plano_atual.read().decode("utf-8"))
            self.assertEqual(data_plano_atual["plano"]["itens"][0]["doses_base"], 2)
            self.assertEqual(data_plano_atual["plano"]["itens"][0]["fator_escala"], 2.0)

        finally:
            ficheiro = pasta_rec / f"{rec_id}.txt"
            if ficheiro.exists():
                ficheiro.unlink()

    def test_post_planear_apenas_selecionadas_escala_quantidades(self):
        # 7 dias, 2 refeicoes/dia = 14 refeições para 2 pessoas (28 doses totais)
        # Escolhas com 1 refeição cada -> devem escalar para 7 refeições (14 doses) cada
        payload = json.dumps({
            "dias": 7,
            "pessoas": 2,
            "refeicoes_dia": 2,
            "escolhas": [
                {"receita_id": "bacalhau_a_bras", "refeicoes": 1},
                {"receita_id": "frango_com_caril", "refeicoes": 1}
            ],
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
        self.assertEqual(plano["total_refeicoes_alvo"], 14)
        self.assertEqual(len(plano["itens"]), 2)
        total_refeicoes = sum(item["refeicoes_cobertas"] for item in plano["itens"])
        self.assertEqual(total_refeicoes, 14)

        for item in plano["itens"]:
            self.assertEqual(item["refeicoes_cobertas"], 7)
            self.assertEqual(item["doses_necessarias"], 14)

    def test_post_planear_com_refeicoes_diferentes(self):
        # 7 dias, 1 pessoa, 2 refeições diferentes -> 2 receitas, 7 refeições e 7 doses cada
        payload = json.dumps({
            "dias": 7,
            "pessoas": 1,
            "refeicoes_dia": 2,
            "refeicoes_diferentes": 2
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
        self.assertEqual(plano["dias"], 7)
        self.assertEqual(plano["pessoas"], 1)
        self.assertEqual(plano["total_refeicoes_alvo"], 14)
        self.assertEqual(len(plano["itens"]), 2)
        total_refeicoes = sum(item["refeicoes_cobertas"] for item in plano["itens"])
        self.assertEqual(total_refeicoes, 14)
        for item in plano["itens"]:
            self.assertEqual(item["refeicoes_cobertas"], 7)
            self.assertEqual(item["doses_necessarias"], 7)


if __name__ == "__main__":
    unittest.main()
