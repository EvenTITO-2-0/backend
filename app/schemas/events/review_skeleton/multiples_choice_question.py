from typing import Literal

from pydantic import Field, model_validator
from typing_extensions import Self

from app.schemas.events.review_skeleton.base_question import BaseQuestion


class MultipleChoiceQuestion(BaseQuestion):
    type_question: Literal["multiple_choice"]
    question: str
    options: list[str] = Field(
        examples=[["first answer", "second answer", "third answer"]], min_length=2, max_length=20
    )
    more_than_one_answer_allowed: bool = False


class MultipleChoiceAnswer(MultipleChoiceQuestion):
    answer: list[str] = Field(examples=[["first answer", "second answer"]])

    @model_validator(mode="after")
    def check_answer(self) -> Self:
        if not self.more_than_one_answer_allowed and len(self.answer) > 1:
            raise ValueError("Only one answer allowed")
        if not all(answer in self.options for answer in self.answer):
            raise ValueError("All answer should be contained in options")
        return self
