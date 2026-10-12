from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.services import rental_service


router = APIRouter(
    prefix="/api/v1/rentals",
    tags=["Rentals"],
)


def get_student_id(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> int:
    if current_user["designation"] != "Student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access rentals",
        )

    return current_user["user_id"]


@router.get("")
def list_student_rentals(
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return rental_service.list_rentals(db, student_id)


@router.get("/{rental_id}")
def get_student_rental(
    rental_id: int,
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return rental_service.get_rental(
        db,
        student_id,
        rental_id,
    )


@router.post("/{rental_id}/return")
def return_student_rental(
    rental_id: int,
    student_id: Annotated[int, Depends(get_student_id)],
    db: Annotated[Session, Depends(get_db)],
):
    return rental_service.return_rental(
        db,
        student_id,
        rental_id,
    )