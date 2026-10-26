from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import TipoTransacao


# ---------- Autenticação ----------
class UsuarioCreate(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=6, max_length=72)


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Categorias ----------
class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=80)


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str


# ---------- Transações ----------
class TransacaoCreate(BaseModel):
    descricao: str = Field(min_length=1, max_length=200)
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    tipo: TipoTransacao
    data: date
    categoria_id: int | None = None


class TransacaoUpdate(BaseModel):
    """PATCH: todos os campos opcionais (atualização parcial)."""

    descricao: str | None = Field(default=None, min_length=1, max_length=200)
    valor: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    tipo: TipoTransacao | None = None
    data: date | None = None
    categoria_id: int | None = None


class TransacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    descricao: str
    valor: Decimal
    tipo: TipoTransacao
    data: date
    categoria_id: int | None
    categoria: CategoriaOut | None = None
    criado_em: datetime


class Resumo(BaseModel):
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal
