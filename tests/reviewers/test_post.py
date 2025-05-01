import datetime

from fastapi.encoders import jsonable_encoder

from app.schemas.members.reviewer_schema import (
    ReviewerCreateRequestSchema,
    ReviewerRequestSchema,
    ReviewerUpdateRequestSchema,
)

from ..commontest import create_headers
from ..works.test_create_work import USER_WORK


async def test_create_reviewers_ok(
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
        work_id=work_id, email=create_user["email"], review_deadline=datetime.date.today() + datetime.timedelta(days=10)
    )
    new_reviewer_2 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_event_creator["email"],
        review_deadline=datetime.date.today() + datetime.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1, new_reviewer_2])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 201


async def test_create_reviewers_already_exist_reviewer(
    client,
    create_user,
    create_event_creator,
    create_event_from_event_creator,
    create_event_started_with_inscription_from_event_creator,
):
    create_work_1_response = await client.post(
        f"/events/{create_event_from_event_creator}/works",
        json=jsonable_encoder(USER_WORK),
        headers=create_headers(create_event_creator["id"]),
    )
    assert create_work_1_response.status_code == 201
    work_id_1 = create_work_1_response.json()

    new_reviewer_1 = ReviewerRequestSchema(
        work_id=work_id_1,
        email=create_user["email"],
        review_deadline=datetime.date.today() + datetime.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 201

    response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 409


async def test_create_reviewers_by_work_id_invalid(
    client,
    create_user,
    create_event_creator,
    create_event_from_event_creator,
    create_event_started_with_inscription_from_event_creator,
):
    create_work_1_response = await client.post(
        f"/events/{create_event_from_event_creator}/works",
        json=jsonable_encoder(USER_WORK),
        headers=create_headers(create_event_creator["id"]),
    )
    assert create_work_1_response.status_code == 201
    work_id_1 = create_work_1_response.json()

    new_reviewer_1 = ReviewerRequestSchema(
        work_id=work_id_1,
        email=create_user["email"],
        review_deadline=datetime.date.today() + datetime.timedelta(days=10),
    )
    new_reviewer_2 = ReviewerRequestSchema(
        work_id="1365bfdb-b718-411c-9132-ec2abad9fbdd",
        email=create_event_creator["email"],
        review_deadline=datetime.date.today() + datetime.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1, new_reviewer_2])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 404


async def test_create_reviewers_without_permissions(
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
        work_id=work_id, email=create_user["email"], review_deadline=datetime.date.today() + datetime.timedelta(days=10)
    )
    new_reviewer_2 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_event_creator["email"],
        review_deadline=datetime.date.today() + datetime.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1, new_reviewer_2])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_user["id"]),
    )

    assert response.status_code == 403


async def test_update_reviewer_ok(
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
        work_id=work_id, email=create_user["email"], review_deadline=datetime.date.today() + datetime.timedelta(days=10)
    )
    new_reviewer_2 = ReviewerRequestSchema(
        work_id=work_id,
        email=create_event_creator["email"],
        review_deadline=datetime.date.today() + datetime.timedelta(days=10),
    )

    request = ReviewerCreateRequestSchema(reviewers=[new_reviewer_1, new_reviewer_2])

    response = await client.post(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 201

    update_request = ReviewerUpdateRequestSchema(
        user_id=create_user["id"], work_id=work_id, review_deadline=datetime.date.today() + datetime.timedelta(days=15)
    )

    response = await client.put(
        f"/events/{create_event_from_event_creator}/reviewers",
        json=jsonable_encoder(update_request),
        headers=create_headers(create_event_creator["id"]),
    )

    assert response.status_code == 201

    get_response = await client.get(
        f"/events/{create_event_from_event_creator}/reviewers", headers=create_headers(create_event_creator["id"])
    )

    assert get_response.status_code == 200

    reviewers_list = get_response.json()
    assert len(reviewers_list) == 2

    assert reviewers_list[0]["works"][0]["review_deadline"] == update_request.review_deadline.strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    assert reviewers_list[1]["works"][0]["review_deadline"] == new_reviewer_2.review_deadline.strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
