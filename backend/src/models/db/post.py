import datetime

import sqlalchemy
from sqlalchemy import (
    Table,
    Column,
    Integer,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import (
    Mapped as SQLAlchemyMapped,
    mapped_column as sqlalchemy_mapped_column,
    relationship,
)
from typing import TYPE_CHECKING

from src.repository.table import Base
from src.models.db.tag import post_tags

if TYPE_CHECKING:
    from src.models.db.account import Account
    from src.models.db.photo import Photo
    from src.models.db.post_stats import PostStats
    from src.models.db.poll import Poll

class Post(Base):
    __tablename__ = "posts"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    content: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(String)
    account_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(ForeignKey("account.id"))
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    # Relationships (only defined on one side)
    account: SQLAlchemyMapped["Account"] = relationship(back_populates="posts")
    stats: SQLAlchemyMapped["PostStats"] = relationship(back_populates="post", uselist=False)
    photos: SQLAlchemyMapped[list["Photo"]] = relationship(back_populates="post")
    poll: SQLAlchemyMapped["Poll"] = relationship(back_populates="post", uselist=False)
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")
    comments: SQLAlchemyMapped[list["Comment"]] = relationship(back_populates="post")