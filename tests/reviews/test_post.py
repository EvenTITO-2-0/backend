import datetime as datetime_library
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from freezegun import freeze_time

from app.database.models.inscription import InscriptionRole
from app.database.models.work import WorkStates
from app.schemas.events.review_skeleton.simple_question import SimpleAnswer
from app.schemas.events.schemas import DynamicTracksEventSchema
from app.schemas.inscriptions.inscription import InscriptionRequestSchema
from app.schemas.members.reviewer_schema import ReviewerCreateRequestSchema, ReviewerRequestSchema
from app.schemas.users.user import UserSchema
from app.schemas.works.review import ReviewAnswer, ReviewCreateRequestSchema, ReviewDecision, ReviewPublishSchema

from ..commontest import create_headers
from ..works.test_create_work import USER_WORK


async def test_create_review_error_after_work_deadline(
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
    new_reviewer_1 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_user["email"],
        review_deadline=datetime.now() + datetime_library.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    answer = ReviewAnswer(
        answers=[SimpleAnswer(question="Comentarios", answer="Muy buen trabajo.", type_question="simple_question")]
    )
    review = ReviewCreateRequestSchema(status=ReviewDecision.APPROVED, review=answer)
    with freeze_time(datetime.now() + datetime_library.timedelta(days=30)):
        create_review_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review),
            headers=create_headers(create_user["id"]),
        )

    assert create_review_response.status_code == 409


async def test_create_review_error_work_has_no_submissions(
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

    new_reviewer = ReviewerRequestSchema(
        work_id=work_id,
        email=create_user["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    answer = ReviewAnswer(
        answers=[SimpleAnswer(question="Comentarios", answer="Muy buen trabajo.", type_question="simple_question")]
    )
    review = ReviewCreateRequestSchema(status=ReviewDecision.APPROVED, review=answer)
    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        create_review_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review),
            headers=create_headers(create_user["id"]),
        )

    assert create_review_response.status_code == 404


async def test_create_review_ok(
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
    assert submission_response.status_code == 201

    new_reviewer = ReviewerRequestSchema(
        work_id=work_id,
        email=create_user["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    answer = ReviewAnswer(
        answers=[SimpleAnswer(question="Comentarios", answer="Muy buen trabajo.", type_question="simple_question")]
    )
    review = ReviewCreateRequestSchema(status=ReviewDecision.APPROVED, review=answer)
    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        create_review_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review),
            headers=create_headers(create_user["id"]),
        )

    assert create_review_response.status_code == 201
    assert create_review_response.json()["upload_url"]["upload_url"] == "mocked-url-upload"
    assert create_review_response.json()["event_id"] == create_event_from_event_creator
    assert create_review_response.json()["work_id"] == work_id
    assert create_review_response.json()["reviewer_id"] == create_user["id"]
    assert len(create_review_response.json()["review"]["answers"]) == 1
    assert create_review_response.json()["review"]["answers"][0]["question"] == "Comentarios"
    assert create_review_response.json()["review"]["answers"][0]["answer"] == "Muy buen trabajo."
    assert create_review_response.json()["review"]["answers"][0]["type_question"] == "simple_question"
    assert create_review_response.json()["status"] == ReviewDecision.APPROVED


async def test_create_review_duplicate_error(
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
    assert submission_response.status_code == 201

    new_reviewer = ReviewerRequestSchema(
        work_id=work_id,
        email=create_user["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    answer = ReviewAnswer(
        answers=[SimpleAnswer(question="Comentarios", answer="Muy buen trabajo.", type_question="simple_question")]
    )
    review = ReviewCreateRequestSchema(status=ReviewDecision.APPROVED, review=answer)
    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        create_review_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review),
            headers=create_headers(create_user["id"]),
        )
        create_review_response2 = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review),
            headers=create_headers(create_user["id"]),
        )
    assert create_review_response.status_code == 201
    assert create_review_response2.status_code == 409


async def test_update_review_ok(
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
    assert submission_response.status_code == 201

    new_reviewer = ReviewerRequestSchema(
        work_id=work_id,
        email=create_user["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    answer = ReviewAnswer(
        answers=[
            SimpleAnswer(
                question="Comentarios",
                answer="Mejorar desarrollo, es demasiado técnico y difícil de leer. Revisar ortografía.",
                type_question="simple_question",
            )
        ]
    )
    review = ReviewCreateRequestSchema(status=ReviewDecision.NOT_APPROVED, review=answer)
    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        create_review_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review),
            headers=create_headers(create_user["id"]),
        )

        assert create_review_response.status_code == 201
        create_review = create_review_response.json()
        assert create_review["upload_url"]["upload_url"] == "mocked-url-upload"
        assert create_review["event_id"] == create_event_from_event_creator
        assert create_review["work_id"] == work_id
        assert create_review["reviewer_id"] == create_user["id"]
        assert len(create_review["review"]["answers"]) == 1
        assert create_review["review"]["answers"][0]["question"] == "Comentarios"
        assert (
            create_review["review"]["answers"][0]["answer"]
            == "Mejorar desarrollo, es demasiado técnico y difícil de leer. Revisar ortografía."
        )
        assert create_review["review"]["answers"][0]["type_question"] == "simple_question"
        assert create_review["status"] == ReviewDecision.NOT_APPROVED

        new_answer = ReviewAnswer(
            answers=[
                SimpleAnswer(
                    question="Comentarios", answer="Bien las correcciones. Aprobado", type_question="simple_question"
                )
            ]
        )
        new_review = ReviewCreateRequestSchema(status=ReviewDecision.APPROVED, review=new_answer)
        update_review_response = await client.put(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/{create_review['id']}",
            json=jsonable_encoder(new_review),
            headers=create_headers(create_user["id"]),
        )

    assert update_review_response.status_code == 201


async def test_publish_reviews_ok(
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

    work_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}", headers=create_headers(create_user["id"])
    )

    work_get = work_response.json()
    assert work_response.status_code == 200
    assert work_get["title"] == USER_WORK.title
    assert work_get["id"] == work_id
    assert work_get["state"] == WorkStates.SUBMITTED

    submission_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/submissions/latest",
        headers=create_headers(create_event_creator["id"]),
    )

    assert submission_response.status_code == 200, f"response error: {submission_response.json()}"
    assert submission_response.json()["state"] == WorkStates.SUBMITTED

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

    work_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}", headers=create_headers(create_event_creator["id"])
    )

    work_get = work_response.json()
    assert work_response.status_code == 200
    assert work_get["title"] == USER_WORK.title
    assert work_get["id"] == work_id
    assert work_get["state"] == WorkStates.RE_SUBMIT

    response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/submissions/latest",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 200, f"response error: {response.json()}"
    assert response.json()["state"] == WorkStates.RE_SUBMIT


async def test_publish_reviews_ok_work_track_chair(
    client,
    create_user,
    create_event_creator,
    create_event_from_event_creator,
    create_event_started_with_inscription_from_event_creator,
    create_event_chair,
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

    new_reviewer = ReviewerRequestSchema(
        work_id=work_id,
        email=create_event_creator["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=7),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        answer = ReviewAnswer(
            answers=[
                SimpleAnswer(
                    question="Comentarios",
                    answer="Mejorar desarrollo, es demasiado técnico y difícil de leer. Revisar ortografía.",
                    type_question="simple_question",
                )
            ]
        )

        review = ReviewCreateRequestSchema(status=ReviewDecision.NOT_APPROVED, review=answer)

        create_review_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review),
            headers=create_headers(create_event_creator["id"]),
        )

        assert create_review_response.status_code == 201

    get_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
        headers=create_headers(create_event_creator["id"]),
    )

    assert get_response.status_code == 200
    reviews = get_response.json()
    assert len(reviews) == 1

    add_tracks_request = DynamicTracksEventSchema(
        tracks=["chemistry"],
    )
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204

    publish_request = ReviewPublishSchema(
        reviews_to_publish=[create_review_response.json()["id"]],
        new_work_status=WorkStates.RE_SUBMIT,
        resend_deadline=datetime.now() + datetime_library.timedelta(days=15),
    )

    publish_response = await client.post(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/publish",
        json=jsonable_encoder(publish_request),
        headers=create_headers(create_event_chair),
    )

    assert publish_response.status_code == 201


async def test_publish_reviews_is_chair_but_not_in_work_track(
    client,
    create_user,
    create_event_creator,
    create_event_from_event_creator,
    create_event_started_with_inscription_from_event_creator,
    create_event_chair,
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

    new_reviewer = ReviewerRequestSchema(
        work_id=work_id,
        email=create_event_creator["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=7),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        answer = ReviewAnswer(
            answers=[
                SimpleAnswer(
                    question="Comentarios",
                    answer="Mejorar desarrollo, es demasiado técnico y difícil de leer. Revisar ortografía.",
                    type_question="simple_question",
                )
            ]
        )

        review = ReviewCreateRequestSchema(status=ReviewDecision.NOT_APPROVED, review=answer)

        create_review_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review),
            headers=create_headers(create_event_creator["id"]),
        )

        assert create_review_response.status_code == 201

    get_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
        headers=create_headers(create_event_creator["id"]),
    )

    assert get_response.status_code == 200
    reviews = get_response.json()
    assert len(reviews) == 1

    add_tracks_request = DynamicTracksEventSchema(
        tracks=["math"],
    )
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204

    publish_request = ReviewPublishSchema(
        reviews_to_publish=[create_review_response.json()["id"]],
        new_work_status=WorkStates.RE_SUBMIT,
        resend_deadline=datetime.now() + datetime_library.timedelta(days=15),
    )

    publish_response = await client.post(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/publish",
        json=jsonable_encoder(publish_request),
        headers=create_headers(create_event_chair),
    )

    assert publish_response.status_code == 403


async def test_publish_reviews_not_is_organizer_or_work_track(
    client,
    create_user,
    create_event_creator,
    create_event_from_event_creator,
    create_event_started_with_inscription_from_event_creator,
    create_event_chair,
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

    new_reviewer = ReviewerRequestSchema(
        work_id=work_id,
        email=create_event_creator["email"],
        review_deadline=datetime_library.date.today() + datetime_library.timedelta(days=7),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer])

    reviewer_response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert reviewer_response.status_code == 201

    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        answer = ReviewAnswer(
            answers=[
                SimpleAnswer(
                    question="Comentarios",
                    answer="Mejorar desarrollo, es demasiado técnico y difícil de leer. Revisar ortografía.",
                    type_question="simple_question",
                )
            ]
        )

        review = ReviewCreateRequestSchema(status=ReviewDecision.NOT_APPROVED, review=answer)

        create_review_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review),
            headers=create_headers(create_event_creator["id"]),
        )

        assert create_review_response.status_code == 201

    get_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
        headers=create_headers(create_event_creator["id"]),
    )

    assert get_response.status_code == 200
    reviews = get_response.json()
    assert len(reviews) == 1

    add_tracks_request = DynamicTracksEventSchema(
        tracks=["chemistry"],
    )
    response = await client.put(
        f"/events/{create_event_from_event_creator}/chairs/{create_event_chair}/tracks",
        json=jsonable_encoder(add_tracks_request),
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.status_code == 204

    publish_request = ReviewPublishSchema(
        reviews_to_publish=[create_review_response.json()["id"]],
        new_work_status=WorkStates.RE_SUBMIT,
        resend_deadline=datetime.now() + datetime_library.timedelta(days=15),
    )

    publish_response = await client.post(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/publish",
        json=jsonable_encoder(publish_request),
        headers=create_headers(user_author_id),
    )

    assert publish_response.status_code == 403


async def test_publish_reviews_empty_list(
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

    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        create_review_1_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review_1),
            headers=create_headers(create_user["id"]),
        )

        assert create_review_1_response.status_code == 201, create_review_1_response.json()

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
        reviews_to_publish=[],
        new_work_status=WorkStates.RE_SUBMIT,
        resend_deadline=datetime.now() + datetime_library.timedelta(days=15),
    )

    publish_response = await client.post(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/publish",
        json=jsonable_encoder(publish_request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert publish_response.status_code == 409


async def test_publish_reviews_from_other_work_id(
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

    new_work = USER_WORK.model_copy()
    new_work.title = "new work title"

    create_other_work_response = await client.post(
        f"/events/{create_event_from_event_creator}/works",
        json=jsonable_encoder(new_work),
        headers=create_headers(user_author_id),
    )
    assert create_other_work_response.status_code == 201

    other_work_id = create_other_work_response.json()

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

    with freeze_time(datetime.now() + datetime_library.timedelta(days=3)):
        create_review_1_response = await client.post(
            f"/events/{create_event_from_event_creator}/works/{work_id}/reviews",
            json=jsonable_encoder(review_1),
            headers=create_headers(create_user["id"]),
        )

        assert create_review_1_response.status_code == 201, create_review_1_response.json()

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
        f"/events/{create_event_from_event_creator}/works/{other_work_id}/reviews/publish",
        json=jsonable_encoder(publish_request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert publish_response.status_code == 409


async def test_publish_reviews_approved_ok(
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

    work_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}", headers=create_headers(create_user["id"])
    )

    work_get = work_response.json()
    assert work_response.status_code == 200
    assert work_get["title"] == USER_WORK.title
    assert work_get["id"] == work_id
    assert work_get["state"] == WorkStates.SUBMITTED

    submission_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/submissions/latest",
        headers=create_headers(create_event_creator["id"]),
    )

    assert submission_response.status_code == 200, f"response error: {submission_response.json()}"
    assert submission_response.json()["state"] == WorkStates.SUBMITTED

    publish_request = ReviewPublishSchema(
        reviews_to_publish=[create_review_2_response.json()["id"]], new_work_status=WorkStates.APPROVED
    )

    publish_response = await client.post(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/publish",
        json=jsonable_encoder(publish_request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert publish_response.status_code == 201

    work_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}", headers=create_headers(create_event_creator["id"])
    )

    work_get = work_response.json()
    assert work_response.status_code == 200
    assert work_get["title"] == USER_WORK.title
    assert work_get["id"] == work_id
    assert work_get["state"] == WorkStates.APPROVED

    response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/submissions/latest",
        headers=create_headers(create_event_creator["id"]),
    )
    # assert response.status_code == 200, f'response error: {response.json()}'
    assert response.json()["state"] == WorkStates.APPROVED
    print(f"test! {response.json}")


async def test_publish_reviews_rejected(
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
        answers=[SimpleAnswer(question="Comentarios", answer="Mal trabajo.", type_question="simple_question")]
    )
    review_1 = ReviewCreateRequestSchema(status=ReviewDecision.NOT_APPROVED, review=answer_1)

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

    work_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}", headers=create_headers(create_user["id"])
    )

    work_get = work_response.json()
    assert work_response.status_code == 200
    assert work_get["title"] == USER_WORK.title
    assert work_get["id"] == work_id
    assert work_get["state"] == WorkStates.SUBMITTED

    submission_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/submissions/latest",
        headers=create_headers(create_event_creator["id"]),
    )

    assert submission_response.status_code == 200, f"response error: {submission_response.json()}"
    assert submission_response.json()["state"] == WorkStates.SUBMITTED

    publish_request = ReviewPublishSchema(
        reviews_to_publish=[create_review_2_response.json()["id"]], new_work_status=WorkStates.REJECTED
    )

    publish_response = await client.post(
        f"/events/{create_event_from_event_creator}/works/{work_id}/reviews/publish",
        json=jsonable_encoder(publish_request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert publish_response.status_code == 201

    work_response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}", headers=create_headers(create_event_creator["id"])
    )

    work_get = work_response.json()
    assert work_response.status_code == 200
    assert work_get["title"] == USER_WORK.title
    assert work_get["id"] == work_id
    assert work_get["state"] == WorkStates.REJECTED

    response = await client.get(
        f"/events/{create_event_from_event_creator}/works/{work_id}/submissions/latest",
        headers=create_headers(create_event_creator["id"]),
    )
    assert response.json()["state"] == WorkStates.REJECTED
    print(f"test! {response.json}")
