from datetime import datetime
from pydantic import BaseModel
from src.models.schemas.base import BaseSchemaModel

class LikeBase(BaseSchemaModel):
    post_id: int

class LikeCreate(LikeBase):
    pass

class LikeInDB(LikeBase):
    id: int
    account_id: int
    created_at: datetime

    class Config:
        orm_mode = True