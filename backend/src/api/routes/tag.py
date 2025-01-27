import fastapi
from fastapi import Depends
from typing import List

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import get_current_user
from src.models.schemas.tag import TagResponse, TagCreate
from src.repository.crud.tag import TagCRUDRepository
from src.models.db.account import Account

router = fastapi.APIRouter(prefix="/tags", tags=["tags"])

@router.get("", response_model=List[TagResponse])
async def get_all_tags(
    tag_repo: TagCRUDRepository = Depends(get_repository(TagCRUDRepository))
):
    tags = await tag_repo.get_all_tags()
    return [TagResponse.from_orm(tag) for tag in tags]

@router.post("/{post_id}/add", response_model=List[TagResponse])
async def add_tags_to_post(
    post_id: int,
    tags: List[str],
    current_user: Account = Depends(get_current_user),
    tag_repo: TagCRUDRepository = Depends(get_repository(TagCRUDRepository))
):
    added_tags = await tag_repo.add_tags_to_post(post_id, tags)
    return [TagResponse.from_orm(tag) for tag in added_tags]