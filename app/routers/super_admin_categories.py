from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.category import Category, Subcategory
from app.schemas.admin_category import (
    CategoryCreate,
    CategoryResponse,
    MessageResponse,
    SubcategoryCreate,
    SubcategoryResponse,
)


router = APIRouter(
    prefix="/api/v1/super-admin/categories",
    tags=["Super Administrator - Categories"],
)


def require_super_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    if current_user.get("designation") != "Super Administrator":
        raise HTTPException(
            status_code=403,
            detail="Only Super Administrators can manage categories",
        )

    return current_user


def book_category_exists(
    db: Session,
    category_name: str,
    subcategory_name: str | None = None,
) -> bool:
    query = """
        SELECT 1
        FROM BOOK_CATEGORY
        WHERE CATEGORY = :category_name
    """

    params = {"category_name": category_name}

    if subcategory_name is not None:
        query += " AND SUBCATEGORY = :subcategory_name"
        params["subcategory_name"] = subcategory_name

    query += " LIMIT 1"

    return (
        db.execute(text(query), params).first()
        is not None
    )


# --------------------------------------------------
# LIST CATEGORIES
# GET /api/v1/super-admin/categories
# --------------------------------------------------

@router.get("", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    return (
        db.query(Category)
        .order_by(Category.category_name)
        .all()
    )


# --------------------------------------------------
# CREATE CATEGORY
# POST /api/v1/super-admin/categories
# --------------------------------------------------

@router.post(
    "",
    response_model=CategoryResponse,
    status_code=201,
)
def create_category(
    request: CategoryCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    existing = db.get(Category, request.category_name)

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Category already exists",
        )

    category = Category(
        category_name=request.category_name,
    )

    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Category already exists",
        )


# --------------------------------------------------
# LIST SUBCATEGORIES
# GET /api/v1/super-admin/categories/{category_name}/subcategories
# --------------------------------------------------

@router.get(
    "/{category_name}/subcategories",
    response_model=list[SubcategoryResponse],
)
def list_subcategories(
    category_name: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    category = db.get(Category, category_name)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    return (
        db.query(Subcategory)
        .filter(
            Subcategory.category_name == category_name,
        )
        .order_by(Subcategory.subcategory_name)
        .all()
    )


# --------------------------------------------------
# CREATE SUBCATEGORY
# POST /api/v1/super-admin/categories/{category_name}/subcategories
# --------------------------------------------------

@router.post(
    "/{category_name}/subcategories",
    response_model=SubcategoryResponse,
    status_code=201,
)
def create_subcategory(
    category_name: str,
    request: SubcategoryCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    category = db.get(Category, category_name)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    existing = db.get(
        Subcategory,
        (category_name, request.subcategory_name),
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Subcategory already exists in this category",
        )

    subcategory = Subcategory(
        category_name=category_name,
        subcategory_name=request.subcategory_name,
    )

    try:
        db.add(subcategory)
        db.commit()
        db.refresh(subcategory)
        return subcategory

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Subcategory already exists or the category is invalid",
        )


# --------------------------------------------------
# DELETE SUBCATEGORY
# DELETE /api/v1/super-admin/categories/{category_name}/subcategories/{subcategory_name}
# --------------------------------------------------

@router.delete(
    "/{category_name}/subcategories/{subcategory_name}",
    response_model=MessageResponse,
)
def delete_subcategory(
    category_name: str,
    subcategory_name: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    subcategory = db.get(
        Subcategory,
        (category_name, subcategory_name),
    )

    if subcategory is None:
        raise HTTPException(
            status_code=404,
            detail="Subcategory not found",
        )

    if book_category_exists(
        db,
        category_name,
        subcategory_name,
    ):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a subcategory that is assigned to books",
        )

    db.delete(subcategory)
    db.commit()

    return {
        "message": "Subcategory deleted successfully",
    }


# --------------------------------------------------
# DELETE CATEGORY
# DELETE /api/v1/super-admin/categories/{category_name}
# --------------------------------------------------

@router.delete(
    "/{category_name}",
    response_model=MessageResponse,
)
def delete_category(
    category_name: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    category = db.get(Category, category_name)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    if book_category_exists(db, category_name):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a category that is assigned to books",
        )

    subcategory_exists = (
        db.query(Subcategory)
        .filter(
            Subcategory.category_name == category_name,
        )
        .first()
        is not None
    )

    if subcategory_exists:
        raise HTTPException(
            status_code=409,
            detail="Delete the category's subcategories first",
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully",
    }