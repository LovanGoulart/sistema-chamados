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
    get_prioridade_label, get_status_label,
    agora_brasil_naive
)

main = Blueprint('main', __name__)
api = Blueprint('api', __name__, url_prefix='/api')

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO AUXILIAR: Ordenação de chamados
# ═══════════════════════════════════════════════════════════════════════════════

def get_prioridade_ordem(prioridade):
    """Retorna a ordem numérica da prioridade para sorting.

    Ordem: urgente -> alta -> media -> baixa
    """
    ordem = {'urgente': 0, 'alta': 1, 'media': 2, 'baixa': 3}
    return ordem.get(prioridade, 99)


def get_status_ordem(status):
    """Retorna a ordem numérica do status para sorting.

    Ordem: aberto -> pendente -> em_andamento -> resolvido -> fechado
    """
    ordem = {
        'aberto': 0,
        'pendente': 1,
        'em_andamento': 2,
        'resolvido': 3,
        'fechado': 4
    }
    return ordem.get(status, 99)


def get_chamados_ordenados(query_or_list):
    """Retorna chamados ordenados por status, prioridade e data.

    Ordenação principal:   Status (aberto -> pendente -> em_andamento -> resolvido -> fechado)
    Ordenação secundária:  Prioridade (urgente -> alta -> media -> baixa)
    Ordenação terciária:   Data de criação (mais recente primeiro)

    Aceita tanto uma Query quanto uma lista já paginada.
    """
    # Se for uma query (não paginada), pegar todos
    if hasattr(query_or_list, 'all'):
        chamados = query_or_list.all()
    # Se for objeto de paginação, pegar items
    elif hasattr(query_or_list, 'items'):
        chamados = list(query_or_list.items)
    # Se já for uma lista
    else:
        chamados = list(query_or_list)

    # Ordenar por status (aberto primeiro), depois prioridade (urgente primeiro), depois data (mais recente)
    chamados.sort(key=lambda c: (
        get_status_ordem(c.status.value),
        get_prioridade_ordem(c.prioridade.value),
        -c.created_at.timestamp() if c.created_at else 0
    ), reverse=False)
    return chamados


def verificar_data_destaque(data_preferencial):
    """Verifica se a data preferencial é hoje ou próxima."""
    if not data_preferencial:
        return False
    hoje = agora_brasil_naive().date()
    if isinstance(data_preferencial, str):
        try:
            data_preferencial = datetime.fromisoformat(data_preferencial.replace('Z', '+00:00')).date()
        except:
            return False
    else:
        data_preferencial = data_preferencial.date() if hasattr(data_preferencial, 'date') else data_preferencial
    return data_preferencial <= hoje


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO AUXILIAR: Verificar permissão de acesso a um chamado
# ═══════════════════════════════════════════════════════════════════════════════

def pode_ver_chamado(chamado):
    """Verifica se o usuário atual pode visualizar/interagir com o chamado.

    REGRAS:
    - ADMIN: pode ver todos os chamados
    - SETOR: pode ver chamados do seu setor DESTINO ou que ELE MESMO CRIOU
    - USUÁRIO: pode ver APENAS seus próprios chamados
    """
    if current_user.perfil.value == PerfilUsuario.ADMIN.value:
        return True

    if current_user.perfil.value == PerfilUsuario.SETOR.value:
        # CORREÇÃO: Setor pode ver se é o destino OU se é o criador
        return (
            chamado.setor_destino_id == current_user.setor_id or
            chamado.usuario_id == current_user.id
        )

    # USUÁRIO: pode ver APENAS seus próprios chamados
    if current_user.perfil.value == PerfilUsuario.USUARIO.value:
        return chamado.usuario_id == current_user.id

    return False


def pode_enviar_mensagem(chamado):
    """Verifica se o usuário atual pode enviar mensagem no chamado.

    REGRAS:
    - ADMIN: pode enviar em todos os chamados
    - SETOR: pode enviar em chamados do seu setor DESTINO ou que ELE MESMO CRIOU
    - USUÁRIO: pode enviar APENAS em seus próprios chamados
    """
    # Forçar comparação como int para evitar problemas de tipo (str vs int)
    user_id = int(current_user.id)
    chamado_autor_id = int(chamado.usuario_id) if chamado.usuario_id else 0
    user_setor_id = int(current_user.setor_id) if current_user.setor_id else None
    chamado_setor_id = int(chamado.setor_destino_id) if chamado.setor_destino_id else None

    if current_user.perfil.value == PerfilUsuario.ADMIN.value:
        return True

    if current_user.perfil.value == PerfilUsuario.SETOR.value:
        # CORREÇÃO: Setor pode enviar mensagem se é o destino OU se é o criador
        return (
            chamado_setor_id == user_setor_id or
            chamado_autor_id == user_id
        )

    # USUÁRIO: pode enviar APENAS em seus próprios chamados
    if current_user.perfil.value == PerfilUsuario.USUARIO.value:
        return chamado_autor_id == user_id

    return False



# ═══════════════════════════════════════════════════════════════════════════════
# ROTA: Meus Chamados - APENAS chamados CRIADOS pelo usuário logado
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/meus-chamados')
@login_required
def meus_chamados():
    """Lista APENAS os chamados CRIADOS pelo usuário logado.

    Esta página mostra SOMENTE os chamados onde o usuário é o solicitante
    (autor), diferente da página /chamados que mostra chamados recebidos.
    """
    pagina = request.args.get('page', 1, type=int)

    filtros = {
        'status': request.args.get('status'),
        'prioridade': request.args.get('prioridade'),
        'busca': request.args.get('busca')
    }

    # Remover filtros vazios
    filtros = {k: v for k, v in filtros.items() if v}

    # Usar o novo serviço que filtra APENAS por usuario_id
    resultado = ChamadoService.listar_meus_chamados(current_user, filtros, pagina)

    # Ordenar por status, prioridade e data
    chamados_ordenados = get_chamados_ordenados(resultado)

    return render_template('meus_chamados.html',
                         chamados=resultado,
                         chamados_ordenados=chamados_ordenados,
                         filtros=filtros,
                         formatar_data=formatar_data,
                         formatar_data_curta=formatar_data_curta,
                         get_status_label=get_status_label,
                         get_prioridade_label=get_prioridade_label,
                         get_status_cor=get_status_cor,
                         get_prioridade_cor=get_prioridade_cor,
                         verificar_data_destaque=verificar_data_destaque)


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
            usuario.ultimo_acesso = agora_brasil_naive()
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

    # Buscar chamados ativos (aberto, pendente, em_andamento)
    if current_user.perfil.value == PerfilUsuario.ADMIN.value:
        query = Chamado.query
    elif current_user.perfil.value == PerfilUsuario.SETOR.value:
        query = Chamado.query.filter_by(setor_destino_id=current_user.setor_id)
    else:
        # USUÁRIO: vê APENAS seus próprios chamados
        query = Chamado.query.filter(Chamado.usuario_id == current_user.id)

    # Filtrar apenas status ativos: aberto, pendente, em_andamento
    query = query.filter(
        Chamado.status.in_([
            StatusChamado.ABERTO,
            StatusChamado.PENDENTE,
            StatusChamado.EM_ANDAMENTO
        ])
    )

    # Ordenar: status (aberto -> pendente -> em_andamento), depois prioridade (urgente -> alta -> media -> baixa)
    chamados_ativos = get_chamados_ordenados(query)

    return render_template('dashboard.html',
                         estatisticas=estatisticas,
                         chamados_ativos=chamados_ativos,
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

    # Ordenar por status, prioridade e data
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
            # CORREÇÃO: Converter data preferencial de string para datetime
            data_str = dados.pop('data_preferencial')  # Remove string dos dados
            data_preferencial = None

            if data_str and data_str.strip():
                # Tenta converter do formato do input datetime-local (YYYY-MM-DDTHH:MM)
                try:
                    data_preferencial = datetime.strptime(data_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    # Tenta formato com segundos
                    try:
                        data_preferencial = datetime.strptime(data_str, '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        # Tenta formato ISO
                        try:
                            data_preferencial = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                        except ValueError:
                            flash('Data preferencial inválida.', 'error')
                            return render_template('novo_chamado.html', setores=setores, dados=dados)

            # Adiciona o datetime convertido aos dados
            dados['data_preferencial'] = data_preferencial
            # FIM CORREÇÃO

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
    current_app.logger.info(f"[DETALHE] Acessando chamado {chamado_id} - usuario_logado={current_user.id}")

    # REGRA: Usar função auxiliar de permissão
    if not pode_ver_chamado(chamado):
        current_app.logger.info(f"[DETALHE] PERMISSAO NEGADA para chamado {chamado_id}")
        flash('Você não tem permissão para visualizar este chamado.', 'error')
        # Redirecionar para a página correta conforme o perfil
        if current_user.perfil.value == PerfilUsuario.USUARIO.value:
            return redirect(url_for('main.meus_chamados'))
        return redirect(url_for('main.chamados'))

    current_app.logger.info(f"[DETALHE] PERMISSAO CONCEDIDA para chamado {chamado_id}")

    mensagens = Mensagem.query.filter_by(chamado_id=chamado_id).order_by(Mensagem.created_at.asc()).all()
    anexos = Anexo.query.filter_by(chamado_id=chamado_id).order_by(Anexo.created_at.desc()).all()

    # Usuários do setor para atribuição (todos os colaboradores do setor)
    usuarios_setor = []
    if current_user.perfil.value in [PerfilUsuario.ADMIN.value, PerfilUsuario.SETOR.value]:
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
    """Atualiza o status de um chamado.

    NOVO: Se o usuário for admin/setor e clicar em resolver/fechar,
    o chamado é automaticamente atribuído a ele.
    """
    chamado = Chamado.query.get_or_404(chamado_id)

    # NOVA REGRA: Verificar permissão
    if not pode_ver_chamado(chamado):
        flash('Permissão negada.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    # Apenas admin e setor podem alterar status
    if current_user.perfil.value == PerfilUsuario.USUARIO.value:
        flash('Apenas administradores e membros do setor podem alterar o status.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    novo_status = request.form.get('status')
    observacao = request.form.get('observacao', '')
    solucao_tecnica = request.form.get('solucao_tecnica', '').strip()

    if novo_status not in [s.value for s in StatusChamado]:
        flash('Status inválido.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))

    try:
        # NOVO: Auto-atribuição para admin/setor ao resolver/fechar
        if current_user.perfil.value in [PerfilUsuario.ADMIN.value, PerfilUsuario.SETOR.value]:
            if not chamado.atendente_id:
                chamado.atendente_id = current_user.id
                registrar_log(current_user.id, 'atribuir', 'chamado', chamado.id,
                             f'Chamado auto-atribuído ao usuário {current_user.id} ao atualizar status')
            elif chamado.atendente_id != current_user.id and novo_status in ['resolvido', 'fechado']:
                # Se já tem atendente mas é diferente, atualiza para quem está resolvendo
                chamado.atendente_id = current_user.id
                registrar_log(current_user.id, 'atribuir', 'chamado', chamado.id,
                             f'Chamado reatribuído ao usuário {current_user.id}')

        # Se o status for resolvido ou fechado, exige solução técnica
        if novo_status in ['resolvido', 'fechado']:
            if not solucao_tecnica or len(solucao_tecnica) < 5:
                flash('Para resolver ou fechar um chamado, é obrigatório descrever o que foi realizado (mínimo 5 caracteres).', 'error')
                return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))
            # Salvar a solução técnica no chamado
            chamado.solucao_tecnica = solucao_tecnica

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
        db.session.rollback()
        flash(f'Erro ao atualizar status: {str(e)}', 'error')

    return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))


@main.route('/chamados/<int:chamado_id>/atribuir', methods=['POST'])
@login_required
def atribuir_chamado(chamado_id):
    """Atribui um chamado a um atendente."""
    if current_user.perfil.value not in [PerfilUsuario.ADMIN.value, PerfilUsuario.SETOR.value]:
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
        db.session.rollback()
        flash(f'Erro ao atribuir chamado: {str(e)}', 'error')

    return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))


@main.route('/chamados/<int:chamado_id>/mensagem', methods=['POST'])
@login_required
def enviar_mensagem(chamado_id):
    """Envia uma mensagem em um chamado."""
    chamado = Chamado.query.get_or_404(chamado_id)

    # NOVA REGRA: Usar função auxiliar de permissão
    if not pode_enviar_mensagem(chamado):
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
        db.session.rollback()
        flash(f'Erro ao enviar mensagem: {str(e)}', 'error')

    return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))


@main.route('/chamados/<int:chamado_id>/upload', methods=['POST'])
@login_required
def upload_anexo(chamado_id):
    """Faz upload de anexo em um chamado."""
    chamado = Chamado.query.get_or_404(chamado_id)

    # NOVA REGRA: Usar função auxiliar de permissão
    if not pode_enviar_mensagem(chamado):
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
            db.session.rollback()
            flash(f'Erro ao enviar arquivo: {str(e)}', 'error')
    else:
        flash('Tipo de arquivo não permitido.', 'error')

    return redirect(url_for('main.chamado_detalhe', chamado_id=chamado_id))




# ═══════════════════════════════════════════════════════════════════════════════
# ROTA PARA VISUALIZAR/BAIXAR ANEXOS
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/anexos/<int:anexo_id>')
@login_required
def ver_anexo(anexo_id):
    """Visualiza ou faz download de um anexo.

    Verifica permissões:
    - ADMIN: pode ver qualquer anexo
    - SETOR: pode ver anexos de chamados do seu setor
    - USUÁRIO: pode ver anexos dos seus próprios chamados + chamados do seu setor
    """
    anexo = Anexo.query.get_or_404(anexo_id)
    chamado = Chamado.query.get_or_404(anexo.chamado_id)

    # NOVA REGRA: Usar função auxiliar de permissão
    if not pode_ver_chamado(chamado):
        flash('Você não tem permissão para acessar este anexo.', 'error')
        return redirect(url_for('main.chamados'))

    # Construir caminho completo do arquivo
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    file_path = os.path.join(upload_folder, anexo.caminho_arquivo)

    # Verificar se arquivo existe
    if not os.path.exists(file_path):
        flash('Arquivo não encontrado no servidor.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=anexo.chamado_id))

    # Determinar tipo MIME para visualização inline
    extensao = anexo.tipo_arquivo.lower()
    mimetypes = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'txt': 'text/plain',
        'csv': 'text/csv',
        'json': 'application/json',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
    }
    mimetype = mimetypes.get(extensao, 'application/octet-stream')

    # Para imagens e PDFs, tentar abrir inline; para outros, forçar download
    as_attachment = extensao not in ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'txt', 'csv', 'json']

    try:
        return send_from_directory(
            upload_folder,
            anexo.caminho_arquivo,
            mimetype=mimetype,
            as_attachment=as_attachment,
            download_name=anexo.nome_arquivo
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar anexo {anexo_id}: {str(e)}")
        flash('Erro ao abrir o arquivo.', 'error')
        return redirect(url_for('main.chamado_detalhe', chamado_id=anexo.chamado_id))

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
        if current_user.perfil.value == PerfilUsuario.USUARIO.value:
            if current_user.setor_id is not None:
                query = query.filter(
                    db.or_(
                        Chamado.usuario_id == current_user.id,
                        Chamado.setor_destino_id == current_user.setor_id
                    )
                )
            else:
                query = query.filter(Chamado.usuario_id == current_user.id)
        elif current_user.perfil.value == PerfilUsuario.SETOR.value:
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
# ROTAS PROTEGIDAS - ADMINISTRAÇÃO (USUÁRIOS - CORRIGIDO)
# ═══════════════════════════════════════════════════════════════════════════════

@main.route('/admin/usuarios')
@login_required
def admin_usuarios():
    """Gerenciamento de usuários (apenas admin).

    Ordenação:
      - Ativos primeiro (mais recentes no topo)
      - Inativos depois (mais recentes no topo)
    """
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

    usuarios = query.order_by(Usuario.ativo.desc(), Usuario.created_at.desc()).paginate(
        page=pagina, per_page=10, error_out=False
    )

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

    perfil = request.form.get('perfil', 'usuario')

    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip(),
        'telefone': request.form.get('telefone', '').strip(),
        'senha': request.form.get('senha', ''),
        'perfil': perfil,
        'setor_id': request.form.get('setor_id', type=int)
    }

    if perfil == 'setor':
        if not dados['setor_id']:
            flash('Para perfil "Setor", é obrigatório selecionar um setor de trabalho.', 'error')
            return redirect(url_for('main.admin_usuarios'))

    if perfil in ('usuario', 'admin'):
        dados['setor_id'] = None

    try:
        UsuarioService.criar_usuario(dados)
        flash('Usuário criado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar usuário: {str(e)}', 'error')

    return redirect(url_for('main.admin_usuarios'))


@main.route('/admin/usuarios/<int:usuario_id>/editar', methods=['POST'])
@login_required
def admin_editar_usuario(usuario_id):
    """Edita um usuário (apenas admin)."""
    if not current_user.is_admin():
        flash('Acesso restrito.', 'error')
        return redirect(url_for('main.dashboard'))

    if usuario_id == current_user.id:
        flash('Use a página de perfil para editar seus próprios dados.', 'warning')
        return redirect(url_for('main.admin_usuarios'))

    perfil = request.form.get('perfil')

    dados = {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip(),
        'telefone': request.form.get('telefone', '').strip(),
        'perfil': perfil,
        'setor_id': request.form.get('setor_id', type=int),
        'ativo': request.form.get('ativo') == 'on'
    }

    if perfil == 'setor':
        if not dados['setor_id']:
            flash('Para perfil "Setor", é obrigatório selecionar um setor de trabalho.', 'error')
            return redirect(url_for('main.admin_usuarios'))

    if perfil in ('usuario', 'admin'):
        dados['setor_id'] = None

    senha = request.form.get('senha', '')
    if senha:
        dados['senha'] = senha

    try:
        UsuarioService.atualizar_usuario(usuario_id, dados, current_user.id)
        flash('Usuário atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar usuário: {str(e)}', 'error')

    return redirect(url_for('main.admin_usuarios'))


# ═══════════════════════════════════════════════════════════════════════════════
# DESATIVAR / REATIVAR (apenas muda o campo 'ativo' - reversível)
# ═══════════════════════════════════════════════════════════════════════════════
@main.route('/admin/usuarios/<int:usuario_id>/toggle-status', methods=['POST'])
@login_required
def admin_toggle_status_usuario(usuario_id):
    """Alterna o status ativo/inativo de um usuário (apenas admin).

    Esta rota APENAS muda o campo 'ativo' do usuário.
    NÃO remove o usuário do banco.
    O usuário pode ser reativado posteriormente.
    """
    if not current_user.is_admin():
        flash('Acesso restrito.', 'error')
        return redirect(url_for('main.dashboard'))

    if usuario_id == current_user.id:
        flash('Você não pode alterar seu próprio status.', 'error')
        return redirect(url_for('main.admin_usuarios'))

    usuario = Usuario.query.get_or_404(usuario_id)

    # Impedir desativação do último admin ativo
    if usuario.perfil.value == PerfilUsuario.ADMIN.value and usuario.ativo:
        total_admins_ativos = Usuario.query.filter_by(
            perfil=PerfilUsuario.ADMIN, 
            ativo=True
        ).count()
        if total_admins_ativos <= 1:
            flash('Não é possível desativar o único administrador ativo.', 'error')
            return redirect(url_for('main.admin_usuarios'))

    try:
        usuario.ativo = not usuario.ativo
        db.session.commit()

        acao = 'reativar' if usuario.ativo else 'desativar'
        status_msg = 'reativado' if usuario.ativo else 'desativado'

        registrar_log(
            current_user.id, 
            acao, 
            'usuario', 
            usuario.id,
            f'Usuário {usuario.nome} {status_msg}'
        )

        flash(f'Usuário {usuario.nome} {status_msg} com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status do usuário: {str(e)}', 'error')

    return redirect(url_for('main.admin_usuarios'))


# ═══════════════════════════════════════════════════════════════════════════════
# EXCLUIR PERMANENTEMENTE (DELETE do banco - IRREVERSÍVEL)
# ═══════════════════════════════════════════════════════════════════════════════
@main.route('/admin/usuarios/<int:usuario_id>/excluir', methods=['POST'])
@login_required
def admin_excluir_usuario(usuario_id):
    """Exclui um usuário PERMANENTEMENTE do banco de dados (apenas admin).

    ATENÇÃO: Esta ação é IRREVERSÍVEL. O usuário é completamente removido.
    Requer confirmação de senha do administrador.
    """
    if not current_user.is_admin():
        flash('Acesso restrito.', 'error')
        return redirect(url_for('main.dashboard'))

    if usuario_id == current_user.id:
        flash('Você não pode excluir seu próprio usuário.', 'error')
        return redirect(url_for('main.admin_usuarios'))

    usuario = Usuario.query.get_or_404(usuario_id)

    # Verificar senha do administrador para confirmação
    senha_confirmacao = request.form.get('senha_confirmacao', '')
    if not current_user.check_senha(senha_confirmacao):
        flash('Senha de confirmação incorreta.', 'error')
        return redirect(url_for('main.admin_usuarios'))

    # Impedir exclusão do último admin
    if usuario.perfil.value == PerfilUsuario.ADMIN.value:
        total_admins = Usuario.query.filter_by(
            perfil=PerfilUsuario.ADMIN, 
            ativo=True
        ).count()
        if total_admins <= 1:
            flash('Não é possível excluir o único administrador ativo.', 'error')
            return redirect(url_for('main.admin_usuarios'))

    try:
        nome_usuario = usuario.nome

        # SOFT DELETE: desativa ao invés de excluir para preservar chamados e histórico
        usuario.ativo = False
        db.session.commit()

        registrar_log(
            current_user.id, 
            'desativar', 
            'usuario', 
            usuario_id,
            f'Usuário {nome_usuario} desativado (soft delete) - chamados preservados'
        )

        flash(f'Usuário {nome_usuario} desativado com sucesso! Chamados e histórico preservados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desativar usuário: {str(e)}', 'error')

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
        db.session.rollback()
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

    if not pode_ver_chamado(chamado):
        return jsonify({'error': 'Permissão negada'}), 403

    return jsonify(chamado.to_dict())