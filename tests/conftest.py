import os

# Banco isolado para os testes (definido ANTES de importar a aplicação)
os.environ["DATABASE_URL"] = "sqlite:///./test_financas.db"
os.environ["SECRET_KEY"] = "chave-de-teste"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def _login(client, email="ana@teste.com", senha="senha123"):
    client.post("/auth/register", json={"email": email, "senha": senha})
    r = client.post("/auth/login", data={"username": email, "password": senha})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return _login(client)


@pytest.fixture()
def auth_outro(client):
    return _login(client, "bia@teste.com")
