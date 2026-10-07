#!/usr/bin/env python3
"""Script para criar o atalho da aplicação no Ambiente de Trabalho (Ecrã Inicial)."""

import os
import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).parent.resolve()
IMG_ORIGEM = REPO_ROOT / "eeb718f1-a947-4011-90ad-0fd144bf7080.jpg"
ICONE_ICO = REPO_ROOT / "icone.ico"
BAT_ALVO = REPO_ROOT / "iniciar.bat"


def gerar_icone():
    """Converte a imagem JPG para ficheiro .ico com vários tamanhos."""
    if not ICONE_ICO.exists() or (IMG_ORIGEM.exists() and IMG_ORIGEM.stat().st_mtime > ICONE_ICO.stat().st_mtime):
        print("A gerar ficheiro de ícone icone.ico a partir da imagem...")
        img = Image.open(IMG_ORIGEM)
        img.save(
            ICONE_ICO,
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        )
        print("Ícone gerado com sucesso.")


def criar_atalho():
    """Cria o atalho .lnk no Ambiente de Trabalho do utilizador."""
    gerar_icone()

    # Caminho do Desktop
    import subprocess
    cmd = """
    $WshShell = New-Object -ComObject WScript.Shell
    $Desktop = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
    $ShortcutPath = Join-Path $Desktop "Recipe Planner.lnk"
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "{bat}"
    $Shortcut.WorkingDirectory = "{cwd}"
    $Shortcut.IconLocation = "{icon},0"
    $Shortcut.Description = "Recipe Planner — Guia de Receitas e Lista de Compras"
    $Shortcut.Save()
    Write-Output $ShortcutPath
    """.format(
        bat=str(BAT_ALVO),
        cwd=str(REPO_ROOT),
        icon=str(ICONE_ICO)
    )

    proc = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    if proc.returncode == 0:
        caminho_criado = proc.stdout.strip()
        print(f"✅ Atalho criado com sucesso em: {caminho_criado}")
        return caminho_criado
    else:
        print(f"Erro ao criar atalho: {proc.stderr}")
        return None


if __name__ == "__main__":
    criar_atalho()
