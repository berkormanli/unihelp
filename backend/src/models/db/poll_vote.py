from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.sql.schema import UniqueConstraint

from src.repository.table import Base

class PollVote(Base):
    __tablename__ = "poll_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("account.id", ondelete="CASCADE"), nullable=False)
    answer_index = Column(Integer, nullable=False)  # Index of the selected answer
    
    # Ensure a user can only vote once per poll
    __table_args__ = (
        UniqueConstraint('poll_id', 'user_id', name='unique_user_poll_vote'),
    )