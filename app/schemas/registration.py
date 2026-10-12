from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentRegistrationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    phone_number: str | None = Field(default=None,min_length=7,max_length=20)
    address: str | None = Field(default=None, max_length=100)
    dob: date | None = None
    university_id: int | None = Field(default=None, gt=0)
    major_field: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=100)
    current_yearofstudy: int | None = Field(default=None, ge=1)


class StudentRegistrationResponse(BaseModel):
    student_id: int
    name: str
    email: str
    approval_status: str
    message: str


class StudentRegistrationSummary(BaseModel):
    student_id: int
    name: str | None = None
    email: str | None = None
    approval_status: str

    model_config = ConfigDict(from_attributes=True)