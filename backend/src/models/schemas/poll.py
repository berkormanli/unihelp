import datetime
from typing import List
from src.models.schemas.base import BaseSchemaModel
from src.models.schemas.post import PostInCreate


class AnswerBase(BaseSchemaModel):
    text: str

class AnswerInResponse(AnswerBase):
    id: int
    is_selected: bool = False
    
class PollDataBase(BaseSchemaModel):
    votes: int = 0
    answers: List[AnswerBase]
    selectedDays: int | None = None
    selectedHour: int | None = None
    selectedMinute: int | None = None

class PollInCreate(PostInCreate):
    answers: List[AnswerBase]
    selectedDays: int | None = None
    selectedHour: int | None = None
    selectedMinute: int | None = None

class PollInResponse(BaseSchemaModel):
    id: int
    post_id: int
    account_id: int
    answers: List[AnswerBase]
    expiration_date: datetime.datetime | None = None
    voted: bool = False
    selected_answer_id: int | None = None  # To track which answer the user selected