import typing

import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from src.models.db.post import Post, post_tags
from src.models.db.poll import Poll
from src.models.db.account import Account
from src.models.db.photo import Photo
from src.models.db.tag import Tag
from src.models.db.post_stats import PostStats
from src.models.schemas.post import PostInCreate, PostInResponse
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists, DatabaseError

class PostCRUDRepository(BaseCRUDRepository):
    async def create_post(self, post_create: PostInCreate, account_id: int) -> Post:
        db_account = await self.async_session.get(Account, account_id)
        if not db_account:
            raise EntityDoesNotExist(f"Account with id {account_id} does not exist")

        # Create post
        db_post = Post(
            content=post_create.content,
            account_id=account_id,
        )
        self.async_session.add(db_post)
        await self.async_session.flush()  # Flush to get db_post.id

        # Create photos
        photos = []
        for photo_url in post_create.photos:
            db_photo = Photo(url=photo_url, post_id=db_post.id)
            self.async_session.add(db_photo)
            photos.append(db_photo)
        
        # --- Handle Tags and Populate post_tags ---
        for tag_name in post_create.tags:
            # 1. Fetch or Create the Tag
            db_tag = await self.async_session.execute(
                sqlalchemy.select(Tag).where(Tag.name == tag_name)
            )
            db_tag = db_tag.scalar_one_or_none()

            if db_tag is None:
                db_tag = Tag(name=tag_name)
                self.async_session.add(db_tag)
                await self.async_session.flush()  # Flush to get db_tag.id

            # 2. Create an entry in the post_tags table
            #    Using the association table directly (post_tags.insert())
            await self.async_session.execute(
                post_tags.insert().values(post_id=db_post.id, tag_id=db_tag.id)
            )
        # --- End of Tag Handling ---


        # Create post stats
        db_post_stats = PostStats(
            post_id=db_post.id,
            comments=0,
            likes=0,
            bookmarks=0
        )
        self.async_session.add(db_post_stats)

        # Commit changes to the database
        await self.async_session.commit()

        # Refresh the post to load relationships
        await self.async_session.refresh(db_post, attribute_names=["photos", "stats", "tags"])

        return db_post

    async def read_post(self, post_id: int) -> Post:
        stmt = (
            sqlalchemy.select(Post)
            .where(Post.id == post_id)
            .options(
                selectinload(Post.account),
                selectinload(Post.stats),
                selectinload(Post.photos),
                selectinload(Post.tags),
                selectinload(Post.poll).options(selectinload(Poll.answers))
            )
        )
        result = await self.async_session.execute(stmt)
        db_post = result.scalar_one_or_none()  # Use scalar_one_or_none() to handle the case where the post doesn't exist
        if not db_post:
            raise EntityDoesNotExist(f"Post with id {post_id} does not exist")

        return db_post


    async def read_posts(self, skip: int = 0, limit: int = 10, tag: int = None) -> typing.Sequence[Post]:
        if tag:
            stmt = (
                sqlalchemy.select(Post)
               .join(post_tags)
               .join(Tag)
               .where(Tag.id == tag)
               .options(
                    selectinload(Post.account),
                    selectinload(Post.stats),
                    selectinload(Post.photos),
                    selectinload(Post.tags),
                    selectinload(Post.poll).options(selectinload(Poll.answers))
                )
              .order_by(Post.created_at.desc())
              .offset(skip)
              .limit(limit)
            )
        else:
            stmt = (
                sqlalchemy.select(Post)
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

    async def read_own_posts(self, user_id: int = None, skip: int = 0, limit: int = 10) -> typing.Sequence[Post]:
        stmt = (
            sqlalchemy.select(Post)
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
        stmt = stmt.where(Post.account_id == user_id)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def update_post(self, post_id: int, post_update: PostInCreate) -> Post:
        # Use select with selectinload for eager loading
        stmt = (
            sqlalchemy.select(Post)
            .where(Post.id == post_id)
            .options(
                selectinload(Post.account),
                selectinload(Post.stats),
                selectinload(Post.photos),
                selectinload(Post.tags).options(selectinload(Poll.answers))
            )
        )
        result = await self.async_session.execute(stmt)
        db_post = result.scalar_one_or_none()
        if not db_post:
            raise EntityDoesNotExist(f"Post with id {post_id} does not exist")

        # Update post fields
        db_post.content = post_update.content

        # Update photos (replace existing photos)
        # Use sqlalchemy delete function instead of a raw query
        delete_stmt = sqlalchemy.delete(Photo).where(Photo.post_id == post_id)
        await self.async_session.execute(delete_stmt)

        for photo_url in post_update.photos:
            db_photo = Photo(url=photo_url, post_id=post_id)
            self.async_session.add(db_photo)
        
        await self.async_session.commit()
        await self.async_session.refresh(db_post)

        return db_post

    async def delete_post(self, post_id: int) -> None:
        stmt = (
            sqlalchemy.select(Post)
            .where(Post.id == post_id)
            .options(
                selectinload(Post.account),
                selectinload(Post.stats),
                selectinload(Post.photos)
            )
        )
        result = await self.async_session.execute(stmt)
        db_post = result.scalar_one_or_none()
        if not db_post:
            raise EntityDoesNotExist(f"Post with id {post_id} does not exist")

        await self.async_session.delete(db_post)
        await self.async_session.commit()
