import fastapi
import pydantic

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import get_current_user
from src.models.schemas.account import AccountDetailBase, AccountInResponse, AccountInUpdate, AccountWithToken
from src.repository.crud.account import AccountCRUDRepository
from src.models.db.account import Account
from src.models.schemas.post import AnswerInResponsePost, PollInResponsePost, PostInResponse, PostStatsBase
from src.repository.crud.bookmark import BookmarkCRUDRepository
from src.repository.crud.like import LikeCRUDRepository
from src.repository.crud.poll_vote import PollVoteCRUDRepository
from src.repository.crud.post import PostCRUDRepository
from src.models.schemas.tag import TagCreate
from fastapi import Depends, Query

from src.securities.authorizations.jwt import jwt_generator
from src.utilities.exceptions.database import EntityDoesNotExist
from src.utilities.exceptions.http.exc_404 import (
    http_404_exc_email_not_found_request,
    http_404_exc_id_not_found_request,
    http_404_exc_username_not_found_request,
)

router = fastapi.APIRouter(prefix="/accounts", tags=["accounts"])

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


@router.get(
    path="/posts",
    name="account:account-posts",
    response_model=list[PostInResponse],
    status_code=fastapi.status.HTTP_200_OK,
)
async def read_posts(
    skip: int = Query(default=0, ge=0, description="Number of posts to skip"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of posts to return"),
    post_repo: PostCRUDRepository = fastapi.Depends(get_repository(PostCRUDRepository)),
    like_repo: LikeCRUDRepository = fastapi.Depends(get_repository(LikeCRUDRepository)),
    bookmark_repo: BookmarkCRUDRepository = fastapi.Depends(get_repository(BookmarkCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
    current_user: Account | None = Depends(get_current_user),
):
    db_posts = await post_repo.read_own_posts(current_user.id, skip=skip, limit=limit)
    
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

@router.get(
    path="",
    name="accountss:read-accounts",
    response_model=list[AccountInResponse],
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_accounts(
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> list[AccountInResponse]:
    db_accounts = await account_repo.read_accounts()
    db_account_list: list = list()

    for db_account in db_accounts:
        access_token = jwt_generator.generate_access_token(account=db_account)
        account = AccountInResponse(
            id=db_account.id,
            authorizedAccount=AccountWithToken(
                token=access_token,
                username=db_account.username,
                email=db_account.email,  # type: ignore
                isVerified=db_account.is_verified,
                isActive=db_account.is_active,
                isLoggedIn=db_account.is_logged_in,
                createdAt=db_account.created_at,
                updatedAt=db_account.updated_at,
            ),
        )
        db_account_list.append(account)

    return db_account_list


@router.get(
    path="/{id}",
    name="accountss:read-account-by-id",
    response_model=AccountInResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_account(
    id: int,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountInResponse:
    try:
        db_account = await account_repo.read_account_by_id(id=id)
        access_token = jwt_generator.generate_access_token(account=db_account)

    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(id=id)

    return AccountInResponse(
        id=db_account.id,
        authorizedAccount=AccountWithToken(
            token=access_token,
            username=db_account.username,
            email=db_account.email,  # type: ignore
            isVerified=db_account.is_verified,
            isActive=db_account.is_active,
            isLoggedIn=db_account.is_logged_in,
            createdAt=db_account.created_at,
            updatedAt=db_account.updated_at,
        ),
    )


@router.patch(
    path="/{id}",
    name="accountss:update-account-by-id",
    response_model=AccountInResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_account(
    query_id: int,
    update_username: str | None = None,
    update_email: pydantic.EmailStr | None = None,
    update_password: str | None = None,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountInResponse:
    account_update = AccountInUpdate(username=update_username, email=update_email, password=update_password)
    try:
        updated_db_account = await account_repo.update_account_by_id(id=query_id, account_update=account_update)

    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(id=query_id)

    access_token = jwt_generator.generate_access_token(account=updated_db_account)

    return AccountInResponse(
        id=updated_db_account.id,
        authorizedAccount=AccountWithToken(
            token=access_token,
            username=updated_db_account.username,
            email=updated_db_account.email,  # type: ignore
            isVerified=updated_db_account.is_verified,
            isActive=updated_db_account.is_active,
            isLoggedIn=updated_db_account.is_logged_in,
            createdAt=updated_db_account.created_at,
            updatedAt=updated_db_account.updated_at,
        ),
    )


@router.delete(path="", name="accountss:delete-account-by-id", status_code=fastapi.status.HTTP_200_OK)
async def delete_account(
    id: int, account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository))
) -> dict[str, str]:
    try:
        deletion_result = await account_repo.delete_account_by_id(id=id)

    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(id=id)

    return {"notification": deletion_result}

@router.patch(
    path="/{id}/avatar",
    name="accountss:update-account-avatar",
    response_model=AccountInResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_account_avatar(
    id: int,
    avatar_url: str,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountInResponse:
    try:
        # Update account avatar URL in repository
        updated_db_account = await account_repo.update_account_avatar(id=id, avatar_url=avatar_url)
        
    except EntityDoesNotExist:
        raise await http_404_exc_id_not_found_request(id=id)

    access_token = jwt_generator.generate_access_token(account=updated_db_account)

    return AccountInResponse(
        id=updated_db_account.id,
        authorizedAccount=AccountWithToken(
            token=access_token,
            username=updated_db_account.username,
            email=updated_db_account.email,  # type: ignore
            isVerified=updated_db_account.is_verified,
            isActive=updated_db_account.is_active,
            isLoggedIn=updated_db_account.is_logged_in,
            createdAt=updated_db_account.created_at,
            updatedAt=updated_db_account.updated_at,
        ),
    )