# Sistema de Chamados - Colégio Mauá

Sistema web completo para gestão de chamados internos do Colégio Mauá. Desenvolvido com Flask, SQLAlchemy, HTML5 semântico, CSS3 moderno e JavaScript vanilla.

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

## Stack Tecnológico

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| Python | 3.8+ | Backend |
| Flask | 3.0.3 | Framework web |
| SQLAlchemy | 3.1.1 | ORM |
| Flask-Login | 0.6.3 | Autenticação |
| SQLite | - | Banco de dados |
| bcrypt | 4.1.3 | Hash de senhas |
| Chart.js | 4.4.1 | Gráficos |
| Font Awesome | 6.5.1 | Ícones |

## Estrutura do Projeto

```
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
```

## Instalação

### 1. Clone ou extraia o projeto

```bash
cd sistema-chamados
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente (opcional)

```bash
cp .env.example .env
# Edite o arquivo .env conforme necessário
```

### 5. Execute a aplicação

```bash
python backend/app.py
```

Ou com o Flask CLI:

```bash
export FLASK_APP=backend/app.py
export FLASK_ENV=development
flask run
```

### 6. Acesse o sistema

Abra o navegador em: `http://localhost:5000`

## Contas de Demonstração

| Perfil | E-mail | Senha |
|--------|--------|-------|
| Administrador | admin@colegiomaua.edu.br | admin123 |
| Setor (TI) | joao@colegiomaua.edu.br | 123456 |
| Setor (Manutenção) | maria@colegiomaua.edu.br | 123456 |
| Usuário | carlos@colegiomaua.edu.br | 123456 |
| Usuário | ana@colegiomaua.edu.br | 123456 |

## Perfis de Usuário

- **Administrador**: Acesso total - dashboard, todos os chamados, relatórios, gestão de usuários, setores e logs
- **Setor**: Visualiza apenas chamados direcionados ao seu setor, pode atribuir e atualizar status
- **Usuário**: Visualiza apenas seus próprios chamados, pode criar novos chamados e acompanhar status

## API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/estatisticas` | GET | Estatísticas dos chamados |
| `/api/notificacoes/nao-lidas` | GET | Notificações não lidas |
| `/api/chamados/<id>` | GET | Detalhes de um chamado (JSON) |

## Segurança

- Senhas hasheadas com bcrypt
- Proteção contra SQL Injection (SQLAlchemy ORM)
- Proteção contra XSS (escape automático do Jinja2)
- Sessões seguras com Flask-Login
- Validação de inputs no cliente e servidor
- Logs de operações importantes

## Responsividade

O sistema é totalmente responsivo e funciona em:
- Desktop (telas grandes)
- Tablet (telas médias)
- Mobile (telas pequenas)

## Licença

Sistema desenvolvido exclusivamente para o Colégio Mauá.
