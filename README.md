# Dashboard Nola

## Descrição

Este projeto é um dashboard web para análise de dados de restaurantes, desenvolvido com Django e Django REST Framework. Ele fornece uma interface para visualizar insights sobre vendas, produtos, clientes e lojas, utilizando dados simulados para demonstração. O sistema inclui APIs RESTful para acesso programático aos dados e uma interface web simples para navegação.

O dashboard foi projetado para restaurantes que desejam monitorar seu desempenho operacional, incluindo métricas de vendas, inventário de produtos e análise de clientes. Os dados são armazenados em um banco de dados PostgreSQL e incluem informações simuladas de 541.979 vendas, 10.000 clientes, 498 produtos e 50 lojas.

## Funcionalidades

- **Análise de Vendas**: Visualização de vendas por loja, produto e período.
- **Gestão de Produtos**: Lista e detalhes de produtos disponíveis.
- **Análise de Clientes**: Insights sobre comportamento de clientes.
- **Gestão de Lojas**: Informações sobre todas as lojas da rede.
- **APIs REST**: Endpoints para integração com outros sistemas.
- **Interface Web**: Páginas HTML para navegação e visualização de dados.
- **Middleware Personalizado**: Tratamento de erros de banco de dados com respostas JSON adequadas.

## Tecnologias Utilizadas

- **Backend**: Django 5.2.7
- **API**: Django REST Framework 3.16.1
- **Banco de Dados**: PostgreSQL (com psycopg2-binary 2.9.11)
- **Servidor**: Gunicorn 23.0.0
- **Arquivos Estáticos**: WhiteNoise 6.8.2
- **Configuração de Banco**: dj-database-url 3.0.1
- **Python**: 3.13.0
- **Deploy**: Render (com suporte a render.yaml)

## Estrutura do Projeto

```
dashboard_nola/
├── dashboard_Maria/          # App principal
│   ├── models.py            # Modelos Django (Stores, Sales, Products, Customers)
│   ├── views.py             # Views para APIs e páginas web
│   ├── serializers.py       # Serializers para DRF
│   ├── urls.py              # URLs do app
│   ├── utils.py             # Utilitários para processamento de dados
│   ├── templates/           # Templates HTML
│   ├── static/              # Arquivos estáticos (CSS, JS, imagens)
│   └── migrations/          # Migrações do banco
├── dashboard_nola/          # Configurações do projeto
│   ├── settings.py          # Configurações Django
│   ├── urls.py              # URLs principais
│   ├── wsgi.py              # Configuração WSGI
│   └── asgi.py              # Configuração ASGI
├── scripts/                 # Scripts auxiliares
├── manage.py                # Comando de gerenciamento Django
├── requirements.txt         # Dependências Python
├── render.yaml              # Configuração para deploy no Render
├── migrate_to_render.sh     # Script de migração para Render
├── dashboard_backup.json    # Backup dos dados simulados
└── README.md                # Este arquivo
```

## Instalação e Configuração

### Pré-requisitos

- Python 3.13.0
- PostgreSQL
- Git

### Passos de Instalação

1. **Clone o repositório**:
   ```
   git clone <URL_DO_REPOSITORIO>
   cd dashboard_nola
   ```

2. **Crie um ambiente virtual**:
   ```
   python -m venv env
   source env/bin/activate  # No Windows: env\Scripts\activate
   ```

3. **Instale as dependências**:
   ```
   pip install -r requirements.txt
   ```

4. **Configure o banco de dados**:
   - Crie um banco PostgreSQL local.
   - Atualize `DATABASE_URL` em `dashboard_nola/settings.py` ou defina como variável de ambiente.

5. **Execute as migrações**:
   ```
   python manage.py migrate
   ```

6. **Importe os dados simulados**:
   ```
   python manage.py loaddata dashboard_backup.json
   ```

7. **Colete arquivos estáticos**:
   ```
   python manage.py collectstatic
   ```

8. **Execute o servidor**:
   ```
   python manage.py runserver
   ```

Acesse em http://127.0.0.1:8000/

## Uso

### Interface Web

- **Página Inicial**: http://127.0.0.1:8000/ - Visão geral do dashboard.
- **Insights**: http://127.0.0.1:8000/insights/ - Análises detalhadas.

### APIs REST

Base URL: http://127.0.0.1:8000/api/

#### Endpoints Principais

- `GET /api/stores/` - Lista todas as lojas.
- `GET /api/stores/{id}/` - Detalhes de uma loja específica.
- `GET /api/products/` - Lista todos os produtos.
- `GET /api/products/{id}/` - Detalhes de um produto.
- `GET /api/customers/` - Lista todos os clientes.
- `GET /api/customers/{id}/` - Detalhes de um cliente.
- `GET /api/sales/` - Lista todas as vendas (com paginação).
- `GET /api/sales/{id}/` - Detalhes de uma venda.
- `GET /api/insights/sales-by-store/` - Vendas agregadas por loja.
- `GET /api/insights/top-products/` - Produtos mais vendidos.
- `GET /api/insights/customer-stats/` - Estatísticas de clientes.
- `GET /api/insights/revenue-trends/` - Tendências de receita.

Todos os endpoints retornam dados em formato JSON. Para autenticação, use tokens se implementado (atualmente não requer autenticação para demonstração).

## Deploy

### Render

1. Faça push do código para um repositório Git (GitHub, GitLab).
2. Crie uma conta no Render.com.
3. Crie um banco PostgreSQL no Render.
4. Crie um Web Service conectando o repositório, usando `render.yaml` para configuração automática.
5. Defina variáveis de ambiente: `DATABASE_URL`, `SECRET_KEY`, `DJANGO_SETTINGS_MODULE`.
6. Execute o script `migrate_to_render.sh` no shell do Render para migrar e importar dados.

O app estará disponível em uma URL como https://dashboard-nola.onrender.com/

## Desenvolvimento

### Executando Testes

```
python manage.py test
```

### Adicionando Novos Insights

1. Adicione lógica em `utils.py`.
2. Crie views em `views.py`.
3. Configure URLs em `urls.py`.
4. Atualize templates se necessário.

### Middleware

O projeto inclui um middleware personalizado (`DBResourceErrorMiddleware`) para capturar erros de recursos do banco e retornar respostas 503 JSON adequadas.

## Contribuição

1. Fork o repositório.
2. Crie uma branch para sua feature: `git checkout -b feature/nova-feature`.
3. Faça commit das mudanças: `git commit -am 'Adiciona nova feature'`.
4. Push para a branch: `git push origin feature/nova-feature`.
5. Abra um Pull Request.

## Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Suporte

Para questões ou bugs, abra uma issue no repositório Git.