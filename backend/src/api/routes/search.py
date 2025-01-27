import fastapi
from fastapi import Depends, Query

import asyncio

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import get_current_user
from src.models.schemas.search import SearchResponse
from src.models.schemas.post import AnswerInResponsePost, PollInResponsePost, PostInResponse, PostStatsBase
from src.models.schemas.tag import TagCreate, TagResponse
from src.models.schemas.account import AccountDetailBase
from src.repository.crud.search import SearchCRUDRepository
from src.models.db.account import Account
from src.repository.crud.bookmark import BookmarkCRUDRepository
from src.repository.crud.like import LikeCRUDRepository
from src.repository.crud.poll_vote import PollVoteCRUDRepository
from src.repository.crud.post import PostCRUDRepository

router = fastapi.APIRouter(prefix="/search", tags=["search"])

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

@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(default=0, ge=0, description="Number of posts to skip"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of posts to return"),
    search_repo: SearchCRUDRepository = fastapi.Depends(get_repository(SearchCRUDRepository)),
    like_repo: LikeCRUDRepository = fastapi.Depends(get_repository(LikeCRUDRepository)),
    bookmark_repo: BookmarkCRUDRepository = fastapi.Depends(get_repository(BookmarkCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
    current_user: Account | None = Depends(get_current_user),
):
    results = await search_repo.search_all(q, skip, limit)

    async def process_user(user):
        return AccountDetailBase(
            username=user.username,
            avatar=user.avatar,
            fullName=user.username,
        )
    
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
    
    users = await asyncio.gather(*[process_user(user) for user in results["users"]])
    posts = await asyncio.gather(*[process_post(post, current_user, like_repo, bookmark_repo, poll_vote_repo) for post in results["posts"]])

    return SearchResponse(
        users=users,
        posts=posts,
        tags=[TagResponse(id=tag.id, name=tag.name) for tag in results["tags"]]
    )