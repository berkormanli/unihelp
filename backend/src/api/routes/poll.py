from src.models.schemas.account import AccountDetailBase
from src.models.schemas.post import AnswerInResponsePost, PollInResponsePost, PostInResponse, PostStatsBase
from src.models.schemas.tag import TagCreate
from src.repository.crud.bookmark import BookmarkCRUDRepository
from src.repository.crud.like import LikeCRUDRepository
import fastapi

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import get_current_user
from src.models.schemas.poll import PollInCreate, PollInResponse, PollDataBase
from src.models.db.account import Account
from src.repository.crud.poll import PollCRUDRepository
from src.repository.crud.post import PostCRUDRepository
from src.repository.crud.poll_vote import PollVoteCRUDRepository
from src.utilities.exceptions.http.exc_404 import (
    http_404_exc_poll_id_not_found_request,
    http_404_exc_post_id_not_found_request,
)
from src.utilities.exceptions.http.exc_409 import (
    http_409_exc_post_already_has_poll_request,
    http_409_exc_poll_already_voted,
)
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists

from fastapi import Depends

router = fastapi.APIRouter(prefix="/polls", tags=["polls"])


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

async def enrich_poll_with_vote_info(
    poll: PollInResponse,
    current_user: Account | None,
    poll_vote_repo: PollVoteCRUDRepository
) -> PollInResponse:
    if current_user:
        vote = await poll_vote_repo.get_user_vote(poll.id, current_user.id)
        if vote:
            poll.voted = True
            poll.selected_answer_id = vote.answer_index
    return poll

@router.post("", response_model=PostInResponse)
async def create_poll(
    poll_create: PollInCreate,
    post_repo: PostCRUDRepository = fastapi.Depends(get_repository(PostCRUDRepository)),
    like_repo: LikeCRUDRepository = fastapi.Depends(get_repository(LikeCRUDRepository)),
    bookmark_repo: BookmarkCRUDRepository = fastapi.Depends(get_repository(BookmarkCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
    poll_repo: PollCRUDRepository = fastapi.Depends(get_repository(PollCRUDRepository)),
    current_user: Account = Depends(get_current_user),
):
    try:
        temp_db_post = await post_repo.create_post(poll_create, current_user.id)
        db_poll = await poll_repo.create_poll(poll_create, temp_db_post.id, current_user.id)
        await poll_repo.async_session.commit()

        db_post = await post_repo.read_post(temp_db_post.id)

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
    except EntityAlreadyExists:
        raise await http_409_exc_post_already_has_poll_request(post_id=db_post.id)
    except EntityDoesNotExist:
        raise await http_404_exc_post_id_not_found_request(post_id=db_post.id)

""" @router.get("/{poll_id}", response_model=PollInResponse)
async def read_poll(
    poll_id: int,
    current_user: Account | None = Depends(get_current_user),
    poll_repo: PollCRUDRepository = fastapi.Depends(get_repository(PollCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
):
    try:
        db_poll = await poll_repo.read_poll(poll_id)
        poll_response = PollInResponse.from_orm(db_poll)
        return await enrich_poll_with_vote_info(poll_response, current_user, poll_vote_repo)
    except EntityDoesNotExist:
        raise await http_404_exc_poll_id_not_found_request(poll_id=poll_id)

@router.get("", response_model=list[PollInResponse])
async def read_polls(
    current_user: Account | None = Depends(get_current_user),
    poll_repo: PollCRUDRepository = fastapi.Depends(get_repository(PollCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
):
    db_polls = await poll_repo.read_polls()
    poll_responses = [PollInResponse.from_orm(poll) for poll in db_polls]
    return [
        await enrich_poll_with_vote_info(poll, current_user, poll_vote_repo)
        for poll in poll_responses
    ] """

@router.patch("/{poll_id}", response_model=PollInResponse)
async def update_poll(
    poll_id: int,
    poll_update: PollInCreate,
    poll_repo: PollCRUDRepository = fastapi.Depends(get_repository(PollCRUDRepository)),
):
    try:
        db_poll = await poll_repo.update_poll(poll_id, poll_update)
    except EntityDoesNotExist:
        raise await http_404_exc_poll_id_not_found_request(poll_id=poll_id)
    return PollInResponse.from_orm(db_poll)

@router.delete("/{poll_id}")
async def delete_poll(
    poll_id: int,
    poll_repo: PollCRUDRepository = fastapi.Depends(get_repository(PollCRUDRepository)),
):
    try:
        await poll_repo.delete_poll(poll_id)
    except EntityDoesNotExist:
        raise await http_404_exc_poll_id_not_found_request(poll_id=poll_id)
    return {"message": "Poll deleted successfully"}

@router.post("/{poll_id}/vote")
async def vote_poll(
    poll_id: int,
    answer_index: int,
    current_user: Account = Depends(get_current_user),
    poll_repo: PollCRUDRepository = fastapi.Depends(get_repository(PollCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
):
    try:
        # First check if poll exists
        await poll_repo.read_poll(poll_id)
        # Create the vote
        await poll_vote_repo.create_vote(poll_id, current_user.id, answer_index)
        return {"message": "Vote recorded successfully"}
    except EntityAlreadyExists:
        raise await http_409_exc_poll_already_voted(poll_id=poll_id)
    except EntityDoesNotExist:
        raise await http_404_exc_poll_id_not_found_request(poll_id=poll_id)
