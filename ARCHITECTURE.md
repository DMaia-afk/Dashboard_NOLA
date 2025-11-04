# Arquitetura do Projeto Dashboard Nola

## Visão Geral

O Dashboard Nola é uma aplicação web baseada em arquitetura MVC (Model-View-Controller) implementada com Django. O sistema segue os princípios do Django REST Framework para APIs e utiliza PostgreSQL como banco de dados relacional. A arquitetura é projetada para ser escalável, modular e fácil de manter, com separação clara entre camadas de apresentação, lógica de negócio e persistência de dados.

## Componentes Principais

### 1. Camada de Apresentação (Presentation Layer)

#### Interface Web
- **Templates HTML**: Localizados em `dashboard_Maria/templates/`, fornecem a interface de usuário para navegação e visualização de dados.
- **Arquivos Estáticos**: CSS, JavaScript e imagens em `dashboard_Maria/static/`, servidos via WhiteNoise em produção.
- **URLs**: Configuradas em `dashboard_nola/urls.py` e `dashboard_Maria/urls.py` para roteamento de páginas.

#### APIs REST
- **Django REST Framework**: Implementa endpoints RESTful para acesso programático aos dados.
- **Serializers**: Em `dashboard_Maria/serializers.py`, convertem objetos Django em JSON e vice-versa.
- **Views**: Em `dashboard_Maria/views.py`, contêm a lógica para processar requisições e retornar respostas.

### 2. Camada de Lógica de Negócio (Business Logic Layer)

#### Models
- **Modelos Django**: Definidos em `dashboard_Maria/models.py`:
  - `Stores`: Representa lojas físicas.
  - `Products`: Catálogo de produtos.
  - `Customers`: Dados de clientes.
  - `Sales`: Registros de vendas.
- Relacionamentos: Vendas estão ligadas a produtos, clientes e lojas via chaves estrangeiras.

#### Utilitários
- **utils.py**: Contém funções auxiliares para processamento de dados, cálculos de métricas e geração de insights.

#### Middleware
- **DBResourceErrorMiddleware**: Middleware personalizado em `dashboard_Maria/middleware.py` para capturar erros de banco de dados e retornar respostas HTTP 503 adequadas.

### 3. Camada de Persistência (Data Layer)

#### Banco de Dados
- **PostgreSQL**: Banco relacional principal.
- **Configuração**: Via `dj-database-url` em `settings.py`, suportando DATABASE_URL para diferentes ambientes.
- **Migrações**: Gerenciadas pelo Django em `dashboard_Maria/migrations/`.

#### Dados
- **Dados Simulados**: Conjunto fixo de dados para demonstração (541.979 vendas, 10.000 clientes, 498 produtos, 50 lojas).
- **Backup**: `dashboard_backup.json` contém fixture para importação rápida.

### 4. Camada de Infraestrutura (Infrastructure Layer)

#### Configurações
- **settings.py**: Configurações centrais do Django, incluindo INSTALLED_APPS, MIDDLEWARE, DATABASES, etc.
- **WSGI/ASGI**: `wsgi.py` e `asgi.py` para servidores web.

#### Deploy
- **Render**: Plataforma de deploy com configuração via `render.yaml`.
- **Gunicorn**: Servidor WSGI para produção.
- **WhiteNoise**: Servidor de arquivos estáticos.

## Fluxo de Dados

### Requisição Web
1. Usuário acessa URL (ex.: `/insights/`).
2. Django roteia via `urls.py` para a view apropriada.
3. View consulta models ou executa lógica em `utils.py`.
4. Dados são renderizados em template HTML ou retornados como JSON.
5. Resposta é enviada ao usuário.

### Requisição API
1. Cliente faz requisição HTTP para endpoint (ex.: `/api/sales/`).
2. DRF autentica/autoriza (atualmente sem autenticação).
3. Serializer valida entrada e converte dados.
4. View processa lógica de negócio.
5. Dados são serializados em JSON e retornados.

### Persistência
- Queries SQL são executadas via ORM Django.
- Dados são armazenados em tabelas PostgreSQL.
- Relacionamentos são mantidos via chaves estrangeiras.

## Padrões de Design Utilizados

### MVC (Model-View-Controller)
- **Model**: Representação dos dados e regras de negócio.
- **View**: Templates e serializers para apresentação.
- **Controller**: Views Django para controle de fluxo.

### Repository Pattern
- Models atuam como repositórios para acesso a dados.

### Middleware Pattern
- Interceptação de requisições para tratamento de erros e segurança.

## Segurança

### Configurações de Segurança
- `DEBUG = False` em produção.
- `SECRET_KEY` via variável de ambiente.
- `ALLOWED_HOSTS` configurado para domínios específicos.
- CSRF protection habilitado por padrão.

### Autenticação
- Atualmente sem autenticação implementada (para demonstração).
- Pronto para adicionar JWT ou sessão-based auth via DRF.

### Validação
- Serializers DRF validam entrada de dados.
- Models Django incluem validações básicas.

## Escalabilidade e Performance

### Otimizações
- **Paginação**: Implementada em endpoints de listagem para grandes volumes de dados.
- **Índices**: Recomendados em campos de busca frequentes (ex.: datas em Sales).
- **Caching**: Não implementado, mas pode ser adicionado via Redis ou cache do Django.
- **Banco**: PostgreSQL suporta alta concorrência.

### Limitações
- Dados simulados são fixos (não crescem).
- Sem cache implementado.
- Single-threaded por padrão (Gunicorn pode ser configurado para múltiplos workers).

## Dependências e Versionamento

### Principais Dependências
- Django 5.2.7: Framework web.
- djangorestframework 3.16.1: APIs REST.
- psycopg2-binary 2.9.11: Driver PostgreSQL.
- dj-database-url 3.0.1: Configuração de banco via URL.
- gunicorn 23.0.0: Servidor WSGI.
- whitenoise 6.8.2: Servidor de arquivos estáticos.

### Versionamento
- Código versionado via Git.
- Dependências fixadas em `requirements.txt`.
- Migrações versionadas automaticamente pelo Django.

## Monitoramento e Logs

### Logs
- Django logging configurado para saída em console/files.
- Erros capturados via middleware.

### Monitoramento
- Render fornece logs e métricas básicas.
- Recomendado adicionar Sentry ou similar para produção.

## Evolução Futura

### Melhorias Possíveis
- Adicionar autenticação/autorização.
- Implementar cache (Redis).
- Adicionar testes unitários e de integração.
- Migrar para microserviços se necessário.
- Adicionar frontend moderno (React/Vue).
- Implementar WebSockets para dados em tempo real.

### Manutenibilidade
- Código modular facilita adições.
- Documentação via README e este arquivo.
- Padrões Django garantem consistência.

## Escolha de Ferramentas e Motivos

### Django 5.2.7
- **Motivo**: Framework web maduro e robusto para Python, com ORM integrado, sistema de templates e administração automática. Escolhido por sua produtividade no desenvolvimento de aplicações web complexas, comunidade ativa e suporte a escalabilidade.
- **Alternativas Consideradas**: Flask (mais leve, mas menos recursos para projetos grandes); FastAPI (mais rápido, mas menos maduro para aplicações full-stack).

### Django REST Framework 3.16.1
- **Motivo**: Biblioteca padrão para construção de APIs REST em Django, oferecendo serialização automática, autenticação e paginação. Facilita a criação de endpoints consistentes e bem documentados.
- **Alternativas Consideradas**: APIView manual do Django (mais verboso); Graphene (para GraphQL, mas REST era suficiente).

### PostgreSQL
- **Motivo**: Banco de dados relacional robusto, com suporte a JSON, transações ACID e alta performance para queries complexas. Ideal para dados estruturados como vendas e relacionamentos.
- **Alternativas Consideradas**: SQLite (para desenvolvimento, mas não escalável); MySQL (menos avançado em JSON).

### psycopg2-binary 2.9.11
- **Motivo**: Driver oficial para PostgreSQL em Python, necessário para conexão com o banco. Versão binary evita dependências de compilação.
- **Alternativas Consideradas**: Outros drivers, mas este é o padrão.

### dj-database-url 3.0.1
- **Motivo**: Simplifica configuração de banco via variável de ambiente DATABASE_URL, essencial para deploys em nuvem como Render.
- **Alternativas Consideradas**: Configuração manual, mas menos flexível.

### Gunicorn 23.0.0
- **Motivo**: Servidor WSGI eficiente para produção, suporta múltiplos workers e é recomendado pelo Django para deploy.
- **Alternativas Consideradas**: uWSGI (mais configurável, mas Gunicorn é mais simples).

### WhiteNoise 6.8.2
- **Motivo**: Permite servir arquivos estáticos diretamente do Django sem necessidade de servidor separado, ideal para deploys simples como no Render.
- **Alternativas Consideradas**: Nginx (mais complexo para setups pequenos).

### Render
- **Motivo**: Plataforma de deploy gratuita com integração fácil via render.yaml, suporta Django nativamente e fornece banco PostgreSQL gerenciado.
- **Alternativas Consideradas**: Heroku (similar, mas Render tem free tier generoso); AWS/GCP (mais poderosos, mas complexos e pagos).

### Python 3.13.0
- **Motivo**: Versão mais recente do Python, com melhorias de performance e compatibilidade com Django 5.2.
- **Alternativas Consideradas**: Versões anteriores (menos otimizadas).

### Git
- **Motivo**: Sistema de controle de versão distribuído, essencial para colaboração e deploy contínuo.
- **Alternativas Consideradas**: SVN (menos popular); GitHub/GitLab para hospedagem.

Essas escolhas priorizam simplicidade, produtividade e adequação ao escopo do projeto (dashboard de dados simulados), garantindo facilidade de desenvolvimento e deploy.