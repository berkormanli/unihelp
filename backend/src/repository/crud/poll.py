import typing

import datetime  # Import the datetime module
from datetime import timedelta  # Import timedelta specifically

import sqlalchemy
from sqlalchemy import select, delete
from sqlalchemy.sql import functions as sqlalchemy_functions
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.models.db.account import Account
from src.models.db.poll import Poll
from src.models.db.answer import Answer
from src.models.db.post import Post
from src.models.schemas.poll import PollInCreate, PollInResponse
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityAlreadyExists, EntityDoesNotExist, DatabaseError

class PollCRUDRepository(BaseCRUDRepository):
    async def create_poll(self, poll_create: PollInCreate, post_id: int, account_id: int) -> Poll:
        db_account = await self.async_session.get(Account, account_id)
        if not db_account:
            raise EntityDoesNotExist(f"Account with id {account_id} does not exist")

        db_post = await self.async_session.execute(select(Post).where(Post.id == post_id).options(selectinload(Post.poll)))
        db_post = db_post.scalar_one_or_none()
        if not db_post:
            raise EntityDoesNotExist(f"Post with id {post_id} does not exist")

        # Check if the post already has a poll
        if db_post.poll:
            raise EntityAlreadyExists(f"Post with id {post_id} already has a poll")

        # Calculate expiration date based on the input
        now = datetime.datetime.utcnow()
        duration = timedelta(
            days=poll_create.selectedDays,
            hours=poll_create.selectedHour,
            minutes=poll_create.selectedMinute
        )
        expiration_date = now + duration

        # Create poll
        db_poll = Poll(
            post_id=post_id,
            account_id=account_id,
            expiration_date=expiration_date  # Set the expiration date
        )
        self.async_session.add(db_poll)
        await self.async_session.flush()

        # Create answers
        for index, answer_data in enumerate(poll_create.answers):
            db_answer = Answer(poll_id=db_poll.id, text=answer_data.text, answer_index=index+1)
            self.async_session.add(db_answer)

        try:
            await self.async_session.commit()
        except IntegrityError as e:
            await self.async_session.rollback()
            raise DatabaseError(f"Failed to create poll: {e}")
        
        await self.async_session.refresh(db_poll)
        await self.async_session.refresh(db_post, attribute_names=["poll"])

        return db_poll

    async def read_poll(self, poll_id: int) -> Poll:
        db_poll = await self.async_session.get(Poll, poll_id)
        if not db_poll:
            raise EntityDoesNotExist(f"Poll with id {poll_id} does not exist")
        return db_poll

    async def read_polls(self) -> typing.Sequence[Poll]:
        stmt = sqlalchemy.select(Poll)
        result = await self.async_session.execute(stmt)
        polls = result.scalars().all()
        return polls

    async def update_poll(self, poll_id: int, poll_update: PollInCreate) -> Poll:
        db_poll = await self.async_session.get(Poll, poll_id)
        if not db_poll:
            raise EntityDoesNotExist(f"Poll with id {poll_id} does not exist")

        # Calculate new expiration date
        expiration_date = datetime.datetime.utcnow() + datetime.timedelta(
            days=poll_update.selectedDays,
            hours=poll_update.selectedHour,
            minutes=poll_update.selectedMinute
        )
        db_poll.expiration_date = expiration_date

        # Update answers (replace existing answers)
        delete_stmt = delete(Answer).where(Answer.poll_id == poll_id)
        await self.async_session.execute(delete_stmt)
        for answer_data in poll_update.answers:
            db_answer = Answer(poll_id=poll_id, text=answer_data.text)
            self.async_session.add(db_answer)

        await self.async_session.flush()        
        await self.async_session.refresh(db_poll)

        return db_poll

    async def delete_poll(self, poll_id: int) -> None:
        db_poll = await self.async_session.get(Poll, poll_id)
        if not db_poll:
            raise EntityDoesNotExist(f"Poll with id {poll_id} does not exist")

        await self.async_session.delete(db_poll)
