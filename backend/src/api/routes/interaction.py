from src.models.schemas.account import AccountDetailBase
from src.models.schemas.tag import TagCreate
from src.repository.crud.poll_vote import PollVoteCRUDRepository
from src.models.schemas.post import AnswerInResponsePost, PollInResponsePost, PostInResponse, PostStatsBase
import fastapi
from fastapi import Depends, HTTPException, status, Query

from src.api.dependencies.repository import get_repository
from src.repository.crud.like import LikeCRUDRepository
from src.repository.crud.bookmark import BookmarkCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists
from src.models.schemas.like import LikeInDB
from src.models.schemas.bookmark import BookmarkInDB
from src.api.dependencies.auth import get_current_user
from src.models.db.account import Account
from src.models.db.post import Post

router = fastapi.APIRouter(prefix="/interactions", tags=["interactions"])

# Gönderi etkileşimlerini zenginleştirme fonksiyonu
async def enrich_post_with_interactions(
    post: PostInResponse,
    current_user: Account | None,
    like_repo: LikeCRUDRepository,
    bookmark_repo: BookmarkCRUDRepository
) -> PostInResponse:
    # Eğer mevcut kullanıcı varsa, gönderinin beğenilip beğenilmediğini ve yer işaretlerine eklenip eklenmediğini kontrol et
    if current_user:
        post.is_liked = await like_repo.is_post_liked(current_user.id, post.id)
        post.is_bookmarked = await bookmark_repo.is_post_bookmarked(current_user.id, post.id)
    return post

# Gönderiyi beğenme endpoint'i
@router.post(
    path="/like/{post_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=bool
)
async def like_post(
    post_id: int,
    current_user: Account = Depends(get_current_user),
    like_repo: LikeCRUDRepository = Depends(get_repository(repo_type=LikeCRUDRepository))
) -> bool:
    # Gönderiyi beğenmeyi dene
    try:
        await like_repo.create_like(account_id=current_user.id, post_id=post_id)
        return True
    except EntityAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except EntityDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# Gönderi beğenisini kaldırma endpoint'i
@router.delete(
    path="/like/{post_id}",
    status_code=status.HTTP_200_OK
)
async def unlike_post(
    post_id: int,
    current_user: Account = Depends(get_current_user),
    like_repo: LikeCRUDRepository = Depends(get_repository(repo_type=LikeCRUDRepository))
) -> dict[str, str]:
    # Gönderi beğenisini kaldırmayı dene
    try:
        result = await like_repo.delete_like(account_id=current_user.id, post_id=post_id)
        return {"message": result}
    except EntityDoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beğeni bulunamadı")

# Gönderiyi yer işaretlerine ekleme endpoint'i
@router.post(
    path="/bookmark/{post_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=bool
)
async def bookmark_post(
    post_id: int,
    current_user: Account = Depends(get_current_user),
    bookmark_repo: BookmarkCRUDRepository = Depends(get_repository(repo_type=BookmarkCRUDRepository))
) -> bool:
    # Gönderiyi yer işaretlerine eklemeyi dene
    try:
        await bookmark_repo.create_bookmark(account_id=current_user.id, post_id=post_id)
        return True
    except EntityAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except EntityDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# Gönderi yer işaretini kaldırma endpoint'i
@router.delete(
    path="/bookmark/{post_id}",
    status_code=status.HTTP_200_OK
)
async def remove_bookmark(
    post_id: int,
    current_user: Account = Depends(get_current_user),
    bookmark_repo: BookmarkCRUDRepository = Depends(get_repository(repo_type=BookmarkCRUDRepository))
) -> dict[str, str]:
    # Gönderi yer işaretini kaldırmayı dene
    try:
        result = await bookmark_repo.delete_bookmark(account_id=current_user.id, post_id=post_id)
        return {"message": result}
    except EntityDoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yer işareti bulunamadı")

""" @router.get(
    path="/likes",
    response_model=list[int],
    status_code=status.HTTP_200_OK
)
async def get_user_liked_posts(
    current_user: Account = Depends(get_current_user),
    like_repo: LikeCRUDRepository = Depends(get_repository(repo_type=LikeCRUDRepository))
) -> list[int]:
    likes = await like_repo.get_user_likes(account_id=current_user.id)
    return likes """

# Kullanıcının beğendiği gönderileri getirme endpoint'i
@router.get(
    path="/likes",
    response_model=list[PostInResponse],
    status_code=status.HTTP_200_OK
)
async def get_user_liked_postsa(
    skip: int = Query(default=0, ge=0, description="Atlanacak gönderi sayısı"), # Atlanacak gönderi sayısı için açıklama
    limit: int = Query(default=10, ge=1, le=50, description="Döndürülecek gönderi sayısı"), # Döndürülecek gönderi sayısı için açıklama
    current_user: Account = Depends(get_current_user),
    like_repo: LikeCRUDRepository = fastapi.Depends(get_repository(LikeCRUDRepository)),
    bookmark_repo: BookmarkCRUDRepository = fastapi.Depends(get_repository(BookmarkCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
):
    # Kullanıcının beğendiği gönderileri al
    liked_posts = await like_repo.get_user_likes(account_id=current_user.id, skip=skip, limit=limit)

    
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
    for post in liked_posts:
        processed_post = await process_post(post, current_user, like_repo, bookmark_repo, poll_vote_repo)
        post_responses.append(processed_post)

    return post_responses

# Kullanıcının yer işaretlediği gönderileri getirme endpoint'i
@router.get(
    path="/bookmarks",
    response_model=list[PostInResponse],
    status_code=status.HTTP_200_OK
)
async def get_user_bookmarked_posts(
    skip: int = Query(default=0, ge=0, description="Atlanacak gönderi sayısı"), # Atlanacak gönderi sayısı için açıklama
    limit: int = Query(default=10, ge=1, le=50, description="Döndürülecek gönderi sayısı"), # Döndürülecek gönderi sayısı için açıklama
    current_user: Account = Depends(get_current_user),
    like_repo: LikeCRUDRepository = fastapi.Depends(get_repository(LikeCRUDRepository)),
    bookmark_repo: BookmarkCRUDRepository = fastapi.Depends(get_repository(BookmarkCRUDRepository)),
    poll_vote_repo: PollVoteCRUDRepository = fastapi.Depends(get_repository(PollVoteCRUDRepository)),
):
    # Kullanıcının yer işaretlediği gönderileri al
    bookmarked_posts = await bookmark_repo.get_user_bookmarks(account_id=current_user.id, skip=skip, limit=limit)
    
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
    for post in bookmarked_posts:
        processed_post = await process_post(post, current_user, like_repo, bookmark_repo, poll_vote_repo)
        post_responses.append(processed_post)

    return post_responses
