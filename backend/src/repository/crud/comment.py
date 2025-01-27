from sqlalchemy import select, func, update
from src.models.db.comment import Comment
from src.models.db.account import Account
from src.models.db.post_stats import PostStats
from src.repository.crud.base import BaseCRUDRepository
from src.models.schemas.comment import CommentCreate
from src.utilities.exceptions.database import EntityDoesNotExist

class CommentCRUDRepository(BaseCRUDRepository):
    async def create_comment(self, comment_create: CommentCreate, author_id: int) -> Comment:
        parent_id = comment_create.parent_id or None
        comment = Comment(
            content=comment_create.content,
            post_id=comment_create.post_id,
            author_id=author_id,
            parent_id=parent_id
        )
        self.async_session.add(comment)
        await self.async_session.flush()  # Flush to get the new_like.id

        # Increment the likes count in PostStats
        await self.increment_comment_count(comment_create.post_id)
        await self.async_session.commit()
        await self.async_session.refresh(comment)
        return comment

    async def get_post_comments(self, post_id: int, skip: int = 0, limit: int = 10) -> list[tuple[Comment, str, str | None, int]]:
        stmt = (
            select(
                Comment,
                Account.username.label('author_username'),
                Account.avatar.label('author_avatar')
            )
            .join(Account, Comment.author_id == Account.id)
            .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
            .group_by(Comment.id, Account.username, Account.avatar)
            .order_by(Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.async_session.execute(stmt)
        return list(result.all())

    async def get_comment_replies(self, comment_id: int, skip: int = 0, limit: int = 10) -> list[tuple[Comment, str, str | None]]:
        stmt = (
            select(
                Comment,
                Account.username.label('author_username'),
                Account.avatar.label('author_avatar')
            )
            .join(Account, Comment.author_id == Account.id)
            .where(Comment.parent_id == comment_id)
            .order_by(Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.async_session.execute(stmt)
        return list(result.all())

    async def get_comment(self, comment_id: int) -> tuple[Comment, str, str | None]:
        stmt = (
            select(
                Comment,
                Account.username.label('author_username'),
                Account.avatar.label('author_avatar')
            )
            .join(Account, Comment.author_id == Account.id)
            .where(Comment.id == comment_id)
        )
        result = await self.async_session.execute(stmt)
        comment_tuple = result.one_or_none()
        if not comment_tuple:
            raise EntityDoesNotExist(f"Comment with id {comment_id} not found")
        return comment_tuple

    async def delete_comment(self, comment_id: int) -> None:
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.async_session.execute(stmt)
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise EntityDoesNotExist(f"Comment with id {comment_id} not found")
        post_id = comment.post_id
        await self.async_session.delete(comment)
        await self.async_session.flush()
        # Decrement the likes count in PostStats
        await self.decrement_likes(post_id)
        await self.async_session.commit()

    async def update_comment(self, comment_id: int, content: str) -> Comment:
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.async_session.execute(stmt)
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise EntityDoesNotExist(f"Comment with id {comment_id} not found")
            
        comment.content = content
        await self.async_session.commit()
        await self.async_session.refresh(comment)
        return comment

    async def increment_comment_count(self, post_id: int) -> None:
        stmt = (
            update(PostStats)
            .where(PostStats.post_id == post_id)
            .values(comments=PostStats.comments + 1)
        )
        await self.async_session.execute(stmt)

    async def decrement_comment_count(self, post_id: int) -> None:
        stmt = (
            update(PostStats)
            .where(PostStats.post_id == post_id)
            .values(comments=PostStats.comments - 1)
        )
        await self.async_session.execute(stmt)
