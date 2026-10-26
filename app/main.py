from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, categorias, transacoes


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Cria as tabelas caso ainda não existam (equivalente a uma migration inicial).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API de Finanças Pessoais",
    description="API RESTful para controle de receitas, despesas e categorias, "
    "com autenticação JWT. Projeto da disciplina Arquitetura e Desenvolvimento de APIs - UNINTER.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS restritivo: apenas as origens listadas em CORS_ORIGINS, métodos e cabeçalhos necessários.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
)

app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(transacoes.router)


@app.get("/", tags=["Status"])
def raiz():
    return {"api": "API de Finanças Pessoais", "versao": app.version, "docs": "/docs"}
