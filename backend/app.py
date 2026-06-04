import sys
import os

# Garantir que o diretório raiz do projeto está no path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

"""
Aplicação principal Flask - Sistema de Chamados - Colégio Mauá
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from flask import Flask
from flask_login import LoginManager
from backend.models.modelos import db, Usuario, Setor, Chamado, Mensagem, Anexo, LogOperacao, Notificacao
from backend.routes.rotas import main, api
from backend.utils.utilitarios import agora_brasil_naive
from config import config


def formatar_tempo(valor):
    """
    Formata um valor de tempo (float em horas ou timedelta)
    para exibição em horas e minutos.
    """
    if valor is None:
        return "-"

    if isinstance(valor, timedelta):
        total_segundos = int(valor.total_seconds())
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60

        if horas > 0 and minutos > 0:
            return f"{horas}h {minutos:02d}m"
        elif horas > 0:
            return f"{horas}h"
        else:
            return f"{minutos}m"

    try:
        horas_total = float(valor)
        if horas_total <= 0:
            return "0m"

        horas = int(horas_total)
        minutos = int((horas_total - horas) * 60)

        if horas > 0 and minutos > 0:
            return f"{horas}h {minutos:02d}m"
        elif horas > 0:
            return f"{horas}h"
        else:
            return f"{minutos}m"
    except (ValueError, TypeError):
        return str(valor)


def criar_app(config_name='default'):
    """Factory de criação da aplicação Flask."""

    # PATH ABSOLUTO para templates e static - ESSENCIAL no PythonAnywhere
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'frontend', 'templates')
    static_dir = os.path.join(base_dir, 'frontend', 'static')

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    # Configurações
    app.config.from_object(config[config_name])

    # Inicializar extensões
    db.init_app(app)

    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        """Carrega o usuário pela ID."""
        return Usuario.query.get(int(user_id))

    # Registrar blueprints
    app.register_blueprint(main)
    app.register_blueprint(api)

    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)

    # Configurar logging
    if not app.debug:
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sistema de Chamados - Colégio Mauá iniciado')

    # Criar tabelas do banco (vazio - sem dados de demonstração)
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados criado/atualizado. Sistema pronto para uso.")

    # Context processor para funções utilitárias
    @app.context_processor
    def inject_utilities():
        from backend.utils.utilitarios import (
            formatar_data, formatar_data_curta,
            get_prioridade_cor, get_status_cor,
            get_prioridade_label, get_status_label
        )
        from backend.routes.rotas import verificar_data_destaque
        return dict(
            formatar_data=formatar_data,
            formatar_data_curta=formatar_data_curta,
            get_prioridade_cor=get_prioridade_cor,
            get_status_cor=get_status_cor,
            get_prioridade_label=get_prioridade_label,
            get_status_label=get_status_label,
            verificar_data_destaque=verificar_data_destaque,
            formatar_tempo=formatar_tempo
        )

    return app


# Criar aplicação
app = criar_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
