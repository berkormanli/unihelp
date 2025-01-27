import datetime
from typing import List, Optional

from src.models.schemas.base import BaseSchemaModel
from src.models.schemas.account import AccountDetailBase
from src.models.schemas.tag import TagCreate

class PostStatsBase(BaseSchemaModel):
    comments: int = 0
    likes: int = 0
    bookmarks: int = 0

class PostBase(BaseSchemaModel):
    content: str
    account: AccountDetailBase
    stats: PostStatsBase

class PostStats(BaseSchemaModel):
    comments: int
    like: int
    bookmark: bool

class PostInCreate(BaseSchemaModel):
    content: str
    photos: Optional[List[str]] = []
    tags: Optional[List[str]] = []


class AnswerBasePost(BaseSchemaModel):
    text: str

class AnswerInResponsePost(AnswerBasePost):
    id: int
    answer_index: int
    answer_count: int
    is_selected: bool = False

class PollInResponsePost(BaseSchemaModel):
    id: int
    post_id: int
    account_id: int
    answers: List[AnswerInResponsePost]
    expiration_date: datetime.datetime | None = None

class PostInResponse(BaseSchemaModel):
    id: int
    content: str
    account: AccountDetailBase
    stats: PostStatsBase
    photos: Optional[List[str]] = []
    tags: Optional[List[TagCreate]] = []
    poll: Optional[PollInResponsePost] = None
    created_at: datetime.datetime
    is_liked: bool = False
    is_bookmarked: bool = False
    likes_count: int = 0

class PhotoInDB(BaseSchemaModel):
    url: str
