from sqlalchemy import Column, ForeignKey, Integer, String
from app.database.base import Base


class TicketFlow(Base):
    __tablename__ = "TICKET_FLOW"

    ticket_id = Column(
        "TICKET_ID",
        Integer,
        ForeignKey("TICKET.TICKET_ID"),
        primary_key=True,
    )

    assigned_by = Column("ASSIGNED_BY", String(100))
    assigned_to = Column("ASSIGNED_TO", String(100))

    assigned_by_id = Column(
        "ASSIGNED_BY_ID",
        Integer,
        ForeignKey("EMPLOYEE.EMPLOYEE_ID"),
    )

    assigned_to_id = Column(
        "ASSIGNED_TO_ID",
        Integer,
        ForeignKey("EMPLOYEE.EMPLOYEE_ID"),
    )