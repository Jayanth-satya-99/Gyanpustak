from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TicketType = Literal["PRODUCT", "CART", "ORDER", "PROFILE", "OTHER"]

TicketStatus = Literal[
    "assigned",
    "in_progress",
    "resolved",
    "closed",
]


class TicketCreate(BaseModel):
    type: TicketType
    title: str = Field(min_length=1, max_length=100)
    problem_description: str = Field(min_length=1, max_length=300)


class TicketStatusUpdate(BaseModel):
    ticket_status: Literal["assigned", "in_progress", "closed"]


class TicketResolve(BaseModel):
    solution_description: str = Field(min_length=1, max_length=300)


class TicketAssignment(BaseModel):
    assigned_to_id: int = Field(gt=0)


class TicketResponse(BaseModel):
    ticket_id: int
    type: str | None = None
    date_of_creation: date | None = None
    user_id: int | None = None
    creater: str | None = None
    title: str | None = None
    problem_description: str | None = None
    solution_description: str | None = None
    completion_date: date | None = None
    ticket_status: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TicketAssignmentResponse(BaseModel):
    ticket_id: int
    assigned_by: str | None = None
    assigned_to: str | None = None
    assigned_by_id: int | None = None
    assigned_to_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class TicketStatisticsResponse(BaseModel):
    total_tickets: int
    status_counts: dict[str, int]


class EmployeeSummary(BaseModel):
    employee_id: int
    first_name: str | None = None
    last_name: str | None = None
    designation: str

    model_config = ConfigDict(from_attributes=True)