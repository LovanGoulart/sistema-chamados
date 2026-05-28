"""
Configurações da aplicação Sistema de Chamados - Colégio Mauá
"""
import os
from datetime import timedelta


class Config:
    """Configurações base da aplicação."""

    # Diretório base
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-sistema-chamados-maua-2026'

    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(BASE_DIR, 'database', 'chamados.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'frontend', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}

    # Paginação
    PER_PAGE = 10

    # Logs
    LOG_FILE = os.path.join(BASE_DIR, 'backend', 'logs', 'app.log')


class DevelopmentConfig(Config):
    """Configurações de desenvolvimento."""
    DEBUG = True


class ProductionConfig(Config):
    """Configurações de produção."""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}