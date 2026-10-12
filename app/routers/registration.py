from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.connection import get_db
from app.models.student import Student
from app.models.user import AuthCredential, User
from app.schemas.registration import (
    StudentRegistrationRequest,
    StudentRegistrationResponse,
)


router = APIRouter(
    prefix="/api/v1/registration",
    tags=["Student Registration"],
)


def generate_student_id(db: Session) -> int:
    sequence = db.execute(
        text(
            """
            SELECT NEXT_ID
            FROM STUDENT_ID_SEQUENCE
            WHERE SEQUENCE_NAME = 'STUDENT'
            FOR UPDATE
            """
        )
    ).scalar_one_or_none()

    if sequence is None:
        raise RuntimeError(
            "Student ID sequence is missing. "
            "Initialize STUDENT_ID_SEQUENCE first."
        )

    db.execute(
        text(
            """
            UPDATE STUDENT_ID_SEQUENCE
            SET NEXT_ID = NEXT_ID + 1
            WHERE SEQUENCE_NAME = 'STUDENT'
            """
        )
    )

    return sequence


@router.post(
    "/students",
    response_model=StudentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_student(
    request: StudentRegistrationRequest,
    db: Session = Depends(get_db),
):
    email = str(request.email).strip().lower()

    existing_student = (
        db.query(Student)
        .filter(Student.email == email)
        .first()
    )

    if existing_student:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    try:
        # Start a transaction. The sequence row is locked until commit.
        student_id = generate_student_id(db)

        student = Student(
            student_id=student_id,
            name=request.name.strip(),
            email=email,
            phone_number=request.phone_number,
            address=request.address,
            dob=request.dob,
            university_id=request.university_id,
            major_field=request.major_field,
            status=request.status,
            current_yearofstudy=request.current_yearofstudy,
            approval_status="PENDING",
        )

        user = User(
            user_id=student_id,
            designation="Student",
            password=None,
        )

        credentials = AuthCredential(
            user_id=student_id,
            designation="Student",
            password_hash=hash_password(request.password),
            is_active=True,
        )

        db.add(student)
        db.add(user)
        db.flush()
        db.add(credentials)

        db.commit()
        db.refresh(student)

        return StudentRegistrationResponse(
            student_id=student.student_id,
            name=student.name or "",
            email=student.email or "",
            approval_status=student.approval_status,
            message=(
                "Registration submitted. "
                "Wait for Super Administrator approval before logging in."
            ),
        )
    # except IntegrityError as exc:
    #     db.rollback()

    #     print("REGISTRATION INTEGRITY ERROR:", repr(exc.orig))

    #     raise HTTPException(
    #         status_code=409,
    #         detail=str(exc.orig),
    #     ) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Registration conflicts with an existing record. "
                "Check the email, university ID, and database constraints."
            ),
        ) from exc

    except Exception:
        db.rollback()
        raise