# API de Finanças Pessoais

API RESTful para controle de **receitas, despesas e categorias**, desenvolvida para a atividade prática da disciplina **Arquitetura e Desenvolvimento de APIs** (UNINTER).

Cada usuário se cadastra, faz login (JWT) e gerencia apenas as suas próprias transações e categorias. Também é possível consultar o **saldo** (receitas − despesas), com filtro por período.

## Tecnologias

| Item | Escolha |
|---|---|
| Linguagem | Python 3.11+ |
| Framework | FastAPI (+ Uvicorn) |
| Banco de dados | SQLite (padrão; qualquer banco suportado pelo SQLAlchemy via `DATABASE_URL`) |
| ORM | SQLAlchemy 2.0 (mapeamento declarativo) |
| Validação | Pydantic v2 |
| Autenticação | JWT (python-jose) + senhas com bcrypt (passlib) |
| Documentação | Swagger UI / OpenAPI automático |
| Testes | pytest + TestClient (httpx) e cURL |

## Pré-requisitos

- Python 3.11 ou superior
- pip

## Instalação

```bash
git clone <URL-DO-REPOSITORIO>
cd financas-api

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração (banco de dados e variáveis de ambiente)

```bash
cp .env.example .env               # Windows: copy .env.example .env
```

Edite o `.env` e **troque a `SECRET_KEY`** (ex.: `openssl rand -hex 32`). Variáveis:

| Variável | Descrição | Padrão |
|---|---|---|
| `DATABASE_URL` | String de conexão do banco | `sqlite:///./financas.db` |
| `SECRET_KEY` | Chave de assinatura dos tokens JWT | — (obrigatório trocar) |
| `JWT_ALGORITHM` | Algoritmo do JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token | `60` |
| `CORS_ORIGINS` | Origens permitidas (separadas por vírgula) | `http://localhost:3000,http://localhost:5173` |

**Banco:** as tabelas são criadas automaticamente na primeira execução (`create_all` no evento de inicialização). O arquivo `schema.sql` traz o script equivalente caso queira criar a estrutura manualmente.

## Executando

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Resumo dos endpoints

| Método | Endpoint | Finalidade | Auth | Respostas |
|---|---|---|---|---|
| POST | `/auth/register` | Cadastrar usuário | Não | 201 / 409 / 422 |
| POST | `/auth/login` | Obter token JWT | Não | 200 / 401 |
| GET | `/categorias` | Listar categorias do usuário | Sim | 200 / 401 |
| POST | `/categorias` | Criar categoria | Sim | 201 / 409 / 422 |
| DELETE | `/categorias/{id}` | Excluir categoria (sem transações) | Sim | 204 / 404 / 409 |
| GET | `/transacoes` | Listar (filtros: `tipo`, `categoria_id`, `data_inicio`, `data_fim`, `skip`, `limit`) | Sim | 200 / 401 |
| GET | `/transacoes/{id}` | Consultar uma transação | Sim | 200 / 404 |
| GET | `/transacoes/resumo` | Total de receitas, despesas e saldo | Sim | 200 |
| POST | `/transacoes` | Criar transação | Sim | 201 / 400 / 422 |
| PATCH | `/transacoes/{id}` | Atualização parcial | Sim | 200 / 400 / 404 |
| DELETE | `/transacoes/{id}` | Excluir transação | Sim | 204 / 404 |

> **Por que PATCH e não PUT?** O cliente normalmente altera um ou dois campos (ex.: corrigir o valor). PATCH permite enviar só o que mudou; PUT exigiria reenviar o recurso inteiro.

## Autenticação (como testar sem expor credenciais)

1. Cadastre um usuário próprio (os dados ficam só no seu banco local):
   ```bash
   curl -X POST http://127.0.0.1:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"voce@exemplo.com","senha":"minhasenha"}'
   ```
2. Faça login (formulário OAuth2: `username` = e-mail):
   ```bash
   curl -X POST http://127.0.0.1:8000/auth/login -d "username=voce@exemplo.com&password=minhasenha"
   ```
3. Use o `access_token` retornado no cabeçalho `Authorization: Bearer <token>`.
   No Swagger, clique em **Authorize** e informe e-mail e senha.

Sem token (ou com token inválido/expirado) os endpoints protegidos retornam **401**.

## Exemplo de requisição

```bash
curl -X POST http://127.0.0.1:8000/transacoes \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"descricao":"Mercado","valor":"250.50","tipo":"despesa","data":"2026-10-10"}'
```

Resposta (201):

```json
{"id":1,"descricao":"Mercado","valor":"250.50","tipo":"despesa","data":"2026-10-10",
 "categoria_id":null,"categoria":null,"criado_em":"2026-10-25T21:40:00.123456"}
```

## Testes e evidências

```bash
pytest -v                  # testes automatizados (usa banco SQLite separado)
bash exemplos_curl.sh      # roteiro completo com cURL (API precisa estar rodando)
```

## Estrutura do projeto

```
financas-api/
├── app/
│   ├── main.py            # criação do app, CORS, registro das rotas
│   ├── config.py          # configurações (variáveis de ambiente)
│   ├── database.py        # engine e sessão do SQLAlchemy
│   ├── models.py          # modelos ORM (Usuario, Categoria, Transacao)
│   ├── schemas.py         # schemas Pydantic (validação de entrada/saída)
│   ├── security.py        # hash de senha e JWT
│   └── routers/           # auth.py, categorias.py, transacoes.py
├── tests/                 # testes automatizados
├── schema.sql             # script de criação das tabelas
├── exemplos_curl.sh       # roteiro de evidências
├── .env.example
└── requirements.txt
```
