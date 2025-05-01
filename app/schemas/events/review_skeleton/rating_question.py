from typing import Literal

from app.schemas.events.review_skeleton.base_question import BaseQuestion


class RatingQuestion(BaseQuestion):
    type_question: Literal["rating"]
    question: str
    max_value: int


class RatingAnswer(RatingQuestion):
    answer: int
