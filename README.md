# Sistema de Chamados 

Sistema web completo para gestão de chamados internos de uma escola. Desenvolvido com Flask, SQLAlchemy, HTML5 semântico, CSS3 moderno e JavaScript vanilla.

## Funcionalidades

### MVP Implementado
- **Autenticação e Autorização**: Login seguro com bcrypt, sessões com Flask-Login, três perfis (Admin, Setor, Usuário)
- **Dashboard**: Estatísticas em tempo real, gráficos interativos (Chart.js), últimos chamados
- **Chamados**: Criação, listagem com filtros avançados, paginação, detalhes completos
- **Relatórios**: Gráficos por mês, setor, status e prioridade, tabelas detalhadas
- **Chat/Mensagens**: Comunicação em tempo real dentro de cada chamado
- **Notificações**: Sistema de notificações em tempo real
- **Upload de Arquivos**: Anexos em chamados com validação de tipos
- **Administração**: Gestão de usuários, setores e logs de operações
- **Perfil do Usuário**: Edição de dados e alteração de senha

### Regras de Negócio
- Cada funcionário realiza seu cadastro e seleciona seu setor
- Cada setor visualiza apenas seus chamados recebidos
- Cada usuário visualiza apenas seus chamados realizados
- Administradores têm acesso total ao sistema
- Logs detalhados de todas as operações

## Estrutura do Projeto

sistema-chamados/
├── backend/
│   ├── app.py              # Aplicação principal Flask
│   ├── models/
│   │   └── modelos.py      # Modelos SQLAlchemy
│   ├── routes/
│   │   └── rotas.py        # Blueprints e endpoints
│   ├── services/
│   │   └── servicos.py     # Lógica de negócio
│   └── utils/
│       └── utilitarios.py  # Funções auxiliares
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── estilos.css # CSS completo
│   │   └── js/
│   │       └── scripts.js  # JavaScript completo
│   └── templates/          # Templates Jinja2
├── database/
│   ├── schema.sql          # Script de criação do BD
│   └── seed.sql            # Dados de exemplo
├── config.py               # Configurações da aplicação
├── requirements.txt        # Dependências Python
├── .env.example            # Exemplo de variáveis de ambiente
└── README.md               # Este arquivo

