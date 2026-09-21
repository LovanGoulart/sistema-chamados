"""
Serviço de IA para o assistente de TI no chat de chamados.

A resposta da IA é gerada em background (thread),
sem travar a requisição do usuário.
"""

import os
import time
import threading
import requests

from flask import current_app
from backend.models.modelos import db, Mensagem


BOT_EMAIL = "assistente-ia@interno.local"
BOT_NOME = "Assistente de TI"


SYSTEM_PROMPT = """Você é o assistente de TI do Colégio Mauá.

Ajude o usuário com dúvidas técnicas relacionadas a:
- senhas;
- rede;
- Wi-Fi;
- impressoras;
- e-mail;
- projetores;
- projeção;
- videoconferência;
- sistema de chamados;
- problemas básicos de informática.

Seja breve, cordial e objetivo.
Use no máximo 3 parágrafos curtos.

Dê orientações simples que o usuário consiga executar sozinho.

Se não souber resolver, se o problema exigir acesso administrativo,
acesso físico ao equipamento ou intervenção da equipe de TI,
oriente o usuário a aguardar o atendente humano do setor.

Nunca invente informações sobre equipamentos, sistemas ou configurações
que não estejam disponíveis no contexto do chamado."""


# ============================================================
# CONFIGURAÇÃO DO BOT
# ============================================================

def get_bot_id():
    """Busca ou cria o usuário bot no banco."""
    from backend.models.modelos import Usuario, PerfilUsuario

    bot = Usuario.query.filter_by(email=BOT_EMAIL).first()

    if bot:
        return bot.id

    bot = Usuario(
        nome=BOT_NOME,
        email=BOT_EMAIL,
        telefone="",
        perfil=PerfilUsuario.ADMIN,
        ativo=True
    )

    # Senha aleatória: o bot não faz login.
    bot.set_senha(os.urandom(24).hex())

    db.session.add(bot)
    db.session.commit()

    return bot.id


# ============================================================
# CHAMADA DA API
# ============================================================

def responder_ia(chamado, pergunta: str) -> str:
    """
    Chama a API Gemini através do endpoint compatível com OpenAI.

    Possui retry automático para erros temporários da API.
    """

    api_url = current_app.config.get("IA_API_URL")
    api_key = current_app.config.get("IA_API_KEY")

    if not api_url or not api_key:
        raise RuntimeError(
            "IA não configurada (IA_API_URL / IA_API_KEY)"
        )

    modelo = current_app.config.get(
        "IA_MODEL",
        "gemini-3.1-flash-lite"
    )

    contexto = (
        f"Título do chamado: {chamado.titulo}\n"
        f"Descrição: {chamado.descricao}\n"
        f"Local: {chamado.local}"
    )

    payload = {
        "model": modelo,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    f"Chamado #{chamado.id}:\n"
                    f"{contexto}\n\n"
                    f"Mensagem do usuário: {pergunta}"
                )
            }
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Número máximo de tentativas.
    max_tentativas = 3

    # Erros temporários que justificam nova tentativa.
    status_retentaveis = {
        429,  # limite de requisições
        500,  # erro interno
        502,  # bad gateway
        503,  # serviço temporariamente indisponível
        504   # gateway timeout
    }

    for tentativa in range(1, max_tentativas + 1):

        try:
            current_app.logger.info(
                f"[IA] Chamado #{chamado.id} - "
                f"tentativa {tentativa}/{max_tentativas} - "
                f"modelo={modelo}"
            )

            resp = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=(10, 60)
            )

        except requests.exceptions.Timeout as e:

            current_app.logger.warning(
                f"[IA] Timeout no chamado #{chamado.id} "
                f"(tentativa {tentativa}/{max_tentativas}): {e}"
            )

            if tentativa < max_tentativas:
                espera = 2 ** tentativa
                time.sleep(espera)
                continue

            raise RuntimeError(
                "A API de IA demorou muito para responder."
            )

        except requests.exceptions.RequestException as e:

            current_app.logger.error(
                f"[IA] Erro de conexão no chamado #{chamado.id}: {e}"
            )

            if tentativa < max_tentativas:
                espera = 2 ** tentativa
                time.sleep(espera)
                continue

            raise RuntimeError(
                f"Erro de conexão com a API de IA: {e}"
            )

        # ----------------------------------------------------
        # RESPOSTA OK
        # ----------------------------------------------------

        if resp.status_code == 200:

            try:
                dados = resp.json()

                resposta = (
                    dados["choices"][0]["message"]["content"]
                    .strip()
                )

            except (ValueError, KeyError, IndexError, TypeError) as e:

                current_app.logger.error(
                    f"[IA] Resposta inválida da API: {resp.text[:1000]}"
                )

                raise RuntimeError(
                    f"Resposta inválida da API de IA: {e}"
                )

            if not resposta:
                raise RuntimeError(
                    "A IA retornou uma resposta vazia."
                )

            current_app.logger.info(
                f"[IA] Resposta gerada com sucesso "
                f"para o chamado #{chamado.id}"
            )

            return resposta

        # ----------------------------------------------------
        # ERROS TEMPORÁRIOS
        # ----------------------------------------------------

        if resp.status_code in status_retentaveis:

            current_app.logger.warning(
                f"[IA] API retornou {resp.status_code} "
                f"no chamado #{chamado.id} "
                f"(tentativa {tentativa}/{max_tentativas}): "
                f"{resp.text[:500]}"
            )

            if tentativa < max_tentativas:

                espera = 2 ** tentativa

                current_app.logger.info(
                    f"[IA] Aguardando {espera}s "
                    f"antes de tentar novamente..."
                )

                time.sleep(espera)
                continue

            raise RuntimeError(
                f"API de IA indisponível após "
                f"{max_tentativas} tentativas "
                f"(HTTP {resp.status_code})."
            )

        # ----------------------------------------------------
        # ERROS DEFINITIVOS
        # ----------------------------------------------------

        current_app.logger.error(
            f"[IA] API retornou erro definitivo: "
            f"HTTP {resp.status_code} - {resp.text[:500]}"
        )

        raise RuntimeError(
            f"API retornou {resp.status_code}: "
            f"{resp.text[:400]}"
        )

    raise RuntimeError(
        "Não foi possível obter resposta da IA."
    )


# ============================================================
# SALVAR RESPOSTA NO CHAT
# ============================================================

def _salvar_resposta_bot(chamado_id: int, resposta: str):
    """
    Salva a mensagem do bot com retry.

    O retry também ajuda quando o SQLite está temporariamente
    bloqueado por outra operação.
    """

    for tentativa in range(3):

        try:

            msg = Mensagem(
                chamado_id=chamado_id,
                usuario_id=get_bot_id(),
                conteudo=resposta
            )

            db.session.add(msg)
            db.session.commit()

            return

        except Exception as e:

            db.session.rollback()

            current_app.logger.warning(
                f"[IA] Erro ao salvar resposta do bot "
                f"no chamado #{chamado_id} "
                f"(tentativa {tentativa + 1}/3): {e}"
            )

            if tentativa < 2:
                time.sleep(0.5)
            else:
                raise


# ============================================================
# PROCESSAR RESPOSTA
# ============================================================

def responder_como_bot(chamado_id: int, pergunta: str):
    """
    Gera resposta da IA e salva como mensagem do bot.

    É chamado somente depois que a mensagem do usuário
    já foi salva.
    """

    from backend.models.modelos import Chamado

    chamado = db.session.get(Chamado, chamado_id)

    if not chamado:
        current_app.logger.warning(
            f"[IA] Chamado #{chamado_id} não encontrado."
        )
        return

    # ========================================================
    # NÃO RESPONDER SE JÁ EXISTE ATENDENTE HUMANO
    # ========================================================

    if chamado.atendente_id:

        current_app.logger.info(
            f"[IA] Chamado #{chamado_id} já possui "
            f"atendente humano. IA não responderá."
        )

        return

    try:

        resposta = responder_ia(
            chamado,
            pergunta
        )

    except Exception as e:

        current_app.logger.error(
            f"[IA] Falha no chamado #{chamado_id}: {e}"
        )

        resposta = (
            "Não consegui processar sua pergunta agora. "
            "Um atendente do setor irá responder em breve."
        )

    _salvar_resposta_bot(
        chamado_id,
        resposta
    )


# ============================================================
# EXECUÇÃO EM BACKGROUND
# ============================================================

def responder_como_bot_async(
    chamado_id: int,
    pergunta: str
):
    """
    Dispara a resposta da IA em uma thread em background.

    A thread cria seu próprio app context e utiliza
    a sessão do SQLAlchemy de forma segura para a thread.
    """

    app = current_app._get_current_object()

    def _worker():

        with app.app_context():

            try:

                responder_como_bot(
                    chamado_id,
                    pergunta
                )

            except Exception as e:

                app.logger.error(
                    f"[IA] Erro na thread do chamado "
                    f"#{chamado_id}: {e}",
                    exc_info=True
                )

    thread = threading.Thread(
        target=_worker,
        daemon=True
    )

    thread.start()