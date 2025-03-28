from typing import Literal

from app.schemas.events.review_skeleton.base_question import BaseQuestion


class SimpleQuestion(BaseQuestion):
    type_question: Literal["simple_question"]
    question: str


class SimpleAnswer(SimpleQuestion):
    answer: str
