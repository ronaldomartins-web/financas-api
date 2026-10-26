from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Categoria, Usuario
from ..schemas import CategoriaCreate, CategoriaOut
from ..security import usuario_atual

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get("", response_model=list[CategoriaOut])
def listar(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_atual)):
    consulta = select(Categoria).where(Categoria.usuario_id == usuario.id).order_by(Categoria.nome)
    return db.scalars(consulta).all()


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: CategoriaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    existe = db.scalar(
        select(Categoria).where(Categoria.usuario_id == usuario.id, Categoria.nome == dados.nome)
    )
    if existe:
        raise HTTPException(status.HTTP_409_CONFLICT, "Categoria já existe.")
    categoria = Categoria(nome=dados.nome, usuario_id=usuario.id)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    categoria = db.get(Categoria, categoria_id)
    if categoria is None or categoria.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada.")
    if categoria.transacoes:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Categoria possui transações vinculadas e não pode ser excluída."
        )
    db.delete(categoria)
    db.commit()
