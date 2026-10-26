
"""
Serviço de IA para o Assistente do Colégio no chat de chamados.

A resposta da IA é gerada em background (thread),
sem travar a requisição do usuário.

O assistente pode atender chamados de diferentes setores,
utilizando o setor e as informações do chamado como contexto.
"""

import os
import time
import threading
import requests

from flask import current_app

from backend.models.modelos import db, Mensagem


# ============================================================
# CONFIGURAÇÃO DO BOT
# ============================================================

BOT_EMAIL = "assistente-ia@interno.local"
BOT_NOME = "Assistente Virtual"


# ============================================================
# PROMPT PRINCIPAL DA IA
# ============================================================

SYSTEM_PROMPT = """Você é o Assistente Virtual do Colégio Mauá,
integrado ao sistema de chamados.

Sua função é auxiliar os usuários respondendo dúvidas e
solicitações de forma rápida, clara e objetiva.

Você pode receber chamados relacionados a qualquer setor
do Colégio, como Informática, Manutenção, Marcenaria,
Limpeza, Serviço de Apoio, Teatro e outros.

============================================================
REGRAS PRINCIPAIS
============================================================

1. Seja curto, direto e objetivo.

2. Prefira respostas de 1 ou 2 parágrafos curtos.

3. Sempre que souber a solução, forneça uma orientação
   prática e objetiva.

4. Quando necessário, apresente poucos passos para resolver
   o problema.

5. Não repita informações que o usuário já forneceu.

6. Evite introduções desnecessárias.

7. Não seja excessivamente formal ou técnico.

8. Responda sempre em português do Brasil.

9. Nunca invente informações.

10. Quando a mensagem do usuário começar com o comando
    "[OBSERVAÇÃO]", não responda à mensagem. Essa mensagem deve
    ser considerada apenas uma anotação do usuário e não deve
    gerar nenhuma resposta do Assistente Virtual.

============================================================
CONTEXTO DO CHAMADO
============================================================

Antes de responder, considere:

- setor do chamado;
- título;
- descrição;
- local;
- mensagem mais recente do usuário.

O setor serve apenas como contexto para compreender melhor
a solicitação.

Não crie regras específicas de atendimento para cada setor.

============================================================
COMO RESPONDER
============================================================

Quando souber como resolver a solicitação, explique a solução
diretamente ao usuário.

Para problemas de Informática, você pode orientar sobre
computadores, notebooks, sistemas, senhas, rede, Wi-Fi,
impressoras, e-mail, projetores, videoconferência,
periféricos e problemas básicos de software e hardware.

Para solicitações relacionadas a outros setores, analise o
contexto e forneça uma orientação geral quando tiver
segurança para fazê-lo.

Quando a solicitação exigir uma ação física, manutenção
especializada ou uma informação que você não possui, não
invente uma solução.

Nesse caso, informe de forma curta que a dúvida ou solicitação
será analisada pela equipe técnica ou pelo responsável pelo
atendimento.

Exemplos de respostas adequadas:

"Não tenho informações suficientes para orientar essa situação.
A dúvida será analisada pela equipe responsável pelo atendimento."

"Não consigo determinar a solução com as informações
disponíveis. A solicitação será analisada por um técnico."

"Esse procedimento precisa de uma avaliação técnica.
A equipe responsável poderá verificar a situação."

Não diga que o chamado foi direcionado ou encaminhado para
outro setor, pois você não realiza esse tipo de ação.

============================================================
O QUE VOCÊ NÃO DEVE FAZER
============================================================

Você NÃO deve:

- direcionar chamados para setores;
- encaminhar chamados;
- transferir chamados;
- afirmar que encaminhou o chamado;
- afirmar que avisou algum funcionário;
- prometer que alguém irá imediatamente ao local;
- informar prazos que não estejam disponíveis;
- afirmar que um serviço foi realizado;
- inventar funcionários ou responsáveis;
- inventar procedimentos internos;
- inventar senhas;
- inventar configurações de rede;
- inventar informações sobre equipamentos;
- afirmar que possui acesso físico ao Colégio;
- afirmar que realizou alguma ação que não pode executar.

============================================================
QUANDO NÃO SOUBER A RESPOSTA
============================================================

Se você não souber a resposta ou não tiver informações
suficientes para orientar o usuário com segurança:

1. Não invente uma solução.
2. Não dê informações duvidosas como se fossem verdadeiras.
3. Informe de forma breve que a solicitação será analisada
   pela equipe técnica ou pelo responsável pelo atendimento.

Não precisa explicar detalhadamente por que não sabe.

============================================================
ESTILO
============================================================

As respostas devem ser:

- curtas;
- objetivas;
- claras;
- cordiais;
- naturais;
- profissionais.

Sempre que possível, responda em até 3 frases.

Evite textos longos.

Não repita a pergunta do usuário.

Não use listas quando uma resposta simples for suficiente.

Não diga que irá direcionar ou encaminhar o chamado
para outro setor.

Seu objetivo é fornecer uma orientação útil e rápida.
Quando não puder solucionar a dúvida, informe que ela será
analisada pela equipe responsável pelo atendimento.
"""

# ============================================================
# USUÁRIO DO BOT
# ============================================================

def get_bot_id():
    """
    Busca ou cria o usuário utilizado pelo assistente de IA.
    """

    from backend.models.modelos import (
        Usuario,
        PerfilUsuario
    )

    bot = Usuario.query.filter_by(
        email=BOT_EMAIL
    ).first()

    if bot:
        return bot.id

    bot = Usuario(
        nome=BOT_NOME,
        email=BOT_EMAIL,
        telefone="",
        perfil=PerfilUsuario.ADMIN,
        ativo=True
    )

    # Senha aleatória.
    # O bot não realiza login.
    bot.set_senha(
        os.urandom(24).hex()
    )

    db.session.add(bot)
    db.session.commit()

    return bot.id


# ============================================================
# IDENTIFICAR SETOR DO CHAMADO
# ============================================================

def obter_nome_setor(chamado):
    """
    Obtém o nome do setor associado ao chamado.

    Caso não seja possível identificar o setor,
    retorna 'Não informado'.
    """

    try:

        setor = getattr(
            chamado,
            "setor",
            None
        )

        if setor:

            nome = getattr(
                setor,
                "nome",
                None
            )

            if nome:

                return str(nome).strip()

    except Exception as e:

        current_app.logger.warning(
            f"[IA] Não foi possível identificar "
            f"o setor do chamado #{chamado.id}: {e}"
        )

    return "Não informado"


# ============================================================
# CHAMADA DA API GEMINI
# ============================================================

def responder_ia(
    chamado,
    pergunta: str
) -> str:
    """
    Chama a API Gemini através do endpoint compatível
    com OpenAI.

    Possui retry automático para erros temporários
    da API.
    """

    api_url = current_app.config.get(
        "IA_API_URL"
    )

    api_key = current_app.config.get(
        "IA_API_KEY"
    )

    if not api_url or not api_key:

        raise RuntimeError(
            "IA não configurada "
            "(IA_API_URL / IA_API_KEY)"
        )

    modelo = current_app.config.get(
        "IA_MODEL",
        "gemini-3.1-flash-lite"
    )

    # ========================================================
    # SETOR
    # ========================================================

    nome_setor = obter_nome_setor(
        chamado
    )

    # ========================================================
    # CONTEXTO DO CHAMADO
    # ========================================================

    contexto = (
        f"Setor responsável: {nome_setor}\n"
        f"Título do chamado: {chamado.titulo}\n"
        f"Descrição do chamado: {chamado.descricao}\n"
        f"Local: {chamado.local}"
    )

    # ========================================================
    # PAYLOAD
    # ========================================================

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
                    f"Chamado #{chamado.id}\n\n"
                    f"{contexto}\n\n"
                    f"Mensagem mais recente do usuário:\n"
                    f"{pergunta}"
                )
            }

        ],

        "temperature": 0.3,
        "max_tokens": 500
    }

    # ========================================================
    # HEADERS
    # ========================================================

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # ========================================================
    # RETRIES
    # ========================================================

    max_tentativas = 3

    status_retentaveis = {
        429,
        500,
        502,
        503,
        504
    }

    # ========================================================
    # CHAMAR API
    # ========================================================

    for tentativa in range(
        1,
        max_tentativas + 1
    ):

        try:

            current_app.logger.info(
                f"[IA] Chamado #{chamado.id} - "
                f"tentativa {tentativa}/"
                f"{max_tentativas} - "
                f"setor={nome_setor} - "
                f"modelo={modelo}"
            )

            resp = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=(10, 60)
            )

        # ====================================================
        # TIMEOUT
        # ====================================================

        except requests.exceptions.Timeout as e:

            current_app.logger.warning(
                f"[IA] Timeout no chamado "
                f"#{chamado.id} "
                f"(tentativa {tentativa}/"
                f"{max_tentativas}): {e}"
            )

            if tentativa < max_tentativas:

                espera = 2 ** tentativa

                time.sleep(
                    espera
                )

                continue

            raise RuntimeError(
                "A API de IA demorou muito "
                "para responder."
            )

        # ====================================================
        # ERRO DE CONEXÃO
        # ====================================================

        except requests.exceptions.RequestException as e:

            current_app.logger.error(
                f"[IA] Erro de conexão com a API "
                f"no chamado #{chamado.id}: {e}"
            )

            if tentativa < max_tentativas:

                espera = 2 ** tentativa

                time.sleep(
                    espera
                )

                continue

            raise RuntimeError(
                f"Erro de conexão com a API "
                f"de IA: {e}"
            )

        # ====================================================
        # RESPOSTA OK
        # ====================================================

        if resp.status_code == 200:

            try:

                dados = resp.json()

                resposta = (
                    dados["choices"][0]
                    ["message"]["content"]
                    .strip()
                )

            except (
                ValueError,
                KeyError,
                IndexError,
                TypeError
            ) as e:

                current_app.logger.error(
                    "[IA] Resposta inválida da API: "
                    f"{resp.text[:1000]}"
                )

                raise RuntimeError(
                    f"Resposta inválida da API de IA: {e}"
                )

            if not resposta:

                raise RuntimeError(
                    "A IA retornou uma resposta vazia."
                )

            current_app.logger.info(
                "[IA] Resposta gerada com sucesso "
                f"para o chamado #{chamado.id}"
            )

            return resposta

        # ====================================================
        # ERROS TEMPORÁRIOS
        # ====================================================

        if resp.status_code in status_retentaveis:

            current_app.logger.warning(
                f"[IA] API retornou "
                f"{resp.status_code} "
                f"no chamado #{chamado.id} "
                f"(tentativa {tentativa}/"
                f"{max_tentativas}): "
                f"{resp.text[:500]}"
            )

            if tentativa < max_tentativas:

                espera = 2 ** tentativa

                current_app.logger.info(
                    f"[IA] Aguardando {espera}s "
                    "antes de tentar novamente..."
                )

                time.sleep(
                    espera
                )

                continue

            raise RuntimeError(
                "API de IA indisponível após "
                f"{max_tentativas} tentativas "
                f"(HTTP {resp.status_code})."
            )

        # ====================================================
        # ERRO DEFINITIVO
        # ====================================================

        current_app.logger.error(
            "[IA] API retornou erro definitivo: "
            f"HTTP {resp.status_code} - "
            f"{resp.text[:500]}"
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

def _salvar_resposta_bot(
    chamado_id: int,
    resposta: str
):
    """
    Salva a mensagem do bot no chat.

    Possui retry para situações em que o SQLite
    esteja temporariamente bloqueado.
    """

    for tentativa in range(3):

        try:

            msg = Mensagem(
                chamado_id=chamado_id,
                usuario_id=get_bot_id(),
                conteudo=resposta
            )

            db.session.add(
                msg
            )

            db.session.commit()

            return

        except Exception as e:

            db.session.rollback()

            current_app.logger.warning(
                "[IA] Erro ao salvar resposta "
                f"do bot no chamado #{chamado_id} "
                f"(tentativa {tentativa + 1}/3): {e}"
            )

            if tentativa < 2:

                time.sleep(0.5)

            else:

                raise


# ============================================================
# PROCESSAR RESPOSTA DO BOT
# ============================================================

def responder_como_bot(
    chamado_id: int,
    pergunta: str
):
    """
    Gera a resposta da IA e salva como mensagem
    no chat do chamado.

    A IA não responde caso já exista um atendente humano.
    """

    from backend.models.modelos import Chamado

    # ========================================================
    # BUSCAR CHAMADO
    # ========================================================

    chamado = db.session.get(
        Chamado,
        chamado_id
    )

    if not chamado:

        current_app.logger.warning(
            f"[IA] Chamado #{chamado_id} "
            "não encontrado."
        )

        return

    # ========================================================
    # VERIFICAR ATENDENTE HUMANO
    # ========================================================

    if chamado.atendente_id:

        current_app.logger.info(
            f"[IA] Chamado #{chamado_id} "
            "já possui atendente humano. "
            "IA não responderá."
        )

        return

    # ========================================================
    # GERAR RESPOSTA
    # ========================================================

    try:

        resposta = responder_ia(
            chamado,
            pergunta
        )

    except Exception as e:

        current_app.logger.error(
            f"[IA] Falha no chamado "
            f"#{chamado_id}: {e}"
        )

        resposta = (
            "Não consegui processar sua solicitação "
            "agora. A equipe responsável pelo setor "
            "irá analisar o chamado e responder em breve."
        )

    # ========================================================
    # SALVAR RESPOSTA
    # ========================================================

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
                    "[IA] Erro na thread do chamado "
                    f"#{chamado_id}: {e}",
                    exc_info=True
                )

    thread = threading.Thread(
        target=_worker,
        daemon=True
    )

    thread.start()
