"""
Funções utilitárias do Sistema de Chamados - Colégio Mauá
"""
import os
import re
from datetime import datetime, timezone, timedelta
from flask import request, current_app


# ═══════════════════════════════════════════════════════════════════════════════
# FUSO HORÁRIO DO BRASIL (UTC-3)
# ═══════════════════════════════════════════════════════════════════════════════

# Fuso horário do Brasil (UTC-3) — não considera horário de verão (extinto desde 2019)
FUSO_BRASIL = timezone(timedelta(hours=-3))


def agora_brasil():
    """Retorna o datetime atual no fuso horário do Brasil (UTC-3), com tzinfo."""
    return datetime.now(FUSO_BRASIL)


def agora_brasil_naive():
    """Retorna o datetime atual no fuso horário do Brasil, sem tzinfo (compatível com SQLAlchemy)."""
    return datetime.now(FUSO_BRASIL).replace(tzinfo=None)


def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    return ("." in filename and
        filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"])


def sanitize_filename(filename):
    """Sanitiza o nome do arquivo removendo caracteres especiais."""
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\s.-]", "", filename)
    timestamp = agora_brasil_naive().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    return f"{name}_{timestamp}{ext}"


def registrar_log(usuario_id, acao, entidade, entidade_id=None, detalhes=None):
    """Registra uma operação no log do sistema."""
    # Import local para evitar circular import
    from backend.models.modelos import LogOperacao, db
    try:
        log = LogOperacao(
            usuario_id=usuario_id,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            detalhes=detalhes,
            ip_address=request.remote_addr if request else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar log: {str(e)}")


def formatar_data(data):
    """Formata uma data para exibição no padrão brasileiro (data + hora)."""
    if not data:
        return "-"
    if isinstance(data, str):
        try:
            data = datetime.fromisoformat(data.replace("Z", "+00:00"))
        except ValueError:
            return data
    return data.strftime("%d/%m/%Y %H:%M")


def formatar_data_curta(data):
    """Formata uma data para exibição curta no padrão brasileiro (apenas data)."""
    if not data:
        return "-"
    if isinstance(data, str):
        try:
            data = datetime.fromisoformat(data.replace("Z", "+00:00"))
        except ValueError:
            return data
    return data.strftime("%d/%m/%Y")


def get_prioridade_cor(prioridade):
    """Retorna a cor associada à prioridade."""
    cores = {
        "baixa": "#28a745",
        "media": "#ffc107",
        "alta": "#fd7e14",
        "urgente": "#dc3545"
    }
    return cores.get(prioridade, "#6c757d")


def get_status_cor(status):
    """Retorna a cor associada ao status."""
    cores = {
        "aberto": "#17a2b8",
        "em_andamento": "#ffc107",
        "pendente": "#6f42c1",
        "resolvido": "#28a745",
        "fechado": "#6c757d"
    }
    return cores.get(status, "#6c757d")


def get_prioridade_label(prioridade):
    """Retorna o label traduzido da prioridade."""
    labels = {
        "baixa": "Baixa",
        "media": "Média",
        "alta": "Alta",
        "urgente": "Urgente"
    }
    return labels.get(prioridade, prioridade)


def get_status_label(status):
    """Retorna o label traduzido do status."""
    labels = {
        "aberto": "Aberto",
        "em_andamento": "Em Andamento",
        "pendente": "Pendente",
        "resolvido": "Resolvido",
        "fechado": "Fechado"
    }
    return labels.get(status, status)


def validar_email(email):
    """Valida formato de e-mail."""
    padrao = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(padrao, email) is not None


def validar_telefone(telefone):
    """Valida formato de telefone brasileiro."""
    numeros = re.sub(r"\D", "", telefone)
    return len(numeros) >= 10 and len(numeros) <= 11


def truncate_text(texto, max_length=100):
    """Trunca um texto para o tamanho máximo especificado."""
    if not texto:
        return ""
    if len(texto) <= max_length:
        return texto
    return texto[:max_length].rsplit(" ", 1)[0] + "..."