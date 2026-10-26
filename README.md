# Sistema de Chamados com Assistente Virtual

Aplicação web para gestão de chamados internos, desenvolvida com Python, Flask e SQLAlchemy e utilizada em um ambiente educacional.

O sistema centraliza solicitações de diferentes setores, permite acompanhar o andamento dos atendimentos e oferece um assistente virtual com inteligência artificial para orientar usuários e auxiliar na abertura de chamados.

## Contexto e objetivo

O projeto foi desenvolvido para organizar demandas internas e reunir, em um único ambiente, as informações necessárias para o atendimento.

Cada solicitação pode conter descrição do problema, local, setor responsável, prioridade e informações complementares. O usuário acompanha o andamento do chamado, enquanto os responsáveis pelo atendimento recebem as solicitações destinadas ao seu setor.

## Situação do projeto

**Em uso e em evolução.**

A aplicação recebe melhorias conforme as necessidades identificadas no uso cotidiano.

## Principais funcionalidades

- Abertura de chamados por formulário ou pelo assistente virtual.
- Acompanhamento do andamento das solicitações.
- Organização dos chamados por setor de destino.
- Controle de acesso com três perfis de usuário.
- Classificação por status e prioridade.
- Registro de local e área patrimonial.
- Informação de data preferencial para atendimento.
- Comunicação entre solicitante e responsável dentro do chamado.
- Envio de anexos.
- Notificações sobre os atendimentos.
- Registro de solução técnica.
- Dashboard com indicadores e gráficos.
- Análise de chamados por setor, status e prioridade.
- Administração de usuários e setores.
- Histórico e logs de operações.

## Perfis de acesso

Todos os perfis podem abrir chamados e acompanhar as próprias solicitações.

| Perfil | Responsabilidades |
|---|---|
| Administrador | Administrar usuários e setores, consultar chamados e acompanhar a operação do sistema. |
| Usuário comum | Registrar solicitações, acompanhar seu andamento e comunicar-se no chamado. |
| Usuário de setor | Receber e atender chamados destinados ao seu setor, além de registrar e acompanhar suas próprias solicitações. |

A visualização e as ações disponíveis seguem as permissões de cada perfil.

## Assistente virtual com IA

O assistente permite que o usuário relate seu problema em linguagem natural, como em uma conversa com um técnico.

Durante o atendimento, o chatbot pode esclarecer dúvidas, sugerir verificações e coletar as informações necessárias para registrar uma solicitação.

### Fluxo de abertura pelo assistente

1. O usuário descreve o problema.
2. O assistente apresenta orientações e solicita as informações que faltam.
3. A conversa reúne os dados necessários para o chamado.
4. O assistente solicita a confirmação do usuário.
5. Após a confirmação, o chamado é criado.
6. O atendimento passa a ser acompanhado pelo fluxo normal do sistema.

A abertura depende da confirmação do usuário. As orientações do assistente apoiam o atendimento e não garantem a resolução de todos os problemas.

O assistente virtual é separado da comunicação entre solicitante e responsável dentro de cada chamado.

## Fluxo de atendimento

1. O usuário abre uma solicitação pelo formulário ou pelo chatbot.
2. O chamado é direcionado ao setor responsável.
3. O usuário de setor acompanha a demanda e realiza o atendimento.
4. Solicitante e responsável podem trocar mensagens e informações.
5. O andamento é registrado por meio das atualizações de status.
6. A solução técnica pode ser registrada para consulta posterior.

## Status e prioridades

| Status | Finalidade |
|---|---|
| Aberto | Solicitação registrada e aguardando atendimento. |
| Em andamento | Atendimento iniciado. |
| Pendente | Solicitação aguardando alguma condição para continuar. |
| Resolvido | Solução registrada para a solicitação. |
| Fechado | Chamado encerrado. |

As prioridades disponíveis são: **baixa, média, alta e urgente**.

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Backend | Python e Flask |
| Persistência | SQLAlchemy e Flask-SQLAlchemy |
| Banco de dados | SQLite na configuração padrão do repositório |
| Autenticação | Flask-Login e bcrypt |
| Interface | HTML, CSS e JavaScript |
| Visualização de dados | Chart.js |
| Configuração | Variáveis de ambiente e python-dotenv |
| Versionamento | Git e GitHub |

## Organização do código

A estrutura principal separa o backend dos templates e arquivos estáticos da interface.

```text
backend/
├── app.py
├── models/
├── routes/
├── services/
└── utils/

frontend/
├── templates/
└── static/

database/
config.py
requirements.txt
run.py
wsgi.py
```

- **models:** entidades e persistência dos dados.
- **routes:** rotas e tratamento das requisições.
- **services:** operações e regras de negócio.
- **utils:** funções auxiliares.
- **templates:** páginas renderizadas pela aplicação.
- **static:** estilos, scripts e recursos visuais.

## Demonstração

O sistema possui telas de acompanhamento, abertura e detalhamento de chamados, além de dashboards e assistente virtual.

As imagens públicas de demonstração devem utilizar dados fictícios ou informações anonimizadas.

## Aspectos técnicos do projeto

- Aplicação de permissões para diferentes perfis de acesso.
- Organização de demandas entre setores.
- Separação de rotas, modelos e serviços no backend.
- Persistência de chamados, mensagens e histórico.
- Integração de uma interface conversacional ao processo de abertura de solicitações.
- Confirmação do usuário antes da criação de chamados pelo assistente.
- Apresentação de indicadores para acompanhamento dos atendimentos.

## Execução e configuração

As dependências Python estão relacionadas em `requirements.txt`, e o repositório possui um arquivo `.env.example` como referência para configuração.

O ponto de entrada local disponível é `run.py`.

A configuração da integração de IA deve corresponder à versão do assistente publicada neste repositório. Credenciais, chaves de API e dados do ambiente de produção não devem ser incluídos no código versionado.

## Autor

Desenvolvido por **Lovan Goulart**.

[Perfil no GitHub](https://github.com/LovanGoulart)
