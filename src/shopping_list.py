"""Módulo de consolidação e geração da lista de compras organizada por secções."""

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set

from src.planner import PlanoRefeicoes, ItemPlano
from src.recipe_parser import Receita, Ingrediente, normalizar_unidade


ORDEM_SECCAO_SUPERMERCADO = [
    "Frutas e Legumes",
    "Talho e Aves",
    "Peixaria",
    "Lacticínios e Ovos",
    "Padaria",
    "Mercearia e Despensa",
    "Azeites, Óleos e Molhos",
    "Especiarias, Ervas e Temperos",
    "Congelados",
    "Bebidas",
    "Outros"
]

MAPEAMENTO_CATEGORIAS = {
    "frutas e legumes": "Frutas e Legumes",
    "fruta": "Frutas e Legumes",
    "legumes": "Frutas e Legumes",
    "hortícolas": "Frutas e Legumes",
    "horticolas": "Frutas e Legumes",
    "talho": "Talho e Aves",
    "carne": "Talho e Aves",
    "aves": "Talho e Aves",
    "peixaria": "Peixaria",
    "peixe": "Peixaria",
    "marisco": "Peixaria",
    "lacticínios": "Lacticínios e Ovos",
    "lacticinios": "Lacticínios e Ovos",
    "lacticínios e ovos": "Lacticínios e Ovos",
    "ovos": "Lacticínios e Ovos",
    "leite": "Lacticínios e Ovos",
    "padaria": "Padaria",
    "pão": "Padaria",
    "mercearia": "Mercearia e Despensa",
    "mercearia e despensa": "Mercearia e Despensa",
    "despensa": "Mercearia e Despensa",
    "conservas": "Mercearia e Despensa",
    "massas": "Mercearia e Despensa",
    "arroz": "Mercearia e Despensa",
    "azeites e óleos": "Azeites, Óleos e Molhos",
    "azeites": "Azeites, Óleos e Molhos",
    "óleos": "Azeites, Óleos e Molhos",
    "especiarias e temperos": "Especiarias, Ervas e Temperos",
    "especiarias": "Especiarias, Ervas e Temperos",
    "temperos": "Especiarias, Ervas e Temperos",
    "ervas": "Especiarias, Ervas e Temperos",
    "congelados": "Congelados",
    "bebidas": "Bebidas",
}


def canonicalizar_categoria(cat_bruta: str) -> str:
    """Mapeia uma categoria livre para a secção padronizada do supermercado."""
    c_low = cat_bruta.lower().strip()
    return MAPEAMENTO_CATEGORIAS.get(c_low, "Mercearia e Despensa" if not c_low else cat_bruta.title())


def simplificar_nome_ingrediente(nome: str) -> str:
    """Normaliza o nome do ingrediente para facilitar a agregação inteligente."""
    nome = nome.strip()
    # Remove detalhes como 'picado', 'cortado em cubos', etc.
    termos_corte = [
        r",\s*picad[oa]s?",
        r",\s*ralad[oa]s?",
        r",\s*em cubos?",
        r",\s*cortad[oa]s?.*",
        r",\s*em rodelas?",
        r",\s*em meias-luas.*",
        r",\s*descascad[oa]s?.*",
        r",\s*escorrido.*",
        r",\s*esfarelado.*",
        r",\s*ou picada.*",
        r"\s+em cubos?",
        r"\s+picad[oa]s?",
        r"^(?:pequeno|pequena|grande)\s+de\s+",
        r"^(?:rasa|cheia)\s+de\s+",
    ]
    for termo in termos_corte:
        nome = re.sub(termo, "", nome, flags=re.IGNORECASE)

    # Remover qualificadores de tamanho que impeçam agregação
    nome = re.sub(r"\b(?:médias?|médios?|pequenas?|pequenos?|grandes?)\b", "", nome, flags=re.IGNORECASE)
    nome = re.sub(r"\s+", " ", nome).strip()

    # Singularização e normalização de ingredientes comuns
    substituicoes = [
        (r"\bcebolas?\b", "cebola"),
        (r"\bcenouras?\b", "cenoura"),
        (r"\bbatatas?\s+doces?\b", "batata doce"),
        (r"\bbatatas?\b", "batata"),
        (r"\bdentes?\s+de\s+alho\b", "alho"),
        (r"\bovos?\b", "ovo"),
        (r"\btomates?\s+cherry\b", "tomate cherry"),
        (r"\bpimentos?\s+vermelhos?\b", "pimento vermelho"),
        (r"\bpimentos?\s+verdes?\b", "pimento verde"),
        (r"\blombos?\s+de\s+salmão(?:\s+fresco)?\b", "lombo de salmão"),
        (r"\bfolhas?\s+de\s+louro\b", "folha de louro"),
    ]
    for padrao, subst in substituicoes:
        nome = re.sub(padrao, subst, nome, flags=re.IGNORECASE)

    return nome.strip().capitalize()


PLURAIS_UNIDADES = {
    "dente": "dentes",
    "unidade": "unidades",
    "lata": "latas",
    "pacote": "pacotes",
    "folha": "folhas",
    "fatia": "fatias",
    "molho": "molhos",
    "pitada": "pitadas",
    "chávena": "chávenas",
    "colher de sopa": "colheres de sopa",
    "c. de sopa": "c. de sopa",
    "c. de chá": "c. de chá",
    "c. de café": "c. de café",
    "g": "g",
    "kg": "kg",
    "ml": "ml",
    "l": "l",
    "dl": "dl",
    "cl": "cl"
}


def pluralizar_unidade(unidade: str, quantidade: float) -> str:
    """Aplica o plural à unidade caso a quantidade seja superior a 1."""
    if not unidade:
        return ""
    if quantidade > 1.001:
        return PLURAIS_UNIDADES.get(unidade.lower(), unidade)
    return unidade


@dataclass
class ItemCompraAgregado:
    """Item agregado na lista de compras final."""
    nome: str
    quantidade: Optional[float]
    unidade: Optional[str]
    categoria: str
    receitas_origem: Set[str] = field(default_factory=set)
    detalhes_combinados: Set[str] = field(default_factory=set)

    def adicionar(self, quantidade: Optional[float], unidade: Optional[str], receita_titulo: str, detalhe: str = ""):
        self.receitas_origem.add(receita_titulo)
        if detalhe:
            self.detalhes_combinados.add(detalhe)

        if self.quantidade is None or quantidade is None:
            return

        # Conversão de unidades compatíveis
        u_atual = self.unidade.lower() if self.unidade else ""
        u_nova = unidade.lower() if unidade else ""

        if u_atual == u_nova:
            self.quantidade += quantidade
        elif (u_atual == "g" and u_nova == "kg"):
            self.quantidade += quantidade * 1000
        elif (u_atual == "kg" and u_nova == "g"):
            self.quantidade += quantidade / 1000
        elif (u_atual == "ml" and u_nova == "l"):
            self.quantidade += quantidade * 1000
        elif (u_atual == "l" and u_nova == "ml"):
            self.quantidade += quantidade / 1000
        elif u_atual in ("unidade", "unidades", "") and u_nova in ("unidade", "unidades", ""):
            self.quantidade += quantidade
        else:
            # Unidades distintas que não convertem diretamente; soma se possível ou preserva
            self.quantidade += quantidade

    def formatar_quantidade(self) -> str:
        """Formata a quantidade com unidade ajustada (ex: converte 1500g em 1.5 kg)."""
        if self.quantidade is None:
            return ""

        qtd = self.quantidade
        unidade = self.unidade or ""

        # Conversão automática para kg se >= 1000g
        if unidade == "g" and qtd >= 1000:
            qtd = qtd / 1000
            unidade = "kg"
        # Conversão automática para l se >= 1000ml
        elif unidade == "ml" and qtd >= 1000:
            qtd = qtd / 1000
            unidade = "l"

        if abs(qtd - round(qtd)) < 1e-4:
            qtd_str = f"{int(round(qtd))}"
        else:
            qtd_str = f"{qtd:.2f}".rstrip("0").rstrip(".")

        if unidade:
            u_formatada = pluralizar_unidade(unidade, qtd)
            return f"{qtd_str} {u_formatada}"
        return qtd_str


class GeradorListaCompras:
    """Gera e consolida a lista de compras para um plano de refeições."""

    def __init__(self, catalogo: Dict[str, Receita]):
        self.catalogo = catalogo

    def gerar(self, plano: PlanoRefeicoes) -> Dict[str, List[ItemCompraAgregado]]:
        """Processa o plano e devolve os itens agrupados por secção de supermercado."""
        agrupados_por_chave: Dict[Tuple[str, str, str], ItemCompraAgregado] = {}

        for item_plano in plano.itens:
            # Encontrar receita correspondente
            rec = self.catalogo.get(item_plano.receita_id) or self.catalogo.get(item_plano.titulo.lower())
            if not rec:
                continue

            for ing in rec.ingredientes:
                categoria = canonicalizar_categoria(ing.categoria)
                nome_simplificado = simplificar_nome_ingrediente(ing.nome)
                
                # Quantidade escalada
                qtd_escalada = (ing.quantidade * item_plano.fator_escala) if ing.quantidade is not None else None
                unidade_padrao = normalizar_unidade(ing.unidade) if ing.unidade else ""

                # Chave de agregação: (Categoria, Nome Normalizado, Família de Unidade)
                familia_unidade = self._obter_familia_unidade(unidade_padrao)
                chave = (categoria, nome_simplificado.lower(), familia_unidade)

                if chave not in agrupados_por_chave:
                    agrupados_por_chave[chave] = ItemCompraAgregado(
                        nome=nome_simplificado,
                        quantidade=0.0 if qtd_escalada is not None else None,
                        unidade=unidade_padrao,
                        categoria=categoria,
                        receitas_origem=set(),
                        detalhes_combinados=set()
                    )

                agrupados_por_chave[chave].adicionar(
                    quantidade=qtd_escalada,
                    unidade=unidade_padrao,
                    receita_titulo=item_plano.titulo,
                    detalhe=ing.detalhes
                )

        # Agrupar por secção de supermercado ordenada
        seccoes: Dict[str, List[ItemCompraAgregado]] = defaultdict(list)
        for item in agrupados_por_chave.values():
            seccoes[item.categoria].append(item)

        # Ordenar itens alfabeticamente dentro de cada secção
        for cat in seccoes:
            seccoes[cat].sort(key=lambda x: x.nome.lower())

        # Devolver dicionário com a ordem recomendada de corredores
        resultado_ordenado: Dict[str, List[ItemCompraAgregado]] = {}
        for cat_ordem in ORDEM_SECCAO_SUPERMERCADO:
            if cat_ordem in seccoes and seccoes[cat_ordem]:
                resultado_ordenado[cat_ordem] = seccoes[cat_ordem]

        # Incluir quaisquer outras secções que tenham surgido
        for cat, itens in seccoes.items():
            if cat not in resultado_ordenado and itens:
                resultado_ordenado[cat] = itens

        return resultado_ordenado

    def _obter_familia_unidade(self, unidade: str) -> str:
        u = (unidade or "").lower()
        if u in ("g", "kg"):
            return "peso_g"
        if u in ("ml", "l", "cl", "dl"):
            return "volume_ml"
        if u in ("c. de sopa", "colher de sopa"):
            return "c_sopa"
        if u in ("c. de chá", "colher de chá"):
            return "c_cha"
        return u or "unidade"

    def exportar_markdown(self, plano: PlanoRefeicoes) -> str:
        """Gera um relatório completo em Markdown pronto para o utilizador."""
        itens_agrupados = self.gerar(plano)

        md = []
        md.append("# 🛒 Lista de Compras e Plano de Refeições\n")
        md.append(f"**Duração:** {plano.dias} dias | **Pessoas:** {plano.pessoas} | **Total de Refeições:** {plano.total_refeicoes_planeadas}")
        md.append("\n---\n")

        md.append("## 🍽️ Ementa Selecionada\n")
        md.append("| Refeição | Refeições Cobertas | Doses a Cozinhar | Fator de Escala |")
        md.append("| :--- | :---: | :---: | :---: |")
        for item in plano.itens:
            escala_fmt = f"{item.fator_escala:.2f}x".rstrip("0").rstrip(".") if item.fator_escala != 1.0 else "1x"
            md.append(f"| **{item.titulo}** | {item.refeicoes_cobertas} | {item.doses_necessarias} doses (base: {item.doses_base}) | {escala_fmt} |")

        md.append("\n---\n")
        md.append("## 📦 Itens para Comprar (por secção)\n")

        for seccao, lista_itens in itens_agrupados.items():
            md.append(f"### 📍 {seccao}")
            for it in lista_itens:
                qtd_str = it.formatar_quantidade()
                conetor = " de " if qtd_str and not it.nome.lower().startswith(("de ", "do ", "da ")) else " "
                if not qtd_str:
                    conetor = ""
                
                origem_str = f" *(para: {', '.join(sorted(it.receitas_origem))})*" if it.receitas_origem else ""
                detalhes_str = f" [{', '.join(sorted(it.detalhes_combinados))}]" if it.detalhes_combinados else ""
                
                md.append(f"- [ ] {qtd_str}{conetor}{it.nome}{detalhes_str}{origem_str}".strip())
            md.append("")

        return "\n".join(md)
