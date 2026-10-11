"""Motor de planeamento de refeições, alocação e ajuste proporcional de doses."""

import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from src.recipe_parser import Receita, carregar_todas_receitas


@dataclass
class ItemPlano:
    """Representa uma receita selecionada dentro do plano semanal ou diário."""
    receita_id: str
    titulo: str
    refeicoes_cobertas: int
    pessoas: int
    doses_necessarias: int
    doses_base: int
    fator_escala: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ItemPlano":
        return cls(**data)


@dataclass
class PlanoRefeicoes:
    """Representa um plano de refeições completo."""
    dias: int
    pessoas: int
    refeicoes_por_dia: int
    total_refeicoes_alvo: int
    itens: List[ItemPlano]

    @property
    def total_refeicoes_planeadas(self) -> int:
        return sum(item.refeicoes_cobertas for item in self.itens)

    def to_dict(self) -> dict:
        return {
            "dias": self.dias,
            "pessoas": self.pessoas,
            "refeicoes_por_dia": self.refeicoes_por_dia,
            "total_refeicoes_alvo": self.total_refeicoes_alvo,
            "itens": [item.to_dict() for item in self.itens]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlanoRefeicoes":
        itens = [ItemPlano.from_dict(it) for it in data.get("itens", [])]
        return cls(
            dias=data.get("dias", 7),
            pessoas=data.get("pessoas", 2),
            refeicoes_por_dia=data.get("refeicoes_por_dia", 2),
            total_refeicoes_alvo=data.get("total_refeicoes_alvo", 14),
            itens=itens
        )

    def guardar(self, caminho: Path) -> None:
        """Guarda o plano atual em ficheiro JSON."""
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def carregar(cls, caminho: Path) -> Optional["PlanoRefeicoes"]:
        """Carrega um plano guardado em ficheiro JSON."""
        if not caminho.exists():
            return None
        with open(caminho, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


def encontrar_receita(termo: str, catalogo: Dict[str, Receita]) -> Optional[Receita]:
    """Procura uma receita por ID exato, título exato ou correspondência parcial."""
    termo_limpo = termo.strip().lower()
    
    # 1. Correspondência exata de ID ou título
    if termo_limpo in catalogo:
        return catalogo[termo_limpo]

    # 2. Pesquisa de correspondência de ID com hífen/sublinhado
    termo_slug = termo_limpo.replace(" ", "_").replace("-", "_")
    if termo_slug in catalogo:
        return catalogo[termo_slug]

    # 3. Correspondência parcial nos títulos ou IDs
    receitas_unicas = {r.id: r for r in catalogo.values()}.values()
    for rec in receitas_unicas:
        if termo_limpo in rec.titulo.lower() or termo_limpo in rec.id.lower():
            return rec

    return None


def distribuir_refeicoes_proporcionalmente(
    total_alvo: int,
    escolhas: List[Tuple[str, int]]
) -> List[Tuple[str, int]]:
    """
    Distribui total_alvo refeições proporcionalmente aos pesos/refeições em escolhas,
    garantindo que a soma final seja exatamente total_alvo e que
    os valores sejam inteiros >= 1 (quando total_alvo >= len(escolhas)).
    """
    if not escolhas or total_alvo <= 0:
        return []

    k = len(escolhas)

    # Se os valores fornecidos já somam exatamente total_alvo, mantemos os valores
    soma_atual = sum(w for _, w in escolhas)
    if soma_atual == total_alvo and all(w > 0 for _, w in escolhas):
        return list(escolhas)

    # Se total_alvo < k (mais receitas selecionadas do que refeições no plano)
    if total_alvo < k:
        indexado = [(escolhas[i][1], -i, escolhas[i][0]) for i in range(k)]
        indexado.sort(reverse=True)
        termos_selecionados = {item[2] for item in indexado[:total_alvo]}
        resultado = []
        for termo, _ in escolhas:
            if termo in termos_selecionados:
                resultado.append((termo, 1))
        return resultado

    # Se total_alvo >= k:
    # Garante pelo menos 1 refeição para cada receita selecionada
    # e distribui o restante (total_alvo - k) proporcionalmente aos pesos
    pesos_positivos = [max(1, w) for _, w in escolhas]
    peso_total = sum(pesos_positivos)
    restante = total_alvo - k

    alocados = [1] * k
    if restante > 0:
        quotas = [(restante * p) / peso_total for p in pesos_positivos]
        inteiros = [int(q) for q in quotas]
        restos = [q - int(q) for q in quotas]

        for i in range(k):
            alocados[i] += inteiros[i]

        diferenca = total_alvo - sum(alocados)
        if diferenca > 0:
            ordem_restos = sorted(range(k), key=lambda i: restos[i], reverse=True)
            for idx in ordem_restos[:diferenca]:
                alocados[idx] += 1

    return [(escolhas[i][0], alocados[i]) for i in range(k)]


def criar_item_plano(receita: Receita, refeicoes_cobertas: int, pessoas: int) -> ItemPlano:
    """Calcula as doses e fator de escala para uma dada receita."""
    doses_necessarias = refeicoes_cobertas * pessoas
    doses_base = max(1, receita.doses)
    fator_escala = doses_necessarias / doses_base
    return ItemPlano(
        receita_id=receita.id,
        titulo=receita.titulo,
        refeicoes_cobertas=refeicoes_cobertas,
        pessoas=pessoas,
        doses_necessarias=doses_necessarias,
        doses_base=doses_base,
        fator_escala=fator_escala
    )


def gerar_plano(
    catalogo: Dict[str, Receita],
    dias: int = 7,
    pessoas: int = 2,
    refeicoes_por_dia: int = 2,
    total_refeicoes_explicito: Optional[int] = None,
    escolhas_manuais: Optional[List[Tuple[str, int]]] = None,
    preencher_aleatorio: bool = True,
    refeicoes_por_lote_aleatorio: int = 2,
    semente_aleatoria: Optional[int] = None,
    escalar_escolhas: Optional[bool] = None
) -> PlanoRefeicoes:
    """
    Gera um plano de refeições com base nos dias, pessoas e escolhas manuais/aleatórias.
    - Se total_refeicoes_explicito for fornecido, prevalece sobre dias * refeicoes_por_dia.
    - escolhas_manuais: Lista de tuplos (termo_receita, num_refeicoes_a_cobrir).
    - escalar_escolhas: Se True (ou por predefinição quando preencher_aleatorio=False),
      ajusta as refeições selecionadas para cobrir a totalidade do plano.
    """
    if semente_aleatoria is not None:
        random.seed(semente_aleatoria)

    total_alvo = total_refeicoes_explicito if total_refeicoes_explicito is not None else (dias * refeicoes_por_dia)
    itens: List[ItemPlano] = []
    refeicoes_alocadas = 0

    receitas_unicas = list({r.id: r for r in catalogo.values()}.values())
    if not receitas_unicas:
        raise ValueError("O catálogo de receitas está vazio. Adicione ficheiros .txt em recipes/")

    ids_usados = set()

    deve_escalar = escalar_escolhas if escalar_escolhas is not None else (not preencher_aleatorio)

    # 1. Processar escolhas manuais
    if escolhas_manuais:
        # Validar previamente a existência de todas as receitas
        for termo, _ in escolhas_manuais:
            rec = encontrar_receita(termo, catalogo)
            if not rec:
                raise ValueError(f"Receita não encontrada: '{termo}'")

        if deve_escalar:
            escolhas_processadas = distribuir_refeicoes_proporcionalmente(total_alvo, escolhas_manuais)
        else:
            escolhas_processadas = escolhas_manuais

        for termo, num_ref in escolhas_processadas:
            rec = encontrar_receita(termo, catalogo)
            if not rec:
                raise ValueError(f"Receita não encontrada: '{termo}'")
            
            # Se for 0 ou não especificado e não tiver sido escalado
            if num_ref <= 0:
                num_ref = max(1, total_alvo - refeicoes_alocadas)
            
            item = criar_item_plano(rec, num_ref, pessoas)
            itens.append(item)
            refeicoes_alocadas += num_ref
            ids_usados.add(rec.id)

    # 2. Preencher refeições restantes se solicitado
    if preencher_aleatorio and refeicoes_alocadas < total_alvo:
        refeicoes_restantes = total_alvo - refeicoes_alocadas
        
        # Filtra receitas ainda não selecionadas para garantir variedade
        disponiveis = [r for r in receitas_unicas if r.id not in ids_usados]
        if not disponiveis:
            disponiveis = list(receitas_unicas)
        random.shuffle(disponiveis)

        idx = 0
        while refeicoes_restantes > 0:
            if idx >= len(disponiveis):
                # Se esgotar as receitas sem repetir, reinicia a lista baralhada
                disponiveis = list(receitas_unicas)
                random.shuffle(disponiveis)
                idx = 0

            rec = disponiveis[idx]
            idx += 1

            # Decide quantas refeições esta receita cobrirá (ex: 2 para almoço+jantar, ou o resto)
            lote = min(refeicoes_restantes, refeicoes_por_lote_aleatorio)
            if lote <= 0:
                lote = 1

            item = criar_item_plano(rec, lote, pessoas)
            itens.append(item)
            refeicoes_alocadas += lote
            refeicoes_restantes -= lote

    return PlanoRefeicoes(
        dias=dias,
        pessoas=pessoas,
        refeicoes_por_dia=refeicoes_por_dia,
        total_refeicoes_alvo=total_alvo,
        itens=itens
    )


def trocar_refeicao_no_plano(
    plano: PlanoRefeicoes,
    catalogo: Dict[str, Receita],
    termo_remover: str,
    termo_adicionar: str,
    novas_refeicoes_cobertas: Optional[int] = None
) -> Tuple[PlanoRefeicoes, ItemPlano, ItemPlano]:
    """
    Substitui uma receita do plano por outra, mantendo as doses/refeições cobertas.
    Retorna o plano atualizado, o item removido e o novo item adicionado.
    """
    rec_nova = encontrar_receita(termo_adicionar, catalogo)
    if not rec_nova:
        raise ValueError(f"Nova receita não encontrada: '{termo_adicionar}'")

    item_remover_idx = -1
    for i, it in enumerate(plano.itens):
        if termo_remover.lower() in it.titulo.lower() or termo_remover.lower() in it.receita_id.lower():
            item_remover_idx = i
            break

    if item_remover_idx == -1:
        raise ValueError(f"Receita a remover não foi encontrada no plano atual: '{termo_remover}'")

    item_antigo = plano.itens[item_remover_idx]
    refeicoes = novas_refeicoes_cobertas if novas_refeicoes_cobertas is not None else item_antigo.refeicoes_cobertas

    novo_item = criar_item_plano(rec_nova, refeicoes, plano.pessoas)
    plano.itens[item_remover_idx] = novo_item

    return plano, item_antigo, novo_item
