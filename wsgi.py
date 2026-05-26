#!/usr/bin/env python3
"""
WSGI entry point - Sistema de Chamados - Colégio Mauá
"""
import os
import sys

# Adicionar o diretório do projeto ao path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Agora os imports funcionam
from backend.app import app

if __name__ == '__main__':
    print("=" * 60)
    print("SISTEMA DE CHAMADOS - COLÉGIO MAUÁ")
    print("=" * 60)
    print("Acesse: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
