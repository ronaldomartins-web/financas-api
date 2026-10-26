import enum
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class TipoTransacao(str, enum.Enum):
    receita = "receita"
    despesa = "despesa"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(default=_agora)

    categorias: Mapped[list["Categoria"]] = relationship(back_populates="usuario")
    transacoes: Mapped[list["Transacao"]] = relationship(back_populates="usuario")


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)

    usuario: Mapped[Usuario] = relationship(back_populates="categorias")
    transacoes: Mapped[list["Transacao"]] = relationship(back_populates="categoria")


class Transacao(Base):
    """Recurso principal: uma receita ou despesa do usuário."""

    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(200))
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tipo: Mapped[TipoTransacao] = mapped_column(Enum(TipoTransacao), index=True)
    data: Mapped[date] = mapped_column(index=True)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"), nullable=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    criado_em: Mapped[datetime] = mapped_column(default=_agora)

    usuario: Mapped[Usuario] = relationship(back_populates="transacoes")
    categoria: Mapped[Categoria | None] = relationship(back_populates="transacoes")
