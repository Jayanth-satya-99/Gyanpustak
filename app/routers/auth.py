from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_current_user,
    verify_password,
)
from app.database.connection import get_db
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

    valid = verify_password(
        credentials.password,
        auth.password_hash,
    )

    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
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