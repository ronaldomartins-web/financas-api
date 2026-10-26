NOVA = {"descricao": "Salário", "valor": "3500.00", "tipo": "receita", "data": "2026-10-05"}


# ---------- Autenticação ----------
def test_registro_e_login(client):
    r = client.post("/auth/register", json={"email": "x@y.com", "senha": "abc123"})
    assert r.status_code == 201 and "senha" not in r.text
    r = client.post("/auth/login", data={"username": "x@y.com", "password": "abc123"})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"


def test_registro_duplicado_409(client):
    dados = {"email": "x@y.com", "senha": "abc123"}
    client.post("/auth/register", json=dados)
    assert client.post("/auth/register", json=dados).status_code == 409


def test_registro_invalido_422(client):
    assert client.post("/auth/register", json={"email": "invalido", "senha": "123"}).status_code == 422


def test_login_senha_errada_401(client):
    client.post("/auth/register", json={"email": "x@y.com", "senha": "abc123"})
    r = client.post("/auth/login", data={"username": "x@y.com", "password": "errada"})
    assert r.status_code == 401


def test_endpoint_protegido_sem_token_401(client):
    assert client.get("/transacoes").status_code == 401


def test_token_invalido_401(client):
    r = client.get("/transacoes", headers={"Authorization": "Bearer token.falso.aqui"})
    assert r.status_code == 401


# ---------- CRUD ----------
def test_post_cria_201(client, auth):
    r = client.post("/transacoes", json=NOVA, headers=auth)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["id"] == 1 and corpo["valor"] == "3500.00" and corpo["tipo"] == "receita"


def test_get_lista_200(client, auth):
    client.post("/transacoes", json=NOVA, headers=auth)
    r = client.get("/transacoes", headers=auth)
    assert r.status_code == 200 and len(r.json()) == 1


def test_get_individual_200_e_404(client, auth):
    client.post("/transacoes", json=NOVA, headers=auth)
    assert client.get("/transacoes/1", headers=auth).status_code == 200
    assert client.get("/transacoes/999", headers=auth).status_code == 404


def test_patch_atualiza_200(client, auth):
    client.post("/transacoes", json=NOVA, headers=auth)
    r = client.patch("/transacoes/1", json={"valor": "4000.00"}, headers=auth)
    assert r.status_code == 200
    assert r.json()["valor"] == "4000.00" and r.json()["descricao"] == "Salário"


def test_patch_inexistente_404(client, auth):
    assert client.patch("/transacoes/999", json={"valor": "1.00"}, headers=auth).status_code == 404


def test_patch_campo_obrigatorio_nulo_400(client, auth):
    client.post("/transacoes", json=NOVA, headers=auth)
    assert client.patch("/transacoes/1", json={"valor": None}, headers=auth).status_code == 400


def test_delete_204_e_depois_404(client, auth):
    client.post("/transacoes", json=NOVA, headers=auth)
    assert client.delete("/transacoes/1", headers=auth).status_code == 204
    assert client.delete("/transacoes/1", headers=auth).status_code == 404
    assert client.get("/transacoes/1", headers=auth).status_code == 404


# ---------- Validação ----------
def test_valor_negativo_422(client, auth):
    r = client.post("/transacoes", json={**NOVA, "valor": "-10"}, headers=auth)
    assert r.status_code == 422


def test_tipo_invalido_422(client, auth):
    r = client.post("/transacoes", json={**NOVA, "tipo": "transferencia"}, headers=auth)
    assert r.status_code == 422


def test_data_invalida_422(client, auth):
    assert client.post("/transacoes", json={**NOVA, "data": "31/12/2026"}, headers=auth).status_code == 422


def test_campo_obrigatorio_ausente_422(client, auth):
    assert client.post("/transacoes", json={"descricao": "x"}, headers=auth).status_code == 422


def test_categoria_inexistente_400(client, auth):
    r = client.post("/transacoes", json={**NOVA, "categoria_id": 99}, headers=auth)
    assert r.status_code == 400


# ---------- Categorias e relacionamento ----------
def test_categoria_crud_e_vinculo(client, auth):
    r = client.post("/categorias", json={"nome": "Alimentação"}, headers=auth)
    assert r.status_code == 201
    cid = r.json()["id"]
    assert client.post("/categorias", json={"nome": "Alimentação"}, headers=auth).status_code == 409
    t = client.post(
        "/transacoes",
        json={"descricao": "Mercado", "valor": "250.50", "tipo": "despesa", "data": "2026-10-10", "categoria_id": cid},
        headers=auth,
    )
    assert t.status_code == 201 and t.json()["categoria"]["nome"] == "Alimentação"
    assert client.delete(f"/categorias/{cid}", headers=auth).status_code == 409  # em uso
    client.delete(f"/transacoes/{t.json()['id']}", headers=auth)
    assert client.delete(f"/categorias/{cid}", headers=auth).status_code == 204


# ---------- Filtros e resumo ----------
def test_filtros_e_resumo(client, auth):
    client.post("/transacoes", json=NOVA, headers=auth)
    client.post(
        "/transacoes",
        json={"descricao": "Aluguel", "valor": "1200.00", "tipo": "despesa", "data": "2026-10-06"},
        headers=auth,
    )
    client.post(
        "/transacoes",
        json={"descricao": "Luz", "valor": "180.25", "tipo": "despesa", "data": "2026-09-20"},
        headers=auth,
    )
    assert len(client.get("/transacoes?tipo=despesa", headers=auth).json()) == 2
    assert len(client.get("/transacoes?data_inicio=2026-10-01&data_fim=2026-10-31", headers=auth).json()) == 2
    r = client.get("/transacoes/resumo", headers=auth).json()
    assert (r["total_receitas"], r["total_despesas"], r["saldo"]) == ("3500.00", "1380.25", "2119.75") or (
        float(r["total_receitas"]), float(r["total_despesas"]), float(r["saldo"])
    ) == (3500.0, 1380.25, 2119.75)


def test_paginacao_limite_invalido_422(client, auth):
    assert client.get("/transacoes?limit=1000", headers=auth).status_code == 422


# ---------- Isolamento entre usuários ----------
def test_usuario_nao_acessa_dados_de_outro(client, auth, auth_outro):
    client.post("/transacoes", json=NOVA, headers=auth)
    assert client.get("/transacoes/1", headers=auth_outro).status_code == 404
    assert client.patch("/transacoes/1", json={"valor": "1"}, headers=auth_outro).status_code == 404
    assert client.delete("/transacoes/1", headers=auth_outro).status_code == 404
    assert client.get("/transacoes", headers=auth_outro).json() == []


# ---------- CORS ----------
def test_cors_origem_permitida_e_bloqueada(client):
    ok = client.options(
        "/transacoes",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    ruim = client.options(
        "/transacoes",
        headers={"Origin": "http://site-malicioso.com", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in ruim.headers
