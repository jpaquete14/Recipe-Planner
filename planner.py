#!/usr/bin/env python3
"""
Guia de Receitas e Planeador de Lista de Compras
Interface de linha de comandos (CLI) em Português de Portugal.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

# Configurar codificação UTF-8 para o terminal Windows quando disponível
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.recipe_parser import carregar_todas_receitas, Receita
from src.planner import (
    PlanoRefeicoes,
    gerar_plano,
    trocar_refeicao_no_plano,
    encontrar_receita
)
from src.shopping_list import GeradorListaCompras

PASTA_RECEITAS_PADRAO = Path("recipes")
FICHEIRO_PLANO_PADRAO = Path(".plano_atual.json")


def comando_listar(args) -> int:
    """Lista todas as receitas disponíveis no catálogo."""
    pasta = Path(args.pasta)
    catalogo = carregar_todas_receitas(pasta)
    receitas_unicas = sorted({r.id: r for r in catalogo.values()}.values(), key=lambda x: x.titulo)

    if not receitas_unicas:
        print(f"Nenhuma receita encontrada na pasta '{pasta}'. Adicione ficheiros .txt baseados em recipes/_modelo.txt.")
        return 1

    filtro_cat = args.categoria.lower() if args.categoria else None
    if filtro_cat:
        receitas_unicas = [r for r in receitas_unicas if any(filtro_cat in c.lower() for c in r.categoria)]

    print(f"\n=======================================================")
    print(f"📖 Catálogo de Receitas ({len(receitas_unicas)} receitas disponíveis)")
    print(f"=======================================================\n")

    for r in receitas_unicas:
        tempo_str = r.tempo_total or f"Prep: {r.tempo_preparacao or 'N/A'} | Coz: {r.tempo_cozedura or 'N/A'}"
        cats_str = ", ".join(r.categoria) if r.categoria else "Geral"
        print(f"🍽️  {r.titulo}")
        print(f"   - Ficheiro: recipes/{r.caminho_ficheiro.name}")
        print(f"   - Doses base: {r.doses} pessoas | Tempo: {tempo_str}")
        print(f"   - Categorias: {cats_str} | Dificuldade: {r.dificuldade or 'Normal'}")
        print(f"   - Total ingredientes: {len(r.ingredientes)}")
        print()

    return 0


def comando_ver(args) -> int:
    """Apresenta os detalhes completos de uma receita específica."""
    catalogo = carregar_todas_receitas(Path(args.pasta))
    rec = encontrar_receita(args.receita, catalogo)

    if not rec:
        print(f"❌ Receita '{args.receita}' não encontrada.")
        return 1

    print(f"\n=======================================================")
    print(f"🥘 {rec.titulo}")
    print(f"=======================================================")
    print(f"Doses base: {rec.doses} pessoas")
    if rec.tempo_preparacao:
        print(f"Tempo de Preparação: {rec.tempo_preparacao}")
    if rec.tempo_cozedura:
        print(f"Tempo de Cozedura: {rec.tempo_cozedura}")
    if rec.categoria:
        print(f"Categorias: {', '.join(rec.categoria)}")
    if rec.dificuldade:
        print(f"Dificuldade: {rec.dificuldade}")

    print(f"\n📋 Ingredientes:")
    for ing in rec.ingredientes:
        print(f"  • {ing.formatar()} [{ing.categoria}]")

    if rec.instrucoes:
        print(f"\n👩‍🍳 Modo de Preparação:")
        for inst in rec.instrucoes:
            print(f"  {inst}")

    if rec.notas:
        print(f"\n💡 Notas:")
        for nota in rec.notas:
            print(f"  {nota}")
    print()
    return 0


def parse_escolhas(escolhas_raw: List[str]) -> List[Tuple[str, int]]:
    """
    Interpreta argumentos como:
    ['bacalhau:4', 'caril:2', 'bolonhesa'] -> [('bacalhau', 4), ('caril', 2), ('bolonhesa', 0)]
    """
    resultado = []
    for item in escolhas_raw:
        if ":" in item:
            partes = item.split(":", 1)
            nome = partes[0].strip()
            try:
                num = int(partes[1].strip())
            except ValueError:
                num = 0
            resultado.append((nome, num))
        else:
            resultado.append((item.strip(), 0))
    return resultado


def comando_planear(args) -> int:
    """Gera um plano de refeições para os dias e pessoas especificados."""
    catalogo = carregar_todas_receitas(Path(args.pasta))
    if not catalogo:
        print(f"❌ Nenhuma receita disponível na pasta '{args.pasta}'.")
        return 1

    escolhas = parse_escolhas(args.escolher) if args.escolher else []

    try:
        plano = gerar_plano(
            catalogo=catalogo,
            dias=args.dias,
            pessoas=args.pessoas,
            refeicoes_por_dia=args.refeicoes_dia,
            total_refeicoes_explicito=args.refeicoes,
            escolhas_manuais=escolhas,
            preencher_aleatorio=not args.sem_aleatorio,
            refeicoes_por_lote_aleatorio=args.refeicoes_por_lote,
            refeicoes_diferentes=args.refeicoes_diferentes
        )
    except Exception as e:
        print(f"❌ Erro ao gerar o plano: {e}")
        return 1

    # Guardar plano atual
    ficheiro_plano = Path(args.ficheiro_plano)
    plano.guardar(ficheiro_plano)

    print(f"\n=======================================================")
    print(f"🗓️  Plano de Refeições Gerado com Sucesso!")
    print(f"=======================================================")
    print(f"Duração: {plano.dias} dias | Pessoas: {plano.pessoas} | Refeições diferentes: {plano.total_refeicoes_diferentes} | Refeições planeadas: {plano.total_refeicoes_planeadas}/{plano.total_refeicoes_alvo}")
    print(f"Plano guardado em: {ficheiro_plano}\n")

    print(f"Refeições selecionadas:")
    for i, it in enumerate(plano.itens, 1):
        escala_str = f"{it.fator_escala:.2f}x" if it.fator_escala != 1.0 else "1x"
        print(f"  {i}. {it.titulo}")
        print(f"     -> Cobre {it.refeicoes_cobertas} refeição(ões) | Confecionar {it.doses_necessarias} doses (Receita base: {it.doses_base} doses, escala: {escala_str})")

    # Gerar e imprimir lista de compras se solicitado
    gerador = GeradorListaCompras(catalogo)
    if args.lista_compras or args.exportar:
        texto_md = gerador.exportar_markdown(plano)
        if args.lista_compras:
            print("\n" + texto_md)
        if args.exportar:
            caminho_exp = Path(args.exportar)
            with open(caminho_exp, "w", encoding="utf-8") as f:
                f.write(texto_md)
            print(f"\n✅ Lista de compras exportada para: {caminho_exp}")
    else:
        print(f"\n💡 Para ver ou exportar a lista de compras, execute:")
        print(f"   python planner.py lista-compras [--exportar lista.md]")

    return 0


def comando_trocar(args) -> int:
    """Substitui uma refeição no plano ativo por outra."""
    ficheiro_plano = Path(args.ficheiro_plano)
    plano = PlanoRefeicoes.carregar(ficheiro_plano)
    if not plano:
        print(f"❌ Nenhum plano encontrado em '{ficheiro_plano}'. Crie um primeiro com 'python planner.py planear'.")
        return 1

    catalogo = carregar_todas_receitas(Path(args.pasta))

    try:
        plano, antigo, novo = trocar_refeicao_no_plano(
            plano=plano,
            catalogo=catalogo,
            termo_remover=args.remover,
            termo_adicionar=args.adicionar,
            novas_refeicoes_cobertas=args.refeicoes
        )
    except Exception as e:
        print(f"❌ Erro ao trocar refeição: {e}")
        return 1

    plano.guardar(ficheiro_plano)

    print(f"\n=======================================================")
    print(f"🔄 Refeição Substituída com Sucesso!")
    print(f"=======================================================")
    print(f"Removido:  {antigo.titulo} ({antigo.refeicoes_cobertas} refeições)")
    print(f"Adicionado: {novo.titulo} ({novo.refeicoes_cobertas} refeições, {novo.doses_necessarias} doses a cozinhar, escala: {novo.fator_escala:.2f}x)")
    print(f"Plano atualizado em: {ficheiro_plano}")

    if args.lista_compras or args.exportar:
        gerador = GeradorListaCompras(catalogo)
        texto_md = gerador.exportar_markdown(plano)
        if args.lista_compras:
            print("\n" + texto_md)
        if args.exportar:
            caminho_exp = Path(args.exportar)
            with open(caminho_exp, "w", encoding="utf-8") as f:
                f.write(texto_md)
            print(f"\n✅ Lista de compras atualizada exportada para: {caminho_exp}")

    return 0


def comando_lista_compras(args) -> int:
    """Gera e exibe a lista de compras para o plano guardado."""
    ficheiro_plano = Path(args.ficheiro_plano)
    plano = PlanoRefeicoes.carregar(ficheiro_plano)
    if not plano:
        print(f"❌ Nenhum plano encontrado em '{ficheiro_plano}'. Crie um plano primeiro com 'python planner.py planear'.")
        return 1

    catalogo = carregar_todas_receitas(Path(args.pasta))
    gerador = GeradorListaCompras(catalogo)
    texto_md = gerador.exportar_markdown(plano)

    print("\n" + texto_md)

    if args.exportar:
        caminho_exp = Path(args.exportar)
        with open(caminho_exp, "w", encoding="utf-8") as f:
            f.write(texto_md)
        print(f"✅ Lista de compras exportada para: {caminho_exp}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Guia de Receitas e Planeador de Lista de Compras (pt-PT)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de utilização:
  # 1. Listar todas as receitas
  python planner.py listar

  # 2. Planear para 1 semana (14 refeições) para 2 pessoas com seleção aleatória
  python planner.py planear --dias 7 --pessoas 2 --lista-compras

  # 3. Planear para 2 dias para 2 pessoas escolhendo apenas 1 refeição (doses aumentadas)
  python planner.py planear --dias 2 --pessoas 2 --escolher "bacalhau:4" --sem-aleatorio --lista-compras

  # 4. Planear escolhendo algumas e preenchendo as restantes aleatoriamente
  python planner.py planear --dias 7 --pessoas 2 --escolher "bolonhesa:4" --escolher "caril:2" --lista-compras

  # 5. Planear para 1 semana para 1 pessoa com apenas 2 refeições diferentes
  python planner.py planear --dias 7 --pessoas 1 --refeicoes-diferentes 2 --lista-compras

  # 6. Trocar uma refeição no plano atual
  python planner.py trocar --remover "caril" --adicionar "salmao" --lista-compras

  # 7. Ver ou exportar a lista de compras atual
  python planner.py lista-compras --exportar lista_compras.md
"""
    )
    parser.add_argument("--pasta", default=str(PASTA_RECEITAS_PADRAO), help="Pasta com os ficheiros de receitas (predefinição: recipes)")

    subparsers = parser.add_subparsers(dest="comando", help="Comando a executar")

    # Subcomando: listar (list)
    p_listar = subparsers.add_parser("listar", aliases=["list"], help="Lista todas as receitas disponíveis")
    p_listar.add_argument("-c", "--categoria", help="Filtrar por categoria (ex: Almoço, Rápido, Peixe)")
    p_listar.set_defaults(func=comando_listar)

    # Subcomando: ver (show)
    p_ver = subparsers.add_parser("ver", aliases=["detalhes", "show"], help="Mostra os detalhes de uma receita")
    p_ver.add_argument("receita", help="Nome ou ID da receita")
    p_ver.set_defaults(func=comando_ver)

    # Subcomando: planear (plan)
    p_planear = subparsers.add_parser("planear", aliases=["plan"], help="Gera um plano de refeições e ajusta doses")
    p_planear.add_argument("-d", "--dias", type=int, default=7, help="Número de dias do plano (predefinição: 7 dias)")
    p_planear.add_argument("-p", "--pessoas", type=int, default=2, help="Número de pessoas para quem cozinhar (predefinição: 2)")
    p_planear.add_argument("--refeicoes-dia", type=int, default=2, help="Refeições principais por dia (predefinição: 2, almoço e jantar)")
    p_planear.add_argument("-r", "--refeicoes", type=int, help="Número total de refeições explícito (ex: 14)")
    p_planear.add_argument("-e", "--escolher", action="append", help="Escolher receita manualmente e número de refeições cobertas. Ex: -e 'bolonhesa:4'")
    p_planear.add_argument("--sem-aleatorio", action="store_true", help="Não preencher automaticamente as refeições restantes com receitas aleatórias")
    p_planear.add_argument("--refeicoes-por-lote", type=int, default=2, help="Quantas refeições cada receita aleatória deve cobrir (predefinição: 2)")
    p_planear.add_argument("-rd", "--refeicoes-diferentes", "--receitas-diferentes", type=int, dest="refeicoes_diferentes", default=None, help="Número de receitas/refeições diferentes a incluir no plano (ex: 2)")
    p_planear.add_argument("--ficheiro-plano", default=str(FICHEIRO_PLANO_PADRAO), help="Ficheiro para guardar o estado do plano")
    p_planear.add_argument("--lista-compras", action="store_true", help="Apresentar de imediato a lista de compras gerada")
    p_planear.add_argument("-o", "--exportar", help="Caminho do ficheiro Markdown para exportar a lista de compras")
    p_planear.set_defaults(func=comando_planear)

    # Subcomando: trocar (swap)
    p_trocar = subparsers.add_parser("trocar", aliases=["swap"], help="Substitui uma refeição no plano ativo por outra")
    p_trocar.add_argument("-r", "--remover", required=True, help="Nome ou ID da receita a remover do plano")
    p_trocar.add_argument("-a", "--adicionar", required=True, help="Nome ou ID da nova receita a adicionar")
    p_trocar.add_argument("--refeicoes", type=int, help="Novo número de refeições cobertas (se omitido, mantém o anterior)")
    p_trocar.add_argument("--ficheiro-plano", default=str(FICHEIRO_PLANO_PADRAO), help="Ficheiro do plano ativo")
    p_trocar.add_argument("--lista-compras", action="store_true", help="Apresentar de imediato a lista de compras após a troca")
    p_trocar.add_argument("-o", "--exportar", help="Exportar a lista de compras atualizada para ficheiro Markdown")
    p_trocar.set_defaults(func=comando_trocar)

    # Subcomando: lista-compras (shopping-list)
    p_lista = subparsers.add_parser("lista-compras", aliases=["shopping-list", "compras"], help="Apresenta a lista de compras do plano ativo")
    p_lista.add_argument("--ficheiro-plano", default=str(FICHEIRO_PLANO_PADRAO), help="Ficheiro do plano ativo")
    p_lista.add_argument("-o", "--exportar", help="Caminho do ficheiro Markdown para exportar a lista de compras")
    p_lista.set_defaults(func=comando_lista_compras)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
