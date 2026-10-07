"""Testes para agregação e geração da lista de compras."""

import unittest
from pathlib import Path
from src.recipe_parser import carregar_todas_receitas
from src.planner import gerar_plano
from src.shopping_list import GeradorListaCompras, ItemCompraAgregado, simplificar_nome_ingrediente


class TestShoppingList(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalogo = carregar_todas_receitas(Path("recipes"))
        cls.gerador = GeradorListaCompras(cls.catalogo)

    def test_simplificar_nome(self):
        self.assertEqual(simplificar_nome_ingrediente("cebolas médias, picadas"), "Cebola")
        self.assertEqual(simplificar_nome_ingrediente("dentes de alho, picados"), "Alho")
        self.assertEqual(simplificar_nome_ingrediente("batatas doces médias, cortadas em rodelas"), "Batata doce")
        self.assertEqual(simplificar_nome_ingrediente("pequeno de salsa fresca"), "Salsa fresca")

    def test_conversao_unidades_compatíveis(self):
        item = ItemCompraAgregado(
            nome="Peito de frango",
            quantidade=500.0,
            unidade="g",
            categoria="Talho e Aves"
        )
        # Adicionar 1 kg (deve somar 1000 g)
        item.adicionar(quantidade=1.0, unidade="kg", receita_titulo="Receita A")
        self.assertEqual(item.quantidade, 1500.0)
        # Formatar quantidade deve converter para 1.5 kg
        self.assertEqual(item.formatar_quantidade(), "1.5 kg")

    def test_gerar_e_exportar_markdown(self):
        plano = gerar_plano(
            self.catalogo,
            dias=2,
            pessoas=2,
            escolhas_manuais=[("bacalhau", 4)],
            preencher_aleatorio=False
        )
        md = self.gerador.exportar_markdown(plano)
        self.assertIn("# 🛒 Lista de Compras e Plano de Refeições", md)
        self.assertIn("Bacalhau à Brás", md)
        self.assertIn("📍 Peixaria", md)
        self.assertIn("📍 Frutas e Legumes", md)
        self.assertIn("📍 Lacticínios e Ovos", md)
        # 4 refeições * 2 pessoas = 8 doses. Receita base tem 400g de bacalhau -> 800g
        self.assertIn("800 g de Bacalhau desfiado demolhado", md)
        # 6 ovos na receita base * 2x = 12 ovos
        self.assertIn("12 unidades de Ovo", md)


if __name__ == "__main__":
    unittest.main()
