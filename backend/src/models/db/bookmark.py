import datetime
import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.sql import functions as sqlalchemy_functions
from src.repository.table import Base

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    account_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"))
    post_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(sqlalchemy.ForeignKey("posts.id", ondelete="CASCADE"))
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), 
        nullable=False, 
        server_default=sqlalchemy_functions.now()
    )

    # Relationships
    account = relationship("Account", backref="bookmarks")
    post = relationship("Post", backref="bookmarks")