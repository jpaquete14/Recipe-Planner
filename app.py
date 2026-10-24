#!/usr/bin/env python3
"""
Servidor Web Local em Python (Standard Library) para o Recipe-Planner.
Serve a interface web gráfica e disponibiliza a API REST.
"""

import json
import mimetypes
import os
import re
import sys
import threading
import unicodedata
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, Optional

# Configurar saída UTF-8 para terminais Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.recipe_parser import carregar_todas_receitas, parse_receita_ficheiro, Receita
from src.planner import (
    PlanoRefeicoes,
    gerar_plano,
    trocar_refeicao_no_plano,
    encontrar_receita
)
from src.shopping_list import GeradorListaCompras

PASTA_BASE = Path(__file__).parent.resolve()
PASTA_RECEITAS = PASTA_BASE / "recipes"
PASTA_WEB = PASTA_BASE / "web"
FICHEIRO_PLANO = PASTA_BASE / ".plano_atual.json"


def slugificar(texto: str) -> str:
    """Gera um slug seguro a partir de um título em português."""
    texto_norm = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    slug = re.sub(r"[^\w\s-]", "", texto_norm).strip().lower()
    return re.sub(r"[-\s]+", "_", slug)


def formatar_conteudo_receita(
    titulo: str,
    doses: int,
    tempo_prep: str = "",
    tempo_coz: str = "",
    categoria: str = "",
    dificuldade: str = "Fácil",
    ingredientes_texto: str = "",
    instrucoes_texto: str = "",
    notas_texto: str = ""
) -> str:
    """Formata os campos da receita no formato padronizado de ficheiro .txt."""
    linhas = []
    linhas.append(f"Título: {titulo}")
    linhas.append(f"Doses: {doses}")
    if tempo_prep:
        linhas.append(f"Tempo de Preparação: {tempo_prep}")
    if tempo_coz:
        linhas.append(f"Tempo de Cozedura: {tempo_coz}")
    if categoria:
        linhas.append(f"Categoria: {categoria}")
    if dificuldade:
        linhas.append(f"Dificuldade: {dificuldade}")
    linhas.append("")

    linhas.append("Ingredientes:")
    for ing in ingredientes_texto.split("\n"):
        ing_limpo = ing.strip()
        if not ing_limpo:
            continue
        if not ing_limpo.startswith(("-", "*", "•")):
            ing_limpo = f"- {ing_limpo}"
        linhas.append(ing_limpo)
    linhas.append("")

    linhas.append("Instruções:")
    idx = 1
    for inst in instrucoes_texto.split("\n"):
        inst_limpa = inst.strip()
        if not inst_limpa:
            continue
        if not re.match(r"^\d+\.", inst_limpa):
            inst_limpa = f"{idx}. {inst_limpa}"
            idx += 1
        linhas.append(inst_limpa)
    linhas.append("")

    if notas_texto:
        linhas.append("Notas:")
        for n in notas_texto.split("\n"):
            n_limpa = n.strip()
            if not n_limpa:
                continue
            if not n_limpa.startswith(("-", "*", "•")):
                n_limpa = f"- {n_limpa}"
            linhas.append(n_limpa)
        linhas.append("")

    return "\n".join(linhas)


def serializar_plano_e_compras(plano: PlanoRefeicoes, catalogo: Dict[str, Receita]) -> Dict[str, Any]:
    """Serializa o plano e os itens de compra para JSON."""
    gerador = GeradorListaCompras(catalogo)
    itens_agrupados = gerador.gerar(plano)
    markdown_compras = gerador.exportar_markdown(plano)

    seccoes_json = {}
    for seccao, lista_itens in itens_agrupados.items():
        seccoes_json[seccao] = []
        for it in lista_itens:
            seccoes_json[seccao].append({
                "nome": it.nome,
                "quantidade_str": it.formatar_quantidade(),
                "receitas": sorted(list(it.receitas_origem)),
                "detalhes": sorted(list(it.detalhes_combinados))
            })

    return {
        "plano": plano.to_dict(),
        "lista_compras": {
            "seccoes": seccoes_json,
            "markdown": markdown_compras
        }
    }


class RecipeHandler(BaseHTTPRequestHandler):
    """Manipulador HTTP para servir a aplicação web e os endpoints REST."""

    def end_headers(self):
        # Permitir requisições locais CORS se necessário
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def responder_json(self, dados: Any, status: int = 200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def responder_erro(self, mensagem: str, status: int = 400):
        self.responder_json({"sucesso": False, "erro": mensagem}, status=status)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        caminho = parsed_url.path

        # 1. API: Listar Receitas
        if caminho == "/api/receitas":
            catalogo = carregar_todas_receitas(PASTA_RECEITAS)
            unicas = sorted({r.id: r for r in catalogo.values()}.values(), key=lambda x: x.titulo)
            lista = []
            for r in unicas:
                lista.append({
                    "id": r.id,
                    "titulo": r.titulo,
                    "doses": r.doses,
                    "tempo_preparacao": r.tempo_preparacao,
                    "tempo_cozedura": r.tempo_cozedura,
                    "tempo_total": r.tempo_total,
                    "categoria": r.categoria,
                    "dificuldade": r.dificuldade,
                    "total_ingredientes": len(r.ingredientes),
                    "ficheiro": r.caminho_ficheiro.name
                })
            self.responder_json({"sucesso": True, "receitas": lista})
            return

        # 2. API: Obter Detalhes de uma Receita
        if caminho.startswith("/api/receitas/"):
            rec_id = urllib.parse.unquote(caminho[len("/api/receitas/"):])
            catalogo = carregar_todas_receitas(PASTA_RECEITAS)
            rec = encontrar_receita(rec_id, catalogo)
            if not rec:
                self.responder_erro("Receita não encontrada", 404)
                return

            detalhes = {
                "id": rec.id,
                "titulo": rec.titulo,
                "doses": rec.doses,
                "tempo_preparacao": rec.tempo_preparacao,
                "tempo_cozedura": rec.tempo_cozedura,
                "categoria": rec.categoria,
                "categoria_str": ", ".join(rec.categoria) if isinstance(rec.categoria, list) else str(rec.categoria),
                "dificuldade": rec.dificuldade,
                "ingredientes": [
                    {
                        "texto": ing.formatar(),
                        "categoria": ing.categoria,
                        "quantidade": ing.quantidade,
                        "unidade": ing.unidade,
                        "nome": ing.nome,
                        "detalhes": ing.detalhes
                    }
                    for ing in rec.ingredientes
                ],
                "ingredientes_bruto": "\n".join(
                    ing.texto_original if ing.texto_original.startswith(("-", "*", "•")) else f"- {ing.texto_original}"
                    for ing in rec.ingredientes
                ),
                "instrucoes": rec.instrucoes,
                "instrucoes_bruto": "\n".join(rec.instrucoes),
                "notas": rec.notas,
                "notas_bruto": "\n".join(rec.notas)
            }
            self.responder_json({"sucesso": True, "receita": detalhes})
            return

        # 3. API: Obter Plano Atual Guardado
        if caminho == "/api/plano":
            plano = PlanoRefeicoes.carregar(FICHEIRO_PLANO)
            if not plano:
                self.responder_json({"sucesso": True, "plano": None})
                return

            catalogo = carregar_todas_receitas(PASTA_RECEITAS)
            resultado = serializar_plano_e_compras(plano, catalogo)
            self.responder_json({"sucesso": True, **resultado})
            return

        # 4. Servir ficheiros estáticos da pasta web/
        ficheiro_alvo = PASTA_WEB / (caminho.lstrip("/") or "index.html")
        if not ficheiro_alvo.exists() or not ficheiro_alvo.is_file():
            ficheiro_alvo = PASTA_WEB / "index.html"

        if ficheiro_alvo.exists():
            tipo_mime, _ = mimetypes.guess_type(str(ficheiro_alvo))
            tipo_mime = tipo_mime or "application/octet-stream"
            with open(ficheiro_alvo, "rb") as f:
                conteudo = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{tipo_mime}; charset=utf-8" if "text" in tipo_mime or "javascript" in tipo_mime or "json" in tipo_mime else tipo_mime)
            self.send_header("Content-Length", str(len(conteudo)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(conteudo)
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 Nao Encontrado")

    def ler_json_corpo(self) -> Optional[Dict[str, Any]]:
        """Lê e converte o corpo da requisição para um dicionário Python."""
        comprimento = int(self.headers.get("Content-Length", 0))
        corpo_raw = self.rfile.read(comprimento).decode("utf-8") if comprimento > 0 else "{}"
        try:
            return json.loads(corpo_raw)
        except json.JSONDecodeError:
            self.responder_erro("JSON inválido no corpo da requisição")
            return None

    def do_PUT(self):
        parsed_url = urllib.parse.urlparse(self.path)
        caminho = parsed_url.path

        if caminho.startswith("/api/receitas/"):
            rec_id = urllib.parse.unquote(caminho[len("/api/receitas/"):])
            dados = self.ler_json_corpo()
            if dados is not None:
                self.salvar_receita(dados, rec_id_editar=rec_id)
            return

        self.responder_erro("Endpoint não encontrado", 404)

    def salvar_receita(self, dados: Dict[str, Any], rec_id_editar: Optional[str] = None):
        titulo = dados.get("titulo", "").strip()
        if not titulo:
            self.responder_erro("O título da receita é obrigatório")
            return

        try:
            doses = int(dados.get("doses", 4))
            if doses < 1:
                doses = 1
        except (ValueError, TypeError):
            doses = 4

        tempo_prep = dados.get("tempo_preparacao", "").strip()
        tempo_coz = dados.get("tempo_cozedura", "").strip()
        categoria = dados.get("categoria", "").strip()
        dificuldade = dados.get("dificuldade", "Fácil").strip()
        ingredientes_texto = dados.get("ingredientes", "").strip()
        instrucoes_texto = dados.get("instrucoes", "").strip()
        notas_texto = dados.get("notas", "").strip()

        if not ingredientes_texto:
            self.responder_erro("A lista de ingredientes é obrigatória")
            return

        if not instrucoes_texto:
            self.responder_erro("O modo de preparação / instruções é obrigatório")
            return

        conteudo = formatar_conteudo_receita(
            titulo=titulo,
            doses=doses,
            tempo_prep=tempo_prep,
            tempo_coz=tempo_coz,
            categoria=categoria,
            dificuldade=dificuldade,
            ingredientes_texto=ingredientes_texto,
            instrucoes_texto=instrucoes_texto,
            notas_texto=notas_texto
        )

        catalogo = carregar_todas_receitas(PASTA_RECEITAS)

        if rec_id_editar:
            # Modo Edição
            rec = encontrar_receita(rec_id_editar, catalogo)
            if not rec:
                self.responder_erro("Receita não encontrada para edição", 404)
                return

            novo_slug = slugificar(titulo)
            novo_caminho = PASTA_RECEITAS / f"{novo_slug}.txt"

            # Se mudou o nome e já existe outro ficheiro com esse nome
            if novo_caminho != rec.caminho_ficheiro and novo_caminho.exists():
                self.responder_erro(f"Já existe outra receita com o título '{titulo}'.", 400)
                return

            with open(novo_caminho, "w", encoding="utf-8") as f:
                f.write(conteudo)

            # Se o ficheiro foi renomeado, remover o antigo
            if novo_caminho != rec.caminho_ficheiro and rec.caminho_ficheiro.exists():
                try:
                    rec.caminho_ficheiro.unlink()
                except Exception:
                    pass

            # Atualizar plano ativo se esta receita estiver presente
            if FICHEIRO_PLANO.exists():
                try:
                    plano = PlanoRefeicoes.carregar(FICHEIRO_PLANO)
                    if plano:
                        atualizou_plano = False
                        for item in plano.itens:
                            if item.receita_id == rec.id or item.receita_id == rec_id_editar:
                                item.receita_id = novo_slug
                                item.titulo = titulo
                                item.doses_base = doses
                                item.fator_escala = (plano.pessoas * item.refeicoes_cobertas) / item.doses_base
                                item.doses_necessarias = plano.pessoas * item.refeicoes_cobertas
                                atualizou_plano = True
                        if atualizou_plano:
                            plano.guardar(FICHEIRO_PLANO)
                except Exception as e:
                    print(f"Aviso ao atualizar plano após edição: {e}")

            self.responder_json({
                "sucesso": True,
                "mensagem": f"Receita '{titulo}' atualizada com sucesso!",
                "ficheiro": novo_caminho.name,
                "id": novo_slug
            })
            return

        # Modo Criação
        nome_ficheiro = f"{slugificar(titulo)}.txt"
        caminho_ficheiro = PASTA_RECEITAS / nome_ficheiro

        with open(caminho_ficheiro, "w", encoding="utf-8") as f:
            f.write(conteudo)

        self.responder_json({
            "sucesso": True,
            "mensagem": f"Receita '{titulo}' guardada com sucesso!",
            "ficheiro": nome_ficheiro,
            "id": caminho_ficheiro.stem
        })

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        caminho = parsed_url.path

        dados = self.ler_json_corpo()
        if dados is None:
            return

        # 1. API: Criar ou Editar Receita
        if caminho == "/api/receitas":
            self.salvar_receita(dados, rec_id_editar=None)
            return

        if caminho.startswith("/api/receitas/"):
            rec_id = urllib.parse.unquote(caminho[len("/api/receitas/"):])
            self.salvar_receita(dados, rec_id_editar=rec_id)
            return

        # 2. API: Planear Refeições
        if caminho == "/api/planear":
            catalogo = carregar_todas_receitas(PASTA_RECEITAS)
            dias = int(dados.get("dias", 7))
            pessoas = int(dados.get("pessoas", 2))
            refeicoes_dia = int(dados.get("refeicoes_dia", 2))
            total_refeicoes = dados.get("total_refeicoes")
            if total_refeicoes is not None:
                total_refeicoes = int(total_refeicoes)

            escolhas_raw = dados.get("escolhas", [])
            escolhas = []
            for item in escolhas_raw:
                if isinstance(item, dict):
                    escolhas.append((item.get("receita_id", ""), int(item.get("refeicoes", 0))))
                elif isinstance(item, list) and len(item) == 2:
                    escolhas.append((str(item[0]), int(item[1])))

            preencher_aleatorio = bool(dados.get("preencher_aleatorio", True))
            refeicoes_por_lote = int(dados.get("refeicoes_por_lote", 2))
            refeicoes_diferentes_raw = dados.get("refeicoes_diferentes")
            refeicoes_diferentes = None
            if refeicoes_diferentes_raw is not None and str(refeicoes_diferentes_raw).strip() != "":
                try:
                    refeicoes_diferentes = int(refeicoes_diferentes_raw)
                except (ValueError, TypeError):
                    refeicoes_diferentes = None

            escalar_selecionadas = dados.get("escalar_selecionadas")
            if escalar_selecionadas is not None:
                escalar_selecionadas = bool(escalar_selecionadas)
            else:
                escalar_selecionadas = not preencher_aleatorio

            try:
                plano = gerar_plano(
                    catalogo=catalogo,
                    dias=dias,
                    pessoas=pessoas,
                    refeicoes_por_dia=refeicoes_dia,
                    total_refeicoes_explicito=total_refeicoes,
                    escolhas_manuais=escolhas,
                    preencher_aleatorio=preencher_aleatorio,
                    refeicoes_por_lote_aleatorio=refeicoes_por_lote,
                    escalar_escolhas=escalar_selecionadas,
                    refeicoes_diferentes=refeicoes_diferentes
                )
                plano.guardar(FICHEIRO_PLANO)
                resultado = serializar_plano_e_compras(plano, catalogo)
                self.responder_json({"sucesso": True, **resultado})
            except Exception as e:
                self.responder_erro(str(e))
            return

        # 3. API: Trocar Refeição
        if caminho == "/api/trocar":
            catalogo = carregar_todas_receitas(PASTA_RECEITAS)
            plano = PlanoRefeicoes.carregar(FICHEIRO_PLANO)
            if not plano:
                self.responder_erro("Nenhum plano ativo encontrado. Crie um plano primeiro.")
                return

            remover = dados.get("remover", "").strip()
            adicionar = dados.get("adicionar", "").strip()
            novas_refeicoes = dados.get("refeicoes")

            try:
                plano, antigo, novo = trocar_refeicao_no_plano(
                    plano=plano,
                    catalogo=catalogo,
                    termo_remover=remover,
                    termo_adicionar=adicionar,
                    novas_refeicoes_cobertas=int(novas_refeicoes) if novas_refeicoes else None
                )
                plano.guardar(FICHEIRO_PLANO)
                resultado = serializar_plano_e_compras(plano, catalogo)
                self.responder_json({
                    "sucesso": True,
                    "removido": antigo.titulo,
                    "adicionado": novo.titulo,
                    **resultado
                })
            except Exception as e:
                self.responder_erro(str(e))
            return

        self.responder_erro("Endpoint não encontrado", 404)


def obter_ip_local() -> str:
    """Obtém o endereço IP local na rede Wi-Fi/Ethernet."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def iniciar_servidor(porta: int = 8000, abrir_browser: bool = True):
    """Inicia o servidor HTTP local."""
    endereco = ("", porta)
    # Tenta usar a porta, incrementando se estiver ocupada
    servidor = None
    for p in range(porta, porta + 10):
        try:
            servidor = HTTPServer(("", p), RecipeHandler)
            porta = p
            break
        except OSError:
            continue

    if not servidor:
        print(f"❌ Não foi possível iniciar o servidor nas portas {porta}-{porta+9}.")
        sys.exit(1)

    url_local = f"http://localhost:{porta}"
    ip_rede = obter_ip_local()
    url_rede = f"http://{ip_rede}:{porta}"

    print(f"\n=======================================================")
    print(f"🚀 Servidor Web do Recipe-Planner ativo!")
    print(f"💻 No seu computador: {url_local}")
    if ip_rede != "127.0.0.1":
        print(f"📱 No seu telemóvel (no mesmo Wi-Fi): {url_rede}")
    print(f"=======================================================")
    print(f"Pressione Ctrl+C para encerrar o servidor.\n")

    if abrir_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url_local)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado.")
        servidor.server_close()


if __name__ == "__main__":
    porta_arg = 8000
    abrir_b = True
    if "--no-browser" in sys.argv:
        abrir_b = False
    iniciar_servidor(porta=porta_arg, abrir_browser=abrir_b)
