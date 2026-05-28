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
from config import config


def criar_app(config_name='default'):
    """Factory de criação da aplicação Flask."""

    app = Flask(
        __name__,
        template_folder='../frontend/templates',
        static_folder='../frontend/static'
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

    # Criar tabelas e dados iniciais
    with app.app_context():
        db.create_all()

        # Verificar se é a primeira execução (nenhum setor cadastrado)
        # Se já existirem dados, NÃO recria os de demonstração
        if not Setor.query.first():
            print("🆕 Primeira execução detectada. Criando dados de demonstração...")
            criar_dados_iniciais()
        else:
            print("✅ Banco de dados já existe. Dados preservados.")


    # Context processor para funções utilitárias disponíveis em todos os templates
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
            verificar_data_destaque=verificar_data_destaque
        )

    return app


def criar_dados_iniciais():
    """Cria dados de exemplo no banco de dados.

    Esta função só é chamada na PRIMEIRA execução do sistema,
    quando o banco de dados está vazio.
    """

    # Criar setores
    setores_data = [
        {'nome': 'TI - Tecnologia da Informação', 'descricao': 'Suporte técnico e infraestrutura de TI'},
        {'nome': 'Manutenção', 'descricao': 'Manutenção predial e equipamentos'},
        {'nome': 'Limpeza', 'descricao': 'Serviços de limpeza e conservação'},
        {'nome': 'Segurança', 'descricao': 'Segurança patrimonial e vigilância'},
        {'nome': 'Administrativo', 'descricao': 'Gestão administrativa e recursos humanos'},
        {'nome': 'Pedagógico', 'descricao': 'Coordenação pedagógica e acadêmica'},
        {'nome': 'Biblioteca', 'descricao': 'Biblioteca e acervo'},
        {'nome': 'Almoxarifado', 'descricao': 'Controle de estoque e suprimentos'},
    ]

    setores = []
    for s_data in setores_data:
        setor = Setor(**s_data)
        db.session.add(setor)
        setores.append(setor)

    db.session.commit()

    # Criar usuário administrador
    admin = Usuario(
        nome='Administrador',
        email='admin@colegiomaua.edu.br',
        perfil='admin',
        ativo=True
    )
    admin.set_senha('admin123')
    db.session.add(admin)

    # Criar usuários de exemplo (colaboradores dos setores)
    usuarios_data = [
        {'nome': 'João Silva', 'email': 'joao@colegiomaua.edu.br', 'perfil': 'setor', 'setor_id': setores[0].id},
        {'nome': 'Maria Oliveira', 'email': 'maria@colegiomaua.edu.br', 'perfil': 'setor', 'setor_id': setores[1].id},
        {'nome': 'Carlos Santos', 'email': 'carlos@colegiomaua.edu.br', 'perfil': 'usuario'},
        {'nome': 'Ana Pereira', 'email': 'ana@colegiomaua.edu.br', 'perfil': 'usuario'},
        {'nome': 'Pedro Costa', 'email': 'pedro@colegiomaua.edu.br', 'perfil': 'usuario'},
        {'nome': 'Fernanda Lima', 'email': 'fernanda@colegiomaua.edu.br', 'perfil': 'setor', 'setor_id': setores[2].id},
        {'nome': 'Ricardo Souza', 'email': 'ricardo@colegiomaua.edu.br', 'perfil': 'usuario'},
        {'nome': 'Juliana Martins', 'email': 'juliana@colegiomaua.edu.br', 'perfil': 'usuario'},
        {'nome': 'Bruno TI', 'email': 'bruno.ti@colegiomaua.edu.br', 'perfil': 'setor', 'setor_id': setores[0].id},
        {'nome': 'Lucas Manutencao', 'email': 'lucas.man@colegiomaua.edu.br', 'perfil': 'setor', 'setor_id': setores[1].id},
    ]

    usuarios = []
    for u_data in usuarios_data:
        usuario = Usuario(**u_data)
        usuario.set_senha('123456')
        db.session.add(usuario)
        usuarios.append(usuario)

    db.session.commit()

    # Datas de exemplo
    hoje = datetime.utcnow()
    ontem = hoje - timedelta(days=1)
    amanha = hoje + timedelta(days=1)
    semana_passada = hoje - timedelta(days=5)
    mes_passado = hoje - timedelta(days=30)

    # Criar chamados de exemplo
    chamados_data = [
        {
            'titulo': 'Projetor não funciona na Sala 101',
            'descricao': 'O projetor da sala 101 não está ligando. Já verifiquei a tomada e os cabos, mas não há sinal de energia. Preciso para a aula de hoje à tarde.',
            'local': 'Sala 101 - Bloco A',
            'area_patrimonial': 'Bloco A',
            'prioridade': 'alta',
            'status': 'em_andamento',
            'data_preferencial': ontem,
            'setor_destino_id': setores[0].id,
            'usuario_id': usuarios[2].id,
            'atendente_id': usuarios[0].id,
        },
        {
            'titulo': 'Vazamento na torneira do banheiro feminino',
            'descricao': 'A torneira do banheiro feminino do térreo está vazando constantemente. O vazamento está há alguns dias e já está molhando o piso.',
            'local': 'Banheiro Feminino - Térreo',
            'area_patrimonial': 'Bloco Principal',
            'prioridade': 'media',
            'status': 'aberto',
            'data_preferencial': hoje,
            'setor_destino_id': setores[1].id,
            'usuario_id': usuarios[3].id,
        },
        {
            'titulo': 'Limpeza urgente no laboratório de química',
            'descricao': 'O laboratório de química precisa de uma limpeza especializada após o experimento de hoje. Há resíduos que precisam de descarte adequado.',
            'local': 'Laboratório de Química - Bloco B',
            'area_patrimonial': 'Bloco B',
            'prioridade': 'urgente',
            'status': 'aberto',
            'data_preferencial': amanha,
            'setor_destino_id': setores[2].id,
            'usuario_id': usuarios[4].id,
        },
        {
            'titulo': 'Troca de lâmpadas no corredor do 2º andar',
            'descricao': 'Várias lâmpadas do corredor do 2º andar estão queimadas, dificultando a circulação dos alunos à noite.',
            'local': 'Corredor 2º Andar - Bloco A',
            'area_patrimonial': 'Bloco A',
            'prioridade': 'baixa',
            'status': 'resolvido',
            'data_preferencial': semana_passada,
            'setor_destino_id': setores[1].id,
            'usuario_id': usuarios[5].id,
            'atendente_id': usuarios[1].id,
        },
        {
            'titulo': 'Computador da secretaria travando constantemente',
            'descricao': 'O computador da secretaria administrativa está travando a cada 10 minutos. Já reiniciei várias vezes mas o problema persiste.',
            'local': 'Secretaria Administrativa',
            'area_patrimonial': 'Bloco Principal',
            'prioridade': 'alta',
            'status': 'pendente',
            'data_preferencial': hoje,
            'setor_destino_id': setores[0].id,
            'usuario_id': usuarios[6].id,
        },
        {
            'titulo': 'Ar condicionado da biblioteca não resfria',
            'descricao': 'O ar condicionado da biblioteca está ligado mas não está resfriando o ambiente. A temperatura está muito alta para leitura.',
            'local': 'Biblioteca - 1º Andar',
            'area_patrimonial': 'Bloco Principal',
            'prioridade': 'media',
            'status': 'em_andamento',
            'data_preferencial': amanha,
            'setor_destino_id': setores[1].id,
            'usuario_id': usuarios[7].id,
            'atendente_id': usuarios[1].id,
        },
        {
            'titulo': 'Portão principal com defeito no motor',
            'descricao': 'O motor do portão principal está fazendo barulho estranho e demorando muito para abrir. Pode parar de funcionar a qualquer momento.',
            'local': 'Portão Principal',
            'area_patrimonial': 'Área Externa',
            'prioridade': 'alta',
            'status': 'aberto',
            'data_preferencial': ontem,
            'setor_destino_id': setores[3].id,
            'usuario_id': usuarios[2].id,
        },
        {
            'titulo': 'Falta de papel A4 no almoxarifado',
            'descricao': 'O estoque de papel A4 está acabando. Precisamos de reposição urgente para as impressões dos relatórios trimestrais.',
            'local': 'Almoxarifado',
            'area_patrimonial': 'Bloco Principal',
            'prioridade': 'media',
            'status': 'fechado',
            'data_preferencial': mes_passado,
            'setor_destino_id': setores[7].id,
            'usuario_id': usuarios[3].id,
        },
        {
            'titulo': 'Sistema de som da quadra com interferência',
            'descricao': 'Durante o evento de ontem o sistema de som da quadra apresentou muita interferência e chiado. Precisa de revisão antes do próximo evento.',
            'local': 'Quadra Poliesportiva',
            'area_patrimonial': 'Área Externa',
            'prioridade': 'media',
            'status': 'aberto',
            'data_preferencial': amanha,
            'setor_destino_id': setores[0].id,
            'usuario_id': usuarios[4].id,
        },
        {
            'titulo': 'Cadeiras quebradas na sala 205',
            'descricao': 'Três cadeiras da sala 205 estão quebradas (pés soltos). Os alunos estão sentando no chão ou levando cadeiras de outras salas.',
            'local': 'Sala 205 - Bloco B',
            'area_patrimonial': 'Bloco B',
            'prioridade': 'baixa',
            'status': 'resolvido',
            'data_preferencial': semana_passada,
            'setor_destino_id': setores[1].id,
            'usuario_id': usuarios[5].id,
            'atendente_id': usuarios[1].id,
        },
        {
            'titulo': 'Wi-Fi caindo constantemente no Bloco C',
            'descricao': 'A conexão Wi-Fi no Bloco C está caindo a cada poucos minutos. Isso está prejudicando as aulas que usam recursos online.',
            'local': 'Bloco C - Todas as salas',
            'area_patrimonial': 'Bloco C',
            'prioridade': 'urgente',
            'status': 'em_andamento',
            'data_preferencial': hoje,
            'setor_destino_id': setores[0].id,
            'usuario_id': usuarios[6].id,
            'atendente_id': usuarios[0].id,
        },
        {
            'titulo': 'Janela do laboratório de informática não fecha',
            'descricao': 'A janela do laboratório de informática não está fechando direito, deixando entrar poeira e chuva nos equipamentos.',
            'local': 'Laboratório de Informática - Bloco A',
            'area_patrimonial': 'Bloco A',
            'prioridade': 'media',
            'status': 'aberto',
            'data_preferencial': amanha,
            'setor_destino_id': setores[1].id,
            'usuario_id': usuarios[7].id,
        },
    ]

    for c_data in chamados_data:
        chamado = Chamado(**c_data)
        db.session.add(chamado)

    db.session.commit()

    # Criar mensagens de exemplo
    mensagens_data = [
        {'chamado_id': 1, 'usuario_id': 1, 'conteudo': 'Vou verificar o projetor agora à tarde. Pode deixar a sala aberta?'},
        {'chamado_id': 1, 'usuario_id': 3, 'conteudo': 'Sim, a chave está com a coordenadora. Obrigado!'},
        {'chamado_id': 1, 'usuario_id': 1, 'conteudo': 'Projetor trocado. O problema era na lâmpada. Já está funcionando.'},
        {'chamado_id': 3, 'usuario_id': 6, 'conteudo': 'Vamos enviar a equipe de limpeza especializada ainda hoje.'},
        {'chamado_id': 5, 'usuario_id': 1, 'conteudo': 'Preciso verificar o computador pessoalmente. Pode agendar um horário?'},
        {'chamado_id': 5, 'usuario_id': 7, 'conteudo': 'Pode vir amanhã de manhã, estarei na secretaria das 8h às 12h.'},
        {'chamado_id': 7, 'usuario_id': 3, 'conteudo': 'O motor já foi trocado? O portão está demorando muito para abrir.'},
        {'chamado_id': 11, 'usuario_id': 1, 'conteudo': 'Identificamos que o roteador do Bloco C está com problema. Vamos trocar amanhã cedo.'},
    ]

    for m_data in mensagens_data:
        mensagem = Mensagem(**m_data)
        db.session.add(mensagem)

    db.session.commit()

    # Criar logs de exemplo
    logs_data = [
        {'usuario_id': 1, 'acao': 'login', 'entidade': 'usuario', 'entidade_id': 1, 'detalhes': 'Login realizado'},
        {'usuario_id': 3, 'acao': 'login', 'entidade': 'usuario', 'entidade_id': 3, 'detalhes': 'Login realizado'},
        {'usuario_id': 3, 'acao': 'criar', 'entidade': 'chamado', 'entidade_id': 1, 'detalhes': 'Chamado #1 criado'},
        {'usuario_id': 1, 'acao': 'atribuir', 'entidade': 'chamado', 'entidade_id': 1, 'detalhes': 'Chamado atribuído ao usuário 1'},
        {'usuario_id': 4, 'acao': 'criar', 'entidade': 'chamado', 'entidade_id': 2, 'detalhes': 'Chamado #2 criado'},
        {'usuario_id': 5, 'acao': 'criar', 'entidade': 'chamado', 'entidade_id': 3, 'detalhes': 'Chamado #3 criado'},
    ]

    for l_data in logs_data:
        log = LogOperacao(**l_data)
        db.session.add(log)

    db.session.commit()

    print("✅ Dados de demonstração criados com sucesso!")


# Criar aplicação
app = criar_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)