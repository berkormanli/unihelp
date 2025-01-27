import sqlalchemy

from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from src.repository.crud.base import BaseCRUDRepository
from src.models.db.tag import Tag
from src.models.db.account import Account
from src.models.db.poll import Poll
from src.models.db.post import Post

class SearchCRUDRepository(BaseCRUDRepository):
    async def search_all(self, query: str, skip, limit):
        # Search in users
        user_stmt = (
            sqlalchemy.select(Account)
            .where(
                or_(
                    Account.username.ilike(f"%{query}%"),
                    Account.email.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
        )


        post_stmt = (
            sqlalchemy.select(Post)
            .where(Post.content.ilike(f"%{query}%"))  # Example: case-insensitive like search on content
            .options(
                selectinload(Post.account),
                selectinload(Post.stats),
                selectinload(Post.photos),
                selectinload(Post.tags)
            )
            .offset(skip)
            .limit(limit)
        )

        # Eagerly load relationships for users
        user_stmt = user_stmt.options(
            selectinload(Account.posts)
        )
        # Eagerly load relationships for posts
        post_stmt = post_stmt.options(
            selectinload(Post.account),
            selectinload(Post.stats),
            selectinload(Post.photos),
            selectinload(Post.tags),
            selectinload(Post.poll).options(selectinload(Poll.answers))
        )

        # Example: Searching for tags (replace with your actual tag search logic)
        tag_stmt = sqlalchemy.select(Tag).where(Tag.name.ilike(f"%{query}%")).offset(skip).limit(limit)

        users = await self.async_session.execute(user_stmt)
        users = users.scalars().all()

        posts = await self.async_session.execute(post_stmt)
        posts = posts.scalars().all()

        tags = await self.async_session.execute(tag_stmt)
        tags = tags.scalars().all()

        return {
            "users": users,
            "posts": posts,
            "tags": tags  # Assuming Tag has a 'name' attribute
        }