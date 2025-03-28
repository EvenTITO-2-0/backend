from fastapi.encoders import jsonable_encoder

from app.schemas.events.review_skeleton.multiples_choice_question import MultipleChoiceQuestion
from app.schemas.events.review_skeleton.rating_question import RatingQuestion
from app.schemas.events.review_skeleton.review_skeleton import ReviewSkeletonQuestions, ReviewSkeletonRequestSchema
from app.schemas.events.review_skeleton.simple_question import SimpleQuestion

from ..commontest import create_headers


async def test_put_review_skeleton(client, admin_data, create_event):
    first_question = "This is a simple question that has a str answer"
    review_skeleton = ReviewSkeletonRequestSchema(
        review_skeleton=ReviewSkeletonQuestions(
            questions=[
                SimpleQuestion(type_question="simple_question", question=first_question),
                MultipleChoiceQuestion(
                    type_question="multiple_choice",
                    question="This is the question",
                    options=["first answer", "second answer", "third answer"],
                    more_than_one_answer_allowed=False,
                ),
                RatingQuestion(type_question="rating", question="Max Points", max_value=10),
            ]
        )
    )
    response = await client.put(
        f"/events/{create_event['id']}/configuration/review-skeleton",
        json=jsonable_encoder(review_skeleton),
        headers=create_headers(admin_data.id),
    )
    assert response.status_code == 204

    response = await client.get(
        f"/events/{create_event['id']}/configuration/review-skeleton", headers=create_headers(admin_data.id)
    )

    assert response.status_code == 200
    assert response.json()["review_skeleton"]["questions"][0]["question"] == first_question
    assert response.json()["review_skeleton"]["recommendation"] is not None
    assert response.json()["review_skeleton"]["recommendation"]["question"] == "Recomendación"
    assert response.json()["review_skeleton"]["recommendation"]["type_question"] == "multiple_choice"
    assert response.json()["review_skeleton"]["recommendation"]["more_than_one_answer_allowed"] is False
