from sqlalchemy import func, select
from src.models.db.poll_vote import PollVote
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityAlreadyExists

class PollVoteCRUDRepository(BaseCRUDRepository):
    async def create_vote(self, poll_id: int, user_id: int, answer_index: int) -> PollVote:
        existing_vote = await self.get_user_vote(poll_id, user_id)
        if existing_vote:
            raise EntityAlreadyExists(f"User with id {user_id} has already voted on poll with id {poll_id}")

        vote = PollVote(
            poll_id=poll_id,
            user_id=user_id,
            answer_index=answer_index
        )
        #    raise EntityAlreadyExists(f"Post with id {post_id} already has a poll")
        self.async_session.add(vote)
        await self.async_session.commit()
        return vote

    async def get_user_vote(self, poll_id: int, user_id: int) -> PollVote | None:
        stmt = select(PollVote).where(
            PollVote.poll_id == poll_id,
            PollVote.user_id == user_id
        )
        result = await self.async_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_poll_votes_detail(self, poll_id: int) -> list[PollVote]:
        stmt = select(PollVote).where(PollVote.poll_id == poll_id)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()
    
    async def get_poll_vote_count(self, poll_id: int, answer_index: int) -> int:
        stmt = select(func.count()).where(
            PollVote.poll_id == poll_id,
            PollVote.answer_index == answer_index
        )
        result = await self.async_session.execute(stmt)
        return result.scalar_one_or_none() or 0