
import sqlalchemy
from sqlalchemy.orm import selectinload
from src.models.db.like import Like
from src.models.db.post import Post
from src.models.db.poll import Poll
from src.models.db.post_stats import PostStats
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists

class LikeCRUDRepository(BaseCRUDRepository):
    async def create_like(self, account_id: int, post_id: int) -> Like:
        stmt = (
            sqlalchemy.select(Post)
            .where(Post.id == post_id)
        )
        result = await self.async_session.execute(stmt)
        db_post = result.scalar_one_or_none()  # Use scalar_one_or_none() to handle the case where the post doesn't exist
        if not db_post:
            raise EntityDoesNotExist(f"Post with id {post_id} does not exist")

        already_liked = await self.async_session.execute(
            sqlalchemy.select(Like).where(
                (Like.account_id == account_id) &
                (Like.post_id == post_id)
            )
        )
        if already_liked.scalar_one_or_none():
            raise EntityAlreadyExists(f"Post with id {post_id} already liked by user with id {account_id}")
        
        new_like = Like(
            account_id=account_id,
            post_id=post_id
        )
        self.async_session.add(instance=new_like)
        await self.async_session.flush()  # Flush to get the new_like.id

        # Increment the likes count in PostStats
        await self.increment_likes(post_id)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_like)
        return new_like

    async def delete_like(self, account_id: int, post_id: int) -> str:
        stmt = sqlalchemy.delete(Like).where(
            (Like.account_id == account_id) & 
            (Like.post_id == post_id)
        )
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()
        
        if result.rowcount == 0:
            raise EntityDoesNotExist("Like does not exist")

        # Decrement the likes count in PostStats
        await self.decrement_likes(post_id)

        await self.async_session.commit()
        
        return "Like removed successfully"

    """async def get_user_likes(self, account_id: int) -> list[Post]:
        stmt = (
            sqlalchemy.select(Post)
            .join(Like, Like.post_id == Post.id)
            .where(Like.account_id == account_id)
            .options(
                selectinload(Post.account),
                selectinload(Post.stats),
                selectinload(Post.photos),
                selectinload(Post.tags),
                selectinload(Post.poll).options(selectinload(Poll.answers))
            )
            .order_by(Like.created_at.desc())
        )
        result = await self.async_session.execute(stmt)
        return result.scalars().all()
    """
    async def get_user_likes(self, account_id: int, skip: int = 0, limit: int = 10) -> list[Post]:
        stmt = (
            sqlalchemy.select(Post)
            .join(Like, Like.post_id == Post.id)
            .where(Like.account_id == account_id)
            .options(
                selectinload(Post.account),  # Eagerly load the account relationship
                selectinload(Post.stats),    # Eagerly load the stats relationship
                selectinload(Post.photos),   # Eagerly load the photos relationship
                selectinload(Post.tags),
                selectinload(Post.poll).options(selectinload(Poll.answers))
            )
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        #stmt = stmt.where(Post.account_id != user_id)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def is_post_liked(self, account_id: int, post_id: int) -> bool:
        stmt = sqlalchemy.select(Like).where(
            (Like.account_id == account_id) & 
            (Like.post_id == post_id)
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalar() is not None

    async def increment_likes(self, post_id: int) -> None:
        stmt = (
            sqlalchemy.update(PostStats)
            .where(PostStats.post_id == post_id)
            .values(likes=PostStats.likes + 1)
        )
        await self.async_session.execute(stmt)

    async def decrement_likes(self, post_id: int) -> None:
        stmt = (
            sqlalchemy.update(PostStats)
            .where(PostStats.post_id == post_id)
            .values(likes=PostStats.likes - 1)
        )
        await self.async_session.execute(stmt)
