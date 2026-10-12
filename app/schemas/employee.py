from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal


EmployeeDesignation = Literal[
    "Customer Support",
    "Administrator",
]


class EmployeeCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    gender: str | None = Field(default=None, max_length=100)
    email: EmailStr
    address: str | None = Field(default=None, max_length=100)
    telephone_number: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )
    designation: EmployeeDesignation
    password: str = Field(min_length=8, max_length=128)


class EmployeeResponse(BaseModel):
    employee_id: int
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    email: str | None = None
    designation: str | None = None

    model_config = ConfigDict(from_attributes=True)