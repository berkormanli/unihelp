import datetime

import sqlalchemy
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped as SQLAlchemyMapped,
    mapped_column as sqlalchemy_mapped_column,
    relationship,
)
from src.repository.table import Base

class Answer(Base):
    __tablename__ = "answers"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    text: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(String)
    poll_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(ForeignKey("polls.id"))
    answer_index: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(Integer)

    # Relationship (only defined on one side)
    poll: SQLAlchemyMapped["Poll"] = relationship(back_populates="answers")