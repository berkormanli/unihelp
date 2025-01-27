import datetime

import sqlalchemy
from sqlalchemy import (
    ForeignKey,
    String,
)
from sqlalchemy.orm import (
    Mapped as SQLAlchemyMapped,
    mapped_column as sqlalchemy_mapped_column,
    relationship,
)
from src.repository.table import Base

class Photo(Base):
    __tablename__ = "photos"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    url: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(String)
    post_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(ForeignKey("posts.id"))

    # Relationship (only defined on one side)
    post: SQLAlchemyMapped["Post"] = relationship(back_populates="photos")