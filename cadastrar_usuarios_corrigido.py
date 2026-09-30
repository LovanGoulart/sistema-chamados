#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
 CADASTRO EM MASSA DE USUÁRIOS — Sistema de Chamados Mauá
============================================================

Lê a planilha Excel (Nome / E-mail) e cadastra/atualiza os
usuários no banco de dados do sistema de chamados.

REGRAS:
  - Senha padrão para TODOS os novos cadastros: 123456 (bcrypt)
  - Perfil correto no banco: USUARIO
  - Setor de destino: Usuário
  - Usuários que já existem são atualizados para o setor Usuário
  - Perfis antigos gravados como "usuario" são corrigidos para "USUARIO"
  - E-mails duplicados DENTRO da planilha são cadastrados uma única vez
  - Usuários já existentes não têm a senha alterada

COMO USAR
---------
1) OFFLINE (SQLite local):

       python cadastrar_usuarios.py

2) BANCO ESPECÍFICO:

       python cadastrar_usuarios.py --db caminho/do/chamados.db

3) PYTHONANYWHERE (MySQL):

       python cadastrar_usuarios.py --online

GERA TAMBÉM um relatório:
       cadastros_realizados.csv
============================================================
"""

import os
import sys
import csv
import glob
import argparse
import re
import unicodedata

# ------------------------------------------------------------
# CONFIGURAÇÕES
# ------------------------------------------------------------

CAMINHO_EXCEL = "planilha_organizada.xlsx"

SENHA_PADRAO = "123456"

# Todos os usuários cadastrados por esta planilha ficarão neste setor.
SETOR_NOME = "Usuário"

# Banco OFFLINE
DB_URL_OFFLINE = os.environ.get(
    "DB_URL_OFFLINE",
    "sqlite:///chamados.db"
)

# Banco ONLINE (PythonAnywhere)
DB_URL_ONLINE = os.environ.get(
    "DB_URL_ONLINE",
    "mysql+pymysql://USUARIO:SENHA@HOST.mysql.pythonanywhere-services.com/USUARIO$chamados"
)

# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------

try:
    import bcrypt
except ImportError:
    sys.exit("Instale o bcrypt: pip install bcrypt")

try:
    import pandas as pd
except ImportError:
    sys.exit("Instale o pandas: pip install pandas openpyxl")

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


# ------------------------------------------------------------
# MODELOS
# ------------------------------------------------------------

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    senha_hash = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=True)

    # IMPORTANTE:
    # O Enum do sistema aceita:
    # ADMIN, SETOR, USUARIO
    perfil = Column(String(20), nullable=False, default="USUARIO")

    ativo = Column(Boolean, nullable=False, default=True)
    setor_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    ultimo_acesso = Column(DateTime, nullable=True)


class Setor(Base):
    __tablename__ = "setores"

    id = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)


# ------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------------------------------------

def normalizar_texto(valor):
    """
    Normaliza texto para comparação:
    - converte para string
    - remove espaços extras
    - remove acentos
    - converte para minúsculas
    """
    if valor is None:
        return ""

    valor = str(valor).strip().lower()

    return "".join(
        c
        for c in unicodedata.normalize("NFKD", valor)
        if not unicodedata.combining(c)
    )


def detectar_banco_local():
    """Procura o arquivo .db do projeto a partir da pasta do script."""
    raiz = os.path.dirname(os.path.abspath(__file__))
    candidatos = []

    for padrao in ("**/*.db", "**/*.sqlite", "**/*.sqlite3"):
        candidatos.extend(
            glob.glob(
                os.path.join(raiz, padrao),
                recursive=True
            )
        )

    # Ignora arquivos temporários
    candidatos = [
        c for c in candidatos
        if not os.path.basename(c).startswith(("~$",))
    ]

    if not candidatos:
        return None

    # O banco real normalmente será o maior arquivo.
    candidatos.sort(
        key=os.path.getsize,
        reverse=True
    )

    return candidatos[0]


EMAIL_RE = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


# ------------------------------------------------------------
# PLANILHA
# ------------------------------------------------------------

def carregar_planilha(caminho):
    """Lê a planilha, limpa e remove duplicados/inválidos."""

    if not os.path.exists(caminho):
        sys.exit(
            f"Arquivo não encontrado: {caminho}"
        )

    df = pd.read_excel(caminho)

    df.columns = [
        str(c).strip().lower()
        for c in df.columns
    ]

    if "nome" not in df.columns or "email" not in df.columns:
        sys.exit(
            "A planilha precisa ter as colunas 'Nome' e 'Email'."
        )

    df = df[["nome", "email"]].copy()

    df["nome"] = (
        df["nome"]
        .astype(str)
        .str.strip()
    )

    df["email"] = (
        df["email"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Remove linhas vazias e cabeçalhos repetidos.
    df = df[
        (df["nome"] != "")
        & (df["email"] != "")
        & (df["nome"].str.lower() != "nome")
    ]

    # Remove e-mails inválidos.
    invalidos = df[
        ~df["email"].str.match(EMAIL_RE)
    ]

    if len(invalidos):
        print(
            f"[!] {len(invalidos)} e-mail(s) inválido(s) ignorados:"
        )

        for _, r in invalidos.iterrows():
            print(
                f"    - {r['nome']}: {r['email']}"
            )

    df = df[
        df["email"].str.match(EMAIL_RE)
    ]

    # Remove duplicados da própria planilha.
    antes = len(df)

    df = df.drop_duplicates(
        subset="email",
        keep="first"
    )

    duplicados = antes - len(df)

    if duplicados:
        print(
            f"[!] {duplicados} e-mail(s) "
            "duplicados na planilha ignorados."
        )

    return df.to_dict("records")


# ------------------------------------------------------------
# SENHA
# ------------------------------------------------------------

def gerar_hash(senha):
    """Gera hash bcrypt compatível com o sistema."""

    return bcrypt.hashpw(
        senha.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


# ------------------------------------------------------------
# SETOR
# ------------------------------------------------------------

def localizar_setor(session):
    """
    Localiza o setor Usuário.

    A comparação ignora:
    - maiúsculas/minúsculas
    - acentos

    Portanto:
        Usuário
        usuario
        USUÁRIO
        USUARIO

    serão considerados o mesmo setor para esta busca.
    """

    setores = session.query(Setor).all()

    nome_desejado = normalizar_texto(SETOR_NOME)

    for setor in setores:
        if normalizar_texto(setor.nome) == nome_desejado:
            return setor

    nomes = [
        setor.nome
        for setor in setores
    ]

    sys.exit(
        "\n[ERRO] O setor 'Usuário' não foi encontrado.\n"
        f"Setores existentes no banco: {nomes}\n\n"
        "Crie o setor 'Usuário' no sistema e execute "
        "este script novamente."
    )


# ------------------------------------------------------------
# CORREÇÃO DO ENUM
# ------------------------------------------------------------

def corrigir_perfis_antigos(session):
    """
    Corrige registros antigos que tenham sido gravados como
    'usuario' em vez de 'USUARIO'.

    Isso é feito com SQL direto porque a coluna real pode ser
    um ENUM do MySQL. Assim evitamos que o SQLAlchemy tente
    converter o valor antigo antes de conseguirmos corrigi-lo.
    """

    resultado = session.execute(
        text("""
            UPDATE usuarios
            SET perfil = 'USUARIO'
            WHERE LOWER(perfil) = 'usuario'
        """)
    )

    quantidade = resultado.rowcount or 0

    if quantidade:
        session.commit()
        print(
            f"[OK] Perfis corrigidos de 'usuario' para "
            f"'USUARIO': {quantidade}"
        )

    return quantidade


# ------------------------------------------------------------
# CADASTRO / ATUALIZAÇÃO
# ------------------------------------------------------------

def cadastrar(db_url, registros):
    """
    Cadastra novos usuários e atualiza os usuários da planilha
    que já existem.

    Todos os usuários da planilha ficam:
        perfil = USUARIO
        setor  = Usuário

    A senha de usuários existentes NÃO é alterada.
    """

    engine = create_engine(
        db_url,
        pool_pre_ping=True
    )

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print(
            f"\nBanco: "
            f"{db_url.split('@')[-1] if '@' in db_url else db_url}"
        )

        # ----------------------------------------------------
        # 1. Corrige perfis antigos
        # ----------------------------------------------------

        corrigir_perfis_antigos(session)

        # ----------------------------------------------------
        # 2. Localiza o setor Usuário
        # ----------------------------------------------------

        setor = localizar_setor(session)
        setor_id = setor.id

        print(
            f"[OK] Setor de destino: "
            f"'{setor.nome}' (id={setor_id})"
        )

        # ----------------------------------------------------
        # 3. Busca usuários existentes
        # ----------------------------------------------------

        usuarios_existentes = {
            email.lower(): usuario
            for usuario in session.query(Usuario).all()
            if usuario.email
        }

        print(
            "Usuários já cadastrados no banco: "
            f"{len(usuarios_existentes)}"
        )

        # ----------------------------------------------------
        # 4. Hash para novos usuários
        # ----------------------------------------------------

        hash_senha = gerar_hash(
            SENHA_PADRAO
        )

        novos = []
        atualizados = []
        ignorados = []

        # ----------------------------------------------------
        # 5. Processa a planilha
        # ----------------------------------------------------

        for registro in registros:

            email = registro["email"].strip().lower()

            usuario_existente = (
                usuarios_existentes.get(email)
            )

            if usuario_existente is None:

                novo_usuario = Usuario(
                    nome=registro["nome"],
                    email=email,
                    senha_hash=hash_senha,
                    telefone=None,

                    # IMPORTANTE:
                    # O Enum do sistema aceita USUARIO.
                    perfil="USUARIO",

                    ativo=True,
                    setor_id=setor_id,
                )

                novos.append(novo_usuario)

            else:
                # Usuário já existe:
                # não recria e não altera a senha.
                alterou = False

                if usuario_existente.perfil != "USUARIO":
                    usuario_existente.perfil = "USUARIO"
                    alterou = True

                if usuario_existente.setor_id != setor_id:
                    usuario_existente.setor_id = setor_id
                    alterou = True

                if not usuario_existente.ativo:
                    usuario_existente.ativo = True
                    alterou = True

                if alterou:
                    atualizados.append(
                        usuario_existente
                    )
                else:
                    ignorados.append(
                        registro
                    )

        # ----------------------------------------------------
        # 6. Insere novos usuários
        # ----------------------------------------------------

        if novos:
            session.bulk_save_objects(novos)

        # ----------------------------------------------------
        # 7. Salva atualizações dos existentes
        # ----------------------------------------------------

        session.commit()

        # ----------------------------------------------------
        # 8. Relatório
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print(" RESULTADO DO CADASTRO")
        print("=" * 60)

        print(
            f" Lidos da planilha : {len(registros)}"
        )

        print(
            f" NOVOS cadastros   : {len(novos)}"
        )

        print(
            f" ATUALIZADOS       : {len(atualizados)}"
        )

        print(
            f" SEM ALTERAÇÃO     : {len(ignorados)}"
        )

        print(
            f" PERFIL             : USUARIO"
        )

        print(
            f" SETOR              : {setor.nome}"
        )

        print("=" * 60)

        # ----------------------------------------------------
        # 9. CSV
        # ----------------------------------------------------

        with open(
            "cadastros_realizados.csv",
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.writer(f)

            writer.writerow(
                [
                    "nome",
                    "email",
                    "status",
                    "perfil",
                    "setor"
                ]
            )

            for usuario in novos:
                writer.writerow(
                    [
                        usuario.nome,
                        usuario.email,
                        "CADASTRADO",
                        "USUARIO",
                        setor.nome
                    ]
                )

            for usuario in atualizados:
                writer.writerow(
                    [
                        usuario.nome,
                        usuario.email,
                        "ATUALIZADO",
                        "USUARIO",
                        setor.nome
                    ]
                )

            for registro in ignorados:
                writer.writerow(
                    [
                        registro["nome"],
                        registro["email"],
                        "JA_ESTAVA_CORRETO",
                        "USUARIO",
                        setor.nome
                    ]
                )

        print(
            "\nRelatório salvo em: "
            "cadastros_realizados.csv"
        )

    except Exception as e:
        session.rollback()

        print(
            f"\n[ERRO] {e}"
        )

        sys.exit(1)

    finally:
        session.close()


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Cadastro em massa de usuários"
    )

    parser.add_argument(
        "--online",
        action="store_true",
        help="Usa o banco do PythonAnywhere (MySQL)"
    )

    parser.add_argument(
        "--db",
        default=None,
        help=(
            "Caminho manual do banco SQLite "
            "(ex: --db backend/chamados.db)"
        )
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Seleção do banco
    # --------------------------------------------------------

    if args.online:

        db_url = DB_URL_ONLINE

    elif args.db:

        db_url = (
            "sqlite:///"
            + os.path.abspath(args.db)
        )

    elif DB_URL_OFFLINE != "sqlite:///chamados.db":

        db_url = DB_URL_OFFLINE

    else:

        db_local = detectar_banco_local()

        if db_local:

            db_url = (
                "sqlite:///"
                + db_local
            )

            print(
                "Banco local detectado automaticamente: "
                f"{db_local}"
            )

        else:

            db_url = DB_URL_OFFLINE

            print(
                "AVISO: nenhum arquivo .db encontrado "
                "no projeto."
            )

            print(
                "Use --db para informar o caminho do banco."
            )

    # --------------------------------------------------------
    # Validação do banco online
    # --------------------------------------------------------

    if args.online and (
        "USUARIO" in db_url
        or "SENHA" in db_url
        or "HOST" in db_url
    ):

        sys.exit(
            "Configure DB_URL_ONLINE "
            "(usuário, senha e host do MySQL) "
            "no topo do script."
        )

    # --------------------------------------------------------
    # Executa
    # --------------------------------------------------------

    print(
        "Carregando planilha..."
    )

    registros = carregar_planilha(
        CAMINHO_EXCEL
    )

    print(
        f"{len(registros)} registros válidos "
        "na planilha."
    )

    cadastrar(
        db_url,
        registros
    )
