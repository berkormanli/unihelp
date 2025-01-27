from typing import List
from src.models.schemas.base import BaseSchemaModel
from src.models.schemas.post import PostInResponse
from src.models.schemas.account import AccountDetailBase
from src.models.schemas.tag import TagResponse

class SearchResponse(BaseSchemaModel):
    users: List[AccountDetailBase] = []
    posts: List[PostInResponse] = []
    tags: List[TagResponse] = []