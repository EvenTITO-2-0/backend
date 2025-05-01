from typing import Union

from pydantic import BaseModel, Field

from app.schemas.events.review_skeleton.multiples_choice_question import MultipleChoiceQuestion
from app.schemas.events.review_skeleton.rating_question import RatingQuestion
from app.schemas.events.review_skeleton.simple_question import SimpleQuestion


class ReviewSkeletonQuestions(BaseModel):
    questions: list[Union[MultipleChoiceQuestion, SimpleQuestion, RatingQuestion]] = Field(default_factory=list)


class ReviewSkeletonQuestionsAndRecommendation(ReviewSkeletonQuestions):
    recommendation: MultipleChoiceQuestion = Field(
        default=MultipleChoiceQuestion(
            question="Recomendación",
            options=["Aprobado", "Desaprobado", "A revisar"],
            type_question="multiple_choice",
            more_than_one_answer_allowed=False,
        )
    )


class ReviewSkeletonResponseSchema(BaseModel):
    review_skeleton: ReviewSkeletonQuestionsAndRecommendation = Field(
        default=ReviewSkeletonQuestionsAndRecommendation()
    )


class ReviewSkeletonRequestSchema(BaseModel):
    review_skeleton: ReviewSkeletonQuestions = Field(default=ReviewSkeletonQuestions())
