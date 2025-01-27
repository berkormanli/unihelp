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

@router.post("", response_model=bool)
async def create_poll(
    poll_create: PollInCreate,
    current_user: Account = Depends(get_current_user),
    post_repo: PostCRUDRepository = fastapi.Depends(get_repository(PostCRUDRepository)),
    poll_repo: PollCRUDRepository = fastapi.Depends(get_repository(PollCRUDRepository)),
):
    try:
        db_post = await post_repo.create_post(poll_create, current_user.id)
        db_poll = await poll_repo.create_poll(poll_create, db_post.id, current_user.id)
    except EntityAlreadyExists:
        raise await http_409_exc_post_already_has_poll_request(post_id=db_post.id)
    except EntityDoesNotExist:
        raise await http_404_exc_post_id_not_found_request(post_id=db_post.id)

    #return PollInResponse.from_orm(db_poll)
    return True

@router.get("/{poll_id}", response_model=PollInResponse)
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
    ]

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