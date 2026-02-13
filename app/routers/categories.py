from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppException
from app.models import Category
from app.schemas import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    exists = db.query(Category).filter(Category.name == payload.name).first()
    if exists:
        raise AppException(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Category name already exists",
            details=[{"field": "name", "message": "must be unique"}],
        )

    category = Category(name=payload.name, description=payload.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("", response_model=list[CategoryOut])
def list_categories(include_inactive: bool = False, db: Session = Depends(get_db)) -> list[Category]:
    query = db.query(Category)
    if not include_inactive:
        query = query.filter(Category.is_active.is_(True))
    return query.order_by(Category.id.asc()).all()


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise AppException(status_code=404, code="NOT_FOUND", message="Category not found")
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise AppException(status_code=404, code="NOT_FOUND", message="Category not found")

    if payload.name and payload.name != category.name:
        exists = db.query(Category).filter(Category.name == payload.name).first()
        if exists:
            raise AppException(
                status_code=400,
                code="VALIDATION_ERROR",
                message="Category name already exists",
                details=[{"field": "name", "message": "must be unique"}],
            )

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> Response:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise AppException(status_code=404, code="NOT_FOUND", message="Category not found")

    category.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
