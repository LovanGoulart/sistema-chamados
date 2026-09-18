"""
Serviço de IA para o assistente de TI no chat de chamados.
Versão assíncrona: a resposta da IA é gerada em background (thread),
sem travar a requisição do usuário.
"""
import os
import time
import threading
import requests
from flask import current_app
from backend.models.modelos import db, Mensagem

BOT_EMAIL = 'assistente-ia@interno.local'
BOT_NOME = 'Assistente de TI'

SYSTEM_PROMPT = """Você é o assistente de TI do Colégio Mauá.
Ajude o usuário com dúvidas técnicas: senhas, rede, Wi-Fi, impressoras,
e-mail, projetor, projeção, videoconferência, sistema de chamados.
Seja breve, cordial e objetivo (máximo 3 parágrafos curtos).
Se não souber resolver ou se o problema exigir acesso físico/equipe,
oriente o usuário a aguardar o atendente humano do setor."""


def get_bot_id():
    """Busca (ou cria) o usuário bot no banco."""
    from backend.models.modelos import Usuario, PerfilUsuario

    bot = Usuario.query.filter_by(email=BOT_EMAIL).first()
    if bot:
        return bot.id

    bot = Usuario(
        nome=BOT_NOME,
        email=BOT_EMAIL,
        telefone='',
        perfil=PerfilUsuario.ADMIN,
        ativo=True
    )
    bot.set_senha(os.urandom(24).hex())  # senha aleatória — bot não faz login
    db.session.add(bot)
    db.session.commit()
    return bot.id


def responder_ia(chamado, pergunta: str) -> str:
    """Chama a API de IA e retorna a resposta em texto."""
    api_url = current_app.config.get('IA_API_URL')
    api_key = current_app.config.get('IA_API_KEY')

    if not api_url or not api_key:
        raise RuntimeError('IA não configurada (IA_API_URL / IA_API_KEY)')

    contexto = (
        f"Título do chamado: {chamado.titulo}\n"
        f"Descrição: {chamado.descricao}\n"
        f"Local: {chamado.local}"
    )

    payload = {
        "model": current_app.config.get('IA_MODEL', 'moonshot-v1-8k'),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Chamado #{chamado.id}:\n{contexto}\n\nMensagem do usuário: {pergunta}"}
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }

    resp = requests.post(
        api_url,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _salvar_resposta_bot(chamado_id: int, resposta: str):
    """Salva a mensagem do bot com retry (SQLite pode bloquear em concorrência)."""
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
        except Exception:
            db.session.rollback()
            if tentativa < 2:
                time.sleep(0.5)  # espera 0.5s e tenta de novo
            else:
                raise


def responder_como_bot(chamado_id: int, pergunta: str):
    """
    Gera resposta da IA e salva como mensagem do bot no chamado.
    Chamado APENAS depois que a mensagem do usuário já foi salva.
    """
    from backend.models.modelos import Chamado

    chamado = Chamado.query.get(chamado_id)
    if not chamado:
        return

    # A IA NÃO responde se já existe atendente humano responsável
    if chamado.atendente_id:
        return

    try:
        resposta = responder_ia(chamado, pergunta)
    except Exception as e:
        current_app.logger.error(f"[IA] Falha no chamado {chamado_id}: {e}")
        resposta = ("⚠️ Não consegui processar sua pergunta agora. "
                    "Um atendente do setor irá responder em breve.")

    _salvar_resposta_bot(chamado_id, resposta)


def responder_como_bot_async(chamado_id: int, pergunta: str):
    """
    Dispara a resposta da IA em uma thread em background.

    A thread cria seu próprio app context e usa sua própria conexão
    com o banco (SQLAlchemy scoped_session é thread-safe).
    """
    app = current_app._get_current_object()  # pega o objeto real do app (não o proxy)

    def _worker():
        with app.app_context():
            try:
                responder_como_bot(chamado_id, pergunta)
            except Exception as e:
                app.logger.error(f"[IA] Erro na thread do chamado {chamado_id}: {e}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
