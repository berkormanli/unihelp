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
from src.repository.table import Base

class PostStats(Base):
    __tablename__ = "post_stats"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    comments: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(Integer, default=0)
    likes: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(Integer, default=0)
    bookmarks: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(Integer, default=0)
    post_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(ForeignKey("posts.id"))

    # Relationship (only defined on one side)
    post: SQLAlchemyMapped["Post"] = relationship(back_populates="stats")