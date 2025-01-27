import fastapi
from fastapi import Depends, Query, HTTPException, status
from typing import List

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import get_current_user
from src.models.schemas.comment import CommentCreate, CommentResponse
from src.repository.crud.comment import CommentCRUDRepository
from src.models.db.account import Account
from src.utilities.exceptions.database import EntityDoesNotExist

router = fastapi.APIRouter(prefix="/comments", tags=["comments"])

@router.post(
    path="",
    name="comments:create-comment",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    comment: CommentCreate,
    current_user: Account = Depends(get_current_user),
    comment_repo: CommentCRUDRepository = Depends(get_repository(CommentCRUDRepository))
):
    db_comment = await comment_repo.create_comment(comment, current_user.id)
    return CommentResponse(
        id=db_comment.id,
        post_id=db_comment.post_id,
        author_id=db_comment.author_id,
        parent_id=db_comment.parent_id,
        created_at=db_comment.created_at,
        updated_at=db_comment.updated_at,
        content=db_comment.content,
        author_username=current_user.username,
        author_avatar=current_user.avatar
    )

@router.get("/post/{post_id}", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: int,
    skip: int = Query(default=0, ge=0, description="Number of comments to skip"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of comments to return"),
    comment_repo: CommentCRUDRepository = Depends(get_repository(CommentCRUDRepository))
):
    comments_data = await comment_repo.get_post_comments(post_id, skip, limit)
    return [
        CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            author_id=comment.author_id,
            parent_id=comment.parent_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            content=comment.content,
            author_username=username,
            author_avatar=avatar
        )
        for comment, username, avatar in comments_data
    ]

""" @router.get("/{comment_id}/replies", response_model=List[CommentResponse])
async def get_comment_replies(
    comment_id: int,
    skip: int = Query(default=0, ge=0, description="Number of replies to skip"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of replies to return"),
    comment_repo: CommentCRUDRepository = Depends(get_repository(CommentCRUDRepository))
):
    replies_data = await comment_repo.get_comment_replies(comment_id, skip, limit)
    return [
        CommentResponse(
            **reply.__dict__,
            author_username=username,
            author_avatar=avatar,
            replies_count=0  # Replies to replies are not supported
        )
        for reply, username, avatar in replies_data
    ]
"""

@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: int,
    comment_repo: CommentCRUDRepository = Depends(get_repository(CommentCRUDRepository))
):
    comment_data = await comment_repo.get_comment(comment_id)
    if not comment_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comment with id {comment_id} not found")
    comment, username, avatar = comment_data
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        parent_id=comment.parent_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        content=comment.content,
        author_username=username,
        author_avatar=avatar
    )

@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: Account = Depends(get_current_user),
    comment_repo: CommentCRUDRepository = Depends(get_repository(CommentCRUDRepository))
):
    try:
        await comment_repo.delete_comment(comment_id)
        return {"message": "Comment deleted successfully"}
    except EntityDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    content: str,
    current_user: Account = Depends(get_current_user),
    comment_repo: CommentCRUDRepository = Depends(get_repository(CommentCRUDRepository))
):
    try:
        updated_comment = await comment_repo.update_comment(comment_id, content)
        return CommentResponse(
            id=updated_comment.id,
            post_id=updated_comment.post_id,
            author_id=updated_comment.author_id,
            parent_id=updated_comment.parent_id,
            created_at=updated_comment.created_at,
            updated_at=updated_comment.updated_at,
            content=updated_comment.content,
            author_username=current_user.username,
            author_avatar=current_user.avatar
        )
    except EntityDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
