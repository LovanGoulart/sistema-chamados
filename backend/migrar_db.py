"""
Script de migração do banco de dados - Sistema de Chamados

Este script adiciona colunas novas ao schema existente SEM apagar dados.
Use quando você adicionou novos campos nos modelos mas o banco já existe.

Como usar:
    python backend/migrar_db.py

O que ele faz:
    1. Verifica se a coluna já existe na tabela
    2. Se não existir, adiciona a coluna
    3. Nunca apaga dados existentes
"""
import os
import sys

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from backend.app import app
from backend.models.modelos import db
import sqlite3

def verificar_e_adicionar_coluna(conn, tabela, coluna, tipo_sql, padrao=None):
    """Verifica se a coluna existe e a adiciona se necessário."""
    cursor = conn.cursor()

    # Verificar colunas existentes
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas_existentes = [row[1] for row in cursor.fetchall()]

    if coluna in colunas_existentes:
        print(f"   ✅ Coluna '{coluna}' já existe em '{tabela}'")
        return False

    # Adicionar coluna
    sql = f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo_sql}"
    if padrao is not None:
        sql += f" DEFAULT {padrao}"

    cursor.execute(sql)
    conn.commit()
    print(f"   ➕ Coluna '{coluna}' adicionada em '{tabela}'")
    return True


def migrar_banco():
    with app.app_context():
        # Pegar caminho do banco SQLite
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if not db_uri.startswith('sqlite:///'):
            print("❌ Este script só funciona com SQLite.")
            print(f"   URI atual: {db_uri}")
            return

        db_path = db_uri.replace('sqlite:///', '')

        if not os.path.exists(db_path):
            print(f"❌ Banco de dados não encontrado: {db_path}")
            print("   O banco será criado automaticamente na primeira execução.")
            return

        print(f"🔧 Migrando banco: {db_path}")
        print()

        conn = sqlite3.connect(db_path)

        # Migrações necessárias
        # Adicione aqui novas colunas conforme você altera os modelos

        print("📋 Verificando tabela 'setores'...")
        verificar_e_adicionar_coluna(conn, 'setores', 'updated_at', 'DATETIME', 'CURRENT_TIMESTAMP')

        print("📋 Verificando tabela 'usuarios'...")
        verificar_e_adicionar_coluna(conn, 'usuarios', 'updated_at', 'DATETIME', 'CURRENT_TIMESTAMP')

        print("📋 Verificando tabela 'chamados'...")
        verificar_e_adicionar_coluna(conn, 'chamados', 'updated_at', 'DATETIME', 'CURRENT_TIMESTAMP')

        print("📋 Verificando tabela 'mensagens'...")
        # Nenhuma coluna nova por enquanto

        print("📋 Verificando tabela 'anexos'...")
        # Nenhuma coluna nova por enquanto

        print("📋 Verificando tabela 'logs_operacoes'...")
        # Nenhuma coluna nova por enquanto

        print("📋 Verificando tabela 'notificacoes'...")
        # Nenhuma coluna nova por enquanto

        conn.close()

        print()
        print("✅ Migração concluída! Seu banco está atualizado.")
        print("   Agora você pode iniciar a aplicação normalmente.")


if __name__ == '__main__':
    migrar_banco()