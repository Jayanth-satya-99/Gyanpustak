from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_current_user,
    verify_password,
)
from app.database.connection import get_db
from app.models.student import Student
from app.models.user import AuthCredential
from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    TokenResponse,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    auth = (
        db.query(AuthCredential)
        .filter(
            AuthCredential.user_id == credentials.user_id,
            AuthCredential.designation == credentials.designation,
        )
        .first()
    )

    if auth is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    if not auth.is_active:
        raise HTTPException(
            status_code=403,
            detail="This account has been deactivated.",
        )

    if not verify_password(
        credentials.password,
        auth.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    # Student accounts require explicit approval.
    if auth.designation == "Student":
        student = (
            db.query(Student)
            .filter(Student.student_id == auth.user_id)
            .first()
        )

        if student is None:
            raise HTTPException(
                status_code=403,
                detail="Student registration was not found.",
            )

        if student.approval_status != "APPROVED":
            if student.approval_status == "REJECTED":
                detail = "Your registration has been rejected."
            else:
                detail = (
                    "Your registration is pending "
                    "Super Administrator approval."
                )

            raise HTTPException(
                status_code=403,
                detail=detail,
            )

    token = create_access_token(
        user_id=auth.user_id,
        designation=auth.designation,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def get_me(
    current_user: dict = Depends(get_current_user),
):
    return current_user