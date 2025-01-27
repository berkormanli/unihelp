from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)

class CommentCreate(CommentBase):
    post_id: int
    parent_id: Optional[int]

class CommentInDB(CommentBase):
    id: int
    post_id: int
    author_id: int
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CommentResponse(CommentInDB):
    author_username: str
    author_avatar: Optional[str]