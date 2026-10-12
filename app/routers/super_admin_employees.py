from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user, hash_password
from app.database.connection import get_db
from app.models.employee import Employee
from app.models.user import User, AuthCredential
from app.schemas.employee import EmployeeCreate, EmployeeResponse


router = APIRouter(
    prefix="/api/v1/super-admin/employees",
    tags=["Super Administrator - Employees"],
)


def require_super_admin(
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("designation") != "Super Administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Administrator access required.",
        )

    return current_user


def generate_employee_id(db: Session) -> int:
    """
    Generate an employee ID using the existing employee table.

    The employee sequence is locked to prevent concurrent ID allocation.
    """

    sequence = db.execute(
        text(
            """
            SELECT NEXT_ID
            FROM EMPLOYEE_ID_SEQUENCE
            WHERE SEQUENCE_NAME = 'EMPLOYEE'
            FOR UPDATE
            """
        )
    ).scalar_one_or_none()

    if sequence is None:
        raise RuntimeError(
            "EMPLOYEE_ID_SEQUENCE is missing or uninitialized."
        )

    db.execute(
        text(
            """
            UPDATE EMPLOYEE_ID_SEQUENCE
            SET NEXT_ID = NEXT_ID + 1
            WHERE SEQUENCE_NAME = 'EMPLOYEE'
            """
        )
    )

    return sequence


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    request: EmployeeCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    email = str(request.email).strip().lower()

    existing_employee = (
        db.query(Employee)
        .filter(func.lower(Employee.email) == email)
        .first()
    )

    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An employee with this email already exists.",
        )

    try:
        employee_id = generate_employee_id(db)

        employee = Employee(
            employee_id=employee_id,
            first_name=request.first_name.strip(),
            last_name=request.last_name.strip(),
            gender=request.gender,
            email=email,
            address=request.address,
            telephone_number=request.telephone_number,
            designation=request.designation,
        )

        user = User(
            user_id=employee_id,
            designation=request.designation,
            password=None,
        )

        credential = AuthCredential(
            user_id=employee_id,
            designation=request.designation,
            password_hash=hash_password(request.password),
            is_active=True,
        )

        db.add(employee)
        db.add(user)

        # Ensure the referenced USER row exists before inserting credentials.
        db.flush()

        db.add(credential)
        db.commit()
        db.refresh(employee)

        return employee

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee creation conflicts with an existing database record.",
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.get(
    "",
    response_model=list[EmployeeResponse],
)
def list_employees(
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    return (
        db.query(Employee)
        .order_by(Employee.employee_id.asc())
        .all()
    )


@router.delete("/{employee_id}")
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    employee = (
        db.query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        )

    if employee.designation == "Super Administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Administrator accounts cannot be deactivated here.",
        )

    credential = (
        db.query(AuthCredential)
        .filter(
            AuthCredential.user_id == employee_id,
            AuthCredential.designation == employee.designation,
        )
        .with_for_update()
        .first()
    )

    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee authentication credentials not found.",
        )

    if not credential.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee is already deactivated.",
        )

    credential.is_active = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "employee_id": employee_id,
        "designation": employee.designation,
        "is_active": False,
        "message": "Employee login deactivated.",
    }