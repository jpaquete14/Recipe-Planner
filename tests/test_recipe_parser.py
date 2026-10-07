"""Testes para o analisador de receitas."""

import unittest
from pathlib import Path
from src.recipe_parser import (
    parse_ingrediente,
    parse_receita_ficheiro,
    carregar_todas_receitas,
    normalizar_unidade,
    extrair_quantidade_e_unidade
)


class TestRecipeParser(unittest.TestCase):

    def test_extrair_quantidade_e_unidade(self):
        qtd, un, nome = extrair_quantidade_e_unidade("500 g de peito de frango")
        self.assertEqual(qtd, 500.0)
        self.assertEqual(un, "g")
        self.assertEqual(nome, "peito de frango")

        qtd, un, nome = extrair_quantidade_e_unidade("1.5 kg de batatas")
        self.assertEqual(qtd, 1.5)
        self.assertEqual(un, "kg")
        self.assertEqual(nome, "batatas")

        qtd, un, nome = extrair_quantidade_e_unidade("2 c. de sopa de azeite")
        self.assertEqual(qtd, 2.0)
        self.assertEqual(un, "c. de sopa")
        self.assertEqual(nome, "azeite")

        qtd, un, nome = extrair_quantidade_e_unidade("1/2 chávena de leite")
        self.assertEqual(qtd, 0.5)
        self.assertEqual(un, "chávena")
        self.assertEqual(nome, "leite")

    def test_parse_ingrediente(self):
        ing = parse_ingrediente("- 500 g de peito de frango [Talho]")
        self.assertEqual(ing.quantidade, 500.0)
        self.assertEqual(ing.unidade, "g")
        self.assertIn("peito de frango", ing.nome.lower())
        self.assertEqual(ing.categoria, "Talho")

        ing2 = parse_ingrediente("- 2 unidades de cebolas médias, picadas [Frutas e Legumes]")
        self.assertEqual(ing2.quantidade, 2.0)
        self.assertEqual(ing2.unidade, "unidade")
        self.assertEqual(ing2.categoria, "Frutas e Legumes")

        ing3 = parse_ingrediente("- 1 lata (aprox. 400 g) de feijão vermelho [Mercearia]")
        self.assertEqual(ing3.quantidade, 1.0)
        self.assertEqual(ing3.unidade, "lata")
        self.assertEqual(ing3.detalhes, "aprox. 400 g")

    def test_carregar_todas_receitas(self):
        pasta = Path("recipes")
        catalogo = carregar_todas_receitas(pasta)
        self.assertGreaterEqual(len(catalogo), 8)
        # Assegurar que _modelo.txt foi ignorado
        self.assertNotIn("_modelo", catalogo)
        self.assertIn("bacalhau_a_bras", catalogo)
        self.assertIn("frango_com_caril", catalogo)

        bacalhau = catalogo["bacalhau_a_bras"]
        self.assertEqual(bacalhau.doses, 4)
        self.assertTrue(len(bacalhau.ingredientes) > 5)
        self.assertTrue(len(bacalhau.instrucoes) > 0)


if __name__ == "__main__":
    unittest.main()
