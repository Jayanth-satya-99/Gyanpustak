from datetime import date

from sqlalchemy import Column, Date, ForeignKeyConstraint, Integer, String
from app.database.base import Base


class Ticket(Base):
    __tablename__ = "TICKET"

    ticket_id = Column("TICKET_ID", Integer, primary_key=True)
    type = Column("TYPE", String(100))
    date_of_creation = Column("DATE_OF_CREATION", Date)
    user_id = Column("USER_ID", Integer, nullable=True)
    creater = Column("CREATER", String(100))
    title = Column("TITLE", String(100))
    problem_description = Column("PROBLEM_DESCRIPTION", String(300))
    solution_description = Column("SOLUTION_DESCRIPTION", String(300))
    completion_date = Column("COMPLETION_DATE", Date)
    ticket_status = Column("TICKET_STATUS", String(100))

    __table_args__ = (
        ForeignKeyConstraint(
            ["USER_ID", "CREATER"],
            ["USER.USER_ID", "USER.DESIGNATION"],
            name="TICKET_ibfk_1",
        ),
    )