@echo off
chcp 65001 >nul
title Recipe Planner — Guia de Receitas e Lista de Compras
echo ================================================================
echo  🍳 Recipe Planner — A iniciar o servidor e a abrir o navegador...
echo ================================================================
echo.
echo Se o navegador nao abrir automaticamente, aceda a:
echo No computador: http://localhost:8000
echo No telemovel (mesmo Wi-Fi): veja o IP indicado abaixo
echo.
echo Para fechar a aplicacao, feche esta janela.
echo ================================================================
echo.
python app.py
pause
