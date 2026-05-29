"""
Modelos SQLAlchemy do Sistema de Chamados - Colégio Mauá
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from datetime import datetime
from backend.utils.utilitarios import agora_brasil_naive
from enum import Enum
import bcrypt

db = SQLAlchemy()


class StatusChamado(str, Enum):
    """Status possíveis de um chamado."""
    ABERTO = 'aberto'
    EM_ANDAMENTO = 'em_andamento'
    PENDENTE = 'pendente'
    RESOLVIDO = 'resolvido'
    FECHADO = 'fechado'


class Prioridade(str, Enum):
    """Níveis de prioridade de um chamado."""
    BAIXA = 'baixa'
    MEDIA = 'media'
    ALTA = 'alta'
    URGENTE = 'urgente'


class PerfilUsuario(str, Enum):
    """Perfis de usuário do sistema."""
    ADMIN = 'admin'
    SETOR = 'setor'
    USUARIO = 'usuario'


class Setor(db.Model):
    """Modelo de Setor da empresa."""
    __tablename__ = 'setores'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=agora_brasil_naive)

    # Relacionamentos
    usuarios = db.relationship('Usuario', backref='setor', lazy=True)
    chamados_recebidos = db.relationship('Chamado', foreign_keys='Chamado.setor_destino_id', backref='setor_destino', lazy=True)

    def __repr__(self):
        return f'<Setor {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'ativo': self.ativo,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Usuario(db.Model, UserMixin):
    """Modelo de Usuário do sistema."""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20))
    perfil = db.Column(db.Enum(PerfilUsuario), default=PerfilUsuario.USUARIO, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=agora_brasil_naive)
    ultimo_acesso = db.Column(db.DateTime)

    # Relacionamentos
    chamados_criados = db.relationship('Chamado', foreign_keys='Chamado.usuario_id', backref='usuario', lazy=True)
    mensagens = db.relationship('Mensagem', backref='autor', lazy=True)

    def __repr__(self):
        return f'<Usuario {self.nome}>'

    def set_senha(self, senha):
        """Hash da senha usando bcrypt."""
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_senha(self, senha):
        """Verifica se a senha corresponde ao hash."""
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))

    def is_admin(self):
        """Verifica se o usuário é administrador."""
        return self.perfil == PerfilUsuario.ADMIN

    def is_setor(self):
        """Verifica se o usuário pertence a um setor."""
        return self.perfil == PerfilUsuario.SETOR

    @hybrid_property
    def perfil_str(self):
        """Retorna o perfil como string para comparação segura em queries."""
        return self.perfil.value if hasattr(self.perfil, 'value') else str(self.perfil)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'perfil': self.perfil.value,
            'ativo': self.ativo,
            'setor_id': self.setor_id,
            'setor_nome': self.setor.nome if self.setor else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None
        }


class Chamado(db.Model):
    """Modelo de Chamado."""
    __tablename__ = 'chamados'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    local = db.Column(db.String(200), nullable=False)
    area_patrimonial = db.Column(db.String(100))
    prioridade = db.Column(db.Enum(Prioridade), default=Prioridade.MEDIA, nullable=False)
    status = db.Column(db.Enum(StatusChamado), default=StatusChamado.ABERTO, nullable=False)
    data_preferencial = db.Column(db.DateTime)

    # NOVO CAMPO: Solução técnica registrada pelo técnico ao resolver
    solucao_tecnica = db.Column(db.Text, nullable=True)

    # Relacionamentos
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    setor_destino_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    atendente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=agora_brasil_naive)
    updated_at = db.Column(db.DateTime, default=agora_brasil_naive, onupdate=agora_brasil_naive)
    data_resolucao = db.Column(db.DateTime)

    # Relacionamentos adicionais
    mensagens = db.relationship('Mensagem', backref='chamado', lazy=True, cascade='all, delete-orphan')
    anexos = db.relationship('Anexo', backref='chamado', lazy=True, cascade='all, delete-orphan')
    atendente = db.relationship('Usuario', foreign_keys=[atendente_id], backref='chamados_atendidos')

    def __repr__(self):
        return f'<Chamado #{self.id} - {self.titulo}>'

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'local': self.local,
            'area_patrimonial': self.area_patrimonial,
            'prioridade': self.prioridade.value,
            'status': self.status.value,
            'data_preferencial': self.data_preferencial.isoformat() if self.data_preferencial else None,
            'solucao_tecnica': self.solucao_tecnica,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome if self.usuario else None,
            'setor_destino_id': self.setor_destino_id,
            'setor_destino_nome': self.setor_destino.nome if self.setor_destino else None,
            'atendente_id': self.atendente_id,
            'atendente_nome': self.atendente.nome if self.atendente else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'data_resolucao': self.data_resolucao.isoformat() if self.data_resolucao else None
        }


class Mensagem(db.Model):
    """Modelo de Mensagem/Chat no chamado."""
    __tablename__ = 'mensagens'

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=agora_brasil_naive)

    def __repr__(self):
        return f'<Mensagem #{self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'chamado_id': self.chamado_id,
            'usuario_id': self.usuario_id,
            'autor_nome': self.autor.nome if self.autor else None,
            'conteudo': self.conteudo,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Anexo(db.Model):
    """Modelo de Anexo do chamado."""
    __tablename__ = 'anexos'

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=False)
    tipo_arquivo = db.Column(db.String(50))
    tamanho = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=agora_brasil_naive)

    def __repr__(self):
        return f'<Anexo {self.nome_arquivo}>'

    def to_dict(self):
        return {
            'id': self.id,
            'chamado_id': self.chamado_id,
            'nome_arquivo': self.nome_arquivo,
            'caminho_arquivo': self.caminho_arquivo,
            'tipo_arquivo': self.tipo_arquivo,
            'tamanho': self.tamanho,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class LogOperacao(db.Model):
    """Modelo de Log de Operações do sistema."""
    __tablename__ = 'logs_operacoes'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    acao = db.Column(db.String(100), nullable=False)
    entidade = db.Column(db.String(50), nullable=False)
    entidade_id = db.Column(db.Integer)
    detalhes = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=agora_brasil_naive)

    def __repr__(self):
        return f'<Log {self.acao} - {self.entidade}>'

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'acao': self.acao,
            'entidade': self.entidade,
            'entidade_id': self.entidade_id,
            'detalhes': self.detalhes,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Notificacao(db.Model):
    """Modelo de Notificações do sistema."""
    __tablename__ = 'notificacoes'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    lida = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=agora_brasil_naive)

    def __repr__(self):
        return f'<Notificacao {self.titulo}>'

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'titulo': self.titulo,
            'mensagem': self.mensagem,
            'lida': self.lida,
            'link': self.link,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }