from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Categoria, TipoTransacao, Transacao, Usuario
from ..schemas import Resumo, TransacaoCreate, TransacaoOut, TransacaoUpdate
from ..security import usuario_atual

# Todas as rotas de transações são protegidas: cada usuário vê apenas os seus dados.
router = APIRouter(prefix="/transacoes", tags=["Transações"])


def _validar_categoria(db: Session, categoria_id: int | None, usuario: Usuario) -> None:
    if categoria_id is None:
        return
    categoria = db.get(Categoria, categoria_id)
    if categoria is None or categoria.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Categoria {categoria_id} não existe.")


def _buscar_ou_404(db: Session, transacao_id: int, usuario: Usuario) -> Transacao:
    transacao = db.get(Transacao, transacao_id)
    # 404 (e não 403) também para transação de outro usuário, para não revelar sua existência.
    if transacao is None or transacao.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transação não encontrada.")
    return transacao


# GET (listagem com filtros e paginação)
@router.get("", response_model=list[TransacaoOut])
def listar(
    tipo: TipoTransacao | None = None,
    categoria_id: int | None = None,
    data_inicio: date | None = Query(None, description="Data inicial (AAAA-MM-DD)"),
    data_fim: date | None = Query(None, description="Data final (AAAA-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    consulta = (
        select(Transacao)
        .options(joinedload(Transacao.categoria))
        .where(Transacao.usuario_id == usuario.id)
        .order_by(Transacao.data.desc(), Transacao.id.desc())
    )
    if tipo:
        consulta = consulta.where(Transacao.tipo == tipo)
    if categoria_id is not None:
        consulta = consulta.where(Transacao.categoria_id == categoria_id)
    if data_inicio:
        consulta = consulta.where(Transacao.data >= data_inicio)
    if data_fim:
        consulta = consulta.where(Transacao.data <= data_fim)
    return db.scalars(consulta.offset(skip).limit(limit)).all()


# GET (resumo/saldo) — declarado ANTES de /{id} para não ser capturado como id
@router.get("/resumo", response_model=Resumo)
def resumo(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    def total(tipo: TipoTransacao) -> Decimal:
        consulta = select(func.coalesce(func.sum(Transacao.valor), 0)).where(
            Transacao.usuario_id == usuario.id, Transacao.tipo == tipo
        )
        if data_inicio:
            consulta = consulta.where(Transacao.data >= data_inicio)
        if data_fim:
            consulta = consulta.where(Transacao.data <= data_fim)
        return Decimal(str(db.scalar(consulta)))

    receitas, despesas = total(TipoTransacao.receita), total(TipoTransacao.despesa)
    return Resumo(total_receitas=receitas, total_despesas=despesas, saldo=receitas - despesas)


# GET (individual)
@router.get("/{transacao_id}", response_model=TransacaoOut)
def consultar(
    transacao_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_atual)
):
    return _buscar_ou_404(db, transacao_id, usuario)


# POST
@router.post("", response_model=TransacaoOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: TransacaoCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_atual)
):
    _validar_categoria(db, dados.categoria_id, usuario)
    transacao = Transacao(**dados.model_dump(), usuario_id=usuario.id)
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    return transacao


# PATCH (atualização parcial: o cliente envia só o que mudou)
@router.patch("/{transacao_id}", response_model=TransacaoOut)
def atualizar(
    transacao_id: int,
    dados: TransacaoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    transacao = _buscar_ou_404(db, transacao_id, usuario)
    campos = dados.model_dump(exclude_unset=True)
    # Campos obrigatórios no banco não aceitam null explícito
    for obrigatorio in ("descricao", "valor", "tipo", "data"):
        if obrigatorio in campos and campos[obrigatorio] is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"O campo '{obrigatorio}' não pode ser nulo.")
    if "categoria_id" in campos:
        _validar_categoria(db, campos["categoria_id"], usuario)
    for campo, valor in campos.items():
        setattr(transacao, campo, valor)
    db.commit()
    db.refresh(transacao)
    return transacao


# DELETE
@router.delete("/{transacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    transacao_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_atual)
):
    transacao = _buscar_ou_404(db, transacao_id, usuario)
    db.delete(transacao)
    db.commit()
