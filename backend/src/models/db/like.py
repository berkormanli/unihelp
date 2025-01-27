import datetime
import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.sql import functions as sqlalchemy_functions
from src.repository.table import Base

class Like(Base):
    __tablename__ = "likes"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    account_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"))
    post_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(sqlalchemy.ForeignKey("posts.id", ondelete="CASCADE"))
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), 
        nullable=False, 
        server_default=sqlalchemy_functions.now()
    )

    # Relationships
    account = relationship("Account", backref="likes")
    post = relationship("Post", backref="likes")