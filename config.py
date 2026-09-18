
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

    DATABASE_DIR = os.path.join(BASE_DIR, "database")

    # O caminho é convertido para absoluto.
    # Isso evita problemas quando o projeto é executado
    # a partir de uma pasta diferente.
    DATABASE_FILE = os.path.join(DATABASE_DIR, "chamados.db")

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "sqlite:///" + DATABASE_FILE
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================================
    # SESSÃO
    # ==========================================================

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ==========================================================
    # UPLOADS
    # ==========================================================

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "frontend",
        "static",
        "uploads"
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

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

    IA_ASSISTENTE_ATIVO = (
        os.environ.get("IA_ASSISTENTE_ATIVO", "true").lower() == "true"
    )

    IA_API_URL = os.environ.get(
        "IA_API_URL",
        "https://api.moonshot.ai/v1/chat/completions"
    )

    # IMPORTANTE:
    # Nunca coloque a chave diretamente neste arquivo.
    # Use variável de ambiente ou arquivo .env.
    IA_API_KEY = os.environ.get("IA_API_KEY", "")

    IA_MODEL = os.environ.get(
        "IA_MODEL",
        "moonshot-v1-8k"
    )


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

