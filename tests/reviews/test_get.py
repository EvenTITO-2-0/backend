import datetime as datetime_library
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from freezegun import freeze_time

from app.database.models.inscription import InscriptionRole
from app.database.models.work import WorkStates
from app.schemas.events.review_skeleton.simple_question import SimpleAnswer
from app.schemas.inscriptions.inscription import InscriptionRequestSchema
from app.schemas.members.reviewer_schema import ReviewerCreateRequestSchema, ReviewerRequestSchema
from app.schemas.users.user import UserSchema
from app.schemas.works.review import ReviewAnswer, ReviewCreateRequestSchema, ReviewDecision, ReviewPublishSchema

from ..commontest import create_headers
from ..works.test_create_work import USER_WORK


async def test_get_reviews_ok(
    client,
    create_user,
    create_event_creator,
    create_event_from_event_creator,
    create_event_started_with_inscription_from_event_creator,
):
    create_work_response = await client.post(
        f"/events/{create_event_from_event_creator}/works",
        json=jsonable_encoder(USER_WORK),
        headers=create_headers(create_event_creator["id"]),
    )
    assert create_work_response.status_code == 201

    work_id = create_work_response.json()

    submission_response = await client.put(
        f"/events/{create_event_from_event_creator}/works/{work_id}/submissions/submit",
        headers=create_headers(create_event_creator["id"]),
    )
    submission_id = submission_response.json()["id"]
    assert submission_response.status_code == 201

    other_user_id = "paoksncaokasdasdl12345678901"
    other_create_user = UserSchema(name="Angel", lastname="Di Maria", email="a.dimaria@email.com")

    await client.post("/users", json=jsonable_encoder(other_create_user), headers=create_headers(other_user_id))

    new_reviewer_1 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_user["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=10),
    )

    new_reviewer_2 = ReviewerRequestSchema(
        work_id=work_id,
        email=other_create_user.email,
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=7),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1, new_reviewer_2])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    answer_1 = ReviewAnswer(
        answers=[SimpleAnswer(question="Comentarios", answer="Muy buen trabajo.", type_question="simple_question")]
    )
    review_1 = ReviewCreateRequestSchema(status=ReviewDecision.APPROVED, review=answer_1)

    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        create_review_1_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review_1),
            headers=create_headers(create_user["id"]),
        )

        assert create_review_1_response.status_code == 201, create_review_1_response.json()

        answer_2 = ReviewAnswer(
            answers=[
                SimpleAnswer(
                    question="Comentarios",
                    answer="Mejorar desarrollo, es demasiado técnico y difícil de leer. Revisar ortografía.",
                    type_question="simple_question",
                )
            ]
        )

        review_2 = ReviewCreateRequestSchema(status=ReviewDecision.NOT_APPROVED, review=answer_2)

        create_review_2_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review_2),
            headers=create_headers(other_user_id),
        )

        assert create_review_2_response.status_code == 201

    get_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
        headers=create_headers(create_event_creator["id"]),
    )

    assert get_response.status_code == 200
    reviews = get_response.json()
    assert len(reviews) == 2

    assert reviews[0]["event_id"] == create_event_from_event_creator
    assert reviews[0]["work_id"] == work_id
    assert reviews[0]["reviewer_id"] == create_user["id"]
    assert reviews[0]["submission_id"] == submission_id
    assert reviews[0]["status"] == ReviewDecision.APPROVED
    assert len(reviews[0]["review"]["answers"]) == 1
    assert reviews[0]["review"]["answers"][0]["question"] == "Comentarios"
    assert reviews[0]["review"]["answers"][0]["answer"] == "Muy buen trabajo."
    assert reviews[0]["review"]["answers"][0]["type_question"] == "simple_question"
    reviewer = reviews[0]["reviewer"]
    assert reviewer["name"] == create_user["name"]
    assert reviewer["lastname"] == create_user["lastname"]
    assert reviewer["email"] == create_user["email"]

    assert reviews[1]["event_id"] == create_event_from_event_creator
    assert reviews[1]["work_id"] == work_id
    assert reviews[1]["reviewer_id"] == other_user_id
    assert reviews[1]["submission_id"] == submission_id
    assert reviews[1]["status"] == ReviewDecision.NOT_APPROVED
    assert len(reviews[1]["review"]["answers"]) == 1
    assert reviews[1]["review"]["answers"][0]["question"] == "Comentarios"
    assert (
        reviews[1]["review"]["answers"][0]["answer"]
        == "Mejorar desarrollo, es demasiado técnico y difícil de leer. Revisar ortografía."
    )
    assert reviews[1]["review"]["answers"][0]["type_question"] == "simple_question"
    reviewer = reviews[1]["reviewer"]
    assert reviewer["name"] == other_create_user.name
    assert reviewer["lastname"] == other_create_user.lastname
    assert reviewer["email"] == other_create_user.email


async def test_get_my_work_reviews_ok(
    client,
    create_user,
    create_event_creator,
    create_event_from_event_creator,
    create_event_started_with_inscription_from_event_creator,
):
    user_author_id = "paoksncaokasdasdl12345678901"
    user_author = UserSchema(name="Angel", lastname="Di Maria", email="a.dimaria@email.com")

    await client.post("/users", json=jsonable_encoder(user_author), headers=create_headers(user_author_id))

    new_inscription = InscriptionRequestSchema(roles=[InscriptionRole.SPEAKER])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/inscriptions",
        headers=create_headers(user_author_id),
        json=jsonable_encoder(new_inscription),
    )
    assert response.status_code == 201, response.json()

    create_work_response = await client.post(
        f"/events/{create_event_from_event_creator}/works",
        json=jsonable_encoder(USER_WORK),
        headers=create_headers(user_author_id),
    )
    assert create_work_response.status_code == 201

    work_id = create_work_response.json()

    submission_response = await client.put(
        f"/events/{create_event_from_event_creator}/works/{work_id}/submissions/submit",
        headers=create_headers(user_author_id),
    )

    assert submission_response.status_code == 201
    submission_id = submission_response.json()["id"]

    new_reviewer_1 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_user["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=10),
    )

    new_reviewer_2 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_event_creator["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=7),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1, new_reviewer_2])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    answer_1 = ReviewAnswer(
        answers=[
            SimpleAnswer(
                question="Comentarios", answer="Muy buen trabajo.", type_question="simple_question", is_public=True
            )
        ]
    )
    review_1 = ReviewCreateRequestSchema(status=ReviewDecision.APPROVED, review=answer_1)

    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        create_review_1_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review_1),
            headers=create_headers(create_user["id"]),
        )

        assert create_review_1_response.status_code == 201, create_review_1_response.json()

        answer_2 = ReviewAnswer(
            answers=[
                SimpleAnswer(
                    question="Comentarios",
                    answer="Mejorar desarrollo, es demasiado técnico y difícil de leer. Revisar ortografía.",
                    type_question="simple_question",
                ),
                SimpleAnswer(
                    question="Comentarios 2", answer="Mejorar", type_question="simple_question", is_public=True
                ),
            ]
        )

        review_2 = ReviewCreateRequestSchema(status=ReviewDecision.NOT_APPROVED, review=answer_2)

        create_review_2_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review_2),
            headers=create_headers(create_event_creator["id"]),
        )

        assert create_review_2_response.status_code == 201

    get_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
        headers=create_headers(create_event_creator["id"]),
    )

    assert get_response.status_code == 200
    reviews = get_response.json()
    assert len(reviews) == 2

    publish_request = ReviewPublishSchema(
        reviews_to_publish=[create_review_2_response.json()["id"]],
        new_work_status=WorkStates.RE_SUBMIT,
        resend_deadline=datetime.now() + datetime_library.timedelta(days=15),
    )

    publish_response = await client.post(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/publish",
        json=jsonable_encoder(publish_request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert publish_response.status_code == 201

    get_my_work_reviews_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/my-work-reviews",
        headers=create_headers(user_author_id),
    )

    assert get_my_work_reviews_response.status_code == 200
    my_work_reviews = get_my_work_reviews_response.json()
    assert len(my_work_reviews) == 1

    assert my_work_reviews[0]["event_id"] == create_event_from_event_creator
    assert my_work_reviews[0]["work_id"] == work_id
    assert my_work_reviews[0]["submission_id"] == submission_id
    assert my_work_reviews[0]["status"] == ReviewDecision.NOT_APPROVED
    assert my_work_reviews[0]["reviewer_id"] == create_event_creator["id"]
    assert len(my_work_reviews[0]["review"]["answers"]) == 1
    assert my_work_reviews[0]["review"]["answers"][0]["question"] == "Comentarios 2"
    assert my_work_reviews[0]["review"]["answers"][0]["answer"] == "Mejorar"
    assert my_work_reviews[0]["review"]["answers"][0]["type_question"] == "simple_question"


async def test_get_my_work_reviews_nothing_shared(
    client,
    create_user,
    create_event_creator,
    create_event_from_event_creator,
    create_event_started_with_inscription_from_event_creator,
):
    user_author_id = "paoksncaokasdasdl12345678901"
    user_author = UserSchema(name="Angel", lastname="Di Maria", email="a.dimaria@email.com")

    await client.post("/users", json=jsonable_encoder(user_author), headers=create_headers(user_author_id))

    new_inscription = InscriptionRequestSchema(roles=[InscriptionRole.SPEAKER])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/inscriptions",
        headers=create_headers(user_author_id),
        json=jsonable_encoder(new_inscription),
    )
    assert response.status_code == 201, response.json()

    create_work_response = await client.post(
        f"/events/{create_event_from_event_creator}/works",
        json=jsonable_encoder(USER_WORK),
        headers=create_headers(user_author_id),
    )
    assert create_work_response.status_code == 201

    work_id = create_work_response.json()

    submission_response = await client.put(
        f"/events/{create_event_from_event_creator}/works/{work_id}/submissions/submit",
        headers=create_headers(user_author_id),
    )

    assert submission_response.status_code == 201

    new_reviewer_1 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_user["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=10),
    )

    new_reviewer_2 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_event_creator["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=7),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1, new_reviewer_2])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    answer_1 = ReviewAnswer(
        answers=[SimpleAnswer(question="Comentarios", answer="Muy buen trabajo.", type_question="simple_question")]
    )
    review_1 = ReviewCreateRequestSchema(status=ReviewDecision.APPROVED, review=answer_1)

    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        create_review_1_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review_1),
            headers=create_headers(create_user["id"]),
        )

        assert create_review_1_response.status_code == 201, create_review_1_response.json()

        answer_2 = ReviewAnswer(
            answers=[
                SimpleAnswer(
                    question="Comentarios",
                    answer="Mejorar desarrollo, es demasiado técnico y difícil de leer. Revisar ortografía.",
                    type_question="simple_question",
                )
            ]
        )

        review_2 = ReviewCreateRequestSchema(status=ReviewDecision.NOT_APPROVED, review=answer_2)

        create_review_2_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review_2),
            headers=create_headers(create_event_creator["id"]),
        )

        assert create_review_2_response.status_code == 201

    get_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
        headers=create_headers(create_event_creator["id"]),
    )

    assert get_response.status_code == 200
    reviews = get_response.json()
    assert len(reviews) == 2

    get_my_work_reviews_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/my-work-reviews",
        headers=create_headers(user_author_id),
    )

    assert get_my_work_reviews_response.status_code == 200
    my_work_reviews = get_my_work_reviews_response.json()
    assert len(my_work_reviews) == 0


async def test_get_my_work_reviews_non_author(
    client, create_user, create_event_from_event_creator, create_event_started_with_inscription_from_event_creator
):
    user_author_id = "paoksncaokasdasdl12345678901"
    user_author = UserSchema(name="Angel", lastname="Di Maria", email="a.dimaria@email.com")

    await client.post("/users", json=jsonable_encoder(user_author), headers=create_headers(user_author_id))

    new_inscription = InscriptionRequestSchema(roles=[InscriptionRole.SPEAKER])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/inscriptions",
        headers=create_headers(user_author_id),
        json=jsonable_encoder(new_inscription),
    )
    assert response.status_code == 201, response.json()

    create_work_response = await client.post(
        f"/events/{create_event_from_event_creator}/works",
        json=jsonable_encoder(USER_WORK),
        headers=create_headers(user_author_id),
    )
    assert create_work_response.status_code == 201

    work_id = create_work_response.json()

    get_my_work_reviews_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/my-work-reviews",
        headers=create_headers(create_user["id"]),
    )

    assert get_my_work_reviews_response.status_code == 403
