"""
Rotas e endpoints da API do Sistema de Chamados - Colégio Mauá
"""
import os
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, session, current_app, send_from_directory
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from backend.models.modelos import (
    db, Usuario, Setor, Chamado, Mensagem, Anexo, 
    LogOperacao, Notificacao, StatusChamado, Prioridade, PerfilUsuario
)
from backend.services.servicos import (
    ChamadoService, UsuarioService, MensagemService, NotificacaoService
)
from backend.utils.utilitarios import (
    allowed_file, sanitize_filename, registrar_log,
    formatar_data, formatar_data_curta, get_prioridade_cor, get_status_cor,
    get_prioridade_label, get_status_label
)

main = Blueprint('main', __name__)
api = Blueprint('api', __name__, url_prefix='/api')

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO AUXILIAR: Prioridade ordenada
# ═══════════════════════════════════════════════════════════════════════════════

def get_prioridade_ordem(prioridade):
    """Retorna a ordem numérica da prioridade para sorting."""
    ordem = {'urgente': 0, 'alta': 1, 'media': 2, 'baixa': 3}
    return ordem.get(prioridade, 99)


def get_chamados_ordenados(query_or_list):
    """Retorna chamados ordenados por prioridade (urgente -> baixa).
    Aceita tanto uma Query quanto uma lista já paginada."""
    # Se for uma query (não paginada), pegar todos
    if hasattr(query_or_list, 'all'):
        chamados = query_or_list.all()
    # Se for objeto de paginação, pegar items
    elif hasattr(query_or_list, 'items'):
        chamados = list(query_or_list.items)
    # Se já for uma lista
    else:
        chamados = list(query_or_list)

    # Ordenar por prioridade (urgente primeiro) e depois por data
    chamados.sort(key=lambda c: (get_prioridade_ordem(c.prioridade.value), c.created_at), reverse=False)
    return chamados


def verificar_data_destaque(data_preferencial):
    """Verifica se a data preferencial é hoje ou próxima."""
    if not data_preferencial:
        return False
    hoje = datetime.utcnow().date()
    if isinstance(data_preferencial, str):
        try:
            data_preferencial = datetime.fromisoformat(data_preferencial.replace('Z', '+00:00')).date()
        except:
            return False
    else:
        data_preferencial = data_preferencial.date() if hasattr(data_preferencial, 'date') else data_preferencial
    return data_preferencial <= hoje


# ═══════════════════════════════════════════════════════════════════════════════
# ROTAS PÚBLICAS
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/')
def index():
    """Página inicial - redireciona para login ou dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash('Preencha todos os campos.', 'error')
            return render_template('login.html')

        usuario = Usuario.query.filter_by(email=email, ativo=True).first()

        if usuario and usuario.check_senha(senha):
            login_user(usuario, remember=True)
            usuario.ultimo_acesso = datetime.utcnow()
            db.session.commit()
            registrar_log(usuario.id, 'login', 'usuario', usuario.id, 'Login realizado')

            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('E-mail ou senha incorretos.', 'error')

    return render_template('login.html')


@main.route('/registro', methods=['GET', 'POST'])
def registro():
    """Página de registro de novo usuário."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    setores = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        telefone = request.form.get('telefone', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        setor_id = request.form.get('setor_id')

        # Validações
        erros = []
        if not nome or len(nome) < 3:
            erros.append('Nome deve ter pelo menos 3 caracteres.')
        if not email or '@' not in email:
            erros.append('E-mail inválido.')
        if len(senha) < 6:
            erros.append('Senha deve ter pelo menos 6 caracteres.')
        if senha != confirmar_senha:
            erros.append('As senhas não conferem.')

        if Usuario.query.filter_by(email=email).first():
            erros.append('Este e-mail já está cadastrado.')

        if erros:
            for erro in erros:
                flash(erro, 'error')
            return render_template('registro.html', setores=setores)

        # Criar usuário
        try:
            usuario = UsuarioService.criar_usuario({
                'nome': nome,
                'email': email,
                'telefone': telefone,
                'senha': senha,
                'perfil': 'usuario',
                'setor_id': int(setor_id) if setor_id else None
            })
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            flash(f'Erro ao criar conta: {str(e)}', 'error')

    return render_template('registro.html', setores=setores)


@main.route('/logout')
@login_required
def logout():
    """Realiza logout do usuário."""
    registrar_log(current_user.id, 'logout', 'usuario', current_user.id, 'Logout realizado')
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('main.login'))


# ═══════════════════════════════════════════════════════════════════════════════
# ROTAS PROTEGIDAS - DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/dashboard')
@login_required
def dashboard():
    """Painel principal do sistema."""
    estatisticas = ChamadoService.get_estatisticas(current_user)
    chamados_por_mes = ChamadoService.get_chamados_por_mes(current_user, 6)

    # Últimos chamados ordenados por prioridade
    if current_user.perfil == PerfilUsuario.ADMIN:
        query = Chamado.query
    elif current_user.perfil == PerfilUsuario.SETOR:
        query = Chamado.query.filter_by(setor_destino_id=current_user.setor_id)
    else:
        query = Chamado.query.filter_by(usuario_id=current_user.id)

    ultimos_chamados = get_chamados_ordenados(query)[:5]

    return render_template('dashboard.html',
                         estatisticas=estatisticas,
                         chamados_por_mes=chamados_por_mes,
                         ultimos_chamados=ultimos_chamados,
                         formatar_data=formatar_data,
                         formatar_data_curta=formatar_data_curta,
                         get_status_label=get_status_label,
                         get_prioridade_label=get_prioridade_label,
                         get_status_cor=get_status_cor,
                         get_prioridade_cor=get_prioridade_cor,
                         verificar_data_destaque=verificar_data_destaque)


# ═══════════════════════════════════════════════════════════════════════════════
# ROTAS PROTEGIDAS - CHAMADOS
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/chamados')
@login_required
def chamados():
    """Lista todos os chamados."""
    pagina = request.args.get('page', 1, type=int)

    filtros = {
        'status': request.args.get('status'),
        'prioridade': request.args.get('prioridade'),
        'setor_destino_id': request.args.get('setor_destino_id', type=int),
        'busca': request.args.get('busca')
    }

    # Remover filtros vazios
    filtros = {k: v for k, v in filtros.items() if v}

    resultado = ChamadoService.listar_chamados(current_user, filtros, pagina)
    setores = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()

    # Ordenar por prioridade
    chamados_ordenados = get_chamados_ordenados(resultado)

    return render_template('chamados.html',
                         chamados=resultado,
                         chamados_ordenados=chamados_ordenados,
                         setores=setores,
                         filtros=filtros,
                         formatar_data=formatar_data,
                         formatar_data_curta=formatar_data_curta,
                         get_status_label=get_status_label,
                         get_prioridade_label=get_prioridade_label,
                         get_status_cor=get_status_cor,
                         get_prioridade_cor=get_prioridade_cor,
                         verificar_data_destaque=verificar_data_destaque)


@main.route('/chamados/novo', methods=['GET', 'POST'])
@login_required
def novo_chamado():
    """Cria um novo chamado."""
    setores = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()

    if request.method == 'POST':
        dados = {
            'titulo': request.form.get('titulo', '').strip(),
            'descricao': request.form.get('descricao', '').strip(),
            'local': request.form.get('local', '').strip(),
            'area_patrimonial': request.form.get('area_patrimonial', '').strip(),
            'prioridade': request.form.get('prioridade', 'media'),
            'setor_destino_id': request.form.get('setor_destino_id', type=int),
            'data_preferencial': request.form.get('data_preferencial')
        }

        # Validações
        erros = []
        if not dados['titulo'] or len(dados['titulo']) < 5:
            erros.append('Título deve ter pelo menos 5 caracteres.')
        if not dados['descricao'] or len(dados['descricao']) < 10:
            erros.append('Descrição deve ter pelo menos 10 caracteres.')
        if not dados['local']:
            erros.append('Informe o local.')
        if not dados['setor_destino_id']:
            erros.append('Selecione o setor de destino.')

        if erros:
            for erro in erros:
                flash(erro, 'error')
            return render_template('novo_chamado.html', setores=setores, dados=dados)

        try:
            # Converter data preferencial
            if dados['data_preferencial']:
                dados['data_preferencial'] = datetime.fromisoformat(dados['data_preferencial'])

            chamado = ChamadoService.criar_chamado(dados, current_user.id)

            # Processar anexos
            if 'anexos' in request.files:
                arquivos = request.files.getlist('anexos')
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                for arquivo in arquivos:
                    if arquivo and arquivo.filename and allowed_file(arquivo.filename):
                        try:
                            filename = sanitize_filename(arquivo.filename)
                            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                            arquivo.save(upload_path)

                            anexo = Anexo(
                                chamado_id=chamado.id,
                                nome_arquivo=arquivo.filename,
                                caminho_arquivo=filename,
                                tipo_arquivo=arquivo.filename.rsplit('.', 1)[1].lower(),
                                tamanho=os.path.getsize(upload_path)
                            )
                            db.session.add(anexo)
                        except Exception as e:
                            current_app.logger.error(f"Erro ao processar anexo: {str(e)}")
                db.session.commit()

            flash(f'Chamado #{chamado.id} criado com sucesso!', 'success')
            return redirect(url_for('main.chamado_detalhe', chamado_id=chamado.id))
        except Exception as e:
            flash(f'Erro ao criar chamado: {str(e)}', 'error')

    return render_template('novo_chamado.html', setores=setores)


@main.route('/chamados/<int:chamado_id>')
@login_required
def chamado_detalhe(chamado_id):
    """Detalhes de um chamado específico."""
    chamado = Chamado.query.get_or_404(chamado_id)

    # Verificar permissão - SETOR: todos do setor veem todos os chamados do setor
    if current_user.perfil == PerfilUsuario.USUARIO and chamado.usuario_id != current_user.id:
        flash('Você não tem permissão para visualizar este chamado.', 'error')
        return redirect(url_for('main.chamados'))

    if current_user.perfil == PerfilUsuario.SETOR and chamado.setor_destino_id != current_user.setor_id:
        flash('Você não tem permissão para visualizar este chamado.', 'error')
        return redirect(url_for('main.chamados'))

    mensagens = Mensagem.query.filter_by(chamado_id=chamado_id).order_by(Mensagem.created_at.asc()).all()
    anexos = Anexo.query.filter_by(chamado_id=chamado_id).order_by(Anexo.created_at.desc()).all()

    # Usuários do setor para atribuição (todos os colaboradores do setor)
    usuarios_setor = []
    if current_user.perfil in [PerfilUsuario.ADMIN, PerfilUsuario.SETOR]:
        usuarios_setor = Usuario.query.filter(
            Usuario.setor_id == chamado.setor_destino_id,
            Usuario.ativo == True,
            Usuario.perfil.in_(['setor', 'admin'])
        ).all()

    return render_template('chamado_detalhe.html',
                         chamado=chamado,
                         mensagens=mensagens,
                         anexos=anexos,
                         usuarios_setor=usuarios_setor,
                         formatar_data=formatar_data,
                         formatar_data_curta=formatar_data_curta,
                         get_status_label=get_status_label,
                         get_prioridade_label=get_prioridade_label,
                         get_status_cor=get_status_cor,
                         get_prioridade_cor=get_prioridade_cor,
                         verificar_data_destaque=verificar_data_destaque)


@main.route('/chamados/<int:chamado_id>/status', methods=['POST'])
@login_required
def atualizar_status_chamado(chamado_id):
    """Atualiza o status de um chamado."""
    chamado = Chamado.query.get_or_404(chamado_id)

    # Verificar permissão
    if current_user.perfil == PerfilUsuario.USUARIO and chamado.usuario_id != current_user.id:
        flash('Permissão negada.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    novo_status = request.form.get('status')
    observacao = request.form.get('observacao', '')

    if novo_status not in [s.value for s in StatusChamado]:
        flash('Status inválido.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    try:
        ChamadoService.atualizar_status(chamado_id, novo_status, current_user.id, observacao)

        # Se houver observação, adicionar como mensagem
        if observacao.strip():
            mensagem_obs = Mensagem(
                chamado_id=chamado_id,
                usuario_id=current_user.id,
                conteudo=f"[OBSERVAÇÃO - Status alterado para {get_status_label(novo_status)}]: {observacao}"
            )
            db.session.add(mensagem_obs)
            db.session.commit()

        flash('Status atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar status: {str(e)}', 'error')

    return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))


@main.route('/chamados/<int:chamado_id>/atribuir', methods=['POST'])
@login_required
def atribuir_chamado(chamado_id):
    """Atribui um chamado a um atendente."""
    if current_user.perfil not in [PerfilUsuario.ADMIN, PerfilUsuario.SETOR]:
        flash('Permissão negada.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    atendente_id = request.form.get('atendente_id', type=int)

    if not atendente_id:
        flash('Selecione um atendente.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    try:
        ChamadoService.atribuir_chamado(chamado_id, atendente_id, current_user.id)
        flash('Chamado atribuído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atribuir chamado: {str(e)}', 'error')

    return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))


@main.route('/chamados/<int:chamado_id>/mensagem', methods=['POST'])
@login_required
def enviar_mensagem(chamado_id):
    """Envia uma mensagem em um chamado."""
    chamado = Chamado.query.get_or_404(chamado_id)

    # Verificar permissão - SETOR: todos do setor podem enviar mensagem
    if current_user.perfil == PerfilUsuario.USUARIO and chamado.usuario_id != current_user.id:
        flash('Permissão negada.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    if current_user.perfil == PerfilUsuario.SETOR and chamado.setor_destino_id != current_user.setor_id:
        flash('Permissão negada.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    conteudo = request.form.get('conteudo', '').strip()

    if not conteudo:
        flash('Digite uma mensagem.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    try:
        MensagemService.enviar_mensagem(chamado_id, current_user.id, conteudo)
        flash('Mensagem enviada!', 'success')
    except Exception as e:
        flash(f'Erro ao enviar mensagem: {str(e)}', 'error')

    return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))


@main.route('/chamados/<int:chamado_id>/upload', methods=['POST'])
@login_required
def upload_anexo(chamado_id):
    """Faz upload de anexo em um chamado."""
    chamado = Chamado.query.get_or_404(chamado_id)

    # Verificar permissão
    if current_user.perfil == PerfilUsuario.USUARIO and chamado.usuario_id != current_user.id:
        flash('Permissão negada.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    if current_user.perfil == PerfilUsuario.SETOR and chamado.setor_destino_id != current_user.setor_id:
        flash('Permissão negada.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    if 'arquivo' not in request.files:
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    arquivo = request.files['arquivo']

    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    if arquivo and allowed_file(arquivo.filename):
        try:
            filename = sanitize_filename(arquivo.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

            arquivo.save(upload_path)

            anexo = Anexo(
                chamado_id=chamado_id,
                nome_arquivo=arquivo.filename,
                caminho_arquivo=filename,
                tipo_arquivo=arquivo.filename.rsplit('.', 1)[1].lower(),
                tamanho=os.path.getsize(upload_path)
            )
            db.session.add(anexo)
            db.session.commit()

            registrar_log(current_user.id, 'upload', 'anexo', anexo.id,
                         f'Anexo {arquivo.filename} enviado no chamado #{chamado_id}')

            flash('Arquivo enviado com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao enviar arquivo: {str(e)}', 'error')
    else:
        flash('Tipo de arquivo não permitido.', 'error')

    return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))


# ═══════════════════════════════════════════════════════════════════════════════
# ROTAS PROTEGIDAS - RELATÓRIOS
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/relatorios')
@login_required
def relatorios():
    """Página de relatórios."""
    estatisticas = ChamadoService.get_estatisticas(current_user)
    chamados_por_mes = ChamadoService.get_chamados_por_mes(current_user, 12)
    setores = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()

    # Chamados por setor
    chamados_por_setor = []
    for setor in setores:
        query = Chamado.query.filter_by(setor_destino_id=setor.id)
        if current_user.perfil == PerfilUsuario.USUARIO:
            query = query.filter_by(usuario_id=current_user.id)
        elif current_user.perfil == PerfilUsuario.SETOR:
            query = query.filter_by(setor_destino_id=current_user.setor_id)

        chamados_por_setor.append({
            'setor': setor.nome,
            'total': query.count()
        })

    # Dados por setor para gráficos (apenas admin)
    graficos_por_setor = {}
    if current_user.is_admin():
        for setor in setores:
            chamados_setor = Chamado.query.filter_by(setor_destino_id=setor.id).all()
            por_status = {}
            por_prioridade = {}
            for c in chamados_setor:
                por_status[c.status.value] = por_status.get(c.status.value, 0) + 1
                por_prioridade[c.prioridade.value] = por_prioridade.get(c.prioridade.value, 0) + 1
            graficos_por_setor[setor.nome] = {
                'total': len(chamados_setor),
                'por_status': por_status,
                'por_prioridade': por_prioridade
            }

    return render_template('relatorios.html',
                         estatisticas=estatisticas,
                         chamados_por_mes=chamados_por_mes,
                         chamados_por_setor=chamados_por_setor,
                         graficos_por_setor=graficos_por_setor,
                         setores=setores,
                         formatar_data=formatar_data,
                         formatar_data_curta=formatar_data_curta,
                         get_status_label=get_status_label,
                         get_prioridade_label=get_prioridade_label,
                         get_status_cor=get_status_cor,
                         get_prioridade_cor=get_prioridade_cor)


# ═══════════════════════════════════════════════════════════════════════════════
# ROTAS PROTEGIDAS - ADMINISTRAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/admin/usuarios')
@login_required
def admin_usuarios():
    """Gerenciamento de usuários (apenas admin)."""
    if not current_user.is_admin():
        flash('Acesso restrito a administradores.', 'error')
        return redirect(url_for('main.dashboard'))

    pagina = request.args.get('page', 1, type=int)
    busca = request.args.get('busca', '')

    query = Usuario.query
    if busca:
        query = query.filter(
            db.or_(
                Usuario.nome.ilike(f'%{busca}%'),
                Usuario.email.ilike(f'%{busca}%')
            )
        )

    usuarios = query.order_by(Usuario.nome).paginate(page=pagina, per_page=10, error_out=False)
    setores = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()

    return render_template('admin_usuarios.html', 
                         usuarios=usuarios, 
                         setores=setores, 
                         busca=busca,
                         formatar_data=formatar_data,
                         formatar_data_curta=formatar_data_curta)


@main.route('/admin/usuarios/novo', methods=['POST'])
@login_required
def admin_criar_usuario():
    """Cria um novo usuário (apenas admin)."""
    if not current_user.is_admin():
        flash('Acesso restrito.', 'error')
        return redirect(url_for('main.dashboard'))

    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip(),
        'telefone': request.form.get('telefone', '').strip(),
        'senha': request.form.get('senha', ''),
        'perfil': request.form.get('perfil', 'usuario'),
        'setor_id': request.form.get('setor_id', type=int)
    }

    try:
        UsuarioService.criar_usuario(dados)
        flash('Usuário criado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao criar usuário: {str(e)}', 'error')

    return redirect(url_for('main.admin_usuarios'))


@main.route('/admin/usuarios/<int:usuario_id>/editar', methods=['POST'])
@login_required
def admin_editar_usuario(usuario_id):
    """Edita um usuário (apenas admin)."""
    if not current_user.is_admin():
        flash('Acesso restrito.', 'error')
        return redirect(url_for('main.dashboard'))

    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip(),
        'telefone': request.form.get('telefone', '').strip(),
        'perfil': request.form.get('perfil'),
        'setor_id': request.form.get('setor_id', type=int),
        'ativo': request.form.get('ativo') == 'on'
    }

    senha = request.form.get('senha', '')
    if senha:
        dados['senha'] = senha

    try:
        UsuarioService.atualizar_usuario(usuario_id, dados, current_user.id)
        flash('Usuário atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar usuário: {str(e)}', 'error')

    return redirect(url_for('main.admin_usuarios'))


@main.route('/admin/setores')
@login_required
def admin_setores():
    """Gerenciamento de setores (apenas admin)."""
    if not current_user.is_admin():
        flash('Acesso restrito a administradores.', 'error')
        return redirect(url_for('main.dashboard'))

    setores = Setor.query.order_by(Setor.nome).all()
    return render_template('admin_setores.html', 
                         setores=setores,
                         formatar_data=formatar_data,
                         formatar_data_curta=formatar_data_curta)


@main.route('/admin/setores/novo', methods=['POST'])
@login_required
def admin_criar_setor():
    """Cria um novo setor (apenas admin)."""
    if not current_user.is_admin():
        flash('Acesso restrito.', 'error')
        return redirect(url_for('main.dashboard'))

    nome = request.form.get('nome', '').strip()
    descricao = request.form.get('descricao', '').strip()

    if not nome:
        flash('Nome do setor é obrigatório.', 'error')
        return redirect(url_for('main.admin_setores'))

    if Setor.query.filter_by(nome=nome).first():
        flash('Já existe um setor com este nome.', 'error')
        return redirect(url_for('main.admin_setores'))

    try:
        setor = Setor(nome=nome, descricao=descricao)
        db.session.add(setor)
        db.session.commit()
        registrar_log(current_user.id, 'criar', 'setor', setor.id, f'Setor {nome} criado')
        flash('Setor criado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao criar setor: {str(e)}', 'error')

    return redirect(url_for('main.admin_setores'))


@main.route('/admin/setores/<int:setor_id>/editar', methods=['POST'])
@login_required
def admin_editar_setor(setor_id):
    """Edita um setor (apenas admin)."""
    if not current_user.is_admin():
        flash('Acesso restrito.', 'error')
        return redirect(url_for('main.dashboard'))

    setor = Setor.query.get_or_404(setor_id)
    setor.nome = request.form.get('nome', '').strip()
    setor.descricao = request.form.get('descricao', '').strip()
    setor.ativo = request.form.get('ativo') == 'on'

    db.session.commit()
    registrar_log(current_user.id, 'atualizar', 'setor', setor.id, f'Setor {setor.nome} atualizado')
    flash('Setor atualizado com sucesso!', 'success')

    return redirect(url_for('main.admin_setores'))


@main.route('/admin/logs')
@login_required
def admin_logs():
    """Visualização de logs (apenas admin)."""
    if not current_user.is_admin():
        flash('Acesso restrito a administradores.', 'error')
        return redirect(url_for('main.dashboard'))

    pagina = request.args.get('page', 1, type=int)
    logs = LogOperacao.query.order_by(LogOperacao.created_at.desc()).paginate(
        page=pagina, per_page=20, error_out=False
    )

    return render_template('admin_logs.html', 
                         logs=logs, 
                         formatar_data=formatar_data,
                         formatar_data_curta=formatar_data_curta)


# ═══════════════════════════════════════════════════════════════════════════════
# ROTAS PROTEGIDAS - PERFIL
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Página de perfil do usuário."""
    if request.method == 'POST':
        current_user.nome = request.form.get('nome', '').strip()
        current_user.telefone = request.form.get('telefone', '').strip()

        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if nova_senha:
            if not current_user.check_senha(senha_atual):
                flash('Senha atual incorreta.', 'error')
                return render_template('perfil.html')

            if len(nova_senha) < 6:
                flash('Nova senha deve ter pelo menos 6 caracteres.', 'error')
                return render_template('perfil.html')

            if nova_senha != confirmar_senha:
                flash('As senhas não conferem.', 'error')
                return render_template('perfil.html')

            current_user.set_senha(nova_senha)

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('main.perfil'))

    return render_template('perfil.html')


# ═══════════════════════════════════════════════════════════════════════════════
# ROTAS PROTEGIDAS - NOTIFICAÇÕES
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/notificacoes')
@login_required
def notificacoes():
    """Página de notificações do usuário."""
    notificacoes_list = Notificacao.query.filter_by(usuario_id=current_user.id).order_by(
        Notificacao.created_at.desc()
    ).all()

    return render_template('notificacoes.html', 
                         notificacoes=notificacoes_list, 
                         formatar_data=formatar_data,
                         formatar_data_curta=formatar_data_curta)


@main.route('/notificacoes/<int:notificacao_id>/ler', methods=['POST'])
@login_required
def marcar_notificacao_lida(notificacao_id):
    """Marca uma notificação como lida."""
    NotificacaoService.marcar_como_lida(notificacao_id, current_user.id)
    return jsonify({'success': True})


@main.route('/notificacoes/ler-todas', methods=['POST'])
@login_required
def marcar_todas_notificacoes_lidas():
    """Marca todas as notificações como lidas."""
    NotificacaoService.marcar_todas_como_lidas(current_user.id)
    return jsonify({'success': True})


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@api.route('/estatisticas')
@login_required
def api_estatisticas():
    """Retorna estatísticas em formato JSON."""
    estatisticas = ChamadoService.get_estatisticas(current_user)
    return jsonify(estatisticas)


@api.route('/notificacoes/nao-lidas')
@login_required
def api_notificacoes_nao_lidas():
    """Retorna notificações não lidas em formato JSON."""
    notificacoes = NotificacaoService.get_nao_lidas(current_user.id)
    return jsonify({
        'count': len(notificacoes),
        'notificacoes': [n.to_dict() for n in notificacoes[:5]]
    })


@api.route('/chamados/<int:chamado_id>')
@login_required
def api_chamado(chamado_id):
    """Retorna detalhes de um chamado em formato JSON."""
    chamado = Chamado.query.get_or_404(chamado_id)

    if current_user.perfil == PerfilUsuario.USUARIO and chamado.usuario_id != current_user.id:
        return jsonify({'error': 'Permissão negada'}), 403

    return jsonify(chamado.to_dict())
