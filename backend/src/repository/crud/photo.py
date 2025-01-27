import typing

import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions
from sqlalchemy.exc import IntegrityError

from src.models.db.photo import Photo
from src.models.db.post import Post
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists, DatabaseError

class PhotoCRUDRepository(BaseCRUDRepository):
    async def create_photo(self, url: str, post_id: int) -> Photo:
        async with self.async_session.begin():
            db_post = await self.async_session.get(Post, post_id)
            if not db_post:
                raise EntityDoesNotExist(f"Post with id {post_id} does not exist")

            db_photo = Photo(url=url, post_id=post_id)
            self.async_session.add(db_photo)

            try:
                await self.async_session.flush()
            except IntegrityError as e:
                await self.async_session.rollback()
                raise DatabaseError(f"Failed to create photo: {e}")

        return db_photo

    async def read_photo(self, photo_id: int) -> Photo:
        async with self.async_session.begin():
            db_photo = await self.async_session.get(Photo, photo_id)
            if not db_photo:
                raise EntityDoesNotExist(f"Photo with id {photo_id} does not exist")
        return db_photo

    async def read_photos_by_post_id(self, post_id: int) -> typing.Sequence[Photo]:
        async with self.async_session.begin():
            stmt = sqlalchemy.select(Photo).where(Photo.post_id == post_id)
            result = await self.async_session.execute(stmt)
            photos = result.scalars().all()
        return photos

    async def update_photo(self, photo_id: int, url: str) -> Photo:
        async with self.async_session.begin():
            db_photo = await self.async_session.get(Photo, photo_id)
            if not db_photo:
                raise EntityDoesNotExist(f"Photo with id {photo_id} does not exist")

            db_photo.url = url

            try:
                await self.async_session.flush()
            except IntegrityError as e:
                await self.async_session.rollback()
                raise DatabaseError(f"Failed to update photo: {e}")

        return db_photo

    async def delete_photo(self, photo_id: int) -> None:
        async with self.async_session.begin():
            db_photo = await self.async_session.get(Photo, photo_id)
            if not db_photo:
                raise EntityDoesNotExist(f"Photo with id {photo_id} does not exist")

            await self.async_session.delete(db_photo)