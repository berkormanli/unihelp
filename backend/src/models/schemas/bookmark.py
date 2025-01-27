from datetime import datetime
from pydantic import BaseModel
from src.models.schemas.base import BaseSchemaModel

class BookmarkBase(BaseSchemaModel):
    post_id: int

class BookmarkCreate(BookmarkBase):
    pass

class BookmarkInDB(BookmarkBase):
    id: int
    account_id: int
    created_at: datetime

    class Config:
        orm_mode = True