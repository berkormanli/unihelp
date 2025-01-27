import sqlalchemy
from sqlalchemy.orm import selectinload
from src.models.db.bookmark import Bookmark
from src.models.db.post import Post
from src.models.db.poll import Poll
from src.models.db.post_stats import PostStats
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists

class BookmarkCRUDRepository(BaseCRUDRepository):
    async def create_bookmark(self, account_id: int, post_id: int) -> Bookmark:
        stmt = (
            sqlalchemy.select(Post)
            .where(Post.id == post_id)
        )
        result = await self.async_session.execute(stmt)
        db_post = result.scalar_one_or_none()  # Use scalar_one_or_none() to handle the case where the post doesn't exist
        if not db_post:
            raise EntityDoesNotExist(f"Post with id {post_id} does not exist")

        already_bookmarked = await self.async_session.execute(
            sqlalchemy.select(Bookmark).where(
                (Bookmark.account_id == account_id) &
                (Bookmark.post_id == post_id)
            )
        )
        if already_bookmarked.scalar_one_or_none():
            raise EntityAlreadyExists(f"Post with id {post_id} already bookmarked by user with id {account_id}")

        new_bookmark = Bookmark(
            account_id=account_id,
            post_id=post_id
        )
        self.async_session.add(instance=new_bookmark)
        await self.async_session.flush()

        await self.increment_bookmarks(post_id)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_bookmark)
        return new_bookmark

    async def delete_bookmark(self, account_id: int, post_id: int) -> str:
        stmt = sqlalchemy.delete(Bookmark).where(
            (Bookmark.account_id == account_id) & 
            (Bookmark.post_id == post_id)
        )
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()
        
        if result.rowcount == 0:
            raise EntityDoesNotExist("Bookmark does not exist")

        await self.decrement_bookmarks(post_id)
        await self.async_session.commit()
        return "Bookmark removed successfully"

    async def get_user_bookmarks(self, account_id: int, skip: int = 0, limit: int = 10) -> list[Post]:
        stmt = (
            sqlalchemy.select(Post)
            .join(Bookmark, Bookmark.post_id == Post.id)
            .where(Bookmark.account_id == account_id)
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
    
    async def is_post_bookmarked(self, account_id: int, post_id: int) -> bool:
        stmt = sqlalchemy.select(Bookmark).where(
            (Bookmark.account_id == account_id) & 
            (Bookmark.post_id == post_id)
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalar() is not None

    async def increment_bookmarks(self, post_id: int) -> None:
        stmt = (
            sqlalchemy.update(PostStats)
            .where(PostStats.post_id == post_id)
            .values(bookmarks=PostStats.bookmarks + 1)
        )
        await self.async_session.execute(statement=stmt)
    
    async def decrement_bookmarks(self, post_id: int) -> None:
        stmt = (
            sqlalchemy.update(PostStats)
           .where(PostStats.post_id == post_id)
           .values(bookmarks=PostStats.bookmarks - 1)
        )
        await self.async_session.execute(statement=stmt)
