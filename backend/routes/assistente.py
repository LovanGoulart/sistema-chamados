"""
Rotas do Chat Geral com Assistente Virtual.
Blueprint separado para não poluir o rotas.py principal.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from backend.services.assistente_service import (
    processar_mensagem,
    listar_historico
)

assistente_bp = Blueprint(
    "assistente",
    __name__,
    url_prefix="/api/assistente"
)


@assistente_bp.route("/historico")
@login_required
def historico():
    """Retorna o histórico de conversa do usuário logado."""
    try:
        mensagens = listar_historico(current_user.id)
        return jsonify({
            "success": True,
            "mensagens": mensagens
        })
    except Exception as e:
        current_app.logger.error(f"[CHAT-IA] Erro ao carregar histórico: {e}")
        return jsonify({
            "success": False,
            "error": "Erro ao carregar histórico."
        }), 500


@assistente_bp.route("/mensagem", methods=["POST"])
@login_required
def enviar_mensagem():
    """
    Recebe uma mensagem do usuário, processa com a IA
    e retorna a resposta do bot em JSON.
    """
    dados = request.get_json(silent=True) or {}
    conteudo = (dados.get("mensagem") or "").strip()

    if not conteudo:
        return jsonify({
            "success": False,
            "error": "Mensagem vazia."
        }), 400

    if len(conteudo) > 2000:
        return jsonify({
            "success": False,
            "error": "Mensagem muito longa (máx. 2000 caracteres)."
        }), 400

    try:
        msg_bot = processar_mensagem(current_user.id, conteudo)
        return jsonify({
            "success": True,
            "resposta": msg_bot
        })
    except Exception as e:
        current_app.logger.error(f"[CHAT-IA] Erro ao processar mensagem: {e}")
        return jsonify({
            "success": False,
            "error": "Erro interno. Tente novamente."
        }), 500