#!/usr/bin/env python3
"""Script de conveniência para iniciar a aplicação web local."""
import sys
from app import iniciar_servidor

if __name__ == "__main__":
    porta = 8000
    abrir_b = True
    if "--no-browser" in sys.argv:
        abrir_b = False
    iniciar_servidor(porta=porta, abrir_browser=abrir_b)
