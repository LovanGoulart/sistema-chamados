
"""
Script de migração para adicionar coluna 'solucao_tecnica' na tabela 'chamados'
Execute este script UMA VEZ para atualizar o banco de dados existente.

Como usar:
1. Certifique-se de que o servidor Flask está PARADO
2. Execute: python migrar_solucao_tecnica.py
3. O script adicionará a coluna ao banco SQLite existente
4. Inicie o servidor normalmente
"""

import sqlite3
import os
import sys

# Ajuste o caminho conforme sua estrutura de projeto
# Exemplo: database_path = 'instance/chamados.db'
# Ou descubra o caminho pela config do Flask

def descobrir_caminho_db():
    """Tenta descobrir o caminho do banco de dados."""
    possiveis_caminhos = [
        'database/chamados.db',
        'chamados.db',
        'backend/database/chamados.db',
        '../database/chamados.db',
        os.path.join(os.path.dirname(__file__), 'database', 'chamados.db'),
        os.path.join(os.path.dirname(__file__), '..', 'database', 'chamados.db'),
    ]
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            return caminho
    return None

def migrar():
    db_path = descobrir_caminho_db()

    if not db_path:
        print("❌ Não foi possível encontrar o banco de dados.")
        print("   Caminhos tentados:")
        for p in ['database/chamados.db', 'chamados.db', 'backend/database/chamados.db']:
            print(f"   - {p}")
        print("\n   Informe o caminho manualmente editando este script.")
        return

    print(f"📁 Banco encontrado: {db_path}")
    print("🔧 Adicionando coluna 'solucao_tecnica' à tabela 'chamados'...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(chamados)")
        colunas = [col[1] for col in cursor.fetchall()]

        if 'solucao_tecnica' in colunas:
            print("✅ Coluna 'solucao_tecnica' já existe. Nada a fazer.")
            conn.close()
            return

        # Adicionar a coluna
        cursor.execute("ALTER TABLE chamados ADD COLUMN solucao_tecnica TEXT")
        conn.commit()

        print("✅ Coluna 'solucao_tecnica' adicionada com sucesso!")
        print("\n🚀 Agora você pode:")
        print("   1. Atualizar o modelo (modelos.py)")
        print("   2. Atualizar as rotas (rotas.py)")
        print("   3. Atualizar o template (chamado_detalhe.html)")
        print("   4. Iniciar o servidor Flask")

    except sqlite3.Error as e:
        print(f"❌ Erro ao migrar: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrar()