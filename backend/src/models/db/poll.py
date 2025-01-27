import datetime

import sqlalchemy
from sqlalchemy import (
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import (
    Mapped as SQLAlchemyMapped,
    mapped_column as sqlalchemy_mapped_column,
    relationship,
)
from src.repository.table import Base  # Assuming you have a common Base

class Poll(Base):
    __tablename__ = "polls"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    # Remove voted and votes fields
    post_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(ForeignKey("posts.id"))
    account_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(ForeignKey("account.id"))
    expiration_date: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(sqlalchemy.DateTime)

    # Relationships (only defined on one side)
    post: SQLAlchemyMapped["Post"] = relationship(back_populates="poll")
    account: SQLAlchemyMapped["Account"] = relationship(backref="polls")
    answers: SQLAlchemyMapped[list["Answer"]] = relationship(back_populates="poll")