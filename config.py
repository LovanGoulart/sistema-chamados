"""
Configurações da aplicação Sistema de Chamados - Colégio Mauá
"""

import os
from datetime import timedelta


class Config:
    """Configurações base da aplicação."""

    # ==========================================================
    # DIRETÓRIO BASE
    # ==========================================================

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # ==========================================================
    # SEGURANÇA
    # ==========================================================

    SECRET_KEY = (
        os.environ.get("SECRET_KEY")
        or "chave-secreta-sistema-chamados-maua-2026"
    )

    # ==========================================================
    # BANCO DE DADOS
    # ==========================================================

    DATABASE_DIR = os.path.join(
        BASE_DIR,
        "database"
    )

    DATABASE_FILE = os.path.join(
        DATABASE_DIR,
        "chamados.db"
    )

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"sqlite:///{DATABASE_FILE}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================================
    # SESSÃO
    # ==========================================================

# ==========================================================
# SESSÃO FLASK
# ==========================================================

    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=8
    )

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False

    # ==========================================================
    # UPLOADS
    # ==========================================================

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "frontend",
        "static",
        "uploads"
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    ALLOWED_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "txt"
    }

    # ==========================================================
    # PAGINAÇÃO
    # ==========================================================

    PER_PAGE = 10

    # ==========================================================
    # LOGS
    # ==========================================================

    LOG_FILE = os.path.join(
        BASE_DIR,
        "backend",
        "logs",
        "app.log"
    )

    # ==========================================================
    # ASSISTENTE DE TI - IA
    # ==========================================================

    # true  = assistente ativo
    # false = assistente desativado
    IA_ASSISTENTE_ATIVO = (
        os.environ.get(
            "IA_ASSISTENTE_ATIVO",
            "true"
        ).strip().lower() == "true"
    )

    # ----------------------------------------------------------
    # API GEMINI
    # ----------------------------------------------------------
    #
    # Endpoint oficial compatível com OpenAI.
    #
    # IMPORTANTE:
    # A URL deve ser somente a URL.
    # Não utilizar Markdown, colchetes ou parênteses.
    #

    IA_API_URL = os.environ.get(
        "IA_API_URL",
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    ).strip()

    # ----------------------------------------------------------
    # CHAVE DA API
    # ----------------------------------------------------------
    #
    # A chave deve ficar no .env ou nas variáveis de ambiente.
    # Nunca coloque a chave diretamente neste arquivo.
    #

    IA_API_KEY = os.environ.get(
        "IA_API_KEY",
        ""
    ).strip()

    # ----------------------------------------------------------
    # MODELO GEMINI
    # ----------------------------------------------------------

    IA_MODEL = os.environ.get(
        "IA_MODEL",
        "gemini-3.1-flash-lite"
    ).strip()


class DevelopmentConfig(Config):
    """Configurações de desenvolvimento."""

    DEBUG = True


class ProductionConfig(Config):
    """Configurações de produção."""

    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}