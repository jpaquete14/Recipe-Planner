"""Módulo de leitura e estruturação de ficheiros de receitas em texto."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class Ingrediente:
    """Representa um ingrediente estruturado com quantidades e unidade."""
    quantidade: Optional[float]
    unidade: Optional[str]
    nome: str
    categoria: str
    texto_original: str
    detalhes: str = ""

    def formatar(self, fator_escala: float = 1.0) -> str:
        """Retorna uma representação legível do ingrediente escalado."""
        if self.quantidade is None:
            return f"{self.nome}" + (f" ({self.detalhes})" if self.detalhes else "")

        qtd_ajustada = self.quantidade * fator_escala
        # Formatação limpa de números inteiros ou decimais
        if abs(qtd_ajustada - round(qtd_ajustada)) < 1e-4:
            qtd_str = f"{int(round(qtd_ajustada))}"
        else:
            qtd_str = f"{qtd_ajustada:.2f}".rstrip("0").rstrip(".")

        unidade_str = f" {self.unidade}" if self.unidade else ""
        conetor = " de " if self.unidade and not self.nome.lower().startswith(("de ", "do ", "da ")) else " "
        if not self.unidade:
            conetor = " "
        
        texto = f"{qtd_str}{unidade_str}{conetor}{self.nome}".strip()
        if self.detalhes:
            texto += f" ({self.detalhes})"
        return texto


@dataclass
class Receita:
    """Representa uma receita completa com metadados, ingredientes e modo de preparação."""
    caminho_ficheiro: Path
    titulo: str
    doses: int
    tempo_preparacao: str = ""
    tempo_cozedura: str = ""
    tempo_total: str = ""
    categoria: List[str] = field(default_factory=list)
    dificuldade: str = ""
    ingredientes: List[Ingrediente] = field(default_factory=list)
    instrucoes: List[str] = field(default_factory=list)
    notas: List[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.caminho_ficheiro.stem


UNIDADES_CONHECIDAS = [
    # Colheres e medidas de volume culinário
    ("c. de sopa", ["c. de sopa", "colher de sopa", "colheres de sopa", "c. sopa", "c.sopa"]),
    ("c. de chá", ["c. de chá", "colher de chá", "colheres de chá", "c. chá", "c.chá", "c. de cha", "colher de cha"]),
    ("c. de café", ["c. de café", "colher de café", "colheres de café", "c. café", "c.cafe"]),
    ("chávena", ["chávena", "chávenas", "chavena", "chavenas", "copo", "copos"]),
    # Peso
    ("kg", ["kg", "quilo", "quilos", "quilograma", "quilogramas"]),
    ("g", ["g", "gr", "grama", "gramas"]),
    # Volume
    ("l", ["l", "litro", "litros"]),
    ("dl", ["dl", "decilitro", "decilitros"]),
    ("cl", ["cl", "centilitro", "centilitros"]),
    ("ml", ["ml", "mililitro", "mililitros"]),
    # Unidades / embalagens
    ("unidade", ["unidade", "unidades", "un.", "un", "uni"]),
    ("dente", ["dente", "dentes"]),
    ("lata", ["lata", "latas"]),
    ("pacote", ["pacote", "pacotes", "embalagem", "embalagens"]),
    ("fatia", ["fatia", "fatias"]),
    ("folha", ["folha", "folhas"]),
    ("molho", ["molho", "molhos"]),
    ("pitada", ["pitada", "pitadas"]),
]


def normalizar_unidade(unidade_bruta: str) -> Optional[str]:
    """Normaliza variantes de escrita para um identificador de unidade canónico."""
    u_lower = unidade_bruta.lower().strip().rstrip(".")
    for unidade_padrao, variantes in UNIDADES_CONHECIDAS:
        for var in variantes:
            if u_lower == var.rstrip("."):
                return unidade_padrao
    return u_lower


def extrair_quantidade_e_unidade(texto: str):
    """Extrai quantidade (float), unidade (str) e o restante nome do ingrediente."""
    texto = texto.strip()
    
    # 1. Tratar frações comuns como 1/2, 1/4, 3/4
    frac_match = re.match(r"^(\d+)\s*/\s*(\d+)\s*(.*)$", texto)
    if frac_match:
        numerador, denominador, resto = frac_match.groups()
        quantidade = float(numerador) / float(denominador)
        return _extrair_unidade_do_resto(quantidade, resto)

    # 2. Tratar números inteiros ou decimais (ex: 500, 1.5, 1,5)
    num_match = re.match(r"^(\d+(?:[.,]\d+)?)\s*(.*)$", texto)
    if num_match:
        qtd_str, resto = num_match.groups()
        quantidade = float(qtd_str.replace(",", "."))
        return _extrair_unidade_do_resto(quantidade, resto)

    return None, None, texto


def _extrair_unidade_do_resto(quantidade: float, resto: str):
    resto = resto.strip()
    # Verifica unidades compostas primeiro (ex: "c. de sopa", "colheres de sopa")
    for unidade_padrao, variantes in UNIDADES_CONHECIDAS:
        for var in sorted(variantes, key=len, reverse=True):
            padrao = r"^" + re.escape(var) + r"(?:\s+(?:de\s+|do\s+|da\s+)?|\s+|$)(.*)"
            m = re.match(padrao, resto, re.IGNORECASE)
            if m:
                nome = m.group(1).strip()
                return quantidade, unidade_padrao, nome

    # Se não houver unidade conhecida explícita, verificar se a primeira palavra parece unidade
    # Caso contrário, assume-se que é unidade simples ou nome direto
    return quantidade, None, resto


def parse_ingrediente(linha: str) -> Ingrediente:
    """Converte uma linha de texto de ingrediente num objeto Ingrediente."""
    texto_original = linha.strip()
    texto = re.sub(r"^[-*•]\s*", "", texto_original).strip()

    # Extrair categoria entre parêntesis retos no final da linha: [Categoria]
    categoria = "Mercearia"
    cat_match = re.search(r"\[(.*?)\]\s*$", texto)
    if cat_match:
        categoria = cat_match.group(1).strip()
        texto = texto[:cat_match.start()].strip()

    # Extrair notas/detalhes opcionais entre parêntesis normais no final ou meio
    detalhes = ""
    det_match = re.search(r"\((.*?)\)", texto)
    if det_match:
        detalhes = det_match.group(1).strip()
        texto = re.sub(r"\(.*?\)", "", texto).strip()

    quantidade, unidade, nome = extrair_quantidade_e_unidade(texto)
    
    # Limpeza do nome do ingrediente
    nome = re.sub(r"^(?:de|do|da|dos|das|d')\s+", "", nome, flags=re.IGNORECASE).strip()
    if not nome:
        nome = texto_original

    return Ingrediente(
        quantidade=quantidade,
        unidade=unidade,
        nome=nome,
        categoria=categoria,
        texto_original=texto_original,
        detalhes=detalhes
    )


def parse_receita_ficheiro(caminho: Path) -> Receita:
    """Lê um ficheiro .txt e devolve o objeto Receita estruturado."""
    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    titulo = caminho.stem.replace("_", " ").title()
    doses = 2
    tempo_prep = ""
    tempo_coz = ""
    tempo_total = ""
    categorias = []
    dificuldade = ""
    ingredientes = []
    instrucoes = []
    notas = []

    seccao_atual = "cabecalho"

    for linha_bruta in linhas:
        linha = linha_bruta.strip()
        if not linha:
            continue
        if linha.startswith("#"):
            continue

        linha_lower = linha.lower()

        # Deteção de secções
        if linha_lower.startswith(("ingredientes:", "ingrediente:")):
            seccao_atual = "ingredientes"
            continue
        elif linha_lower.startswith(("instruções:", "instrucoes:", "modo de preparação:", "modo de preparacao:", "preparação:", "preparacao:")):
            seccao_atual = "instrucoes"
            continue
        elif linha_lower.startswith(("notas:", "nota:", "dicas:", "dica:")):
            seccao_atual = "notas"
            continue

        if seccao_atual == "cabecalho":
            if ":" in linha:
                chave, valor = [p.strip() for p in linha.split(":", 1)]
                chave_low = chave.lower()
                if chave_low in ("título", "titulo", "title", "nome"):
                    titulo = valor
                elif chave_low in ("doses", "dose", "porções", "porcoes", "servings", "rendimento"):
                    d_match = re.search(r"\d+", valor)
                    if d_match:
                        doses = int(d_match.group(0))
                elif chave_low in ("tempo de preparação", "tempo de preparacao", "prep time"):
                    tempo_prep = valor
                elif chave_low in ("tempo de cozedura", "cook time"):
                    tempo_coz = valor
                elif chave_low in ("tempo total", "tempo", "total time"):
                    tempo_total = valor
                elif chave_low in ("categoria", "categorias", "category", "tipo"):
                    categorias = [c.strip() for c in valor.split(",") if c.strip()]
                elif chave_low in ("dificuldade", "difficulty"):
                    dificuldade = valor

        elif seccao_atual == "ingredientes":
            if linha.startswith(("-", "*", "•")) or re.match(r"^\d", linha):
                ingredientes.append(parse_ingrediente(linha))

        elif seccao_atual == "instrucoes":
            instrucoes.append(linha)

        elif seccao_atual == "notas":
            notas.append(linha)

    return Receita(
        caminho_ficheiro=caminho,
        titulo=titulo,
        doses=doses,
        tempo_preparacao=tempo_prep,
        tempo_cozedura=tempo_coz,
        tempo_total=tempo_total,
        categoria=categorias,
        dificuldade=dificuldade,
        ingredientes=ingredientes,
        instrucoes=instrucoes,
        notas=notas
    )


def carregar_todas_receitas(pasta_receitas: Path) -> Dict[str, Receita]:
    """Carrega todas as receitas da pasta, ignorando ficheiros que comecem por '_'."""
    receitas = {}
    if not pasta_receitas.exists():
        return receitas

    for ficheiro in sorted(pasta_receitas.glob("*.txt")):
        if ficheiro.name.startswith("_"):
            continue
        rec = parse_receita_ficheiro(ficheiro)
        receitas[rec.id] = rec
        # Permite também indexar pelo título em minúsculas para pesquisas flexíveis
        receitas[rec.titulo.lower()] = rec

    return receitas
