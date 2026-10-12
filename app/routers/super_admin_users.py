from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.student import Student
from app.models.user import AuthCredential, User
from app.schemas.registration import StudentRegistrationSummary


router = APIRouter(
    prefix="/api/v1/super-admin",
    tags=["Super Administrator - Users"],
)


def require_super_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    if current_user.get("designation") != "Super Administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Administrator access required.",
        )

    return current_user


@router.get("/registrations/pending")
def get_pending_registrations(
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    students = (
        db.query(Student)
        .filter(Student.approval_status == "PENDING")
        .order_by(Student.student_id.asc())
        .all()
    )

    return [
        StudentRegistrationSummary.model_validate(student)
        for student in students
    ]


@router.patch("/registrations/{student_id}/approve")
def approve_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    student = (
        db.query(Student)
        .filter(Student.student_id == student_id)
        .with_for_update()
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student registration not found.",
        )

    if student.approval_status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only pending registrations can be approved. "
                f"Current status: {student.approval_status}."
            ),
        )

    credential = (
        db.query(AuthCredential)
        .filter(
            AuthCredential.user_id == student_id,
            AuthCredential.designation == "Student",
        )
        .first()
    )

    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student authentication credentials were not found.",
        )

    student.approval_status = "APPROVED"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "student_id": student_id,
        "approval_status": "APPROVED",
        "message": "Student registration approved.",
    }


@router.patch("/registrations/{student_id}/reject")
def reject_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    student = (
        db.query(Student)
        .filter(Student.student_id == student_id)
        .with_for_update()
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student registration not found.",
        )

    if student.approval_status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only pending registrations can be rejected. "
                f"Current status: {student.approval_status}."
            ),
        )

    student.approval_status = "REJECTED"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "student_id": student_id,
        "approval_status": "REJECTED",
        "message": "Student registration rejected.",
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    users = (
        db.query(User, AuthCredential.is_active)
        .outerjoin(
            AuthCredential,
            (AuthCredential.user_id == User.user_id)
            & (AuthCredential.designation == User.designation),
        )
        .order_by(User.user_id.asc(), User.designation.asc())
        .all()
    )

    return [
        {
            "user_id": user.user_id,
            "designation": user.designation,
            "is_active": is_active,
        }
        for user, is_active in users
    ]


@router.delete("/users/{user_id}/{designation}")
def deactivate_user(
    user_id: int,
    designation: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_super_admin),
):
    if designation == "Super Administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Administrator accounts cannot be deactivated here.",
        )

    credential = (
        db.query(AuthCredential)
        .filter(
            AuthCredential.user_id == user_id,
            AuthCredential.designation == designation,
        )
        .with_for_update()
        .first()
    )

    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User credentials not found.",
        )

    if not credential.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This account is already deactivated.",
        )

    credential.is_active = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "user_id": user_id,
        "designation": designation,
        "is_active": False,
        "message": "User account deactivated.",
    }