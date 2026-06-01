"""
Serviços de lógica de negócio do Sistema de Chamados - Colégio Mauá
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from backend.models.modelos import (
    db, Usuario, Setor, Chamado, Mensagem, Anexo, 
    LogOperacao, Notificacao, StatusChamado, Prioridade, PerfilUsuario
)
from backend.utils.utilitarios import registrar_log, agora_brasil_naive


class ChamadoService:
    """Serviço para operações relacionadas a chamados."""

    @staticmethod
    def criar_chamado(dados, usuario_id):
        """Cria um novo chamado."""
        chamado = Chamado(
            titulo=dados.get('titulo'),
            descricao=dados.get('descricao'),
            local=dados.get('local'),
            area_patrimonial=dados.get('area_patrimonial'),
            prioridade=Prioridade(dados.get('prioridade', 'media')),
            status=StatusChamado.ABERTO,
            data_preferencial=dados.get('data_preferencial'),
            usuario_id=usuario_id,
            setor_destino_id=dados.get('setor_destino_id')
        )
        db.session.add(chamado)
        db.session.commit()

        # Registrar log
        registrar_log(usuario_id, 'criar', 'chamado', chamado.id, 
                     f'Chamado #{chamado.id} criado')

        # Criar notificação para o setor destino
        usuarios_setor = Usuario.query.filter_by(
            setor_id=chamado.setor_destino_id, 
            ativo=True
        ).all()

        for u in usuarios_setor:
            notificacao = Notificacao(
                usuario_id=u.id,
                titulo='Novo chamado recebido',
                mensagem=f'Chamado #{chamado.id}: {chamado.titulo}',
                link=f'/chamados/{chamado.id}'
            )
            db.session.add(notificacao)

        db.session.commit()
        return chamado

    
    @staticmethod
    def atualizar_status(chamado_id, novo_status, usuario_id, observacao=None):
        """Atualiza o status de um chamado."""
        chamado = Chamado.query.get_or_404(chamado_id)
        status_anterior = chamado.status.value
        chamado.status = StatusChamado(novo_status)

        if novo_status in ['resolvido', 'fechado']:
            chamado.data_resolucao = agora_brasil_naive()

        db.session.commit()

        # Registrar log
        log_detalhes = f'Status alterado de {status_anterior} para {novo_status}'
        if chamado.solucao_tecnica:
            log_detalhes += f' | Solução: {chamado.solucao_tecnica[:100]}...'
        registrar_log(usuario_id, 'atualizar_status', 'chamado', chamado.id, log_detalhes)

        # Notificar o criador do chamado
        notificacao = Notificacao(
            usuario_id=chamado.usuario_id,
            titulo=f'Status do chamado atualizado',
            mensagem=f'Chamado #{chamado.id} agora está: {novo_status}',
            link=f'/chamados/{chamado.id}'
        )
        db.session.add(notificacao)
        db.session.commit()

        return chamado

    @staticmethod
    def atribuir_chamado(chamado_id, atendente_id, usuario_id):
        """Atribui um chamado a um atendente."""
        chamado = Chamado.query.get_or_404(chamado_id)
        chamado.atendente_id = atendente_id
        chamado.status = StatusChamado.EM_ANDAMENTO
        db.session.commit()

        registrar_log(usuario_id, 'atribuir', 'chamado', chamado.id,
                     f'Chamado atribuído ao usuário {atendente_id}')

        # Notificar o atendente
        notificacao = Notificacao(
            usuario_id=atendente_id,
            titulo='Chamado atribuído a você',
            mensagem=f'Chamado #{chamado.id}: {chamado.titulo}',
            link=f'/chamados/{chamado.id}'
        )
        db.session.add(notificacao)
        db.session.commit()

        return chamado

    @staticmethod
    def listar_chamados(usuario, filtros=None, pagina=1, por_pagina=10):
        """Lista chamados com base no perfil do usuário."""
        query = Chamado.query

        # Filtrar por perfil
        # Usar hybrid_property perfil_str para comparação segura em queries SQL
        perfil_atual = usuario.perfil_str

        if perfil_atual == PerfilUsuario.USUARIO.value:
            query = query.filter(Chamado.usuario_id == usuario.id)
        elif perfil_atual == PerfilUsuario.SETOR.value:
            query = query.filter(Chamado.setor_destino_id == usuario.setor_id)
        # Admin vê todos

        # Aplicar filtros
        if filtros:
            if filtros.get('status'):
                query = query.filter(Chamado.status == StatusChamado(filtros['status']))
            if filtros.get('prioridade'):
                query = query.filter(Chamado.prioridade == Prioridade(filtros['prioridade']))
            if filtros.get('setor_destino_id'):
                query = query.filter(Chamado.setor_destino_id == filtros['setor_destino_id'])
            if filtros.get('busca'):
                busca = f"%{filtros['busca']}%"
                query = query.filter(
                    or_(
                        Chamado.titulo.ilike(busca),
                        Chamado.descricao.ilike(busca),
                        Chamado.local.ilike(busca)
                    )
                )

        # Ordenar por data de criação decrescente
        query = query.order_by(Chamado.created_at.desc())

        return query.paginate(page=pagina, per_page=por_pagina, error_out=False)

    @staticmethod
    def get_estatisticas(usuario=None):
        """Retorna estatísticas dos chamados."""
        query = Chamado.query

        if usuario and usuario.perfil == PerfilUsuario.USUARIO:
            query = query.filter(Chamado.usuario_id == usuario.id)
        elif usuario and usuario.perfil == PerfilUsuario.SETOR:
            query = query.filter(Chamado.setor_destino_id == usuario.setor_id)

        total = query.count()

        # Por status
        por_status = {}
        for status in StatusChamado:
            por_status[status.value] = query.filter(Chamado.status == status).count()

        # Por prioridade
        por_prioridade = {}
        for prioridade in Prioridade:
            por_prioridade[prioridade.value] = query.filter(Chamado.prioridade == prioridade).count()

        # Chamados do mês atual
        hoje = agora_brasil_naive()
        inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        chamados_mes = query.filter(Chamado.created_at >= inicio_mes).count()

        # Chamados da semana
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
        chamados_semana = query.filter(Chamado.created_at >= inicio_semana).count()

        # Tempo médio de resolução
        resolvidos = query.filter(Chamado.data_resolucao.isnot(None)).all()
        if resolvidos:
            tempo_total = sum(
                (c.data_resolucao - c.created_at).total_seconds() 
                for c in resolvidos
            )
            tempo_medio = tempo_total / len(resolvidos) / 3600  # em horas
        else:
            tempo_medio = 0

        return {
            'total': total,
            'por_status': por_status,
            'por_prioridade': por_prioridade,
            'chamados_mes': chamados_mes,
            'chamados_semana': chamados_semana,
            'tempo_medio_resolucao': round(tempo_medio, 1),
            'abertos': por_status.get('aberto', 0),
            'em_andamento': por_status.get('em_andamento', 0),
            'resolvidos': por_status.get('resolvido', 0)
        }

    @staticmethod
    def get_chamados_por_mes(usuario=None, meses=6):
        """Retorna contagem de chamados por mês para gráficos."""
        hoje = agora_brasil_naive()
        resultado = []

        for i in range(meses - 1, -1, -1):
            data_ref = hoje - timedelta(days=i * 30)
            inicio_mes = data_ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            if i < meses - 1:
                fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            else:
                fim_mes = hoje

            query = Chamado.query.filter(
                and_(Chamado.created_at >= inicio_mes, Chamado.created_at <= fim_mes)
            )

            if usuario and usuario.perfil == PerfilUsuario.USUARIO:
                query = query.filter(Chamado.usuario_id == usuario.id)
            elif usuario and usuario.perfil == PerfilUsuario.SETOR:
                query = query.filter(Chamado.setor_destino_id == usuario.setor_id)

            resultado.append({
                'mes': inicio_mes.strftime('%b/%Y'),
                'total': query.count()
            })

        return resultado


class UsuarioService:
    """Serviço para operações relacionadas a usuários."""

    @staticmethod
    def criar_usuario(dados):
        """Cria um novo usuário."""
        usuario = Usuario(
            nome=dados.get('nome'),
            email=dados.get('email'),
            telefone=dados.get('telefone'),
            perfil=PerfilUsuario(dados.get('perfil', 'usuario')),
            setor_id=dados.get('setor_id')
        )
        usuario.set_senha(dados.get('senha'))

        db.session.add(usuario)
        db.session.commit()

        registrar_log(None, 'criar', 'usuario', usuario.id,
                     f'Usuário {usuario.nome} criado')

        return usuario

    @staticmethod
    def atualizar_usuario(usuario_id, dados, quem_alterou_id):
        """Atualiza dados de um usuário."""
        usuario = Usuario.query.get_or_404(usuario_id)

        if dados.get('nome'):
            usuario.nome = dados['nome']
        if dados.get('email'):
            usuario.email = dados['email']
        if dados.get('telefone'):
            usuario.telefone = dados['telefone']
        if dados.get('setor_id') is not None:
            usuario.setor_id = dados['setor_id']
        if dados.get('perfil'):
            usuario.perfil = PerfilUsuario(dados['perfil'])
        if dados.get('ativo') is not None:
            usuario.ativo = dados['ativo']
        if dados.get('senha'):
            usuario.set_senha(dados['senha'])

        db.session.commit()

        registrar_log(quem_alterou_id, 'atualizar', 'usuario', usuario.id,
                     f'Usuário {usuario.nome} atualizado')

        return usuario


class MensagemService:
    """Serviço para operações de mensagens."""

    @staticmethod
    def enviar_mensagem(chamado_id, usuario_id, conteudo):
        """Envia uma mensagem em um chamado."""
        mensagem = Mensagem(
            chamado_id=chamado_id,
            usuario_id=usuario_id,
            conteudo=conteudo
        )
        db.session.add(mensagem)
        db.session.commit()

        # Notificar participantes
        chamado = Chamado.query.get(chamado_id)

        # Notificar o outro participante
        if usuario_id == chamado.usuario_id and chamado.atendente_id:
            notificar_id = chamado.atendente_id
        elif chamado.atendente_id and usuario_id == chamado.atendente_id:
            notificar_id = chamado.usuario_id
        else:
            notificar_id = chamado.usuario_id

        notificacao = Notificacao(
            usuario_id=notificar_id,
            titulo='Nova mensagem no chamado',
            mensagem=f'Nova mensagem no chamado #{chamado_id}',
            link=f'/chamados/{chamado_id}'
        )
        db.session.add(notificacao)
        db.session.commit()

        return mensagem


class NotificacaoService:
    """Serviço para operações de notificações."""

    @staticmethod
    def get_nao_lidas(usuario_id):
        """Retorna notificações não lidas do usuário."""
        return Notificacao.query.filter_by(
            usuario_id=usuario_id, 
            lida=False
        ).order_by(Notificacao.created_at.desc()).all()

    @staticmethod
    def marcar_como_lida(notificacao_id, usuario_id):
        """Marca uma notificação como lida."""
        notificacao = Notificacao.query.filter_by(
            id=notificacao_id, 
            usuario_id=usuario_id
        ).first()

        if notificacao:
            notificacao.lida = True
            db.session.commit()

        return notificacao

    @staticmethod
    def marcar_todas_como_lidas(usuario_id):
        """Marca todas as notificações do usuário como lidas."""
        Notificacao.query.filter_by(usuario_id=usuario_id, lida=False).update({'lida': True})
        db.session.commit()