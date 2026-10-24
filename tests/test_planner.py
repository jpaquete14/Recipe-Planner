"""Testes para o motor de planeamento de refeições e cálculo de doses."""

import unittest
from pathlib import Path
from src.recipe_parser import carregar_todas_receitas
from src.planner import (
    gerar_plano,
    trocar_refeicao_no_plano,
    PlanoRefeicoes,
    encontrar_receita,
    distribuir_refeicoes_proporcionalmente
)


class TestPlanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalogo = carregar_todas_receitas(Path("recipes"))

    def test_gerar_plano_1_semana_2_pessoas(self):
        # 1 semana = 7 dias * 2 refeicoes/dia = 14 refeições
        plano = gerar_plano(self.catalogo, dias=7, pessoas=2, preencher_aleatorio=True, semente_aleatoria=10)
        self.assertEqual(plano.dias, 7)
        self.assertEqual(plano.pessoas, 2)
        self.assertEqual(plano.total_refeicoes_planeadas, 14)

    def test_gerar_plano_2_dias_1_refeicao_escalada(self):
        # 2 dias * 2 refeições = 4 refeições no total
        # 1 única receita (ex: Bacalhau à Brás com base de 4 doses) para 2 pessoas * 4 refeições = 8 doses
        # Fator de escala deve ser 8 / 4 = 2.0x
        plano = gerar_plano(
            self.catalogo,
            dias=2,
            pessoas=2,
            escolhas_manuais=[("bacalhau_a_bras", 4)],
            preencher_aleatorio=False
        )
        self.assertEqual(len(plano.itens), 1)
        item = plano.itens[0]
        self.assertEqual(item.refeicoes_cobertas, 4)
        self.assertEqual(item.doses_necessarias, 8)
        self.assertEqual(item.doses_base, 4)
        self.assertAlmostEqual(item.fator_escala, 2.0)

    def test_trocar_refeicao_no_plano(self):
        plano = gerar_plano(
            self.catalogo,
            dias=2,
            pessoas=2,
            escolhas_manuais=[("bacalhau_a_bras", 4)],
            preencher_aleatorio=False
        )
        self.assertEqual(plano.itens[0].receita_id, "bacalhau_a_bras")

        plano_atualizado, antigo, novo = trocar_refeicao_no_plano(
            plano, self.catalogo, termo_remover="bacalhau", termo_adicionar="caril"
        )
        self.assertEqual(antigo.receita_id, "bacalhau_a_bras")
        self.assertEqual(novo.receita_id, "frango_com_caril")
        self.assertEqual(plano_atualizado.itens[0].receita_id, "frango_com_caril")
        self.assertEqual(plano_atualizado.itens[0].refeicoes_cobertas, 4)

    def test_guardar_e_carregar_plano_json(self):
        caminho_tmp = Path("tests/.teste_plano.json")
        try:
            plano_orig = gerar_plano(self.catalogo, dias=3, pessoas=2, semente_aleatoria=99)
            plano_orig.guardar(caminho_tmp)
            self.assertTrue(caminho_tmp.exists())

            plano_carregado = PlanoRefeicoes.carregar(caminho_tmp)
            self.assertIsNotNone(plano_carregado)
            self.assertEqual(plano_carregado.dias, 3)
            self.assertEqual(plano_carregado.pessoas, 2)
            self.assertEqual(len(plano_carregado.itens), len(plano_orig.itens))
        finally:
            if caminho_tmp.exists():
                caminho_tmp.unlink()

    def test_usar_apenas_selecionadas_escala_proporcionalmente(self):
        # 7 dias * 2 refeições/dia = 14 refeições para 2 pessoas = 28 doses no total
        # Selecionando apenas 2 receitas (1 refeição indicada para cada)
        # Ambas devem aumentar para 7 refeições (14 doses cada) cobrindo as 14 refeições do plano
        plano = gerar_plano(
            self.catalogo,
            dias=7,
            pessoas=2,
            escolhas_manuais=[("bacalhau_a_bras", 1), ("frango_com_caril", 1)],
            preencher_aleatorio=False
        )
        self.assertEqual(plano.total_refeicoes_planeadas, 14)
        self.assertEqual(len(plano.itens), 2)
        for item in plano.itens:
            self.assertEqual(item.refeicoes_cobertas, 7)
            self.assertEqual(item.doses_necessarias, 14)
        total_doses = sum(it.doses_necessarias for it in plano.itens)
        self.assertEqual(total_doses, 28)

    def test_usar_apenas_selecionadas_pesos_diferentes(self):
        # 14 refeições totais distribuídas na proporção 2:1
        plano = gerar_plano(
            self.catalogo,
            dias=7,
            pessoas=2,
            escolhas_manuais=[("bacalhau_a_bras", 2), ("frango_com_caril", 1)],
            preencher_aleatorio=False
        )
        self.assertEqual(plano.total_refeicoes_planeadas, 14)
        self.assertEqual(plano.itens[0].refeicoes_cobertas, 9)
        self.assertEqual(plano.itens[1].refeicoes_cobertas, 5)

    def test_distribuir_refeicoes_proporcionalmente_casos_limite(self):
        # 1 receita para 14 refeições
        res1 = distribuir_refeicoes_proporcionalmente(14, [("rec1", 1)])
        self.assertEqual(res1, [("rec1", 14)])

        # 3 receitas para 14 refeições com pesos iguais
        res3 = distribuir_refeicoes_proporcionalmente(14, [("r1", 1), ("r2", 1), ("r3", 1)])
        self.assertEqual([qtd for _, qtd in res3], [5, 5, 4])
        self.assertEqual(sum(qtd for _, qtd in res3), 14)

        # Mais receitas que refeições no plano (ex: 2 refeições para 3 receitas)
        res_excesso = distribuir_refeicoes_proporcionalmente(2, [("r1", 3), ("r2", 2), ("r3", 1)])
        self.assertEqual(len(res_excesso), 2)
        self.assertEqual(sum(qtd for _, qtd in res_excesso), 2)

    def test_gerar_plano_refeicoes_diferentes_7_dias_1_pessoa(self):
        # O exemplo do utilizador: 2 refeições diferentes para 7 dias e 1 pessoa
        # 7 dias * 2 refeicoes/dia = 14 refeições totais
        # 2 refeições diferentes -> 7 refeições cada, 7 doses cada para 1 pessoa
        plano = gerar_plano(
            self.catalogo,
            dias=7,
            pessoas=1,
            refeicoes_diferentes=2,
            semente_aleatoria=42
        )
        self.assertEqual(plano.dias, 7)
        self.assertEqual(plano.pessoas, 1)
        self.assertEqual(plano.total_refeicoes_planeadas, 14)
        self.assertEqual(plano.total_refeicoes_diferentes, 2)
        self.assertEqual(len(plano.itens), 2)
        for item in plano.itens:
            self.assertEqual(item.refeicoes_cobertas, 7)
            self.assertEqual(item.doses_necessarias, 7)

    def test_gerar_plano_refeicoes_diferentes_7_dias_2_pessoas(self):
        # 14 refeições para 2 pessoas com 2 receitas diferentes
        # 7 refeições cada -> 14 doses necessárias para cada receita
        plano = gerar_plano(
            self.catalogo,
            dias=7,
            pessoas=2,
            refeicoes_diferentes=2,
            semente_aleatoria=123
        )
        self.assertEqual(plano.total_refeicoes_planeadas, 14)
        self.assertEqual(plano.total_refeicoes_diferentes, 2)
        self.assertEqual(len(plano.itens), 2)
        for item in plano.itens:
            self.assertEqual(item.refeicoes_cobertas, 7)
            self.assertEqual(item.doses_necessarias, 14)

    def test_gerar_plano_refeicoes_diferentes_3_receitas(self):
        # 14 refeições divididas por 3 receitas diferentes (5 + 5 + 4)
        plano = gerar_plano(
            self.catalogo,
            dias=7,
            pessoas=2,
            refeicoes_diferentes=3,
            semente_aleatoria=7
        )
        self.assertEqual(plano.total_refeicoes_planeadas, 14)
        self.assertEqual(plano.total_refeicoes_diferentes, 3)
        self.assertEqual(len(plano.itens), 3)
        refeicoes = sorted([item.refeicoes_cobertas for item in plano.itens])
        self.assertEqual(refeicoes, [4, 5, 5])

    def test_gerar_plano_refeicoes_diferentes_com_escolha_manual(self):
        # 2 refeições diferentes no total, com 1 escolha manual
        plano = gerar_plano(
            self.catalogo,
            dias=7,
            pessoas=1,
            escolhas_manuais=[("bacalhau_a_bras", 0)],
            refeicoes_diferentes=2,
            semente_aleatoria=9
        )
        self.assertEqual(plano.total_refeicoes_planeadas, 14)
        self.assertEqual(plano.total_refeicoes_diferentes, 2)
        ids = {item.receita_id for item in plano.itens}
        self.assertIn("bacalhau_a_bras", ids)

    def test_gerar_plano_refeicoes_diferentes_validacoes(self):
        # refeicoes_diferentes <= 0
        with self.assertRaises(ValueError):
            gerar_plano(self.catalogo, dias=7, refeicoes_diferentes=0)

        # refeicoes_diferentes > total_alvo (ex: 20 pratos para 14 refeições)
        with self.assertRaises(ValueError):
            gerar_plano(self.catalogo, dias=7, refeicoes_por_dia=2, refeicoes_diferentes=20)

        # escolhas manuais em excesso em relação ao limite solicitado
        with self.assertRaises(ValueError):
            gerar_plano(
                self.catalogo,
                dias=7,
                escolhas_manuais=[("bacalhau_a_bras", 1), ("frango_com_caril", 1), ("chili_com_carne", 1)],
                refeicoes_diferentes=2
            )


if __name__ == "__main__":
    unittest.main()
