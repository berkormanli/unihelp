import fastapi
import asyncio
import sqlalchemy

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import get_current_user
from src.models.schemas.post import PostInCreate, PostInResponse, PostStatsBase
from src.models.db.poll_vote import PollVote
from src.models.schemas.tag import TagCreate
from src.models.schemas.poll import PollInResponse, AnswerInResponse
from src.models.schemas.post import PollInResponsePost, AnswerInResponsePost
from src.models.db.account import Account
from src.models.schemas.account import AccountDetailBase
from src.repository.crud.post import PostCRUDRepository
from src.repository.crud.poll_vote import PollVoteCRUDRepository
from src.repository.crud.like import LikeCRUDRepository
from src.repository.crud.bookmark import BookmarkCRUDRepository
from src.utilities.exceptions.http.exc_404 import http_404_exc_post_id_not_found_request
from src.utilities.exceptions.database import EntityDoesNotExist
from fastapi import Depends, Query

router = fastapi.APIRouter(prefix="/posts", tags=["posts"])

async def enrich_post_with_interactions(
    post: PostInResponse,
    current_user: Account | None,
    like_repo: LikeCRUDRepository,
    bookmark_repo: BookmarkCRUDRepository
) -> PostInResponse:
    if current_user:
        post.is_liked = await like_repo.is_post_liked(current_user.id, post.id)
        post.is_bookmarked = await bookmark_repo.is_post_bookmarked(current_user.id, post.id)
    return post

@router.post("", response_model=PostInResponse)
async def create_post(
    post_create: PostInCreate,
    current_user: Account = Depends(get_current_user),
    post_repo: PostCRUDRepository = fastapi.Depends(get_repository(PostCRUDRepository)),
):
    db_post = await post_repo.create_post(post_create, current_user.id)
    
    return PostInResponse(
        id=db_post.id,
        content=db_post.content,
        account=AccountDetailBase(
            avatar=current_user.avatar,
            username=current_user.username,
            fullName=current_user.username
        ),
        stats=PostStatsBase(
            comments=0,
            likes=0,
            bookmarks=0
        ),
        photos=[photo.url for photo in db_post.photos] if db_post.photos else [],
        tags=[TagCreate(name=tag.name) for tag in db_post.tags] if db_post.tags else [],
        createdAt=db_post.created_at
    )

@router.get("/{post_id}", response_model=PostInResponse)
async def read_post(
    post_id: int,
    post_repo: PostCRUDRepository = fastapi.Depends(get_repository(PostCRUDRepository)),
    like_repo: LikeCRUDRepository = fastapi.Depends(get_repository(LikeCRUDRepository)),
    bookmark_repo: BookmarkCRUDRepository = fastapi.Depends(get_repository(BookmarkCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
    current_user: Account | None = Depends(get_current_user),
):
    try:
        db_post = await post_repo.read_post(post_id)

        async def process_post(post, current_user, like_repo, bookmark_repo, poll_vote_repo):
            poll_response = None
            if post.poll:
                if current_user:
                    user_vote = await poll_vote_repo.get_user_vote(post.poll.id, current_user.id)
                else:
                    user_vote = None

                answers_response = []
                for answer in post.poll.answers:
                    answer_count = await poll_vote_repo.get_poll_vote_count(post.poll.id, answer.answer_index)

                    is_selected = False
                    if user_vote:
                        is_selected = (answer.answer_index == user_vote.answer_index)
                    answers_response.append(AnswerInResponsePost(
                        id=answer.id,
                        answerIndex=answer.answer_index,
                        text=answer.text,
                        answerCount=answer_count,
                        isSelected=is_selected
                    ))

                poll_response = PollInResponsePost(
                    id=post.poll.id,
                    postId=post.poll.post_id,
                    accountId=post.poll.account_id,
                    answers=answers_response,
                    expirationDate=post.poll.expiration_date,
                )

            return await enrich_post_with_interactions(
                PostInResponse(
                    id=post.id,
                    content=post.content,
                    account=AccountDetailBase(
                        avatar=post.account.avatar,
                        username=post.account.username,
                        fullName=post.account.username
                    ),
                    stats=PostStatsBase(
                        comments=post.stats.comments,
                        likes=post.stats.likes,
                        bookmarks=post.stats.bookmarks
                    ),
                    photos=[photo.url for photo in post.photos],
                    tags=[TagCreate(name=tag.name) for tag in post.tags],
                    poll=poll_response,
                    createdAt=post.created_at
                ),
                current_user, like_repo, bookmark_repo
            )
        
        processed_post = await process_post(db_post, current_user, like_repo, bookmark_repo, poll_vote_repo)
        return processed_post

    except EntityDoesNotExist:
        raise await http_404_exc_post_id_not_found_request(post_id=post_id)


@router.get("", response_model=list[PostInResponse])
async def read_posts(
    skip: int = Query(default=0, ge=0, description="Number of posts to skip"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of posts to return"),
    tag: int = Query(default=None, description="Tag ID to filter posts by"),
    post_repo: PostCRUDRepository = fastapi.Depends(get_repository(PostCRUDRepository)),
    like_repo: LikeCRUDRepository = fastapi.Depends(get_repository(LikeCRUDRepository)),
    bookmark_repo: BookmarkCRUDRepository = fastapi.Depends(get_repository(BookmarkCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
    current_user: Account | None = Depends(get_current_user),
):
    db_posts = await post_repo.read_posts(user_id=current_user.id, skip=skip, limit=limit, tag=tag)
    
    async def process_post(post, current_user, like_repo, bookmark_repo, poll_vote_repo):
        poll_response = None
        if post.poll:
            if current_user:
                user_vote = await poll_vote_repo.get_user_vote(post.poll.id, current_user.id)
            else:
                user_vote = None

            #poll_votes = await poll_vote_repo.get_poll_votes_detail(post.poll.id)

            answers_response = []
            for answer in post.poll.answers:
                answer_count = await poll_vote_repo.get_poll_vote_count(post.poll.id, answer.answer_index)

                is_selected = False
                if user_vote:
                    is_selected = (answer.answer_index == user_vote.answer_index)
                print(answer.answer_index)
                answers_response.append(AnswerInResponsePost(
                    id=answer.id,
                    answerIndex=answer.answer_index,
                    text=answer.text,
                    answerCount=answer_count,
                    isSelected=is_selected
                ))

            poll_response = PollInResponsePost(
                id=post.poll.id,
                postId=post.poll.post_id,
                accountId=post.poll.account_id,
                answers=answers_response,
                expirationDate=post.poll.expiration_date,
            )

        return await enrich_post_with_interactions(
            PostInResponse(
                id=post.id,
                content=post.content,
                account=AccountDetailBase(
                    avatar=post.account.avatar,
                    username=post.account.username,
                    fullName=post.account.username
                ),
                stats=PostStatsBase(
                    comments=post.stats.comments,
                    likes=post.stats.likes,
                    bookmarks=post.stats.bookmarks
                ),
                photos=[photo.url for photo in post.photos],
                tags=[TagCreate(name=tag.name) for tag in post.tags],
                poll=poll_response,
                createdAt=post.created_at
            ),
            current_user, like_repo, bookmark_repo
        )
    
    post_responses = []
    for post in db_posts:
        processed_post = await process_post(post, current_user, like_repo, bookmark_repo, poll_vote_repo)
        post_responses.append(processed_post)

    return post_responses
    #return await asyncio.gather(*[process_post(post, current_user, like_repo, bookmark_repo, poll_vote_repo) for post in db_posts])

@router.patch("/{post_id}", response_model=PostInResponse)
async def update_post(
    post_id: int,
    post_update: PostInCreate,
    post_repo: PostCRUDRepository = fastapi.Depends(get_repository(PostCRUDRepository)),
):
    try:
        db_post = await post_repo.update_post(post_id, post_update)
        async def process_post(db_post):
            return PostInResponse(
                id=db_post.id,
                content=db_post.content,
                account=AccountDetailBase(
                    avatar=db_post.account.avatar,
                    username=db_post.account.username,
                    fullName=db_post.account.username
                ),
                stats=PostStatsBase(
                    comments=db_post.stats.comments,
                    likes=db_post.stats.likes,
                    bookmarks=db_post.stats.bookmarks
                ),
                photos=[photo.url for photo in db_post.photos],
                tags=[TagCreate(name=tag.name) for tag in db_post.tags],
                createdAt=db_post.created_at
            )
        return await process_post(db_post)
    except EntityDoesNotExist:
        raise await http_404_exc_post_id_not_found_request(post_id=post_id)
    #return PostInResponse.from_orm(db_post)

@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    post_repo: PostCRUDRepository = fastapi.Depends(get_repository(PostCRUDRepository)),
):
    try:
        await post_repo.delete_post(post_id)
    except EntityDoesNotExist:
        raise await http_404_exc_post_id_not_found_request(post_id=post_id)
    return {"message": "Post deleted successfully"}